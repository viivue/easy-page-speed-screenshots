from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from tqdm import tqdm
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime

OP_DIR = r'' # Update the correct path to store screenshots, for example: I:\easy-page-speed-screenshots\images

"""
Define Global Variables
"""

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument('--log-level=3')
driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                       "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.4103.97 Safari/537.36'})
"""
Define functions
"""

def S(X): return driver.execute_script('return document.body.scrollHeight') + X

# collect user input link
def user_input():
   res_inputs = []
   while(1):
      print("Input link (input -1 to finish): ")
      res_input = input()
      if (res_input=="-1"):
         break;
      res_inputs.append(res_input)
   return res_inputs

# append form_factor if url is pagespeed   
def add_form_factor(links):
   new_links = []
   for link in links:
    if link.find('pagespeed.web.dev') != -1:
        new_links.append(link + '?form_factor=desktop')
        new_links.append(link + '?form_factor=mobile')
    else:
        new_links.append(link)
   return new_links

# replace character in url to append to file name
def replace_url(url): 
   # replace special characters with '-'
   url = url.replace('://', '-')
   url = url.replace('/', '-')
   url = url.replace('.', '-')
   #if the url ends with '/' the url will contain '-' at the end, remove it
   if url.endswith('-'):
      url = url.removesuffix('-')
   return url

# Screenshot
# Ref: https://stackoverflow.com/a/52572919/
def take_screenshot(file_name):
   original_size = driver.get_window_size()
   required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
   required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
   driver.set_window_size(2560, required_height)
   driver.find_element(By.TAG_NAME, "body").screenshot(
      f'{OP_DIR}\{file_name}')  # avoids scrollbar
   driver.set_window_size(original_size['width'], original_size['height'])

# check specific tool
def is_tool(link, tool):
   return link.find(tool) != -1

# append file name
def gen_file_name(number, tools, file_name, form_factor = ''):
   current_date = datetime.today().strftime('%Y%m%d');
   if (form_factor):
      return number + '-' + tools + '-' + current_date + '-' + file_name + '-' + form_factor + '.png'
   else:
      return number + '-' + tools + '-' + current_date + '-' + file_name + '.png'

# execute screenshot for all link input
def execute_screenshot(links):
   i = 1
   for link in tqdm(links, ncols=65):
    try:
      # Convert link to file name
      if is_tool(link=link,tool="pagespeed"):
         parsed_url = urlparse(link)
         form_factor = parse_qs(parsed_url.query)['form_factor'][0]
         file_name = link.replace("https://pagespeed.web.dev/analysis/", "")
         file_name = file_name.split('/', 1)[0]
         file_name = gen_file_name(str(i), 'gps',file_name=file_name,form_factor=form_factor)
      elif is_tool(link=link,tool="gtmetrix"):
         # get the url from site's html
         driver.get(link)
         url = driver.find_element(By.CSS_SELECTOR,'div.report-details > h2 > a').text

         file_name = replace_url(url)
         file_name = gen_file_name(str(i), 'gtmetrix',file_name=file_name)
      elif is_tool(link=link,tool="pingdom"):
         import requests
         from requests.exceptions import HTTPError
         id = link.split('#',1)[1]
         request_url = 'https://tools.pingdom.com/v1/tests/' + id;
         try:
            resp = requests.get(request_url)
            data = resp.json()
            url = data['url']
            file_name = replace_url(url)
            file_name = gen_file_name(str(i), 'pingdom',file_name=file_name)
         except HTTPError as http_err:
             print(f'HTTP error occurred: {http_err}')
         except Exception as err:
             print(f'Other error occurred: {err}')
      driver.get(link)
      time.sleep(10)
      take_screenshot(file_name=file_name)

      i = i + 1;
    except WebDriverException:
        print(link)
        continue
   driver.quit()

def main():
   links = user_input()
   links = add_form_factor(links=links)
   execute_screenshot(links=links)

main()