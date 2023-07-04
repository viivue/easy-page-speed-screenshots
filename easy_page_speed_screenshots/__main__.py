import os
import tkinter
from tkinter import ttk
from tkinter import filedialog
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

from . import __version__
from . import config
from . import helpers

# webdriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_experimental_option(
    "excludeSwitches", ["enable-logging"]
)  # disable output the 'DevTools listening on ws://127.0.0.1:56567/devtools/browser/' line
options.add_argument("--log-level=3")

# get report of gtmetrix with API
# docs: https://gtmetrix.com/api/docs/2.0/#api-test-start
def epss_get_link_gtmetrix(tool, link, current_link):
    import requests
    from requests.structures import CaseInsensitiveDict

    while 1:
        try:
            base_url = tool
            headers = CaseInsensitiveDict()
            headers["Content-Type"] = "application/vnd.api+json"
            url = base_url + "/api/2.0/tests"
            data = """
            {
                 "data": {
                    "type": "test",
                    "attributes": {
                       "url": "%s",
                       "adblock":0
                    }
                 }
            }
            """ % (
                link
            )
            resp = requests.post(
                url, auth=(config.API_KEY.lstrip(), ""), headers=headers, data=data
            )

            # API key limited
            if resp.status_code == 402:
                tkinter.messagebox.showwarning(
                    title="API Key", message="Your API Key has reached limit"
                )
                config.use_gt_metrix = False
                return

            resp = resp.json()
            report = ""
            while 1:
                links = helpers.epss_json_field_exists("links", resp)
                self_link = helpers.epss_json_field_exists("self", links)
                test_result = requests.get(
                    self_link,
                    auth=(config.API_KEY.lstrip(), ""),
                    headers=headers,
                )
                test_result = test_result.json()
                data = helpers.epss_json_field_exists("data", test_result)
                data_links = helpers.epss_json_field_exists("links", data)
                if "report_url" in data_links:
                    report = data_links["report_url"]
                    break
            current_link.append(report)
            break
        except Exception as e:
            continue

def epss_result_thread_function(link):
    current_link = []
    worker_threads = []
    for tool in config.TOOLS:
        if helpers.epss_is_tool(link=tool, tool="pagespeed"):
            # Desire url: https://pagespeed.web.dev/analysis/https-en-wikipedia-org-wiki-Main_Page/5ohv3rfffg (without ?form_factor=mobile)
            worker_thread = threading.Thread(
                target=helpers.epss_submit_by_form,
                args=(
                    tool,
                    link,
                    current_link,
                ),
            )
        elif helpers.epss_is_tool(link=tool, tool="gtmetrix") and config.use_gt_metrix:
            worker_thread = threading.Thread(
                target=epss_get_link_gtmetrix,
                args=(
                    tool,
                    link,
                    current_link,
                ),
            )
        elif helpers.epss_is_tool(link=tool, tool="pingdom"):
            worker_thread = threading.Thread(
                target=helpers.epss_get_link_pingdom,
                args=(
                    tool,
                    link,
                    current_link,
                ),
            )
        worker_threads.append(worker_thread)
        if not worker_thread.is_alive():
            worker_thread.start()
    for thread in worker_threads:
        thread.join()
    current_link.append(link)
    config.RESULT_LINKS.append(current_link)

# run through all testing tool
def epss_send_link_for_test(links):
    config.RESULT_LINKS = []
    pb_label.config(text="Analyzing requests")
    threads = []
    for link in links:
        thread = threading.Thread(target=epss_result_thread_function, args=(link,))
        threads.append(thread)
        if not thread.is_alive():
            thread.start()
    for thread in threads:
        thread.join()

    return config.RESULT_LINKS


