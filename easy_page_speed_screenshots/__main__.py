import tkinter
import tkinter.messagebox
from tkinter import ttk
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime
import threading
import validators
import os.path

from . import __version__
from . import config
from . import entry
from . import helpers

# webdriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_experimental_option(
    "excludeSwitches", ["enable-logging"]
)  # disable output the 'DevTools listening on ws://127.0.0.1:56567/devtools/browser/' line
options.add_argument("--log-level=3")

# close window handling
def epss_on_closing():
    if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
        # close chromedriver if quit at random point

        for driver in config.CHROME_DRIVERS:
            if driver.service.is_connectable():
                driver.quit()

        # quit the interface
        main.destroy()


# get report links by type
def epss_get_report_links(st_url, site_url, result_links):
    if helpers.epss_is_tool(link=st_url, tool="pagespeed"):
        helpers.epss_get_links_gps(site_url, result_links)  # Google Page Speed
    elif helpers.epss_is_tool(link=st_url, tool="gtmetrix") and config.use_gt_metrix:
        helpers.epss_get_links_gtmetrix(site_url, result_links)  # GTMetrix
    else:
        helpers.epss_get_links_pingdom(site_url, result_links)  # Pingdom


# report thread
def epss_report_thread(site_url):
    result_links = []
    worker_threads = []
    for st_url in config.URLS:
        worker_thread = threading.Thread(
            target=epss_get_report_links,
            args=(st_url, site_url, result_links),
        )
        worker_threads.append(worker_thread)
        if not worker_thread.is_alive():
            worker_thread.start()
    for thread in worker_threads:
        thread.join()
    result_links.append(site_url)
    config.RESULT_LINKS.append(result_links)


# collect user input link
def epss_get_input_links():
    config.RESULT_LINKS = []
    pb_label.config(text="Analyzing requests")
    threads = []
    for link in config.INPUT_LINKS:
        if not validators.url(link):
            continue
        thread = threading.Thread(target=epss_report_thread, args=(link,))
        threads.append(thread)
        if not thread.is_alive():
            thread.start()
    for thread in threads:
        thread.join()

    return config.RESULT_LINKS


# take screenshots
# Ref: https://stackoverflow.com/a/52572919/
def epss_take_screenshots(file_name, driver):
    original_size = driver.get_window_size()
    required_width = driver.execute_script(
        "return document.body.parentNode.scrollWidth"
    )
    required_height = driver.execute_script(
        "return document.body.parentNode.scrollHeight"
    )
    driver.set_window_size(1440, required_height)
    driver.find_element(By.TAG_NAME, "body").screenshot(
        f"{config.OP_DIR}\{file_name}"
    )  # avoids scrollbar
    driver.set_window_size(original_size["width"], original_size["height"])


# create file names from input links
def epss_create_file_name_groups():
    filename_groups = []
    n = len(config.INPUT_LINKS)
    gps_i = 1
    gtmetrix_i = 2 * n + 1
    pingdom_i = 3 * n + 1 if config.use_gt_metrix else 2 * n + 1
    for link in config.INPUT_LINKS:
        filenames = []
        filenames.append(link)
        slug = helpers.epss_slugify_url(link)
        current_date = datetime.today().strftime("%Y%m%d")

        gps_desktop = (str(gps_i) + "-" + "gps" + "-" + current_date + "-" + slug + "-desktop" + config.IMG_EXT)
        gps_mobile = (str(gps_i + 1) + "-" + "gps" + "-" + current_date + "-" + slug + "-mobile" + config.IMG_EXT)
        filenames.append(gps_desktop)
        filenames.append(gps_mobile)
        gps_i = gps_i + 2

        if config.use_gt_metrix:
            gtmetrix_name = (str(gtmetrix_i) + "-" + "gtmetrix" + "-" + current_date + "-" + slug + config.IMG_EXT)
            gtmetrix_i = gtmetrix_i + 1
            filenames.append(gtmetrix_name)

        pingdom_name = (str(pingdom_i) + "-" + "pingdom" + "-" + current_date + "-" + slug + config.IMG_EXT)
        pingdom_i = pingdom_i + 1
        filenames.append(pingdom_name)

        filename_groups.append(filenames)
    return filename_groups


# get corresponding name group for result group
def epss_get_file_name_group(link):
    groups = epss_create_file_name_groups()
    for filenames in groups:
        if link == filenames[0]:
            return filenames


