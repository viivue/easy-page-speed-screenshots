# Easy Page Speed Screenshot (EPSS)

This tool allow automatically taking screenshot from page speed test websites.

Current websites supported:
- https://pagespeed.web.dev/
- https://gtmetrix.com/
- https://tools.pingdom.com/

## Installation

Clone from GitHub:
```
git clone https://github.com/viivue/easy-page-speed-screenshots.git
```

### 1. Using `.exe` file

Find and double-click on `easy-page-speed-screenshots.exe` file. The file locate in `your-path-to-tool/easy-page-speed-screenshots/dist/`. Then see [usage below](#usage)

### 2. Using `.py` file

> ❌ Only try this if you failed to run `.exe` file

First, install dependencies

- Python: Install [Python](https://www.python.org/downloads/). Simply download the installer and follow the installation wizard

> It's important to add python to PATH to run python in terminal. ![image](https://github.com/viivue/easy-page-speed-screenshots/assets/80519358/3560a298-998e-47e4-a3ec-53d0eaab72ae)

Verify your installation with `python --version`. If it is correctly configuration. You should be run python command globally

![image](https://github.com/viivue/easy-page-speed-screenshots/assets/80519358/6266976e-ca8e-4e96-971c-c5a5844a4209)

- Selenium:
```
pip install selenium
```

- Webdriver:

First, check your browser version by go to Chrome -> Setting -> About Chrome

Then download [ChromeDriver](https://chromedriver.chromium.org/downloads). After installation done, add `chromedriver.exe` to `your_path_to_python/Python/Scripts` folder

> ⚠️ You have to have Chrome installed in order to get this tool to work

- Request: 
```
pip install requests
```

Then, simply run

```
cd easy-page-speed-screenshots/src
python easy-page-speed-screenshots.py
```

## Usage

> 👉 Press Enter to perform any action

Your terminal will tell you to input save directory, enter your desire directory

![image](https://github.com/viivue/easy-page-speed-screenshots/assets/80519358/92e7876f-08f0-4c0e-876e-e89630caedbb)

> Directory path must be absolute path (include hard drive name), e.g C:\Users\user\screenshots

After that, enter the urls you need to test

![image](https://github.com/viivue/easy-page-speed-screenshots/assets/80519358/cfc7e527-bca0-4ce5-8a6d-21992371a4f3)

Now wait for the tool to complete

## Result

Testing url: https://en.wikipedia.org/wiki/Main_Page

Result in terminal:

![image](https://github.com/viivue/easy-page-speed-screenshots/assets/80519358/d86c22b2-12f8-4517-8457-cff64e4d3e0e)

Screenshot result:

![image](https://github.com/viivue/easy-page-speed-screenshots/assets/80519358/192bda1b-99a2-458a-8331-b22e347486cc)

Tutorial:

![image](https://github.com/viivue/easy-page-speed-screenshots/blob/enhancement/Tutorial.gif)

## License

[MIT License](https://github.com/viivue/easy-page-speed-screenshots/blob/enhancement/LICENSE)

Copyright (c) 2023 ViiVue
