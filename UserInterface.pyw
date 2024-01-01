import tkinter as tk
import pystray
from pystray import Icon, Menu, MenuItem
import subprocess
import threading
import time
from PIL import Image
import os

# Module path (replace with your actual path)
module_path = "Notion-GCal-2WaySync-Public.pyw"

run_thread = None  # Store the thread object globally

# ... other code ...

MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB

def rotate_log():
    """Rotates the log file if it exceeds the maximum size."""
    if os.path.exists("sync_logs.txt") and os.path.getsize("sync_logs.txt") > MAX_LOG_SIZE:
        os.rename("sync_logs.txt", "sync_logs.old.txt")  # Create a backup
        log_file = open("sync_logs.txt", "a")  # Create a new, empty log file

log_file = open("sync_logs.txt", "a")  # Open log file for appending


def run_module():
    global run_thread  # Access the global thread variable
    while getattr(run_thread, "do_run", True):
        try:
            # Reuse subprocess outside the loop
            if not hasattr(run_thread, "subprocess"):
                try:
                    output = subprocess.check_output(["pythonw", module_path]).decode("utf-8")
                except subprocess.CalledProcessError as e:
                    # Handle subprocess error, e.g., log the error message
                    output = str(e)  # Or handle the error differently

            log_file.write(output + "\n")  # Write to log file
            log_file.flush()

            # Display only recent log line in GUI
            output_text.delete("1.0", tk.END)  # Clear previous output
            output_text.insert(tk.END, output)
            output_text.see(tk.END)

            output_text.insert(tk.END, "\n")
            output_text.insert(tk.END, "=====NEXT Sync in 5 Min=====")
            output_text.insert(tk.END, "\n")
            output_text.see(tk.END)

            rotate_log()  # Check for log rotation

        except Exception as e:
            output_text.insert(tk.END, f"Error running module: {e}\n")
            log_file.write(f"Error running module: {e}\n")  # Log error to file
            log_file.flush()

        time.sleep(300)  # Adjust update frequency as needed

        if getattr(run_thread, "do_run") == "False":
            run_thread = None
            log_file.close()  # Close log file


def stop_module():
    global run_thread
    if run_thread is not None:
        run_thread.do_run = False  # Set the flag to stop the loop
        output_text.insert(tk.END, "\n")
        output_text.insert(tk.END, "The Code Has Been Stopped")
        output_text.see(tk.END)



def minimize_to_tray():
    root.withdraw()
    icon.run()


def restore_from_tray():
    icon.stop()
    root.deiconify()


def start_module():
    global run_thread
    run_thread = threading.Thread(target=run_module)
    run_thread.do_run = True
    run_thread.start()
    output_text.insert(tk.END, "Initiating Sync Between Notion And Google")
    output_text.see(tk.END)



root = tk.Tk()
root.title("Notion Sync Helper")

output_text = tk.Text(root, wrap=tk.WORD, width=40, height=10)
output_text.pack(fill=tk.BOTH, expand=True)

run_button = tk.Button(root, text="Start Module", command=start_module)
run_button.pack()

stop_button = tk.Button(root, text="Stop Module", command=stop_module)
stop_button.pack()

minimize_button = tk.Button(root, text="Minimize to Tray", command=minimize_to_tray)
minimize_button.pack(side=tk.BOTTOM)

menu = Menu(MenuItem("Restore", restore_from_tray))

icon_image = Image.open("Notion_Sync_Helper.ico")  # Load icon using Pillow
icon = Icon("Notion Sync Helper", icon=icon_image, menu=menu)



root.mainloop()

#After editing try running pyinstaller --onefile --windowed UserInterface.py
# To create A exe file which can run the script at startup if placed at startup folder , or be executed at will.
