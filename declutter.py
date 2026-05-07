import os
import shutil
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime, timedelta
import webbrowser

# =====================================================================
# CONFIGURATION & GLOBAL STATE
# =====================================================================
LOG_FILE = "declutter_log.json"

EXTENSION_MAP = {
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"],
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp"],
    "Code_and_Scripts": [".py", ".cs", ".json", ".html", ".css", ".js", ".cpp"],
    "Executables": [".exe", ".msi"],
    "Compressed_Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Media_Audio_Video": [".mp4", ".mkv", ".mp3", ".wav", ".mov"]
}


def browse_folder():
    """Opens a native Windows folder picker and updates the text field."""
    selected_dir = filedialog.askdirectory(title="Select Folder to Declutter")
    if selected_dir:
        # Normalize path slashes for clean rendering
        clean_path = os.path.normpath(selected_dir)
        folder_input.delete(0, tk.END)
        folder_input.insert(0, clean_path)


def get_time_folder(file_path):
    """Calculates file age and returns the appropriate folder name."""
    stat_info = os.stat(file_path)
    modified_date = datetime.fromtimestamp(stat_info.st_mtime)
    now = datetime.now()
    age = now - modified_date

    if age < timedelta(days=1):
        return "Today"
    elif age < timedelta(days=7):
        return "This_Week"
    elif age < timedelta(days=30):
        return "This_Month"
    else:
        return "Older_Than_A_Month"


def clean_folder():
    # Read the folder path dynamically from the GUI user input field
    target_folder = folder_input.get().strip()

    if not target_folder or not os.path.exists(target_folder):
        messagebox.showerror(
            "Error", f"Invalid target directory choice:\n'{target_folder}'")
        return

    sort_method = sort_choice.get()
    moved_files_history = []
    moved_count = 0

    protected_folders = list(EXTENSION_MAP.keys(
    )) + ["Unsorted_Other", "Today", "This_Week", "This_Month", "Older_Than_A_Month"]

    for item in os.listdir(target_folder):
        item_path = os.path.join(target_folder, item)

        if os.path.isdir(item_path) or item == LOG_FILE or item in protected_folders:
            continue

        filename, file_extension = os.path.splitext(item)
        file_extension = file_extension.lower()

        # --- OPTION 1: SORT BY FILE TYPE ---
        if sort_method == 1:
            destination_folder_name = "Unsorted_Other"
            for folder_name, extensions in EXTENSION_MAP.items():
                if file_extension in extensions:
                    destination_folder_name = folder_name
                    break

        # --- OPTION 2: SORT BY TIME ---
        else:
            destination_folder_name = get_time_folder(item_path)

        destination_dir = os.path.join(target_folder, destination_folder_name)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        final_destination_path = os.path.join(destination_dir, item)

        try:
            shutil.move(item_path, final_destination_path)
            moved_files_history.append({
                "original": item_path,
                "current": final_destination_path
            })
            moved_count += 1
        except Exception as e:
            print(f"Skipped file {item}: {e}")

    # Save log history locally alongside our execution engine module
    if moved_files_history:
        # Write down which specific folder we operated on so Undo can find it later
        log_data = {
            "target_dir": target_folder,
            "transactions": moved_files_history
        }
        with open(LOG_FILE, 'w') as f:
            json.dump(log_data, f, indent=4)
        messagebox.showinfo(
            "Success", f"Cleaned up {moved_count} files inside successfully!")
    else:
        messagebox.showinfo(
            "Info", "No loose files found to organize inside that folder.")


def undo_last_action():
    if not os.path.exists(LOG_FILE):
        messagebox.showwarning("Warning", "No tracking logs found to undo.")
        return

    try:
        with open(LOG_FILE, 'r') as f:
            log_data = json.load(f)

        # Support reading old flat-array structures or new nested dictionary log models
        if isinstance(log_data, dict):
            target_folder = log_data.get("target_dir")
            history = log_data.get("transactions", [])
        else:
            target_folder = folder_input.get().strip()  # Fallback
            history = log_data
    except Exception as e:
        messagebox.showerror("Error", f"Failed to parse tracking logs: {e}")
        return

    undo_count = 0
    for transaction in reversed(history):
        current_path = transaction["current"]
        original_path = transaction["original"]

        if os.path.exists(current_path):
            try:
                shutil.move(current_path, original_path)
                undo_count += 1
            except Exception as e:
                print(f"Could not reverse mapping for {current_path}: {e}")

    os.remove(LOG_FILE)

    # Clean up any empty directories inside the specific folder we processed
    if os.path.exists(target_folder):
        all_possible_folders = list(EXTENSION_MAP.keys(
        )) + ["Unsorted_Other", "Today", "This_Week", "This_Month", "Older_Than_A_Month"]
        for folder_name in all_possible_folders:
            dir_to_check = os.path.join(target_folder, folder_name)
            if os.path.exists(dir_to_check) and not os.listdir(dir_to_check):
                os.rmdir(dir_to_check)

    messagebox.showinfo(
        "Undo Complete", f"Successfully restored {undo_count} files back to their home destination.")


