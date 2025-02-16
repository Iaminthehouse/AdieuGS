import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import os
import cv2
import webbrowser
from datetime import datetime
from rembg import remove , new_session
from PIL import Image
from pathlib import Path
import threading
import multiprocessing as mp
models = [
    "u2net", "u2netp", "u2net_human_seg", "u2net_cloth_seg", "silueta", 
    "isnet-general-use", "isnet-anime", "sam", "birefnet-general", 
    "birefnet-general-lite", "birefnet-portrait", "birefnet-dis", 
    "birefnet-hrsod", "birefnet-cod", "birefnet-massive"
]

def update_console_output(message, progress=None):
    """Updates the Tkinter console output box dynamically."""
    console_output.insert(tk.END, message + "\n") 
    console_output.see(tk.END)
    console_output.update_idletasks()

    if progress is not None:
        progress_bar["value"] = progress
        #progress_label.config(text=f"Progress: {progress:.1f}%")
        root.update_idletasks()  # Refresh UI immediately

def open_model_test_link():
    webbrowser.open("https://huggingface.co/spaces/KenjieDec/RemBG")

def browse_input():
    directory = filedialog.askdirectory()
    if directory:
        input_var.set(directory)

def browse_output():
    directory = filedialog.askdirectory()
    if directory:
        output_var.set(directory)


def delete_non_image_files(directory):
    """Deletes all files in 'directory' that are not images (JPG, PNG, JPEG)."""
    valid_extensions = ('.jpg', '.png', '.jpeg')

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Check if it's a file (not a folder) and if it doesn't have a valid extension
        if os.path.isfile(file_path) and not filename.lower().endswith(valid_extensions):
            #print(f"Deleting: {file_path}")  # Debugging output
            os.remove(file_path)

def open_output_directory():
    output_dir = output_var.get()
    if os.path.exists(output_dir):
        os.startfile(output_dir)
    else:
        messagebox.showerror("Error", "Output directory does not exist.")

def log_run(model, input_dir, output_dir):
    with open("run_log.txt", "a") as log_file:
        log_file.write(f"[{datetime.now()}] Called runAdieuGS.bat with model: {model}, "
                       f"input: {input_dir}, output: {output_dir}\n")

def run_inference_threaded():
    """Runs the inference model in a separate thread to avoid UI freezing."""
    thread = threading.Thread(target=run_inference_model_safe, daemon=True)
    thread.start()

def run_inference_model_safe():
    import normalmap as nm
    import tempfile, shutil

    console_output.insert(tk.END, "\nStarting normal maps creation...\n")
    progress_bar.pack(pady=5)

    # Annahme: Für die Normal Map-Erstellung wird als Input der Ordner verwendet,
    # in dem die Bilder (z. B. von der rmbg-Verarbeitung) liegen.
    input_dir = os.path.join(output_var.get(), "images")
    output_dir = os.path.join(output_var.get(), "normals")

    # Falls das Normal Map-Verzeichnis noch nicht existiert, erstelle es.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Liste aller Bilddateien im Input-Verzeichnis (nur jpg, png, jpeg)
    all_images = [f for f in sorted(os.listdir(input_dir))
                  if f.lower().endswith((".jpg", ".png", ".jpeg"))]

    # Wenn "overwrite" deaktiviert ist, werden nur Bilder verarbeitet, für die noch keine Normal Map existiert.
    if not overwrite_var.get():
        images_to_process = []
        for img_name in all_images:
            output_image_path = os.path.join(output_dir, img_name)
            if not os.path.exists(output_image_path):
                images_to_process.append(img_name)
    else:
        images_to_process = all_images

    if not images_to_process:
        update_console_output("No new images to process for normal maps.\n")
        progress_bar.stop()
        progress_bar.pack_forget()
        return

    update_console_output(f"Processing {len(images_to_process)} images for normal maps.")

    # Erstelle ein temporäres Verzeichnis, in das nur die zu verarbeitenden Bilder kopiert werden.
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as temp_dir:
        for img_name in images_to_process:
            src = os.path.join(input_dir, img_name)
            dst = os.path.join(temp_dir, img_name)
            shutil.copy2(src, dst)

        try:
            nm.run_inference_model(
                checkpoint="A:/adieuGS/AdieuGS/ext/normals/sapiens/lite/normal/checkpoints/sapiens_2b/sapiens_2b_normal_render_people_epoch_70_torchscript.pt2",
                input_path=temp_dir,
                output_root=output_dir,
                device="cuda:0",
                batch_size=8,
                shape=(1024, 768),
                fp16=False, 
                callback=update_console_output
            )
            # Entferne nicht-Bild-Dateien aus dem Output-Verzeichnis, falls nötig.
            delete_non_image_files(output_dir)
            update_console_output("Normal maps creation finished.\n")
        except Exception as e:
            messagebox.showerror("Error", f"Inference failed: {e}")

    progress_bar.stop()
    progress_bar.pack_forget()

