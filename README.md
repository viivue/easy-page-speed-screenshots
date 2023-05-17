# Easy Page Speed Screenshot (EPSS)

This tool allow automatically taking screenshot from page speed test websites.

![](https://i.imgur.com/HoE7jmF.gif)

Current websites supported:
- https://pagespeed.web.dev/
- https://gtmetrix.com/
- https://tools.pingdom.com/

## Current Result

Testing url: https://en.wikipedia.org/wiki/Main_Page

Result in terminal:

![](https://i.imgur.com/JBJDtQW.png)

Screenshot result:

![](https://i.imgur.com/BRbLID7.png)

## Getting Started

### Install Dependencies

- Python: Install [Python](https://www.python.org/downloads/). Simply download the installer and follow the installation wizard

> It's importart to add python to PATH to run python in terminal. ![](https://i.imgur.com/PDfQgJO.png)

Verify your installation with `python --version`. If it is correctly configuration. You should be run python command globally

![](https://i.imgur.com/46LL6jZ.png)

Verify if python is your computer can run python, by run an example program.

![](https://i.imgur.com/0Q2JXrD.png)

- Selenium: `pip install selenium`

- Webdriver: Download [ChromeDriver](https://chromedriver.chromium.org/downloads). After installation done, add `chromedriver.exe` to `your_path_to_python/Python/Scripts` folder

> With who don't use Chrome, the version for others browser is in development.

- Request: `pip install requests`

## Installation

Clone from github:
```
git clone https://github.com/viivue/easy-page-speed-screenshots.git
```

## Usage

Simply run

```
cd easy-page-speed-screenshots
python easy-page-speed-screenshots.py
```

Your terminal will tell you to input save directory, enter your desire directory, press `Enter`

![](https://i.imgur.com/g8eNUZT.png)

> Directory path must be absolute path

After that, enter the url of the page you need to test, press `Enter`

![](https://i.imgur.com/WQovfpU.png)

Now wait for the tool to complete

## Developers

The program will run by `epss_main()` function

### Variables

| Variable   | Type            | Description                                |
| ---------- | --------------- |:------------------------------------------ |
| `INPUT_LINK` | Array of String | Hold the input links of users              |
| `OP_DIR`     | String          | Holds the output directory for screenshots |


### Functions

| Functions                 | Parameters                                                                                                                 | Return                             | Description                                                                                         |
| ------------------------- |:---------------------------------------------------------------------------------------------------------------------------|:-----------------------------------|:--------------------------------------------------------------------------------------------------- |
| `epss_send_link_for_test` | `links` : Array of String                                                                                                  | `result_links`: 2d array of String | Send the `input` data link to all tools for testing and return all result links                     |
| `epss_submit_link`        | `tool`: String <br/> `link` : String <br/>input_selector: String, default `''` <br/> `form_selector`: String, default `''` | None                               | Submit the input of that tool, specify the selector because some page can be different              |
| `epss_get_res_link`       | None                                                                                                                       | `new_link`: String                 | Get the result link without encoded                                                                 |
| `epss_user_input`         | None                                                                                                                       | `result_links`: 2d array of String | Get user input and run the testing process, this function also set the `INPUT_LINK` global variable |
| `epss_add_form_factor`    | `links`: 2d Array of String                                                                                                | `new_links`: 2d array of String    | add `form_factor` param to Google Page Speed links                                                  |
| `epss_execute_screenshot` | `links`: 2d Array of String                                                                                                | None                               | execute taking screenshot with result after process with user_input()                               |
| `epss_replace_url`        | `url`: String                                                                                                              | `new_url`: String                  | replace some character in link to -                                                                 |
| `epss_is_tool`            | `link`: String<br/> `tool`: String                                                                                         | Boolean                            | `True` if the `link` belong to `tool`, otherwise, `False`                                           |
| `epss_take_screenshot`    | `file_name`: String                                                                                                        | None                               | take screenshot and save the file with `file_name`                                                  |
| `epss_gen_file_name`      | `number`: String <br/>`tools`: String<br/> `file_name`: String<br/> `form_factor`: String, default `''`                    | `new_file_name`: String            | generate `file_name`                                                                                |

> Note:
>
> ⚠️ `epss_submit_link` and `epss_get_res_link` share the same `driver` global var. In `epss_submit_link` have called `driver.get(link)` itself, no need to call `driver.get(link)` again
>
> ⚠️ `epss_submit_link` should run before `epss_get_res_link`
>
> ⚠️ `epss_execute_screenshot` will call `driver.quit()` after the screenshot process finish

## License

Copyright (c) 2023 ViiVue