# =====================================================================
# GUI DESIGN
# =====================================================================
root = tk.Tk()
root.title("Desktop File Declutter Engine Pro")
root.geometry("480x400")  # Expanded geometry card window structure size
root.configure(bg="#1e1e24")
root.resizable(False, False)

# Title Panel Elements
title_label = tk.Label(root, text="AUTOMATED FILE UTILITY", font=(
    "Segoe UI", 16, "bold"), bg="#1e1e24", fg="#ff4655")
title_label.pack(pady=(20, 15))

# --- NEW: ACTIVE PATH CHANGER ELEMENT PANEL ---
path_frame = tk.LabelFrame(root, text=" Target Path Selection ", font=(
    "Segoe UI", 10, "bold"), bg="#1e1e24", fg="#eceff4", padx=10, pady=10)
path_frame.pack(pady=5, fill="x", padx=20)

# Default to the Downloads folder but leave it editable
default_path = os.path.normpath(os.path.expanduser("~/Downloads"))

folder_input = tk.Entry(path_frame, font=(
    "Segoe UI", 10), bg="#2d3139", fg="#eceff4", insertbackground="white", width=34)
folder_input.insert(0, default_path)
folder_input.pack(side="left", padx=(0, 5), ipady=3)

btn_browse = tk.Button(path_frame, text="Browse...", font=(
    "Segoe UI", 9, "bold"), bg="#4c566a", fg="white", command=browse_folder, cursor="hand2")
btn_browse.pack(side="right", padx=(5, 0))

# Sorting Method Selection Controls
options_frame = tk.LabelFrame(root, text=" Sorting Strategy ", font=(
    "Segoe UI", 10, "bold"), bg="#1e1e24", fg="#eceff4", padx=10, pady=10)
options_frame.pack(pady=10, fill="x", padx=20)

sort_choice = tk.IntVar()
sort_choice.set(1)

radio_type = tk.Radiobutton(options_frame, text="Sort by File Type (PDF, PNG, Py...)", variable=sort_choice, value=1, font=(
    "Segoe UI", 10), bg="#1e1e24", fg="#eceff4", selectcolor="#1e1e24", activebackground="#1e1e24", activeforeground="#ff4655")
radio_type.pack(anchor="w")

radio_time = tk.Radiobutton(options_frame, text="Sort by File Age (Today, This Week...)", variable=sort_choice, value=2, font=(
    "Segoe UI", 10), bg="#1e1e24", fg="#eceff4", selectcolor="#1e1e24", activebackground="#1e1e24", activeforeground="#ff4655")
radio_time.pack(anchor="w", pady=(5, 0))

# Execution Action Control Triggers
btn_clean = tk.Button(root, text="Run Folder Cleanup", font=("Segoe UI", 11, "bold"), bg="#ff4655", fg="white",
                      activebackground="#e03e4c", activeforeground="white", width=22, command=clean_folder, cursor="hand2")
btn_clean.pack(pady=(15, 5))

btn_undo = tk.Button(root, text="↩ Undo Last Action", font=("Segoe UI", 10, "bold"), bg="#2d3139", fg="#eceff4",
                     activebackground="#4c566a", activeforeground="white", width=22, command=undo_last_action, cursor="hand2")
btn_undo.pack(pady=5)

def open_donation():
    # Replace this placeholder link with your actual Buy Me a Coffee URL!
    webbrowser.open("https://www.buymeacoffee.com/localfiletwex")

# Donation Link UI Component
lnk_coffee = tk.Label(
    root, 
    text="☕ Enjoying this tool? Buy me a coffee!", 
    font=("Segoe UI", 9, "underline"), 
    bg="#1e1e24", 
    fg="#ecc94b", 
    cursor="hand2"
)
lnk_coffee.pack(pady=(15, 0))
lnk_coffee.bind("<Button-1>", lambda e: open_donation())

root.mainloop()
