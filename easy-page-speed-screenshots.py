from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from tqdm import tqdm
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs
from datetime import datetime

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

"""
Page speed and GTmetrix run through 2 pages:
1. Analyze Page
2. Result Page
So this function run the same code twice to get the result page
"""
def get_res_link(): 
  from urllib.parse import unquote

  new_link = driver.current_url
  decoded_url = unquote(new_link)
  time.sleep(5)
  driver.get(decoded_url)
  time.sleep(5)
  new_link = driver.current_url
  return unquote(new_link)

# submit link for testing
def submit_link(tool, link, input_selector = '', form_selector = ''):
  driver.get(tool)
  input_field = driver.find_element(By.CSS_SELECTOR,'input' + input_selector)
  input_field.send_keys(link)  # Replace with your desired URL
  form = driver.find_element(By.CSS_SELECTOR,'form' + form_selector)
  form.submit()

# run through all testing tool
def send_link_for_test(link):
  tools = ['https://pagespeed.web.dev/', 'https://gtmetrix.com/', 'https://tools.pingdom.com/']
  result_links = []
  print("Getting result: ")
  for tool in tqdm(tools, ncols=65):
    if is_tool(link=tool,tool='pagespeed.web'):
      submit_link(tool=tool, link=link)
      
      res = get_res_link()
      res = res.split('?',1)[0]
      result_links.append(res)
    elif is_tool(link=tool,tool='gtmetrix'):
      submit_link(tool=tool, link=link, input_selector='.js-analyze-form-url', form_selector='.analyze-form')

      res = get_res_link()
      result_links.append(res)
    elif is_tool(link=tool,tool='pingdom'):
      import requests
      #get id
      base_url = tool + 'v1/tests/'
      url = base_url + 'create'
      data = {
        'url': link
      }
      resp = requests.post(url,json=data)
      resp = resp.json()
      result_id = resp['id']
      return_url = tool + '#' + result_id
      result_links.append(return_url)
  return result_links

# collect user input link
def user_input():
   global INPUT_LINK
   global OP_DIR
   print("Enter save directory: ")
   OP_DIR = input()
   print("Enter link to test: ")
   INPUT_LINK = input()
   res_inputs = send_link_for_test(INPUT_LINK)
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

# check specific tool
def is_tool(link, tool):
   return link.find(tool) != -1

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

# append file name
def gen_file_name(number, tools, file_name, form_factor = ''):
   current_date = datetime.today().strftime('%Y%m%d')
   if (form_factor):
      return number + '-' + tools + '-' + current_date + '-' + file_name + '-' + form_factor + '.png'
   else:
      return number + '-' + tools + '-' + current_date + '-' + file_name + '.png'

# execute screenshot for all link input
def execute_screenshot(links):
   i = 1
   print("Generating screenshot")
   for link in tqdm(links, ncols=65):
      file_name = replace_url(INPUT_LINK)
      try:
        if is_tool(link=link,tool="pagespeed"):
           parsed_url = urlparse(link)
           form_factor = parse_qs(parsed_url.query)['form_factor'][0]
           file_name = gen_file_name(str(i), 'gps',file_name=file_name,form_factor=form_factor)
        elif is_tool(link=link,tool="gtmetrix"):
           file_name = gen_file_name(str(i), 'gtmetrix',file_name=file_name)
        elif is_tool(link=link,tool="pingdom"):
           file_name = gen_file_name(str(i), 'pingdom',file_name=file_name) 
        driver.get(link)
        time.sleep(10)
        take_screenshot(file_name=file_name)

        i = i + 1
      except WebDriverException:
        print(link)
        continue
   driver.quit()

"""
Main Function
"""

def main():
   links = user_input()
   links = add_form_factor(links=links)
   execute_screenshot(links=links)

main()