# thread execution
def epss_screenshots_thread(group):
    screenshots_driver = helpers.epss_get_webdriver()
    screenshots_driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": config.USER_AGENT},
    )
    config.CHROME_DRIVERS.append(screenshots_driver)
    for link in group:
        file_names = epss_get_file_name_group(group[-1])
        can_take_screenshot = True
        if link in config.INPUT_LINKS:
            continue
        try:
            if helpers.epss_is_tool(link=link, tool="pagespeed"):
                parsed_url = urlparse(link)
                form_factor = parse_qs(parsed_url.query)["form_factor"][0]
                file_name = file_names[1] if form_factor == "desktop" else file_names[2]
                html_selector = "div.PePDG"
            elif (
                helpers.epss_is_tool(link=link, tool="gtmetrix")
                and config.use_gt_metrix
            ):
                file_name = file_names[3]
                html_selector = "main.page-report-content"
            elif helpers.epss_is_tool(link=link, tool="pingdom"):
                file_name = file_names[4] if config.use_gt_metrix else file_names[3]
                html_selector = "app-report.ng-star-inserted"

            screenshots_driver.get(link)
            can_take_screenshot = helpers.epss_content_loaded(
                screenshots_driver, html_selector
            )

            if can_take_screenshot and helpers.epss_is_tool(
                link=link, tool="pagespeed"
            ):
                time.sleep(5)  # make sure the report circle is finished

            if can_take_screenshot:
                time.sleep(2)
                epss_take_screenshots(file_name=file_name, driver=screenshots_driver)

            config.success_link.append(link)
        except Exception as e:
            continue

    screenshots_driver.quit()


# execute screenshots for all link input
def epss_execute_screenshots(links):
    pb_label.config(text="Screenshot")
    screenshots_threads = []
    for group in links:
        screenshots_thread = threading.Thread(
            target=epss_screenshots_thread, args=(group,)
        )
        screenshots_threads.append(screenshots_thread)
        screenshots_thread.start()
    for thread in screenshots_threads:
        thread.join()


"""
UI settings
"""

# main function
def epss_main():
    try:
        links = epss_get_input_links()
        links = helpers.epss_add_form_factor(links=links)
        epss_execute_screenshots(links=links)
        pb.stop()
        pb_frame.grid_forget()
        tkinter.messagebox.showinfo(
            title=config.txt_finish_title, message=config.txt_finish_message
        )
        test_button.config(text="Take screenshots", state="normal")
        gtmetrix_checkbox.config(state="normal")
        folder_button.config(state="normal")
        links_text.config(state="normal")
        gtmetrix_entry.config(state="normal")
        test_frame.grid(row=6, sticky="ew")
    except Exception as e:
        tkinter.messagebox.showerror(title=e, message=e)


# start test
def epss_start():
    links = links_text.get("1.0", "end-1c")
    if bool(links) and os.path.exists(folder_entry.get()):
        config.OP_DIR = folder_entry.get()
        config.INPUT_LINKS = [line.strip() for line in links.splitlines()]
        for link in config.INPUT_LINKS:
            if not validators.url(link):
                tkinter.messagebox.showwarning(
                    config.txt_invalid_input_title, config.txt_invalid_input_message
                )
        if config.use_gt_metrix:
            config.API_KEY = gtmetrix_entry.get()
            if not bool(config.API_KEY) or config.API_KEY == config.txt_placeholder_apikey:
                tkinter.messagebox.showwarning(
                    config.txt_empty_api_title, config.txt_empty_api_message
                )
                config.use_gt_metrix = False
        elif (
            not config.use_gt_metrix
            and gtmetrix_entry.get()
            and gtmetrix_entry.get() != config.txt_placeholder_apikey
        ):
            config.use_gt_metrix = True
            config.API_KEY = gtmetrix_entry.get()
        execute_thread = threading.Thread(target=epss_main, args=())
        execute_thread.daemon = True
        execute_thread.start()
        test_button.config(text="Taking Screenshots", state="disabled")
        gtmetrix_checkbox.config(state="disabled")
        folder_button.config(state="disabled")
        links_text.config(state="disabled")
        gtmetrix_entry.config(state="disabled")
        pb_frame.grid(row=6, sticky="ew", ipady=7, pady=20)
        main_label.grid(pady=(14,0))
        pb.start()
    else:
        message = config.txt_please_input_links
        title = config.txt_no_links_title
        if not os.path.exists(folder_entry.get()):
            message = config.txt_please_valid_folder
            title = config.txt_invalid_folder_title
        if folder_entry.get() == config.txt_placeholder_folder or not bool(folder_entry.get()):
            message = config.txt_please_choose_folder
            title = config.txt_no_folder_title
        tkinter.messagebox.showerror(title=title, message=message)


# close window handling
def epss_on_closing():
    if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
        # close chromedriver if quit at random point
        for driver in config.CHROME_DRIVERS:
            if driver.service.is_connectable():
                driver.quit()

        # quit the interface
        main.destroy()


"""
UI
"""

main = tkinter.Tk()

# UI meta
main.title("Easy Page Speed Screenshots")
main.iconbitmap(tkinter.PhotoImage(config.ASSET_FOLDER + "/images/favicon.ico"))
main.resizable(False, False)
main.tk.call("tk", "scaling", 1.0)
main.config(bg=config.primary_color)

main_frame = tkinter.Frame(main)
main_frame.grid(row=0, column=0, padx=20, pady=(20, 0))
main_frame.config(bg=config.primary_color)

main_label = tkinter.Label(
    main_frame,
    text="Easy Page Speed Screenshots",
    bg=config.primary_color,
    fg=config.txt_color,
    font=(config.font, 25, "bold"),
)
main_label.grid(row=0, column=0, pady=20)
main_label.config(bg=config.primary_color)

