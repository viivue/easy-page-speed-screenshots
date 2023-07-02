import os
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from urllib.parse import parse_qs

from . import config

# webdriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_experimental_option(
    "excludeSwitches", ["enable-logging"]
)  # disable output the 'DevTools listening on ws://127.0.0.1:56567/devtools/browser/' line
options.add_argument("--log-level=3")

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
        executable_path = config.ASSET_FOLDER + "/driver/chromedriver.exe", options=options
    )

# submit link for testing
def epss_submit_link(tool, link, input_selector="", form_selector=""):
    get_link_driver = epss_get_webdriver()
    get_link_driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {
            "userAgent": config.USER_AGENT
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

# check if json field exists
def epss_json_field_exists(field, json):
    if field in json:
        return json[field]
    else:
        return False

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

def epss_submit_by_form(tool, link, current_link):
    res = epss_submit_link(tool=tool, link=link)
    if res != "":
        res = res.split("?", 1)[0]
    current_link.append(res)

# check specific tool
def epss_is_tool(link, tool):
    return link.find(tool) != -1

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