import os
import tkinter
import requests

from tkinter import ttk
from tkinter import filedialog
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os.path

from . import config

# webdriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_experimental_option(
    "excludeSwitches", ["enable-logging"]
)  # disable output the 'DevTools listening on ws://127.0.0.1:56567/devtools/browser/' line
options.add_argument("--log-level=3")

"""
General
"""

# close chromedriver if not quit
def epss_close_drivers():
    for driver in config.CHROME_DRIVERS:
        if driver.service.is_connectable():
            driver.quit()


# check if specific content exists
def epss_content_loaded(driver, selector):
    try:
        report = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return True
    except Exception as e:
        return False


# get webdriver with options
def epss_get_webdriver():
    return webdriver.Chrome(
        executable_path=config.ASSET_FOLDER + "/driver/chromedriver.exe",
        options=options,
    )


# check if json field exists
def epss_json_field_exists(field, json):
    if field in json:
        return json[field]
    else:
        return False


# check specific tool
def epss_is_tool(link, tool):
    return link.find(tool) != -1


# replace character in url to append to file name
# e.g https://gtmetrix.com/ will become https-gtmetrix-com
def epss_slugify_url(url):
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


# append form_factor param for Google Page Speed
def epss_add_form_factor(links):
    new_links = []
    for group in links:
        current_new_group = []
        for link in group:
            if epss_is_tool(link=link, tool="pagespeed"):
                current_new_group.append(link + "?form_factor=desktop")
                current_new_group.append(link + "?form_factor=mobile")
            else:
                current_new_group.append(link)
        new_links.append(current_new_group)
    return new_links


"""
UI
"""

# browse folder path
def epss_browse_button(folder_entry):
    directory = filedialog.askdirectory()
    folder_entry.delete(0, "end")
    folder_entry.insert(0, directory)
    folder_entry.configure(fg=config.txt_color)
    config.OP_DIR = directory


# set use GTmetrix & toggle insert field
def epss_toggle_api_key_field(gtmetrix_api_frame):
    config.use_gt_metrix = True if not config.use_gt_metrix else False
    if config.use_gt_metrix:
        gtmetrix_api_frame.grid(row=0, column=2, padx=10, pady=0, columnspan=2)
    else:
        gtmetrix_api_frame.grid_forget()


"""
Handle report links
"""

# get report from Google Page Speed
def epss_get_links_gps(site_url, result_links):
    res = ""
    get_link_driver = epss_get_webdriver()
    get_link_driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": config.USER_AGENT},
    )

    config.CHROME_DRIVERS.append(get_link_driver)

    get_link_driver.get(config.PS_URL)
    input_field = get_link_driver.find_element(By.CSS_SELECTOR, "input")
    input_field.send_keys(site_url)  # Replace with your desired URL
    form = get_link_driver.find_element(By.CSS_SELECTOR, "form")
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
    res = unquote(new_link)

    if res != "":
        res = res.split("?", 1)[0]

    result_links.append(res)
    get_link_driver.quit()


# get report from Pingdom
def epss_get_links_pingdom(site_url, result_links):
    while 1:
        try:
            # Desire url: https://tools.pingdom.com/#62079906f1c00000 with 62079906f1c00000 as id
            base_url = config.PD_URL + "v1/tests/"
            url = base_url + "create"
            data = {"url": site_url}
            # call the api to receive the id
            resp = requests.post(url, json=data)
            resp = resp.json()
            result_id = resp["id"]
            return_url = config.PD_URL + "#" + result_id  # create result url
            result_links.append(return_url)
            break
        except Exception as e:
            continue


# get report from GTMetrix with API
# docs: https://gtmetrix.com/api/docs/2.0/#api-test-start
def epss_get_links_gtmetrix(site_url, result_links):
    from requests.structures import CaseInsensitiveDict

    if not bool(config.use_gt_metrix):
        return
    while 1:
        try:
            base_url = config.GM_URL
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
                site_url
            )
            resp = requests.post(
                url, auth=(config.API_KEY.lstrip(), ""), headers=headers, data=data
            )

            if resp.status_code == 401:
                tkinter.messagebox.showwarning(
                    title=config.txt_warning_title, message=config.txt_gt_invalid_api
                )
                config.use_gt_metrix = False
                return

            # API key limited
            if resp.status_code == 402:
                tkinter.messagebox.showwarning(
                    title=config.txt_warning_title,
                    message=config.txt_gt_reached_limit,
                )
                config.use_gt_metrix = False
                return

            resp = resp.json()
            report = ""
            while 1:
                links = epss_json_field_exists("links", resp)
                self_link = epss_json_field_exists("self", links)
                test_result = requests.get(
                    self_link,
                    auth=(config.API_KEY.lstrip(), ""),
                    headers=headers,
                )
                test_result = test_result.json()
                data = epss_json_field_exists("data", test_result)
                data_links = epss_json_field_exists("links", data)
                if "report_url" in data_links:
                    report = data_links["report_url"]
                    break
            result_links.append(report)
            break
        except Exception as e:
            continue