# create all of the main containers
folder_frame = tkinter.Frame(main_frame)
links_frame = tkinter.Frame(main_frame)
gtmetrix_frame = tkinter.Frame(main_frame)
gtmetrix_api_frame = tkinter.Frame(gtmetrix_frame)
test_frame = tkinter.Frame(main_frame)
pb_frame = tkinter.Frame(main_frame)

# layout all of the main containers
folder_frame.grid(row=1, sticky="ew")
links_frame.grid(row=2, sticky="ew")
gtmetrix_frame.grid(row=3, sticky="ew")
test_frame.grid(row=6, sticky="ew")

# select folder
folder_entry = entry.EntryWithPlaceholder(folder_frame, config.txt_placeholder_folder)
folder_entry.grid(row=1, column=0, ipadx=7, ipady=7)

button_image = tkinter.PhotoImage(file=config.ASSET_FOLDER + "/images/icon-folder.png")
folder_button = tkinter.Button(
    folder_frame,
    image=button_image,
    borderwidth=0,
    bg=config.color_white,
    highlightthickness=0,
    relief="flat",
    command=lambda: helpers.epss_browse_button(folder_entry),
    height=20,
    width=20,
)
folder_button.place(x=510, y=8)

folder_frame.config(bg=config.primary_color, pady=15)

# links
links_label = tkinter.Label(
    links_frame,
    text="URLs for the page speed screenshots",
    font=(config.font, config.body_txt),
)
links_label.grid(row=0, column=0, sticky="ew", pady=3)
links_label.config(bg=config.primary_color)

links_text = tkinter.Text(
    links_frame,
    height=20,
    font=(config.font, config.body_txt),
    width=config.app_width,
    highlightbackground=config.color_black,
    borderwidth=2,
    relief="solid",
)
links_text.grid(row=1, column=0, pady=10, ipadx=7, ipady=7)
links_frame.config(bg=config.primary_color)

# gtmetrix
gtmetrix_frame.config(bg=config.primary_color, pady=5)
gtmetrix_checkbox = tkinter.Checkbutton(
    gtmetrix_frame,
    activebackground=config.primary_color,
    command=lambda: helpers.epss_toggle_api_key_field(gtmetrix_api_frame),
)
gtmetrix_checkbox.config(bg=config.primary_color)
gtmetrix_checkbox.grid(row=0, column=0, padx=(0, 7), pady=7)

gtmetrix_label = tkinter.Label(
    gtmetrix_frame, text="Use GTmetrix", font=(config.font, config.body_txt)
)
gtmetrix_label.grid(row=0, column=1)
gtmetrix_label.config(bg=config.primary_color)

gtmetrix_entry = entry.EntryWithPlaceholder(gtmetrix_api_frame, config.txt_placeholder_apikey, 40)
gtmetrix_entry.grid(row=0, column=0, ipadx=7, ipady=7)

gtmetrix_api_frame.config(bg=config.primary_color)

# test button
test_button = tkinter.Button(
    test_frame,
    text="Take screenshots",
    width=config.app_width,
    fg=config.color_white,
    highlightbackground=config.color_black,
    borderwidth=2,
    bg=config.txt_color,
    relief="solid",
    font=(config.font, config.body_txt),
    command=epss_start,
)
test_button.grid(row=0, column=0, ipadx=5, ipady=7, pady=20)
test_frame.config(bg=config.primary_color)

# copyright
main_label = tkinter.Label(
    main_frame, text="Copyright © ViiVue 2023", font=(config.font, 11)
)
main_label.grid(row=7, column=0, pady=(20, 0))
main_label.config(bg=config.primary_color)

# progress bar
pb_style = ttk.Style()
pb_style.theme_use("clam")
pb_style.configure(
    "default.Horizontal.TProgressbar",
    troughcolor=config.color_black,
    background=config.primary_color,
    bordercolor=config.color_black,
)
pb = ttk.Progressbar(
    pb_frame,
    style="default.Horizontal.TProgressbar",
    orient="horizontal",
    mode="indeterminate",
    length=545,
)
pb.grid(row=0, column=0)
pb_label = tkinter.Label(pb_frame)
pb_label.grid(row=1, column=0)
pb_label.config(bg=config.primary_color)
pb_frame.config(bg=config.primary_color)

# center window
screen_width = main.winfo_screenwidth()
screen_height = main.winfo_screenheight()

x_cordinate = int((screen_width / 2) - (config.window_width / 2))
y_cordinate = int((screen_height / 2) - (config.window_height / 2))

main.geometry(
    "{}x{}+{}+{}".format(
        config.window_width, config.window_height, x_cordinate, y_cordinate
    )
)

def epss_on_closing():
    if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
        # close chromedriver if quit at random point

        for driver in config.CHROME_DRIVERS: 
            if driver.service.is_connectable():
                driver.quit()

        # quit the interface
        main.destroy()

# run
main.protocol("WM_DELETE_WINDOW", epss_on_closing)
main.mainloop()
