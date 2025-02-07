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

def open_output_directory():
    output_dir = output_var.get()
    if os.path.exists(output_dir):
        os.startfile(output_dir)  # Opens the folder in file explorer
    else:
        messagebox.showerror("Error", "Output directory does not exist.")

def log_run(model, input_dir, output_dir):
    with open("run_log.txt", "a") as log_file:
        log_file.write(f"[{datetime.now()}] Called runAdieuGS.bat with model: {model}, input: {input_dir}, output: {output_dir}\n")

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
    
    log_run(model, input_dir, output_dir)
    
    try:
        process = subprocess.Popen([bat_file, model, input_dir, output_dir, "%CD%"], 
                                   shell=True, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
        console_output.delete(1.0, tk.END)
        for line in process.stdout:
            console_output.insert(tk.END, line)
            console_output.see(tk.END)
            root.update()
        
        process.wait()
        messagebox.showinfo("Success", "Script executed successfully.")
        open_output_directory()
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Execution Error", f"An error occurred: {e}")

# Create UI
root = tk.Tk()
root.title("AdieuGS Runner")
root.geometry("500x500")

tk.Label(root, text="Select Model:").pack(pady=5)
model_var = tk.StringVar(value="birefnet-general")
model_dropdown = ttk.Combobox(root, textvariable=model_var, values=models, state="readonly")
model_dropdown.pack()

tk.Button(root, text="Test Models Online", command=open_model_test_link, fg="blue").pack(pady=5)

tk.Label(root, text="Input Directory:").pack(pady=5)
input_var = tk.StringVar()
tk.Entry(root, textvariable=input_var, width=50).pack()
tk.Button(root, text="Browse", command=browse_input).pack()

tk.Label(root, text="Output Directory:").pack(pady=5)
output_var = tk.StringVar()
tk.Entry(root, textvariable=output_var, width=50).pack()
tk.Button(root, text="Browse", command=browse_output).pack()

tk.Button(root, text="Run", command=run_script, bg="green", fg="white").pack(pady=10)

console_output = scrolledtext.ScrolledText(root, height=10, width=60)
console_output.pack(pady=5)

root.mainloop()