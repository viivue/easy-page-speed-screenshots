import os
import tkinter
from tkinter import ttk
from tkinter import filedialog
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime
import threading
import sys
from ctypes import windll
windll.shcore.SetProcessDpiAwareness(2)

from . import helpers

# browse folder path
def epss_browse_button():
    directory = filedialog.askdirectory()
    folder_entry.delete(0, "end")
    folder_entry.insert(0, directory)
    global OP_DIR
    OP_DIR = directory

# start test
def epss_start():
    links = links_text.get("1.0", "end-1c")
    global INPUT_LINK
    INPUT_LINK = [line.strip() for line in links.splitlines()]
    global API_KEY
    API_KEY = gtmetrix_entry.get()
    execute_thread = threading.Thread(target=epss_main, args=())
    execute_thread.start()
    test_button.config(text="Taking Screenshots", state="disabled")
    gtmetrix_checkbox.config(state="disabled")
    folder_button.config(state="disabled")
    folder_entry.config(state="disabled")
    links_text.config(state="disabled")
    gtmetrix_entry.config(state="disabled")
    pb_frame.grid(row=5, column=0, pady=5)
    pb.start()

def epss_main():
    try:
        links = epss_user_input()
        links = epss_add_form_factor(links=links)
        epss_execute_screenshots(links=links)
        pb.stop()
        pb_frame.grid_forget()
        tkinter.messagebox.showinfo(
            title="Finish", message="Result screenshots saved successfully!"
        )
        test_button.config(text="Take screenshots", state="normal")
        gtmetrix_checkbox.config(state="normal")
        folder_button.config(state="normal")
        folder_entry.config(state="normal")
        links_text.config(state="normal")
        gtmetrix_entry.config(state="normal")
    except Exception as e:
        tkinter.messagebox.showerror(title=e, message=e)


# set use GTmetrix & toggle insert field
def epss_toggle_api_key_field():
    global use_gt_metrix
    use_gt_metrix = True if not use_gt_metrix else False
    if use_gt_metrix:
        gtmetrix_api_frame.grid(row=4, column=0, padx=10, pady=15)
    else:
        gtmetrix_api_frame.grid_forget()

def epss_start_ui():
    main = tkinter.Tk()

    # ui meta
    main.title("Easy Page Speed Screenshots")
    program_directory = sys.path[0]
    main.iconbitmap(
        tkinter.PhotoImage(helpers.epss_resource_path("../assets/icons8-screenshot-64.ico"))
    )
    main.resizable(False, False)
    main.tk.call('tk', 'scaling', 1.0)

    main_frame = tkinter.Frame(main)
    main_frame.grid(row=0, column=0, padx=30, pady=(30,0))

    main_label = tkinter.Label(
        main_frame, text="Easy Page Speed Screenshots", font=("Nirmala UI", 26, "bold")
    )
    main_label.grid(row=0, column=0)

    # select folder
    folder_frame = tkinter.Frame(main_frame)
    folder_frame.grid(row=1, column=0, pady=20)
    folder_label = tkinter.Label(folder_frame, text="Choose result folder", font=("Nirmala UI", 14))
    folder_label.grid(row=0, column=0)
    folder_entry = tkinter.Entry(folder_frame, width=45, font=("Nirmala UI", 14))
    folder_entry.grid(row=0, column=1, padx=20)
    folder_button = tkinter.Button(
        folder_frame, text="Browse directory", command=epss_browse_button, font=("Nirmala UI", 14)
    )
    folder_button.grid(row=0, column=2)

    # links
    links_frame = tkinter.Frame(main_frame)
    links_frame.grid(row=2, column=0)
    links_frame.grid_columnconfigure(1, weight=1)
    links_label = tkinter.Label(links_frame, text="URLs for the page speed screenshots", font=("Nirmala UI", 14))
    links_label.grid(row=0, column=0, pady=10)
    links_text = tkinter.Text(links_frame, height=20, font=("Nirmala UI", 14))
    links_text.grid(row=1, column=0, pady=5)

    # gtmetrix

    gtmetrix_frame = tkinter.Frame(main_frame)
    gtmetrix_frame.grid(row=3, column=0)
    gtmetrix_checkbox = tkinter.Checkbutton(
        gtmetrix_frame, command=epss_toggle_api_key_field
    )
    gtmetrix_checkbox.grid(row=0, column=0,pady=10)
    gtmetrix_label = tkinter.Label(gtmetrix_frame, text="Use GTmetrix", font=("Nirmala UI", 14))
    gtmetrix_label.grid(row=0, column=1)
    gtmetrix_api_frame = tkinter.Frame(main_frame)
    gtmetrix_api_label = tkinter.Label(gtmetrix_api_frame, text="API Key", font=("Nirmala UI", 14))
    gtmetrix_api_label.grid(row=0, column=0)
    gtmetrix_entry = tkinter.Entry(gtmetrix_api_frame, width=50, font=("Nirmala UI", 14))
    gtmetrix_entry.grid(row=0, column=1)


    # test button
    test_frame = tkinter.Frame(main_frame)
    test_frame.grid(row=6, column=0)
    test_button = tkinter.Button(test_frame, text="Take screenshots", font=("Nirmala UI", 14),command=epss_start)
    test_button.grid(row=0, column=0, pady=(10,0))

    # copyright
    main_label = tkinter.Label(main_frame, text="Copyright © by ViiVue 2023", font=("Nirmala UI", 10))
    main_label.grid(row=7, column=0, pady=(30,0))
    # progress bar
    pb_frame = tkinter.Frame(main_frame)
    pb = ttk.Progressbar(pb_frame, orient="horizontal", mode="indeterminate", length=280)
    pb.grid(row=0, column=0)
    pb_label = tkinter.Label(pb_frame)
    pb_label.grid(row=1, column=0)

    main.mainloop()