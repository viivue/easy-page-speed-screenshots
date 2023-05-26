"""
Tool to bulk save page speed screenshots

Author: Viivue
Date: May 26, 2023
Version: 1.0.0
"""

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
import sys
import pyglet
from ctypes import windll
windll.shcore.SetProcessDpiAwareness(2)

"""
Define Global Variables
"""

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_experimental_option(
    "excludeSwitches", ["enable-logging"]
)  # disable output the 'DevTools listening on ws://127.0.0.1:56567/devtools/browser/' line
options.add_argument("--log-level=3")

"""
Define functions
"""

use_gt_metrix = False


def epss_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


# check if specific content exists
def epss_content_loaded(driver, selector, link):
    try:
        report = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return True
    except Exception as e:
        return False


# submit link for testing
def epss_submit_link(tool, link, input_selector="", form_selector=""):
    get_link_driver = webdriver.Chrome(
        executable_path=epss_resource_path("./driver/chromedriver.exe"), options=options
    )
    get_link_driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.4103.97 Safari/537.36"
        },
    )

    get_link_driver.get(tool)
    input_field = get_link_driver.find_element(
        By.CSS_SELECTOR, "input" + input_selector
    )
    input_field.send_keys(link)  # Replace with your desired URL
    form = get_link_driver.find_element(By.CSS_SELECTOR, "form" + form_selector)
    form.submit()

    from urllib.parse import unquote

    try:
        report = WebDriverWait(get_link_driver, 40).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.PePDG"))
        )
    except Exception as e:
        return ""
    new_link = get_link_driver.current_url
    get_link_driver.quit()
    return unquote(new_link)


def epss_submit_by_form(tool, link, current_link):
    res = epss_submit_link(tool=tool, link=link)
    if res != "":
        res = res.split("?", 1)[0]
    current_link.append(res)


# get report of pingdom with api
def epss_get_link_pingdom(tool, link, current_link):
    import requests

    while 1:
        try:
            # Desire url: https://tools.pingdom.com/#62079906f1c00000 with 62079906f1c00000 as id
            base_url = tool + "v1/tests/"
            url = base_url + "create"
            data = {"url": link}
            # call the api to receive the id
            resp = requests.post(url, json=data)
            resp = resp.json()
            result_id = resp["id"]
            return_url = tool + "#" + result_id  # create result url
            current_link.append(return_url)
            break
        except Exception as e:
            continue


API_KEY = ""

# check if json field exists
def epss_json_field_exists(field, json):
    if field in json:
        return json[field]
    else:
        return False


# get report of gtmetrix with api
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
                url, auth=(API_KEY.lstrip(), ""), headers=headers, data=data
            )
            if resp.status_code == 402:
                tkinter.messagebox.showwarning(
                    title="API Key", message="Your API Key has reached limit"
                )
                global use_gt_metrix
                use_gt_metrix = False
                return
            resp = resp.json()
            report = ""
            while 1:
                links = epss_json_field_exists("links", resp)
                self_link = epss_json_field_exists("self", links)
                test_result = requests.get(
                    self_link,
                    auth=(API_KEY.lstrip(), ""),
                    headers=headers,
                )
                test_result = test_result.json()
                data = epss_json_field_exists("data", test_result)
                data_links = epss_json_field_exists("links", data)
                if "report_url" in data_links:
                    report = data_links["report_url"]
                    break
            current_link.append(report)
            break
        except Exception as e:
            continue


def epss_result_thread_function(link):
    tools = [
        "https://pagespeed.web.dev/",
        "https://gtmetrix.com/",
        "https://tools.pingdom.com/",
    ]
    current_link = []
    worker_threads = []
    for tool in tools:
        if epss_is_tool(link=tool, tool="pagespeed.web"):
            # Desire url: https://pagespeed.web.dev/analysis/https-en-wikipedia-org-wiki-Main_Page/5ohv3rfffg (without ?form_factor=mobile)
            worker_thread = threading.Thread(
                target=epss_submit_by_form,
                args=(
                    tool,
                    link,
                    current_link,
                ),
            )
            worker_threads.append(worker_thread)
            worker_thread.start()
        elif epss_is_tool(link=tool, tool="gtmetrix") and use_gt_metrix:
            worker_thread = threading.Thread(
                target=epss_get_link_gtmetrix,
                args=(
                    tool,
                    link,
                    current_link,
                ),
            )
            worker_threads.append(worker_thread)
            worker_thread.start()
        elif epss_is_tool(link=tool, tool="pingdom"):
            worker_thread = threading.Thread(
                target=epss_get_link_pingdom,
                args=(
                    tool,
                    link,
                    current_link,
                ),
            )
            worker_threads.append(worker_thread)
            worker_thread.start()
    for thread in worker_threads:
        thread.join()
    current_link.append(link)
    RESULT_LINKS.append(current_link)


