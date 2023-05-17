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

> It's important to add python to PATH to run python in terminal. ![](https://i.imgur.com/PDfQgJO.png)

Verify your installation with `python --version`. If it is correctly configuration. You should be run python command globally

![](https://i.imgur.com/46LL6jZ.png)

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
cd easy-page-speed-screenshots
python easy-page-speed-screenshots.py
```

## Usage

> 👉 Press Enter to perform any action

Your terminal will tell you to input save directory, enter your desire directory

![](https://i.imgur.com/g8eNUZT.png)

> Directory path must be absolute path (include hard drive name), e.g C:\Users\user\screenshots

After that, enter the urls you need to test

![](https://i.imgur.com/WQovfpU.png)

Now wait for the tool to complete

## Result

Testing url: https://en.wikipedia.org/wiki/Main_Page

Result in terminal:

![](https://i.imgur.com/JBJDtQW.png)

Screenshot result:

![](https://i.imgur.com/BRbLID7.png)

Tutorial:

![](https://i.imgur.com/HoE7jmF.gif)

## License

Copyright (c) 2023 ViiVue