# Easy Page Speed Screenshots

This application allows you to take screenshots of Page Speed Insights (PSI) and GTmetrix test results for given URLs. It is designed to work across Windows, macOS, and Linux environments, making it easy for your team to use.

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
   git clone <repository-url>
   cd easy-page-speed-screenshots
   ```
   Replace `<repository-url>` with the actual URL of your Git repository (e.g., `https://github.com/yourusername/easy-page-speed-screenshots.git`).

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
   - Optionally, enable GTmetrix testing and provide a GTmetrix API key and location if desired.
   - Click 'Submit' to start the screenshot process.

3. **View Results**:
   - Once processing is complete, the app will display a list of generated screenshots (PSI Desktop, PSI Mobile, and optionally GTmetrix) or indicate failures.
   - Screenshots are saved temporarily and can be viewed or downloaded from the results page.

## Notes
- The app includes embedded ChromeDriver binaries in the `drivers` directory for Windows (`chromedriver-win.exe`), macOS (`chromedriver-mac`), and Linux (`chromedriver-linux`), so no manual ChromeDriver installation is required.
- On macOS or Linux, the app automatically sets execute permissions for the ChromeDriver binary. If permission issues occur, run `chmod +x drivers/chromedriver-mac` or `chmod +x drivers/chromedriver-linux` manually.
- The app runs in single-process mode to reduce memory usage, which may trigger a warning (`Cannot use V8 Proxy resolver in single process mode`). This can be ignored unless you encounter network issues behind a proxy.
- Logs are written to `app.log` in the project directory for troubleshooting.

## Troubleshooting
- **Chrome Not Found**:
  - Ensure Chrome is installed in the default location, or set the `GOOGLE_CHROME_BIN` environment variable to the correct path.
  - Check `app.log` for messages like “Chrome binary not found.”
- **Permission Issues (macOS/Linux)**:
  - Run `chmod +x drivers/chromedriver-*` if the app fails to set permissions.
- **Network Errors**:
  - If pages fail to load (e.g., behind a proxy), set the `GOOGLE_CHROME_BIN` environment variable and test with a direct connection.
- **Windows Errors ([WinError 193])**:
  - Ensure your Chrome and Python installations are 64-bit (check with `python -c "import platform; print(platform.architecture())"`).
  - Reinstall Chrome or Python if mismatched.
- **Memory Issues on Render**:
  - If deploying to Render and encountering `SIGKILL` errors, consider upgrading to a higher memory plan (e.g., Standard tier with 2 GB RAM).

## Contributing
- Report issues or suggest improvements by creating a pull request or opening an issue in the repository.
- Ensure Chrome and ChromeDriver versions match when updating dependencies.

## License
[MIT License](https://github.com/viivue/easy-page-speed-screenshots/blob/enhancement/LICENSE)