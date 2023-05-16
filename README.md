# Easy Page Speed Screenshot

This tool allow automatically taking screenshot from page speed test websites. 

Current websites supported:
- https://pagespeed.web.dev/
- https://gtmetrix.com/
- https://tools.pingdom.com/

## Current Result

Testing url: https://en.wikipedia.org/wiki/Main_Page

Result in terminal:

![](https://i.imgur.com/nijoaba.png)

Screenshot result:

![](https://i.imgur.com/77jWcRc.png)

## Dependencies

- Python: Install [Python](https://www.python.org/downloads/). Simply download the installer and follow the installation wizard

> It's importart to add python to PATH to run python in terminal. Verify your installation with `python --version`

- Selenium: `pip install selenium`

- Webdriver: Download [ChromeDriver](https://chromedriver.chromium.org/downloads). After installation done, add `chromedriver.exe` to `your_path_to_python/Python/Scripts` folder

> With who don't use Chrome, the version for others browser is in development. 

- Request: `pip install requests`

## Users Instruction

Open your terminal in the tool directory. Simply run:

```
python easy-page-speed-screenshots.py
```

Your terminal will tell you to input save directory, enter your desire directory, press `Enter`

> Directory path must be absolute path

After that, enter the url of the page you need to test, press `Enter`

Now wait for the tool to complete

## For Developers

### Code Overview

The program will run by `main()` function

#### Side function

| Functions          | Parameters                                          | Description                                                                                         |
| ------------------ |:--------------------------------------------------- |:--------------------------------------------------------------------------------------------------- |
| send_link_for_test | link                                                | Send the `input` data link to all tools for testing                                                 |
| submit_link        | tool, link, input_selector = '', form_selector = '' | Submit the input of that tool, specify the selector because some page can be different              |
| get_res_link       |                                                     | Get the result link without encoded                                                                 |
| user_input         |                                                     | Get user input and run the testing process, this function also set the `INPUT_LINK` global variable |
| add_form_factor    | link                                                | add `form_factor` param to Google Page Speed links                                                  |
| execute_screenshot | links                                               | execute taking screenshot with result after process with user_input()                               |
| replace_url        | url                                                 | replace some character in link to -                                                                 |
| is_tool            | link, tool                                          | check if the `link` belong to `tool`                                                              |
| take_screenshot    | file_name                                           | take screenshot and save the file with `file_name`                                                |
| gen_file_name      | number, tools, file_name, form_factor = ''          | generate `file_name`                                                                                |
