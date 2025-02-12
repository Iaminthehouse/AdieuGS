import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import os
import webbrowser
from datetime import datetime

models = [
    "u2net", "u2netp", "u2net_human_seg", "u2net_cloth_seg", "silueta", 
    "isnet-general-use", "isnet-anime", "sam", "birefnet-general", 
    "birefnet-general-lite", "birefnet-portrait", "birefnet-dis", 
    "birefnet-hrsod", "birefnet-cod", "birefnet-massive"
]

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

# Create UI
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

# Run button
run_button = tk.Button(
    root, 
    text="Run", 
    command=run_script,
    bg="azure",
    fg="black",
    font=("Arial", 10, "bold"),
    width=10,   # Number of text units for width
    height=1    # Number of text units for height
)
run_button.pack(pady=10)

# Progress bar (hidden by default; we show it in run_script)
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")

# Scrolled Text
console_output = scrolledtext.ScrolledText(root, height=15, width=60, bd=2, relief="groove")
console_output.pack(padx=10, pady=5)

root.mainloop()
