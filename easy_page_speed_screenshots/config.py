import os
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# webdriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_experimental_option(
    "excludeSwitches", ["enable-logging"]
)  # disable output the 'DevTools listening on ws://127.0.0.1:56567/devtools/browser/' line
options.add_argument("--log-level=3")

# global variable
use_gt_metrix = False
execute_threads = []
success_link = []

# constant
ASSET_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets')
API_KEY = ""