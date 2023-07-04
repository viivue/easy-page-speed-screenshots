import os

# constant
ASSET_FOLDER = os.path.join(os.path.dirname(__file__), '../assets')
TOOLS = [
    "https://pagespeed.web.dev/",
    "https://gtmetrix.com/",
    "https://tools.pingdom.com/",
]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.4103.97 Safari/537.36"
API_KEY = ""
OP_DIR = ""
INPUT_LINK = ""
RESULT_LINKS = []

# variables
use_gt_metrix = False
success_link = []

# UI
font = "Nirmala UI"
body_txt = 12
bg_color = "#f1c400"
txt_color = "#141414"
btn_bg_color = "#fff"
btn_txt_color = "#141414"