def run_rmbg():
    console_output.delete(1.0, tk.END)
    input_dir = input_var.get()
    output_dir = os.path.join(output_var.get(), "images")
    selected_model = model_var.get()  # Holt den aktuell ausgewählten Modellnamen aus der Combobox
    # Erstelle eine neue Session für das ausgewählte Modell
    session = new_session(selected_model)
    
    console_output.insert(tk.END, "Starting removing background\n")
    progress_bar.pack(pady=5)
    progress_bar.start(10)  # speed of the moving “bar”

    for filename in os.listdir(input_dir):
        # Nur Bilddateien verarbeiten
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # Falls der Overwrite-Flag deaktiviert ist und das Output-Bild existiert, überspringe dieses Bild
        if not overwrite_var.get() and os.path.exists(output_path):
            update_console_output("Skipping existing file: " + output_path)
            continue

        # Bild öffnen und Hintergrund entfernen
        with Image.open(input_path) as img:
            processed = remove(img, session=session)
                    
            # Ergebnis speichern
            processed.save(output_path)
            update_console_output("Saved: " + output_path)
            root.update()
    
    progress_bar.stop()
    progress_bar.pack_forget()
    console_output.insert(tk.END, "Removing background finished\n")


def run_processing():
    input_dir = input_var.get()
    output_dir = output_var.get()
    model = model_var.get()
    
    if not input_dir or not output_dir:
        messagebox.showerror("Error", "Please select both input and output directories.")
        return
    # Prüfe, ob mindestens eine Option ausgewählt wurde
    if not rmbg_var.get() and not normal_var.get():
        messagebox.showerror("Error", "Please select at least one processing option (Remove Background or Create Normal Maps).")
        return

    console_output.delete(1.0, tk.END)
    
    # Starte die Aufgaben basierend auf den Checkbutton-Zuständen
    if rmbg_var.get():
        # Hintergrundentfernung ausführen
        # Wenn run_rmbg() länger dauert, kannst du sie in einem eigenen Thread starten:
        #threading.Thread(target=run_rmbg, daemon=True).start()
        run_rmbg()  # Direkter Aufruf ohne Thread
    
    if normal_var.get():
        # Normal Map-Erstellung ausführen (run_inference_threaded() startet bereits einen Thread)
        run_inference_threaded()
    
    # Optional: Öffne das Output-Verzeichnis, wenn beide Aufgaben gestartet wurden
    open_output_directory()


