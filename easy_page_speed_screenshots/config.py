import os

# constant
ASSET_FOLDER = os.path.join(os.path.dirname(__file__), "../assets")
PS_URL = "https://pagespeed.web.dev/"
GM_URL = "https://gtmetrix.com/"
PD_URL = "https://tools.pingdom.com/"
URLS = [
    PS_URL,
    GM_URL,
    PD_URL,
]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.4103.97 Safari/537.36"
API_KEY = ""
OP_DIR = ""
INPUT_LINKS = ""
RESULT_LINKS = []
IMG_EXT = ".png"
CHROME_DRIVERS = []

# variables
use_gt_metrix = False
success_link = []
worker_threads = []

# UI
font = "Nirmala UI"
body_txt = 13
txt_color = "#141414"
color_white = "#fff"
color_black = "#000"
primary_color = "#f1c400"

app_width = 75

window_height = 750
window_width = 590

# Error Text
txt_error_title = "Error"
txt_warning_title = "Warning"
txt_please_valid_folder = "Please enter a valid folder"
txt_please_choose_folder = "Please choose folder"
txt_please_input_links = "Please input links"
txt_empty_api_message = "Empty API Key. GTMetrix will be skipped."
txt_gt_invalid_api = "Invalid API Key"
txt_gt_reached_limit = "Your API Key has reached limit"
txt_invalid_links_message = "The invalid links will be skipped"
txt_invalid_link_message = "Please enter a valid site URL starting with 'http'"
txt_finish_title = "Finish"
txt_finish_message = "Result screenshots saved successfully!"
txt_quit_title = "Quit"
txt_quit_message = "Are you sure you want to exit?"

txt_placeholder_folder = "Choose output directory"
txt_placeholder_apikey = "API Key"

