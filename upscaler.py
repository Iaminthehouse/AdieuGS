import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from PIL import Image
import torch
import torch.nn.functional as F
torch.cuda.empty_cache()
from diffusers import StableDiffusionUpscalePipeline

def upscale_images_in_folder(
    input_folder: str,
    output_folder: str,
    model_id: str = "stabilityai/stable-diffusion-x4-upscaler",
    prompt: str = "",  # Prompt kann das Ergebnis beeinflussen ("a photo of a cat" etc.)
    device: str = "cuda",
    num_inference_steps: int = 50
):
    """
    Lädt die Stable Diffusion x4 Upscale-Pipeline, iteriert über alle Bilder im Eingabeordner,
    skaliert sie hoch und speichert die Ergebnisse im Ausgabeordner.
    """

    # 1) Pipeline laden
    pipe = StableDiffusionUpscalePipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    pipe.to(device)

    # Output-Verzeichnis anlegen (falls nicht vorhanden)
    os.makedirs(output_folder, exist_ok=True)

    # 2) Über alle Bilddateien im Ordner iterieren
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            image_path = os.path.join(input_folder, filename)
            # Bild laden
            image = Image.open(image_path).convert("RGB")

            # 3) Upscaling über die Pipeline in einem no_grad-Block
            with torch.no_grad():
                result = pipe(
                    prompt=prompt,
                    image=image,
                    num_inference_steps=num_inference_steps
                )
                upscaled_image = result.images[0]

            # 4) Ergebnis speichern
            output_path = os.path.join(output_folder, f"upscaled_{filename}")
            upscaled_image.save(output_path)
            print(f"[INFO] {filename} wurde hochskaliert und unter {output_path} gespeichert.")
            
            # GPU-Speicher freigeben
            torch.cuda.empty_cache()

if __name__ == "__main__":
    # Beispielpfade anpassen
    input_folder = "A:/adieuGS/AdieuGS/upscaler/input"
    output_folder = "A:/adieuGS/AdieuGS/upscaler/output"

    # Prompt kann leer sein oder z. B. "a beautiful landscape"
    prompt_text = ""

    upscale_images_in_folder(
        input_folder=input_folder,
        output_folder=output_folder,
        model_id="stabilityai/stable-diffusion-x4-upscaler",
        prompt=prompt_text,
        device="cuda",  # oder "cpu"
        num_inference_steps=50
    )

