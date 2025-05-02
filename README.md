# Easy Page Speed Screenshots

This application enables you to capture screenshots of web performance test results for given URLs, supporting multiple platforms including Windows, macOS, and Linux.

## Prerequisites
- **Google Chrome**: Install Google Chrome on your machine. The app will attempt to locate Chrome at default paths, but you can set the `GOOGLE_CHROME_BIN` environment variable if it’s installed elsewhere.
  - Windows: Default path is `C:\Program Files\Google\Chrome\Application\chrome.exe` (64-bit) or `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe` (32-bit).
  - macOS: Default path is `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
  - Linux: Install via your package manager (e.g., `apt-get install google-chrome-stable` on Debian-based systems).
- **Python 3.9+**: Install Python from [https://www.python.org/downloads/](https://www.python.org/downloads/).
- **Git**: Install Git to clone the repository (available at [https://git-scm.com/downloads](https://git-scm.com/downloads)).

## Installation and Setup
Follow these steps to set up and run the application on your machine:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/easy-page-speed-screenshots.git
   cd easy-page-speed-screenshots
   ```

2. **Install Python Dependencies**:
   Ensure you have `pip` installed, then run:
   ```bash
   pip install -r requirements.txt
   ```
   This will install all necessary Python packages, including Selenium, Flask, and Gunicorn.

3. **Verify Chrome Installation**:
   - Ensure Google Chrome is installed and accessible. The app will try to find it at the default locations listed above.
   - If Chrome is installed in a custom location, set the `GOOGLE_CHROME_BIN` environment variable:
     - **Windows**:
       - Open 'Environment Variables' (right-click 'This PC' > 'Properties' > 'Advanced system settings' > 'Environment Variables').
       - Add or edit `GOOGLE_CHROME_BIN` and set it to the full path (e.g., `C:\Path\To\chrome.exe`).
       - Alternatively, run in Command Prompt: `set GOOGLE_CHROME_BIN=C:\Path\To\chrome.exe` before starting the app.
     - **macOS/Linux**:
       - Run in Terminal: `export GOOGLE_CHROME_BIN=/path/to/chrome` (e.g., `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`).
       - Add to your shell profile (e.g., `~/.bashrc` or `~/.zshrc`) for permanence: `echo 'export GOOGLE_CHROME_BIN=/path/to/chrome' >> ~/.bashrc` followed by `source ~/.bashrc`.

4. **Run the Application**:
   - Start the app by running:
     ```bash
     python app.py
     ```
   - The app will be available at `http://127.0.0.1:5001`.

## Usage
1. **Access the Web Interface**:
   - Open your web browser and go to `http://127.0.0.1:5001`.

2. **Enter URLs and Options**:
   - Enter one or more URLs (one per line) in the provided text area.
   - Optionally, enable GTMetrix testing and provide a GTMetrix API key and location if desired.
   - Click 'Submit' to start the screenshot process.

3. **View Results**:
   - Once processing is complete, the app will display a list of generated screenshots (PSI Desktop, PSI Mobile, and optionally GTMetrix) or indicate failures.
   - Screenshots are saved temporarily and can be viewed or downloaded from the results page.

## Notes
- The app includes embedded ChromeDriver binaries in the `drivers` directory for Windows (`chromedriver-win.exe`), macOS (`chromedriver-mac`), and Linux (`chromedriver-linux`), so no manual ChromeDriver installation is required.
- On macOS or Linux, the app automatically sets execute permissions for the ChromeDriver binary. If permission issues occur, run `chmod +x drivers/chromedriver-mac` or `chmod +x drivers/chromedriver-linux` manually.
- The app runs in single-process mode to reduce memory usage, which may trigger a warning (`Cannot use V8 Proxy resolver in single process mode`). This can be ignored unless you encounter network issues behind a proxy.
- Logs are written to `app.log` in the project directory for troubleshooting.

## FAQs & Troubleshooting

<details>
<summary>What should I do if Chrome is not found?</summary>
Ensure Google Chrome is installed in the default location for your operating system:

- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe` (64-bit) or `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe` (32-bit).
- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
- Linux: Install via your package manager (e.g., `apt-get install google-chrome-stable`).

If Chrome is installed elsewhere, set the `GOOGLE_CHROME_BIN` environment variable to the correct path (see Installation and Setup step 3). Check `app.log` for messages like “Chrome binary not found” to confirm the issue.
</details>

<details>
<summary>Why am I seeing a permission issue on macOS or Linux?</summary>
The app automatically sets execute permissions for the ChromeDriver binary, but this might fail depending on your system. To fix this manually:

- Run `chmod +x drivers/chromedriver-mac` (macOS) or `chmod +x drivers/chromedriver-linux` (Linux) in the project directory.
- Retry running the app.
</details>

<details>
<summary>What should I do if pages fail to load (network errors)?</summary>
Network errors might occur if you’re behind a proxy:

- Test with a direct internet connection if possible.
- Ensure the `GOOGLE_CHROME_BIN` environment variable is set correctly (see Installation and Setup step 3).
- If using a proxy, you may need to configure proxy settings in the app (contact the app maintainer for assistance).
</details>

<details>
<summary>Why am I seeing a "[WinError 193]" error on Windows?</summary>
The `[WinError 193] %1 is not a valid Win32 application` error typically occurs due to an architecture mismatch:

- Ensure both your Chrome and Python installations are 64-bit. Check Python’s architecture with:
  ```bash
  python -c "import platform; print(platform.architecture())"
  ```
  It should return `('64bit', 'WindowsPE')`.
- If Python or Chrome is 32-bit, reinstall the 64-bit version:
  - Python: Download from [https://www.python.org/downloads/](https://www.python.org/downloads/).
  - Chrome: Download from [https://www.google.com/chrome/](https://www.google.com/chrome/).
- Reinstall dependencies after upgrading Python: `pip install -r requirements.txt`.
</details>

<details>
<summary>What if I encounter memory issues when deploying to Render?</summary>
If deploying to Render and seeing `SIGKILL` errors (e.g., “Worker was sent SIGKILL! Perhaps out of memory?”):

- Consider upgrading to a higher memory plan on Render (e.g., the Standard tier with 2 GB RAM).
- Test with simpler URLs to confirm if the issue is related to page complexity.
- Check `app.log` for memory usage details (logged via `psutil`) to identify peak usage.
</details>

## Contributing
- Report issues or suggest improvements by creating a pull request or opening an issue in the repository.
- Ensure Chrome and ChromeDriver versions match when updating dependencies.

## License
[MIT License](https://github.com/viivue/easy-page-speed-screenshots/blob/enhancement/LICENSE)