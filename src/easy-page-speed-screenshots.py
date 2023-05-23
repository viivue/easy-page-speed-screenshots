from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from tqdm import tqdm
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
options.add_argument("--log-level=3")

threads = []
"""
Define functions
"""

"""
Page speed and GTmetrix run through 2 pages:
1. Analyze Page
2. Result Page
So this function run the same code twice to get the result page
"""

# submit link for testing
def epss_submit_link(tool, link, input_selector="", form_selector=""):
    get_link_driver = webdriver.Chrome(options=options)
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

    gps_fail = 0

    while 1:
        try:
            report = get_link_driver.find_element(By.CSS_SELECTOR, "div.PePDG")
            break
        except Exception as e:
            if gps_fail <= 10:
                continue
            else:
                break    
    new_link = get_link_driver.current_url
    print(unquote(new_link))
    return unquote(new_link)


def epss_submit_by_form(tool, link, current_link):
    res = epss_submit_link(tool=tool, link=link)
    res = res.split("?", 1)[0]
    current_link.append(res)


fail_pingdom = 0


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
            global fail_pingdom
            if fail_pingdom <= 10:
                print("Run test on " + link + " failed. Trying again")
                fail_pingdom = fail_pingdom + 1
                continue
            else:
                break


API_KEY = ""

# check if json field exists
def epss_json_field_exists(field, json):
    if field in json:
        return json[field]
    else:
        return False


def epss_get_link_gtmetrix(tool, link, current_link):
    import requests
    from requests.structures import CaseInsensitiveDict

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


def epss_thread_function(link):
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
        elif epss_is_tool(link=tool, tool="gtmetrix"):
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
    print("Getting results: ")
    for link in links:
        thread = threading.Thread(target=epss_thread_function, args=(link,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return RESULT_LINKS


# collect user input link
def epss_user_input():
    global INPUT_LINK
    INPUT_LINK = []
    global OP_DIR
    print("Enter save directory: ")
    OP_DIR = input()
    print("Enter API Key for GTmetrix: ")
    global API_KEY
    API_KEY = input()
    print("Enter links to test (type 'done' to finish input): ")
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
def epss_replace_url(url):
    # replace special characters with '-'
    url = url.replace("://", "-")
    url = url.replace("/", "-")
    url = url.replace(".", "-")
    # if the url ends with '/' the url will contain '-' at the end, remove it
    if url.endswith("-"):
        url = url.removesuffix("-")
    return url


# check specific tool
def epss_is_tool(link, tool):
    return link.find(tool) != -1


# Screenshot
# Ref: https://stackoverflow.com/a/52572919/
def epss_take_screenshot(file_name, driver):
    original_size = driver.get_window_size()
    required_width = driver.execute_script(
        "return document.body.parentNode.scrollWidth"
    )
    required_height = driver.execute_script(
        "return document.body.parentNode.scrollHeight"
    )
    driver.set_window_size(2560, required_height)
    driver.find_element(By.TAG_NAME, "body").screenshot(
        f"{OP_DIR}\{file_name}"
    )  # avoids scrollbar
    driver.set_window_size(original_size["width"], original_size["height"])


# append file name
def epss_gen_file_name(number, tools, file_name, form_factor=""):
    current_date = datetime.today().strftime("%Y%m%d")
    new_file_name = tools + "-" + number + "-" + current_date + "-" + file_name
    if form_factor:
        return new_file_name + "-" + form_factor + ".png"
    else:
        return new_file_name + ".png"


gps_i = 1
gtmetrix_i = 1
pingdom_i = 1
success_link = []

def epss_screenshot_thread_function(group):
    screenshot_driver = webdriver.Chrome(options=options)
    screenshot_driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.4103.97 Safari/537.36"
        },
    )

    for link in group:
        file_name = epss_replace_url(group[-1])
        if link in INPUT_LINK:
            continue
        try:
            if epss_is_tool(link=link, tool="pagespeed"):
                parsed_url = urlparse(link)
                form_factor = parse_qs(parsed_url.query)["form_factor"][0]
                global gps_i
                file_name = epss_gen_file_name(
                    str(gps_i), "gps", file_name=file_name, form_factor=form_factor
                )
                gps_i = gps_i + 1
            elif epss_is_tool(link=link, tool="gtmetrix"):
                global gtmetrix_i
                file_name = epss_gen_file_name(
                    str(gtmetrix_i), "gtmetrix", file_name=file_name
                )
                gtmetrix_i = gtmetrix_i + 1
            elif epss_is_tool(link=link, tool="pingdom"):
                global pingdom_i
                file_name = epss_gen_file_name(
                    str(pingdom_i), "pingdom", file_name=file_name
                )
                pingdom_i = pingdom_i + 1
            screenshot_driver.get(link)
            time.sleep(5)
            epss_take_screenshot(file_name=file_name, driver=screenshot_driver)
            global success_link
            success_link.append(link)
        except WebDriverException as e:
            print(e)
            print("Error at: ", link)
            continue


# execute screenshot for all link input
def epss_execute_screenshot(links):
    print("Generating screenshot")
    screenshot_threads = []
    for group in links:
        screenshot_thread = threading.Thread(
            target=epss_screenshot_thread_function, args=(group,)
        )
        screenshot_threads.append(screenshot_thread)
        screenshot_thread.start()
    for thread in screenshot_threads:
        thread.join()


"""
Main Function
"""


def epss_main():
    try:
        while 1:
            links = epss_user_input()
            links = epss_add_form_factor(links=links)
            epss_execute_screenshot(links=links)
            print("Finish Generating Screenshot\n")
            print("Screenshot took: ")
            for link in success_link:
                    print(link + "\n")
            print("Press any key to run again or type 'exit' to exit...")
            choice = input()
            if choice == "exit":
                break
    except Exception as e:
        print(e)
        input()


epss_main()
