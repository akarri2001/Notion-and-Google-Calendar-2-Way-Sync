import tkinter as tk
import pystray
from pystray import Icon, Menu, MenuItem
import subprocess
import threading
import time
from PIL import Image

# Module path (replace with your actual path)
module_path = "Notion-GCal-2WaySync-Public.py"

run_thread = None  # Store the thread object globally


def run_module():
    global run_thread  # Access the global thread variable
    while getattr(run_thread, "do_run", True):  # Check the flag
        try:
            output = subprocess.check_output(["python", module_path])
            output_text.insert(tk.END, output.decode("utf-8"))  #Adding The Logs of Sync to The window
            output_text.insert(tk.END, "\n")
            output_text.insert(tk.END, "=====NEXT Sync in 5 Min=====")
            output_text.insert(tk.END, "\n")
            output_text.see(tk.END)
        except Exception as e:
            output_text.insert(tk.END, f"Error running module: {e}")
        time.sleep(300)  # Adjust update frequency as needed
        if getattr(run_thread,"do_run") == "False":
            run_thread = None



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