def run_script():
    input_dir = input_var.get()
    output_dir = output_var.get()
    model = model_var.get()
    
    if not input_dir or not output_dir:
        messagebox.showerror("Error", "Please select both input and output directories.")
        return
    
    bat_file = "runAdieuGS.bat"
    
    if not os.path.exists(bat_file):
        messagebox.showerror("Error", f"{bat_file} not found in the current directory.")
        return
    
    # Start progress bar before launching the process
    progress_bar.pack(pady=5)
    progress_bar.start(10)  # speed of the moving “bar”

    #log_run(model, input_dir, output_dir)
    
    try:
        process = subprocess.Popen(
            [bat_file, model, input_dir, output_dir, "%CD%"], 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        console_output.delete(1.0, tk.END)

        # Continuously read output
        for line in process.stdout:
            console_output.insert(tk.END, line)
            console_output.see(tk.END)
            root.update()  # so the UI remains responsive (incl. the progress bar)

        # Wait for process to finish
        process.wait()
        
        messagebox.showinfo("Success", "Script executed successfully.")
        open_output_directory()
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Execution Error", f"An error occurred: {e}")
    finally:
        # Stop and hide the progress bar once everything is done
        progress_bar.stop()
        progress_bar.pack_forget()

if __name__ == "__main__":
    # Create UI
    mp.set_start_method("spawn", force=True)  # Ensure multiprocessing is set correctly
    root = tk.Tk()
    root.title("AdieuGS 1.0 by Fransoavirtuality")
    root.iconbitmap("moi.ico")
    root.geometry("500x500")

    # Frame for Model selection
    frame_model = tk.Frame(root)
    frame_model.pack(pady=5)

    tk.Label(frame_model, text="Select Model:").pack(side="left", padx=5)
    model_var = tk.StringVar(value="birefnet-general")
    model_dropdown = ttk.Combobox(frame_model, textvariable=model_var, values=models, state="readonly")
    model_dropdown.pack(side="left", padx=5)
    tk.Button(frame_model, text="Test Models Online", command=open_model_test_link, fg="blue").pack(side="left", padx=5)

    # Input Directory
    tk.Label(root, text="Input Directory:").pack(pady=5)
    frame_input = tk.Frame(root)
    frame_input.pack(pady=5)
    input_var = tk.StringVar()
    tk.Entry(frame_input, textvariable=input_var, width=50).pack(side="left", fill="x", expand=True)
    tk.Button(frame_input, text="Browse", command=browse_input).pack(side="left", padx=5)

    # Output Directory
    tk.Label(root, text="Output Directory:").pack(pady=5)
    frame_output = tk.Frame(root)
    frame_output.pack(pady=5)
    output_var = tk.StringVar()
    tk.Entry(frame_output, textvariable=output_var, width=50).pack(side="left", fill="x", expand=True)
    tk.Button(frame_output, text="Browse", command=browse_output).pack(side="left", padx=5)

    # --- Füge diese Variablen und Checkbuttons im UI-Bereich hinzu, z. B. nach dem Output-Directory ---

    # Frame für Optionen
    frame_options = tk.Frame(root)
    frame_options.pack(pady=5)

    # BooleanVar für die beiden Optionen
    rmbg_var = tk.BooleanVar(value=True)
    normal_var = tk.BooleanVar(value=True)
    overwrite_var = tk.BooleanVar(value=False)  # Standard: nicht überschreiben

    # Checkbutton für Background Removal
    rmbg_checkbox = tk.Checkbutton(frame_options, text="Remove Background", variable=rmbg_var)
    rmbg_checkbox.pack(side="left", padx=5)

    # Checkbutton für Normal Map Creation
    normal_checkbox = tk.Checkbutton(frame_options, text="Create Normal Maps", variable=normal_var)
    normal_checkbox.pack(side="left", padx=5)

    # Checkbutton für Überschreiben vorhandener Normal Maps
    overwrite_checkbox = tk.Checkbutton(frame_options, text="Overwrite Existing Files", variable=overwrite_var)
    overwrite_checkbox.pack(side="left", padx=5)

    # Run button
    run_button = tk.Button(
        root, 
        text="Run", 
        command=run_processing,
        bg="azure",
        fg="black",
        font=("Arial", 10, "bold"),
        width=10,   # Number of text units for width
        height=1    # Number of text units for height
    )
    run_button.pack(pady=10)

    # Progress bar (hidden by default; we show it in run_script)
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    #progress_label = tk.Label(root, text="Progress: 0%", font=("Arial", 10))
    #progress_label.pack(pady=5)

    # Scrolled Text
    console_output = scrolledtext.ScrolledText(root, height=15, width=60, bd=2, relief="groove")
    console_output.pack(padx=10, pady=5)

    root.mainloop()
