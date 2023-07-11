import os

# constant
ASSET_FOLDER = os.path.join(os.path.dirname(__file__), '../assets')
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
IMG_EXT = '.png'
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