from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from tqdm import tqdm
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime

lines = []
Links_File = r'' # Update the correct path file for urls.txt, for example: I:\easy-page-speed-screenshots\urls.txt
OP_DIR = r'' # Update the correct path to store screenshots, for example: I:\easy-page-speed-screenshots\images
i = 1


def S(X): return driver.execute_script('return document.body.scrollHeight') + X


with open(Links_File, "r") as f:
    lines = f.readlines()
lines = [line.rstrip() for line in lines]

new_lines = []
for line in lines:
    if line.find('pagespeed.web.dev') != -1:
      new_lines.append(line + '?form_factor=desktop')
      new_lines.append(line + '?form_factor=mobile')
    else:
       new_lines.append(line)

lines = new_lines

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument('--log-level=3')
driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                       "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.4103.97 Safari/537.36'})
print(driver.execute_script("return navigator.userAgent;"))
for link in tqdm(lines, ncols=65):
    try:
      current_date = datetime.today().strftime('%Y%m%d');

      # Convert link to file name
      if link.find('pagespeed.web.dev') != -1:
         parsed_url = urlparse(link)
         form_factor = parse_qs(parsed_url.query)['form_factor'][0]
         file_name = link.replace("https://pagespeed.web.dev/analysis/", "")
         file_name = file_name.split('/', 1)[0]
         file_name = 'gps-' + current_date + '-' + str(i) + '-' + file_name + '-' + form_factor + '.png'
      elif link.find('gtmetrix') != -1:
         file_name = link.replace("https://gtmetrix.com/reports/", "")
         file_name = file_name.split('/', 1)[0]
         file_name = 'gtmetrix-' + current_date + '-' + str(i) + '-' + file_name + '.png'
      
      driver.get(link)
      time.sleep(10)
      
      # Screenshot
      # Ref: https://stackoverflow.com/a/52572919/
      original_size = driver.get_window_size()
      required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
      required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
      driver.set_window_size(2560, required_height)
      driver.find_element(By.TAG_NAME, "body").screenshot(
         f'{OP_DIR}\{file_name}')  # avoids scrollbar
      driver.set_window_size(original_size['width'], original_size['height'])

      i = i + 1;
    except WebDriverException:
        print(link)
        continue
driver.quit()
