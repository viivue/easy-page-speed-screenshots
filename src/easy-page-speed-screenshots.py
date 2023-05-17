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

"""
Page speed and GTmetrix run through 2 pages:
1. Analyze Page
2. Result Page
So this function run the same code twice to get the result page
"""
def epss_get_res_link():
  from urllib.parse import unquote

  #load the analyze page and get url
  new_link = driver.current_url
  decoded_url = unquote(new_link)
  time.sleep(5)
  # proceed from the analyze page
  driver.get(decoded_url)
  time.sleep(5)
  new_link = driver.current_url

  return unquote(new_link)

# submit link for testing
def epss_submit_link(tool, link, input_selector = '', form_selector = ''):
  driver.get(tool)
  input_field = driver.find_element(By.CSS_SELECTOR,'input' + input_selector)
  input_field.send_keys(link)  # Replace with your desired URL
  form = driver.find_element(By.CSS_SELECTOR,'form' + form_selector)
  form.submit()

# run through all testing tool
def epss_send_link_for_test(links):
  tools = ['https://pagespeed.web.dev/', 'https://gtmetrix.com/', 'https://tools.pingdom.com/']
  result_links = []
  print("Getting results: ")
  for link in tqdm(links, ncols=65):
      current_link = []
      print("\nRunning test for: " + link)
      for tool in tools:
        if epss_is_tool(link=tool,tool='pagespeed.web'):
          epss_submit_link(tool=tool, link=link)
          # Desire url: https://pagespeed.web.dev/analysis/https-en-wikipedia-org-wiki-Main_Page/5ohv3rfffg (without ?form_factor=mobile)
          res = epss_get_res_link()
          res = res.split('?',1)[0]
          current_link.append(res)
        elif epss_is_tool(link=tool,tool='gtmetrix'):
          epss_submit_link(tool=tool, link=link, input_selector='.js-analyze-form-url', form_selector='.analyze-form')
          # Desire url: https://gtmetrix.com/reports/en.wikipedia.org/aVrv18kF/
          res = epss_get_res_link()
          current_link.append(res)
        elif epss_is_tool(link=tool,tool='pingdom'):
          import requests
          #Desire url: https://tools.pingdom.com/#62079906f1c00000 with 62079906f1c00000 as id
          base_url = tool + 'v1/tests/'
          url = base_url + 'create'
          data = {
            'url': link
          }
          # call the api to receive the id
          resp = requests.post(url,json=data)
          resp = resp.json()
          result_id = resp['id']
          return_url = tool + '#' + result_id # create result url
          current_link.append(return_url)
      result_links.append(current_link)
  return result_links

# collect user input link
def epss_user_input():
   global INPUT_LINK
   INPUT_LINK = []
   global OP_DIR
   print("Enter save directory: ")
   OP_DIR = input()
   print("Enter links to test (type 'done' to finish input): ")
   while(1):
      input_link = input()
      if (input_link == 'done'):
         break
      elif input_link == '':
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
         if link.find('pagespeed.web.dev') != -1:
            current_new_group.append(link + '?form_factor=desktop')
            current_new_group.append(link + '?form_factor=mobile')
         else:
            current_new_group.append(link)
      new_links.append(current_new_group)
   return new_links

# replace character in url to append to file name
def epss_replace_url(url):
   # replace special characters with '-'
   url = url.replace('://', '-')
   url = url.replace('/', '-')
   url = url.replace('.', '-')
   #if the url ends with '/' the url will contain '-' at the end, remove it
   if url.endswith('-'):
      url = url.removesuffix('-')
   return url

# check specific tool
def epss_is_tool(link, tool):
   return link.find(tool) != -1

# Screenshot
# Ref: https://stackoverflow.com/a/52572919/
def epss_take_screenshot(file_name):
   original_size = driver.get_window_size()
   required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
   required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
   driver.set_window_size(2560, required_height)
   driver.find_element(By.TAG_NAME, "body").screenshot(
      f'{OP_DIR}\{file_name}')  # avoids scrollbar
   driver.set_window_size(original_size['width'], original_size['height'])

# append file name
def epss_gen_file_name(number, tools, file_name, form_factor = ''):
   current_date = datetime.today().strftime('%Y%m%d')
   new_file_name = tools + '-' + number + '-' + current_date + '-' + file_name
   if (form_factor):
      return new_file_name + '-' + form_factor + '.png'
   else:
      return new_file_name + '.png'

# execute screenshot for all link input
def epss_execute_screenshot(links):
   i = 0
   gps_i = 1
   gtmetrix_i = 1
   pingdom_i = 1
   print("Generating screenshot")
   for group in tqdm(links, ncols=65):
      print("\nGenerating screenshot for: " + INPUT_LINK[i])
      for link in group:
         file_name = epss_replace_url(INPUT_LINK[i])
         try:
           if epss_is_tool(link=link,tool="pagespeed"):
              parsed_url = urlparse(link)
              form_factor = parse_qs(parsed_url.query)['form_factor'][0]
              file_name = epss_gen_file_name(str(gps_i), 'gps',file_name=file_name,form_factor=form_factor)
              gps_i = gps_i + 1
           elif epss_is_tool(link=link,tool="gtmetrix"):
              file_name = epss_gen_file_name(str(gtmetrix_i), 'gtmetrix',file_name=file_name)
              gtmetrix_i = gtmetrix_i + 1
           elif epss_is_tool(link=link,tool="pingdom"):
              file_name = epss_gen_file_name(str(pingdom_i), 'pingdom',file_name=file_name)
              pingdom_i = pingdom_i + 1
           driver.get(link)
           time.sleep(5)
           epss_take_screenshot(file_name=file_name)
         except WebDriverException:
           print(link)
           continue
      i = i + 1
   driver.quit()

"""
Main Function
"""

def epss_main():
   links = epss_user_input()
   links = epss_add_form_factor(links=links)
   epss_execute_screenshot(links=links)

epss_main()