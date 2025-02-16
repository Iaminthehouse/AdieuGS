# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import multiprocessing as mp
import tempfile
import time
from argparse import ArgumentParser
from functools import partial
from multiprocessing import cpu_count, Pool, Process

import torch
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader

import cv2
import numpy as np
from tqdm import tqdm

from adhoc_image_dataset import AdhocImageDataset
from worker_pool import WorkerPool


torchvision.disable_beta_transforms_warning()

timings = {}
#BATCH_SIZE = 32
BATCH_SIZE = 8

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)  # Windows-Multiprocessing sichern

def run_inference_model(
    checkpoint: str,
    input_path: str,
    output_root: str = None,
    seg_dir: str = None,
    device: str = "cuda:0",
    batch_size: int = 8,
    shape=(1024, 768),
    fp16: bool = False,
    callback=None
):
    """
    Lädt ein Modell und führt die Inferenz durch.
    Anstelle von argparse kannst du diese Funktion direkt 
    aus deinem UI-Code aufrufen, z.B.:

        run_inference_model(
            checkpoint="model_torchscript.pt",
            input_path="my_images/",
            output_root="results/",
            ...
        )

    :param checkpoint: Pfad zum Checkpoint (.pt / .pt2 / TorchScript)
    :param input_path: Ordner mit Bildern oder .txt mit Bildpfaden
    :param output_root: Ausgabeverzeichnis
    :param seg_dir: Pfad für Segmentations (falls benötigt)
    :param device: PyTorch-Gerät, z.B. "cuda:0" oder "cpu"
    :param batch_size: Batch-Größe
    :param shape: Tuple (H, W) oder (H,) für Inputgröße
    :param fp16: True = Benutze Halbfloating / BF16
    """

    # --- 1) Input-Shape festlegen ---
    if isinstance(shape, (list, tuple)):
        if len(shape) == 1:
            input_shape = (3, shape[0], shape[0])
        elif len(shape) == 2:
            input_shape = (3,) + tuple(shape)
        else:
            raise ValueError("Ungültige input shape, erwarte 1D/2D (z.B. [768] oder [1024,768]).")
    else:
        raise ValueError("Parameter 'shape' muss list oder tuple sein.")
    
    # --- 2) Logging + Torch-Inductor Config (optional) ---
    mp.log_to_stderr()
    torch._inductor.config.force_fuse_int_mm_with_mul = True
    torch._inductor.config.use_mixed_mm = True

    start_time = time.time()
    
    # --- 3) Modell laden ---
    USE_TORCHSCRIPT = "_torchscript" in checkpoint
    exp_model = load_model(checkpoint, USE_TORCHSCRIPT)

   
    # --- 4) Model auf dtype & device einstellen ---
    if not USE_TORCHSCRIPT:
        # -> Normaler PyTorch-Checkpoint
        # wähle float16 oder bfloat16
        dtype = torch.half if fp16 else torch.bfloat16
        exp_model.to(dtype)
        # Kompilieren (PyTorch 2.x + CUDA)
        exp_model = torch.compile(exp_model, mode="max-autotune", fullgraph=True)
    else:
        # -> TorchScript-Modell
        dtype = torch.float32
        exp_model = exp_model.to(device)
    
    # --- 5) Input ermitteln: Ordner oder Textdatei ---
    image_names = []
    if os.path.isdir(input_path):
        # Pfad ist ein Verzeichnis
        input_dir = input_path
        # Liste aller Bilddateien
        image_names = [
            f for f in sorted(os.listdir(input_dir))
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ]
        if callback:
            callback(f"🖼️ Found {len(image_names)} images in input directory.")
    elif os.path.isfile(input_path) and input_path.endswith(".txt"):
        # Pfad ist eine .txt-Datei
        with open(input_path, "r") as file:
            image_paths = [line.strip() for line in file if line.strip()]
        image_names = [os.path.basename(p) for p in image_paths]
        # Ordner = Verzeichnis der ersten Bilddatei (falls vorhanden)
        input_dir = os.path.dirname(image_paths[0]) if image_paths else ""
    else:
        raise ValueError(
            f"Ungültiger input_path: '{input_path}'. "
            f"Bitte einen Ordner mit Bildern oder eine .txt mit Pfaden angeben."
        )
    
    # --- 6) Output-Verzeichnis anlegen ---
    if output_root is not None and not os.path.exists(output_root):
        os.makedirs(output_root)
    
    # --- 7) Dataset & Dataloader vorbereiten ---
    inference_dataset = AdhocImageDataset(
        [os.path.join(input_dir, img_name) for img_name in image_names],
        (input_shape[1], input_shape[2]),
        mean=[123.5, 116.5, 103.5],
        std=[58.5, 57.0, 57.5],
    )
    inference_dataloader = DataLoader(
        inference_dataset,
        batch_size=batch_size,
        shuffle=True,
        #num_workers=max(min(batch_size, cpu_count()), 1),
        num_workers=0,
        drop_last=False 
    )

    if callback:
        callback(f"📦 DataLoader initialized with {len(inference_dataset)} images.",progress=0)

    

    # --- 8) WorkerPool für asynchrones Speichern / Visualisieren ---
    img_save_pool = WorkerPool(
        img_save_and_viz,
        processes=max(min(batch_size, cpu_count()), 1)
    )
    
    processed_img = 0 
    # --- 9) Inferenzschleife ---
    for batch_idx, (batch_image_name, batch_orig_imgs, batch_imgs) in tqdm(
        enumerate(inference_dataloader), total=len(inference_dataloader)

    ):
        valid_images_len = len(batch_imgs)
        print(f" Processing batch {batch_idx + 1}/{len(inference_dataloader)}")
        print(f"   - Batch contains {valid_images_len} images")
        if callback:
            #callback(f"   - Batch contains {valid_images_len} images")
            progress_percentage = (batch_idx + 1) / (len(inference_dataloader)) * 100  # Calculate progress %
            #callback(f" Percentage {progress_percentage} %")
            callback(f" Processing batch {batch_idx + 1}/{len(inference_dataloader)} with {valid_images_len} images", progress=progress_percentage)
        
        # Falls dein Code Fake-Padding nutzt:
        batch_imgs = fake_pad_images_to_batchsize(batch_imgs)
        # Vorwärtsdurchlauf
        result = inference_model(exp_model, batch_imgs, dtype=dtype)

       
        # Asynchron speichern
        args_list = []
        for orig_img, res, img_name in zip(
            batch_orig_imgs[:valid_images_len],
            result[:valid_images_len],
            batch_image_name
        ):
           
            out_path = os.path.join(output_root, os.path.basename(img_name))
            args_list.append((orig_img, res, out_path, seg_dir))
        #if callback:
            #callback(f" Saving normal map: {out_path}")

        img_save_pool.run_async(args_list)
        processed_img = processed_img + valid_images_len
        if callback:
            callback(f" Created normal maps: {processed_img }/{len(image_names)}")
    # --- 10) Worker abschließen ---
    img_save_pool.finish()
   
    # --- 11) Statistik ---
    total_time = time.time() - start_time
    n_images = len(image_names) if image_names else 1
    fps = n_images / total_time
   
    result_message = (
        f"\n\033[92mTotal inference time: {total_time:.2f} seconds for {n_images} images. "
        f"FPS (images/s): {fps:.2f}\033[0m"
    )
    if callback:
        callback(result_message )