# run through all testing tool
def epss_send_link_for_test(links):
    global RESULT_LINKS
    RESULT_LINKS = []
    pb_label.config(text="Analyzing requests")
    threads = []
    for link in links:
        thread = threading.Thread(target=epss_result_thread_function, args=(link,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    return RESULT_LINKS


# collect user input link
def epss_user_input():
    global INPUT_LINK
    global OP_DIR
    global API_KEY
    res_inputs = epss_send_link_for_test(INPUT_LINK)
    return res_inputs


# append form_factor if url is pagespeed
def epss_add_form_factor(links):
    new_links = []
    for group in links:
        current_new_group = []
        for link in group:
            if link.find("pagespeed.web.dev") != -1:
                current_new_group.append(link + "?form_factor=desktop")
                current_new_group.append(link + "?form_factor=mobile")
            else:
                current_new_group.append(link)
        new_links.append(current_new_group)
    return new_links


# replace character in url to append to file name
# e.g https://gtmetrix.com/ will become https-gtmetrix-com
def epss_replace_url(url):
    # replace special characters with '-'
    url = url.replace("://", "-")
    url = url.replace("/", "-")
    url = url.replace(".", "-")
    url = url.replace(":", "-")
    url = url.replace("?", "-")
    url = url.replace("=", "-")
    # if the url ends with '/' the url will contain '-' at the end, remove it
    if url.endswith("-"):
        url = url.removesuffix("-")
    return url


# check specific tool
def epss_is_tool(link, tool):
    return link.find(tool) != -1


# screenshots
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
        f"{OP_DIR}\{file_name}"
    )  # avoids scrollbar
    driver.set_window_size(original_size["width"], original_size["height"])


# create file names from input links
def epss_create_file_name_array():
    filename_group_array = []
    n = len(INPUT_LINK)
    gps_i = 1
    gtmetrix_i = 2 * n + 1
    pingdom_i = 3 * n + 1 if use_gt_metrix else 2 * n + 1
    for link in INPUT_LINK:
        filenames = []
        filenames.append(link)
        link = epss_replace_url(link)
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
        if use_gt_metrix:
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


# function use in screenshots thread
success_link = []


def epss_screenshots_thread_function(group):
    screenshots_driver = webdriver.Chrome(
        executable_path=epss_resource_path("./driver/chromedriver.exe"), options=options
    )
    screenshots_driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.4103.97 Safari/537.36"
        },
    )
    for link in group:
        file_names = epss_get_file_name_group(group[-1])
        can_take_screenshot = True
        if link in INPUT_LINK:
            continue
        try:
            if epss_is_tool(link=link, tool="pagespeed"):
                parsed_url = urlparse(link)
                form_factor = parse_qs(parsed_url.query)["form_factor"][0]
                file_name = file_names[1] if form_factor == "desktop" else file_names[2]
                screenshots_driver.get(link)
                can_take_screenshot = epss_content_loaded(
                    screenshots_driver, "div.PePDG", link
                )
            elif epss_is_tool(link=link, tool="gtmetrix") and use_gt_metrix:
                file_name = file_names[3]
                screenshots_driver.get(link)
                can_take_screenshot = epss_content_loaded(
                    screenshots_driver, "main.page-report-content", link
                )
            elif epss_is_tool(link=link, tool="pingdom"):
                file_name = file_names[4] if use_gt_metrix else file_names[3]
                screenshots_driver.get(link)
                can_take_screenshot = epss_content_loaded(
                    screenshots_driver, "app-report.ng-star-inserted", link
                )
            time.sleep(5)
            if can_take_screenshot:
                epss_take_screenshots(file_name=file_name, driver=screenshots_driver)
            global success_link
            success_link.append(link)
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
Main Function
"""


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
        gtmetrix_api_frame.grid(row=4, column=0, padx=10, pady=10)
    else:
        gtmetrix_api_frame.grid_forget()


# browse folder path
def epss_browse_button():
    directory = filedialog.askdirectory()
    folder_entry.delete(0, "end")
    folder_entry.insert(0, directory)
    global OP_DIR
    OP_DIR = directory


execute_threads = []

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

pyglet.font.add_file(epss_resource_path('./assets/BasisGrotesquePro-Bold.otf'))
pyglet.font.add_file(epss_resource_path('./assets/BasisGrotesquePro-Regular.otf'))


main = tkinter.Tk()

main.title("Easy Page Speed Screenshots")
program_directory = sys.path[0]
main.iconbitmap(
    tkinter.PhotoImage(epss_resource_path("./assets/icons8-screenshot-64.ico"))
)
main.resizable(False, False)
main.tk.call('tk', 'scaling', 1.0)

main_frame = tkinter.Frame(main)
main_frame.grid(row=0, column=0, padx=10, pady=10)

main_label = tkinter.Label(
    main_frame, text="Easy Page Speed Screenshots", font=("Basis Grotesque Pro", 18, "bold")
)
main_label.grid(row=0, column=0, pady=30)

# select folder
folder_frame = tkinter.Frame(main_frame)
folder_frame.grid(row=1, column=0)
folder_label = tkinter.Label(folder_frame, text="Choose result folder", font=("Basis Grotesque Pro", 14))
folder_label.grid(row=0, column=0)
folder_entry = tkinter.Entry(folder_frame, width=50, font=("Basis Grotesque Pro", 14))
folder_entry.grid(row=0, column=1, padx=10)
folder_button = tkinter.Button(
    folder_frame, text="Browse directory", command=epss_browse_button, font=("Basis Grotesque Pro", 14)
)
folder_button.grid(row=0, column=2)

# links
links_frame = tkinter.Frame(main_frame)
links_frame.grid(row=2, column=0,pady=15)
links_label = tkinter.Label(links_frame, text="URLs for the page speed screenshots", font=("Basis Grotesque Pro", 14))
links_label.grid(row=0, column=0)
links_text = tkinter.Text(links_frame, height=20, font=("Basis Grotesque Pro", 14))
links_text.grid(row=1, column=0, pady=5, padx=10)

# gtmetrix

gtmetrix_frame = tkinter.Frame(main_frame)
gtmetrix_frame.grid(row=3, column=0)
gtmetrix_checkbox = tkinter.Checkbutton(
    gtmetrix_frame, command=epss_toggle_api_key_field
)
gtmetrix_checkbox.grid(row=0, column=0)
gtmetrix_label = tkinter.Label(gtmetrix_frame, text="Use GTmetrix", font=("Basis Grotesque Pro", 14))
gtmetrix_label.grid(row=0, column=1)
gtmetrix_api_frame = tkinter.Frame(main_frame)
gtmetrix_api_label = tkinter.Label(gtmetrix_api_frame, text="API Key", font=("Basis Grotesque Pro", 14))
gtmetrix_api_label.grid(row=0, column=0, padx=10)
gtmetrix_entry = tkinter.Entry(gtmetrix_api_frame, width=50, font=("Basis Grotesque Pro", 14))
gtmetrix_entry.grid(row=0, column=1)


# test button
test_frame = tkinter.Frame(main_frame)
test_frame.grid(row=6, column=0)
test_button = tkinter.Button(test_frame, text="Take screenshots", font=("Basis Grotesque Pro", 14),command=epss_start)
test_button.grid(row=0, column=0, pady=20)

# copyright
main_label = tkinter.Label(main_frame, text="Copyright by ViiVue 2023 ©", font=("Basis Grotesque Pro", 10))
main_label.grid(row=7, column=0)
# progress bar
pb_frame = tkinter.Frame(main_frame)
pb = ttk.Progressbar(pb_frame, orient="horizontal", mode="indeterminate", length=280)
pb.grid(row=0, column=0)
pb_label = tkinter.Label(pb_frame)
pb_label.grid(row=1, column=0)

main.mainloop()
