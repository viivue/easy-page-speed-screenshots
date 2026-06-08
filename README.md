# Easy Page Speed Screenshots

Capture full-page screenshots of PageSpeed Insights (and optionally GTmetrix) results for any list of URLs. Screenshots can be uploaded to Dropbox automatically, and a Word report with Dropbox links is generated after each run.

## Prerequisites
- **Google Chrome**: Install Google Chrome on your machine. (The app locates Chrome at default paths, but you can override with the `GOOGLE_CHROME_BIN` environment variable.)
  - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe` (64-bit) or `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe` (32-bit)
  - macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
  - Linux: Install via your package manager (e.g., `apt-get install google-chrome-stable`)
- **Python 3.9+**: [https://www.python.org/downloads/](https://www.python.org/downloads/)

## Installation and Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/viivue/easy-page-speed-screenshots.git
   cd easy-page-speed-screenshots
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (optional — required for Dropbox integration):
   ```bash
   cp .env.example .env
   # then fill in your values
   ```

4. **Run the app**:
   ```bash
   python app.py
   ```
   The app is available at `http://127.0.0.1:5001`.

## Usage

1. Open `http://127.0.0.1:5001` in your browser.
2. Paste one or more URLs (one per line) into the text area.
3. Optionally enable GTmetrix testing and supply your GTmetrix API key and location.
4. Click **Submit** — the app captures PSI Desktop and PSI Mobile screenshots (plus GTmetrix if enabled), uploads them to Dropbox (if configured), and generates a Word report.
5. From the results page you can download a ZIP of all screenshots or the `.docx` report.

## Dropbox integration

When Dropbox credentials are present in `.env`, screenshots are uploaded automatically after each run and shareable links are embedded in the Word report.

### Set up a Dropbox app

1. Go to [https://www.dropbox.com/developers/apps/create](https://www.dropbox.com/developers/apps/create) and create a **Scoped access / Full Dropbox** app.
2. On the **Permissions** tab enable: `files.content.write`, `files.content.read`, `sharing.write`, `sharing.read`, `files.metadata.read`, then click **Submit**.
3. Copy the **App key** and **App secret** from the Settings tab.

### Get a refresh token

The Dropbox console "Generate" button issues short-lived tokens — use the helper script instead:

```bash
python get_dropbox_token.py
```

Follow the prompts (open the URL, paste the code). The script prints a `DROPBOX_REFRESH_TOKEN=…` line to add to your `.env`.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `DROPBOX_APP_KEY` | Yes (for Dropbox) | Your Dropbox app key |
| `DROPBOX_APP_SECRET` | Yes (for Dropbox) | Your Dropbox app secret |
| `DROPBOX_REFRESH_TOKEN` | Yes (for Dropbox) | Long-lived refresh token (see above) |
| `DROPBOX_FOLDER` | No | Dropbox destination folder (default: `/PageSpeed Reports`) |
| `DROPBOX_PATH_ROOT_NS` | No | Namespace ID for Dropbox Business team space roots |
| `GOOGLE_CHROME_BIN` | No | Path to Chrome binary if not at the default location |
| `PORT` | No | HTTP port (default: `5001`) |

Copy `.env.example` to `.env` and fill in the values.

> **Dropbox not configured?** The app still runs fine — screenshots are saved locally and the Word report notes that Dropbox was not configured.

## Word report

After each run the app writes a `report_<session_id>.docx` file in the session directory. The report contains a table with one row per URL: Date, Page, Desktop link, Mobile link. When Dropbox is configured the Desktop/Mobile cells are clickable "Open in Dropbox" hyperlinks.

Download the report from the results page via the **Download Report** button.

## Notes

- **ChromeDriver**: The app uses Selenium Manager (bundled with Selenium 4.6+) to locate and download a matching ChromeDriver automatically. No manual ChromeDriver installation is required. A `drivers/` directory with platform binaries is kept as a fallback; Selenium Manager is preferred.
- **Logging**: Logging is disabled by default. Set `CONFIG['DEBUG'] = True` in `app.py` to enable it. Logs are written to `app.log`.
- **Session cleanup**: The app keeps the last 5 sessions in `temp_screenshots/` and removes older ones automatically.

## FAQs & Troubleshooting

<details>
<summary>What should I do if Chrome is not found?</summary>

Ensure Google Chrome is installed in the default location for your operating system:

- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe` (64-bit) or `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe` (32-bit)
- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Linux: `apt-get install google-chrome-stable`

If Chrome is installed elsewhere, set `GOOGLE_CHROME_BIN` in `.env`. Check `app.log` for "Chrome binary not found" messages.
</details>

<details>
<summary>Why am I seeing a permission issue on macOS or Linux?</summary>

Run `chmod +x drivers/chromedriver-mac` (macOS) or `chmod +x drivers/chromedriver-linux` (Linux) in the project directory, then retry.
</details>

<details>
<summary>What should I do if pages fail to load (network errors)?</summary>

- Test with a direct internet connection if possible.
- Verify `GOOGLE_CHROME_BIN` points to the correct Chrome binary.
- If behind a proxy, configure proxy settings before starting the app.
</details>

<details>
<summary>Why am I seeing a "[WinError 193]" error on Windows?</summary>

This usually means an architecture mismatch between Chrome and Python. Verify both are 64-bit:

```bash
python -c "import platform; print(platform.architecture())"
```

It should return `('64bit', 'WindowsPE')`. Reinstall the 64-bit versions if needed, then run `pip install -r requirements.txt` again.
</details>

<details>
<summary>What if I encounter memory issues when deploying to Render?</summary>

- Upgrade to a higher-memory plan on Render (Standard tier with 2 GB RAM recommended).
- Test with simpler URLs to confirm whether the issue is page complexity.
- Enable logging (`CONFIG['DEBUG'] = True`) and check `app.log` for memory usage details.
</details>

<details>
<summary>Dropbox upload fails with an ApiError</summary>

- Confirm all three credential variables (`DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN`) are set in `.env`.
- Make sure the required permissions are enabled in the Dropbox app's Permissions tab and that you re-ran `get_dropbox_token.py` after changing permissions.
- For Dropbox Business team spaces, set `DROPBOX_PATH_ROOT_NS` to the namespace ID of the team root.
</details>

## Contributing
Report issues or suggest improvements by opening an issue or pull request in the repository.

## License
[MIT License](https://github.com/viivue/easy-page-speed-screenshots/blob/master/LICENSE)