def warmup_model(model, batch_size):
    # Warm up the model with a dummy input.
    imgs = torch.randn(batch_size, 3, 1024, 768).to(dtype=torch.bfloat16).cuda()
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s), torch.no_grad(), torch.autocast(
        device_type="cuda", dtype=torch.bfloat16
    ):
        for i in range(3):
            model(imgs)
    torch.cuda.current_stream().wait_stream(s)
    imgs = imgs.detach().cpu().float().numpy()
    del imgs, s


def inference_model(model, imgs, dtype=torch.bfloat16):
    with torch.no_grad():
        results = model(imgs.to(dtype).cuda())
        imgs.cpu()

    results = [r.cpu() for r in results]
    return results


def fake_pad_images_to_batchsize(imgs):
    return F.pad(imgs, (0, 0, 0, 0, 0, 0, 0, BATCH_SIZE - imgs.shape[0]), value=0)


def img_save_and_viz(image, result, output_path, seg_dir=None):
    """
    Speichert und visualisiert die Normal Map.

    Parameters:
        image (numpy.ndarray): Eingabebild als HxWxC Array.
        result (torch.Tensor): Modellvorhersage als Tensor.
        output_path (str): Pfad zum Speichern der Ausgabe.
        seg_dir (str, optional): Verzeichnis mit Segmentationsdateien. Standard ist None.
    """
    # Speichere die Ausgabe als .npy Datei
    #output_file = (
    #    output_path.replace(".jpg", ".npy")
    #    .replace(".jpeg", ".npy")
    #    .replace(".png", ".npy")
    #)

    # Interpoliere Ergebnisse und generiere Normal Map
    seg_logits = F.interpolate(
        result.unsqueeze(0), size=image.shape[:2], mode="bilinear"
    ).squeeze(0)
    normal_map = seg_logits.float().data.numpy().transpose(1, 2, 0)  # H x W x C

    # Optional: Maske anwenden (wenn `seg_dir` angegeben ist)
    if seg_dir is not None:
        mask_path = os.path.join(
            seg_dir,
            os.path.basename(output_path)
            .replace(".png", ".npy")
            .replace(".jpg", ".npy")
            .replace(".jpeg", ".npy"),
        )
        try:
            mask = np.load(mask_path)  # Versuche, die Maske zu laden
        except FileNotFoundError:
            print(f"Warnung: Maske {mask_path} nicht gefunden. Standardmaske wird verwendet.")
            mask = np.ones(normal_map.shape[:2], dtype=np.uint8)
    else:
        # Standardmaske verwenden (falls seg_dir nicht angegeben ist)
        mask = np.ones(normal_map.shape[:2], dtype=np.uint8)

    # Normalisiere die Normal Map
    normal_map_norm = np.linalg.norm(normal_map, axis=-1, keepdims=True)
    normal_map_normalized = normal_map / (normal_map_norm + 1e-5)  # Epsilon für Stabilität
    #np.save(output_file, normal_map_normalized)

    # Hintergrund (Maske == 0) schwarz darstellen
    normal_map_normalized[mask == 0] = -1
    normal_map = ((normal_map_normalized + 1) / 2 * 255).astype(np.uint8)
    normal_map = normal_map[:, :, ::-1]  # RGB zu BGR für OpenCV

    # Speichere Normal Map und optional visualisiere sie
    cv2.imwrite(output_path, normal_map)
    #print(f"Normal Map gespeichert unter: {output_path}")


def load_model(checkpoint, use_torchscript=False):
    if use_torchscript:
        return torch.jit.load(checkpoint)
    else:
        return torch.export.load(checkpoint).module()