# collect user input link
def epss_user_input():
    res_inputs = epss_send_link_for_test(config.INPUT_LINK)
    return res_inputs

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
def epss_create_file_name_array():
    filename_group_array = []
    n = len(config.INPUT_LINK)
    gps_i = 1
    gtmetrix_i = 2 * n + 1
    pingdom_i = 3 * n + 1 if config.use_gt_metrix else 2 * n + 1
    for link in config.INPUT_LINK:
        filenames = []
        filenames.append(link)
        link = helpers.epss_replace_url(link)
        current_date = datetime.today().strftime("%Y%m%d")
        gps_desktop = (
            str(gps_i)
            + "-"
            + "gps"
            + "-"
            + current_date
            + "-"
            + link
            + "-desktop"
            + ".png"
        )
        gps_mobile = (
            str(gps_i + 1)
            + "-"
            + "gps"
            + "-"
            + current_date
            + "-"
            + link
            + "-mobile"
            + ".png"
        )
        filenames.append(gps_desktop)
        filenames.append(gps_mobile)
        gps_i = gps_i + 2
        if config.use_gt_metrix:
            gtmetrix_name = (
                str(gtmetrix_i)
                + "-"
                + "gtmetrix"
                + "-"
                + current_date
                + "-"
                + link
                + ".png"
            )
            gtmetrix_i = gtmetrix_i + 1
            filenames.append(gtmetrix_name)
        pingdom_name = (
            str(pingdom_i) + "-" + "pingdom" + "-" + current_date + "-" + link + ".png"
        )
        pingdom_i = pingdom_i + 1
        filenames.append(pingdom_name)
        filename_group_array.append(filenames)
    return filename_group_array

# get corresponding name group for result group
def epss_get_file_name_group(link):
    groups = epss_create_file_name_array()
    for filenames in groups:
        if link == filenames[0]:
            return filenames

# thread execution
def epss_screenshots_thread_function(group):
    screenshots_driver = helpers.epss_get_webdriver()
    screenshots_driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {
            "userAgent": config.USER_AGENT
        },
    )
    for link in group:
        file_names = epss_get_file_name_group(group[-1])
        can_take_screenshot = True
        if link in config.INPUT_LINK:
            continue
        try:
            if helpers.epss_is_tool(link=link, tool="pagespeed"):
                parsed_url = urlparse(link)
                form_factor = parse_qs(parsed_url.query)["form_factor"][0]
                file_name = file_names[1] if form_factor == "desktop" else file_names[2]
                html_selector = "div.PePDG"
            elif helpers.epss_is_tool(link=link, tool="gtmetrix") and config.use_gt_metrix:
                file_name = file_names[3]
                html_selector = "main.page-report-content"
            elif helpers.epss_is_tool(link=link, tool="pingdom"):
                file_name = file_names[4] if config.use_gt_metrix else file_names[3]
                html_selector = "app-report.ng-star-inserted"

            screenshots_driver.get(link)
            can_take_screenshot = helpers.epss_content_loaded(
                screenshots_driver, html_selector
            )
            if can_take_screenshot:
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
            target=epss_screenshots_thread_function, args=(group,)
        )
        screenshots_threads.append(screenshots_thread)
        screenshots_thread.start()
    for thread in screenshots_threads:
        thread.join()

"""
UI settings
"""

# set use GTmetrix & toggle insert field
def epss_toggle_api_key_field():
    config.use_gt_metrix = True if not config.use_gt_metrix else False
    if config.use_gt_metrix:
        gtmetrix_api_frame.grid(row=4, column=0, padx=10, pady=15)
    else:
        gtmetrix_api_frame.grid_forget()


# browse folder path
def epss_browse_button():
    directory = filedialog.askdirectory()
    folder_entry.delete(0, "end")
    folder_entry.insert(0, directory)
    config.OP_DIR = directory

# main function
def epss_main():
    try:
        links = epss_user_input()
        links = helpers.epss_add_form_factor(links=links)
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

# start test
def epss_start():
    links = links_text.get("1.0", "end-1c")
    config.INPUT_LINK = [line.strip() for line in links.splitlines()]
    config.API_KEY = gtmetrix_entry.get()
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

"""
UI
"""

main = tkinter.Tk()

# UI meta
main.title("Easy Page Speed Screenshots")
main.iconbitmap(
    tkinter.PhotoImage(config.ASSET_FOLDER + '/images/favicon.ico')
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
main_label = tkinter.Label(main_frame, text="Copyright © ViiVue 2023", font=("Nirmala UI", 10))
main_label.grid(row=7, column=0, pady=(30,0))

# progress bar
pb_frame = tkinter.Frame(main_frame)
pb = ttk.Progressbar(pb_frame, orient="horizontal", mode="indeterminate", length=280)
pb.grid(row=0, column=0)
pb_label = tkinter.Label(pb_frame)
pb_label.grid(row=1, column=0)

main.mainloop()