from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import sys
import os
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime
import threading

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

running = True

def epss_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# running dot
def epss_running_dot_animation():
    while running:
        for dot_count in range(5):
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write("\b" * 5)
        sys.stdout.flush()  
        sys.stdout.write(" " * 5)
        sys.stdout.flush()
        sys.stdout.write("\b" * 5)
        sys.stdout.flush()

# check if specific content exists
def epss_content_loaded(driver, selector, link):
    try:
        report = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return True
    except Exception as e:
        print("Content on " + link + " took too long to load. Skipping screenshot")
        return False


# submit link for testing
def epss_submit_link(tool, link, input_selector="", form_selector=""):
    get_link_driver = webdriver.Chrome(executable_path=epss_resource_path("./driver/chromedriver.exe"),options=options)
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
        print("Running test on " + link + " on GPS took so long. Skipping")
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
                       "adblock":1
                    }
                 }
            }
            """ % (
                link
            )
            resp = requests.post(url, auth=(API_KEY, ""), headers=headers, data=data)
            if (resp.status_code == 402):
                print("\nYour API key has reached limit")
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
                    auth=(API_KEY, ""),
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
    print("Analyze requests: ")
    threads = []
    for link in links:
        thread = threading.Thread(target=epss_result_thread_function, args=(link,))
        threads.append(thread)
        thread.start()
    running_thread = threading.Thread(target=epss_running_dot_animation, args=())
    running_thread.start()
    for thread in tqdm(threads, ncols=65):
        thread.join()
    global running
    running = False
    running_thread.join()
    running = True
    
    return RESULT_LINKS


# collect user input link
def epss_user_input():
    print(
        """
Easy Page Speed Screenshot (EPSS)
-----
Bulk save page speed screenshots automatically.
List of tools supported:
• https://pagespeed.web.dev/
• https://gtmetrix.com/
• https://tools.pingdom.com/
-----
    """
    )
    global INPUT_LINK
    INPUT_LINK = []
    global OP_DIR
    print("Input full directory path to store screenshot result: ")
    OP_DIR = input()
    print("Do you want to test with GTmetrix (need an API key to proceed)?")
    print("1. Yes")
    print("2. No")
    choice = input()
    if int(choice) == 1:
        global use_gt_metrix
        use_gt_metrix = True
        print("Enter GTmextrix API key (required): ")
        global API_KEY
        API_KEY = input()
    print(
        "Input site URLs for the page speed screenshots (use <Enter> for multiple links & type 'done' to take screenshots): "
    )
    while 1:
        input_link = input()
        if input_link == "done":
            break
        elif input_link == "":
            continue
        INPUT_LINK.append(input_link)
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
    gtmetrix_i = 2*n + 1
    pingdom_i = 3*n + 1 if use_gt_metrix else 2*n + 1
    for link in INPUT_LINK:
        filenames = []
        filenames.append(link)
        link = epss_replace_url(link)
        current_date = datetime.today().strftime("%Y%m%d")
        gps_desktop = (
            "gps"
            + "-"
            + str(gps_i)
            + "-"
            + current_date
            + "-"
            + link
            + "-desktop"
            + ".png"
        )
        gps_mobile = (
            "gps"
            + "-"
            + str(gps_i + 1)
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
                "gtmetrix"
                + "-"
                + str(gtmetrix_i)
                + "-"
                + current_date
                + "-"
                + link
                + ".png"
            )
            gtmetrix_i = gtmetrix_i + 1
            filenames.append(gtmetrix_name)
        pingdom_name = (
            "pingdom" + "-" + str(pingdom_i) + "-" + current_date + "-" + link + ".png"
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
    screenshots_driver = webdriver.Chrome(executable_path=epss_resource_path("./driver/chromedriver.exe"),options=options)
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
            print(e)
            print("Error at: ", link)
            continue


# execute screenshots for all link input
def epss_execute_screenshots(links):
    print("Screenshots: ")
    screenshots_threads = []
    for group in links:
        screenshots_thread = threading.Thread(
            target=epss_screenshots_thread_function, args=(group,)
        )
        screenshots_threads.append(screenshots_thread)
        screenshots_thread.start()
    running_thread = threading.Thread(target=epss_running_dot_animation, args=())
    running_thread.start()
    for thread in tqdm(screenshots_threads, ncols=65):
        thread.join()
    global running
    running = False
    running_thread.join()
    running = True
    

"""
Main Function
"""


def epss_main():
    try:
        while 1:
            links = epss_user_input()
            links = epss_add_form_factor(links=links)
            epss_execute_screenshots(links=links)
            print("Result URLs of taken screenshots: ")
            for link in success_link:
                print(link + "\n")
            print("To quit the tool, type 'exit'")
            choice = input()
            if choice == "exit":
                break
    except Exception as e:
        print(e)
        input()


epss_main()
