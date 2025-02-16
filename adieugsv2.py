import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import webbrowser
import threading
import subprocess
from rembg import remove, new_session
from PIL import Image, ImageTk
import ttkbootstrap as tb  

def update_console_output(message, progress=None):
    """Updates the Tkinter console output box dynamically."""
    console_output.insert(tk.END, message + "\n") 
    console_output.see(tk.END)
    console_output.update_idletasks()

    if progress is not None:
        progress_bar["value"] = progress
        #progress_label.config(text=f"Progress: {progress:.1f}%")
        root.update_idletasks()  # Refresh UI immediately

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
    #open_output_directory()


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
            #delete_non_image_files(output_dir)
            update_console_output("Normal maps creation finished.\n")
        except Exception as e:
            messagebox.showerror("Error", f"Inference failed: {e}")

    progress_bar.stop()
    progress_bar.pack_forget()

def run_rmbg():
    console_output.delete(1.0, tk.END)
    input_dir = input_var.get()
    output_dir = os.path.join(output_var.get(), "images")
    session = new_session(model_var.get())

    console_output.insert(tk.END, "Starting removing background\n")
    progress_bar.pack(pady=5)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            with Image.open(os.path.join(input_dir, filename)) as img:
                remove(img, session=session).save(os.path.join(output_dir, filename))
                console_output.insert(tk.END, f"Saved: {filename}\n")

    progress_bar.stop()
    progress_bar.pack_forget()

# 🔹 Funktionen für Datei- und Model-Auswahl
def browse_input():
    directory = filedialog.askdirectory()
    if directory:
        input_var.set(directory)

def browse_output():
    directory = filedialog.askdirectory()
    if directory:
        output_var.set(directory)

def open_model_test_link():
    webbrowser.open("https://huggingface.co/spaces/KenjieDec/RemBG")

def move_window(event):
    root.geometry(f"+{event.x_root}+{event.y_root}")

# 🔹 Hauptfunktion für das UI-Setup
def main():
    global root, input_var, output_var, model_var, rmbg_var, normal_var, overwrite_var
    global console_output, progress_bar  

    # 🔹 Hauptfenster erstellen (Dark Mode)
    root = tb.Window(themename="darkly")
    root.geometry("600x500")
    root.overrideredirect(1)  # Versteckt die Standard-Titelleiste

    # 🔹 Eigene schwarze Titelleiste erstellen
    title_bar = tk.Frame(root, bg="#1E1E1E", relief="raised", bd=0, height=30)
    title_bar.pack(fill="x")

    # 🔹 Icon laden & skalieren
    icon_path = "moi.ico"  
    icon_size = (20, 20)  

    try:
        icon_image = Image.open(icon_path).resize(icon_size, Image.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)

        icon_label = tk.Label(title_bar, image=icon_photo, bg="#1E1E1E")
        icon_label.image = icon_photo  
        icon_label.pack(side="left", padx=5)

    except Exception as e:
        print(f"⚠ Fehler beim Laden des Icons: {e}")

    # 🔹 Fenster-Titel hinzufügen
    title_label = tk.Label(title_bar, text="AdieuGS 1.0", fg="white", bg="#1E1E1E", font=("Segoe UI", 10, "bold"))
    title_label.pack(side="left", padx=5)

    # 🔹 Weiße Linie unter der Titelleiste
    tk.Frame(root, bg="white", height=2).pack(fill="x")

    # 🔹 Fenster-Schließen-Button
    close_button = tk.Button(
        title_bar, text="✖", fg="white", bg="red", font=("Segoe UI", 12, "bold"),  
        command=root.destroy, bd=0, padx=12, pady=5
    )
    close_button.pack(side="right", padx=10, pady=3)

    # 🔹 Fenster verschiebbar machen
    title_bar.bind("<B1-Motion>", move_window)

    # 🔹 UI-Container
    container = tk.Frame(root, bg="#1E1E1E", padx=10, pady=10)
    container.pack(fill="both", expand=True)
    container.grid_columnconfigure(1, weight=1)

    # 🔹 Input Directory
    input_var = tk.StringVar()
    tk.Label(container, text="📂 Input Directory:", fg="white", bg="#1E1E1E", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=5)
    tb.Entry(container, textvariable=input_var, bootstyle="dark").grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    tb.Button(container, text="Browse", command=browse_input, bootstyle="info").grid(row=0, sticky="w", column=2, padx=5, pady=5)

    # 🔹 Output Directory
    output_var = tk.StringVar()
    tk.Label(container, text="📁 Output Directory:", fg="white", bg="#1E1E1E", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=5)
    tb.Entry(container, textvariable=output_var, bootstyle="dark").grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    tb.Button(container, text="Browse", command=browse_output, bootstyle="info").grid(row=1, sticky="w", column=2, padx=5, pady=5)

    # 🔹 Model Selection mit "Test online"-Button
    models = ["u2net", "u2netp", "u2net_human_seg", "u2net_cloth_seg", "silueta", 
    "isnet-general-use", "isnet-anime", "sam", "birefnet-general", 
    "birefnet-general-lite", "birefnet-portrait", "birefnet-dis", 
    "birefnet-hrsod", "birefnet-cod", "birefnet-massive"]

    model_var = tk.StringVar(value=models[9])
    tk.Label(container, text="🎛 Select Model:", fg="white", bg="#1E1E1E", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=5)
    ttk.Combobox(container, textvariable=model_var, values=models, state="readonly").grid(row=2, column=1, sticky="ew", padx=5, pady=5)
    tb.Button(container, text="Test online", command=open_model_test_link, bootstyle="info").grid(row=2,sticky="w", column=2, padx=5, pady=5)

       # 🔹 Run-Button
    run_button = tb.Button(root, text="Run", bootstyle="info", command=run_processing, width=15)
    run_button.pack(pady=10)


    # 🔹 Konsolenausgabe
    console_output = scrolledtext.ScrolledText(root, height=12, width=75, bg="#252526", fg="white", font=("Consolas", 10))
    console_output.pack(padx=10, pady=5)

    # 🔹 Fortschrittsbalken
    progress_bar = tb.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress_bar.pack(pady=5)

    # 🔹 Optionen für Verarbeitung
    frame_options = tk.Frame(container, bg="#1E1E1E")
    frame_options.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)

    rmbg_var = tk.BooleanVar(value=True)
    normal_var = tk.BooleanVar(value=True)
    overwrite_var = tk.BooleanVar(value=False)

    tb.Checkbutton(frame_options, text="Remove Background", variable=rmbg_var, bootstyle="primary").pack(side="left", padx=5)
    tb.Checkbutton(frame_options, text="Create Normal Maps", variable=normal_var, bootstyle="success").pack(side="left", padx=5)
    tb.Checkbutton(frame_options, text="Overwrite Files", variable=overwrite_var, bootstyle="danger").pack(side="left", padx=5)

 

    root.mainloop()

# 🔹 Starte das Programm nur, wenn die Datei direkt ausgeführt wird
if __name__ == "__main__":
    main()
