from flask import Flask, request, render_template, send_file, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
import os
import zipfile
import shutil
import traceback
import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import re
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
OUTPUT_DIR = "temp_screenshots"
MAX_WORKERS = 2  # Adjust based on your server's resources
MAX_SESSIONS_TO_KEEP = 5  # Number of session directories to keep
SCREENSHOT_TIMEOUT = 120  # Timeout for waiting for elements (seconds)
EXPAND_DELAY = 0.1  # Time between expanding sections (seconds)
LOAD_DELAY = 2  # Additional waiting time after elements load (seconds)


# Clean URL for filename
def clean_url_for_filename(url):
    # Remove protocol and replace problematic characters
    cleaned = re.sub(r'https?://', '', url)
    # Replace any remaining non-alphanumeric characters with hyphen
    cleaned = re.sub(r'[^a-zA-Z0-9]', '-', cleaned)
    # Prevent duplicate hyphens
    cleaned = cleaned.strip("-")

    return cleaned


# Naming pattern function
def generate_filename(index, tool, url, device):
    date_str = datetime.now().strftime("%Y%m%d")
    decoded_url = clean_url_for_filename(url)
    return f"{index}-{tool}-{date_str}-{decoded_url}-{device}"


# Function to expand all sections
def expand_all_sections(driver):
    try:
        expandable_elements = driver.find_elements(By.CSS_SELECTOR, ".lh-audit-group__header")
        for element in expandable_elements:
            try:
                # Scroll to element with smooth behavior
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                    element
                )
                time.sleep(EXPAND_DELAY)

                if element.is_displayed() and element.is_enabled():
                    try:
                        element.click()
                    except:
                        driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                # Continue with other elements if one fails
                logger.warning(f"Failed to expand element: {e}")
                continue
    except Exception as e:
        logger.warning(f"No expandable elements or failed to expand: {e}")


# Function to take a CDP full-page screenshot
def take_cdp_screenshot(driver, output_path):
    try:
        # First, temporarily disable any sticky positioning to ensure proper screenshot
        driver.execute_script("""
            const stickies = document.querySelectorAll('header, [style*="position: fixed"], [style*="position:fixed"], [style*="position: sticky"], [style*="position:sticky"], [role="tablist"]');
            window.__originalPositions = [];
            for (let i = 0; i < stickies.length; i++) {
                const el = stickies[i];
                const style = window.getComputedStyle(el);
                window.__originalPositions.push({
                    element: el,
                    position: style.position
                });
                el.style.position = 'static';
            }
        """)

        # Get the content size to set the correct viewport size
        metrics = driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
        width = metrics['contentSize']['width']

        # Find the actual height of content by detecting the last meaningful element
        actual_height = driver.execute_script("""
            // Find the bottom-most visible element that's not empty space or a footer
            const allElements = Array.from(document.querySelectorAll('body *'));
            let maxBottom = 0;

            // Find footer position to exclude it from calculation
            const footer = document.querySelector('footer');
            const footerTop = footer ? footer.getBoundingClientRect().top : document.body.scrollHeight;

            for (let el of allElements) {
                // Skip invisible elements
                if (el.offsetParent === null) continue;

                const rect = el.getBoundingClientRect();
                // Only consider elements above the footer and that have content
                if (rect.bottom < footerTop && rect.height > 0 && rect.bottom > maxBottom) {
                    maxBottom = rect.bottom;
                }
            }

            // Add a small buffer to ensure we capture everything
            return maxBottom + 50;
        """)

        # Use the calculated height or fall back to content height if script fails
        height = actual_height or metrics['contentSize']['height']

        # Set the viewport to encompass the entire content
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            'mobile': False,
            'width': width,
            'height': height,
            'deviceScaleFactor': 1,
            'screenWidth': width,
            'screenHeight': height
        })

        # Capture the full-page screenshot
        screenshot_data = driver.execute_cdp_cmd('Page.captureScreenshot', {
            'format': 'png',
            'captureBeyondViewport': True,
            'fromSurface': True
        })

        # Restore sticky positioning
        driver.execute_script("""
            if (window.__originalPositions) {
                for (let i = 0; i < window.__originalPositions.length; i++) {
                    const item = window.__originalPositions[i];
                    item.element.style.position = item.position;
                }
                delete window.__originalPositions;
            }
        """)

        # Make sure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save the screenshot
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(screenshot_data['data']))

        logger.info(f"Screenshot saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return False


# Process a single tab (Desktop or Mobile)
def process_tab(driver, device_type, url, index, total_urls, output_dir):
    try:
        # Switch to appropriate tab
        tab_id = f"{device_type.lower()}_tab"
        tab = driver.find_element(By.ID, tab_id)
        driver.execute_script("arguments[0].click();", tab)

        # Wait for the tab to load
        WebDriverWait(driver, SCREENSHOT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.PePDG"))
        )
        time.sleep(LOAD_DELAY)

        # Expand all sections
        expand_all_sections(driver)

        # Calculate the correct index for PSI screenshots
        file_index = get_psi_index(index, device_type)
        filename = generate_filename(file_index, "gps", url.strip(), device_type.lower())
        output_path = os.path.join(output_dir, f"{filename}.png")

        # Reduce unnecessary spacing before taking screenshot
        driver.execute_script("""
            // Remove extra padding/margin at the bottom if possible
            const footer = document.querySelector('footer');
            const contentEnd = document.querySelector('.PePDG'); // Main content container

            if (footer) {
                // If there's unnecessary margin or padding above the footer
                footer.style.marginTop = '10px';
            }

            // Remove any large empty spaces at the bottom of the content
            const allElements = document.querySelectorAll('body *');
            for (let el of allElements) {
                const style = window.getComputedStyle(el);
                if (parseInt(style.marginBottom) > 50) {
                    el.style.marginBottom = '20px';
                }
                if (parseInt(style.paddingBottom) > 50) {
                    el.style.paddingBottom = '20px';
                }
            }

            // Hide cookie notice
            const cookieBanner = document.querySelector('.glAfi');
            cookieBanner.style.display = 'none';
        """)

        return take_cdp_screenshot(driver, output_path)
    except Exception as e:
        logger.error(f"Error processing {device_type} tab for {url}: {e}")
        return False


# Function to run PSI test and take full-page screenshots for both Desktop and Mobile tabs
def run_psi_test_and_screenshot(url, index, total_urls, output_dir):
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1440,1080')  # Set a standard window size

    # Environment-specific options
    if os.getenv("GOOGLE_CHROME_BIN"):
        options.binary_location = os.getenv("GOOGLE_CHROME_BIN")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    service = Service(os.getenv("CHROMEDRIVER_PATH", ChromeDriverManager().install()))
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=options)
        # Enable CDP (Chrome DevTools Protocol)
        driver.execute_cdp_cmd('Page.enable', {})

        # Set page load timeout
        driver.set_page_load_timeout(SCREENSHOT_TIMEOUT)

        # Navigate to PageSpeed Insights
        driver.get("https://pagespeed.web.dev/")
        url_input = driver.find_element(By.CSS_SELECTOR, "input")
        url_input.clear()
        url_input.send_keys(url)
        url_input.submit()

        # Wait for initial results to load
        WebDriverWait(driver, SCREENSHOT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.PePDG"))
        )
        time.sleep(LOAD_DELAY)

        # Process Desktop tab - pass total_urls
        desktop_success = process_tab(driver, "Desktop", url, index, total_urls, output_dir)

        # Process Mobile tab - pass total_urls
        mobile_success = process_tab(driver, "Mobile", url, index, total_urls, output_dir)

        if desktop_success and mobile_success:
            return url  # At least one screenshot was successful
        return None

    except Exception as e:
        logger.error(f"Error processing {url} (PSI): {str(e)}\n{traceback.format_exc()}")
        return None
    finally:
        if driver:
            driver.quit()


# Function to run GTmetrix test and take a screenshot
def run_gtmetrix_screenshot(url, index, total_urls, output_dir, api_key, location):
    if not api_key:
        logger.error("GTmetrix API key not provided")
        return None

    headers = {
        'Authorization': f'Basic {base64.b64encode(api_key.encode()).decode()}',
        'Content-Type': 'application/vnd.api+json'
    }

    driver = None

    try:
        # Create test
        test_data = {
            "data": {
                "type": "test",
                "attributes": {
                    "url": url,
                    "location": location,
                    "browser": 3
                }
            }
        }

        response = requests.post(
            'https://gtmetrix.com/api/2.0/tests',
            headers=headers,
            json=test_data
        )
        response.raise_for_status()

        test_data = response.json().get('data', {})
        test_id = test_data.get('id')

        if not test_id:
            logger.error("No test ID in response")
            return None

        logger.info(f"GTmetrix test created with ID: {test_id}")

        # Poll for report URL
        max_attempts = 60
        attempt = 0
        while attempt < max_attempts:
            time.sleep(5)
            attempt += 1

            status_response = requests.get(
                f'https://gtmetrix.com/api/2.0/tests/{test_id}',
                headers=headers
            )
            status_response.raise_for_status()
            logger.info(f"GTmetrix status response: {status_response.text}")

            # Check for report_url in the response
            data = status_response.json().get('data', {})
            links = data.get('links', {})
            report_url = links.get('report_url')

            if report_url:
                logger.info(f"Found report URL: {report_url}")

                # Define a custom user agent string
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

                # Set up Chrome options
                options = Options()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1440,900')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument(f"user-agent={user_agent}")

                # Create Chrome driver
                service = Service(os.getenv("CHROMEDRIVER_PATH", ChromeDriverManager().install()))
                driver = webdriver.Chrome(service=service, options=options)

                try:
                    # Navigate to report URL
                    driver.get(report_url)
                    time.sleep(5)  # Wait for report to load

                    # Take full page screenshot
                    total_height = driver.execute_script("return document.body.scrollHeight")
                    driver.set_window_size(1440, total_height)

                    # Calculate the correct index for GTmetrix screenshots
                    gtm_index = get_gtm_index(index, total_urls)  # Pass total_urls
                    filename = f"{gtm_index}-gtm-{datetime.now().strftime('%Y%m%d')}-{clean_url_for_filename(url)}.png"

                    # Save screenshot
                    screenshot_path = os.path.join(output_dir, filename)
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"GTmetrix screenshot saved: {screenshot_path}")
                    return screenshot_path

                finally:
                    if driver:
                        driver.quit()

        logger.error("Failed to get report URL within timeout")
        return None

    except Exception as e:
        logger.error(f"Error in GTmetrix screenshot: {str(e)}\n{traceback.format_exc()}")
        return None
    finally:
        if driver and driver.service.is_connectable():
            driver.quit()


# Function to generate index for PSI screenshots
def get_psi_index(url_index, device_type):
    # For first URL: Desktop=1, Mobile=2, Second URL: Desktop=3, Mobile=4
    base = (url_index - 1) * 2
    return base + (1 if device_type.lower() == "desktop" else 2)


# Function to generate index for GTmetrix screenshots
def get_gtm_index(url_index, total_urls):
    # Start GTmetrix indices after all PSI screenshots
    # If 2 URLs: PSI ends at 4, GTmetrix starts at 5
    return (total_urls * 2) + url_index


# Clean up old session directories
def cleanup_old_sessions():
    try:
        if not os.path.exists(OUTPUT_DIR):
            return

        # Get all session directories
        sessions = [d for d in os.listdir(OUTPUT_DIR)
                    if os.path.isdir(os.path.join(OUTPUT_DIR, d))]

        # Sort by creation time (oldest first)
        sessions.sort(key=lambda x: os.path.getctime(os.path.join(OUTPUT_DIR, x)))

        # Remove oldest sessions if we have more than MAX_SESSIONS_TO_KEEP
        if len(sessions) > MAX_SESSIONS_TO_KEEP:
            for old_session in sessions[:-MAX_SESSIONS_TO_KEEP]:
                shutil.rmtree(os.path.join(OUTPUT_DIR, old_session), ignore_errors=True)
                logger.info(f"Cleaned up old session: {old_session}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Route to download the ZIP file
@app.route("/download/<session_id>")
def download_results(session_id):
    zip_path = f"screenshots_{session_id}.zip"
    session_dir = os.path.join(OUTPUT_DIR, session_id)

    try:
        # Check if the session directory exists
        if not os.path.exists(session_dir):
            return "Session not found", 404

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(session_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = file_path.replace(OUTPUT_DIR, "screenshots")
                    zipf.write(file_path, arcname)

        return send_file(zip_path, as_attachment=True, download_name=f"screenshots_{session_id}.zip")
    except Exception as e:
        error_msg = f"Error creating ZIP file: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"Error: {error_msg}", 500
    finally:
        # Clean up the ZIP file after sending
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass


# Web Interface
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            input_urls = request.form.get("urls", "").splitlines()
            input_urls = [url.strip() for url in input_urls if url.strip()]
            total_urls = len(input_urls)
            use_gtmetrix = request.form.get("use_gtmetrix") == "on"
            gtmetrix_key = request.form.get("gtmetrix_key", "").strip()

            if not input_urls:
                return "Error: Please enter at least one URL."

            if use_gtmetrix and not gtmetrix_key:
                return "Error: GTmetrix API key is required when using GTmetrix."

            # Create a unique session ID and output directory
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(OUTPUT_DIR, session_id)
            os.makedirs(output_dir, exist_ok=True)

            results = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Process with PageSpeed Insights
                psi_futures = {
                    executor.submit(
                        run_psi_test_and_screenshot,
                        url,
                        idx + 1,
                        total_urls,  # Pass total_urls
                        output_dir
                    ): (url, "PSI") for idx, url in enumerate(input_urls)
                }

                # Process with GTmetrix if enabled
                if use_gtmetrix:
                    gtmetrix_location = request.form.get("gtmetrix_location")
                    gtm_futures = {
                        executor.submit(
                            run_gtmetrix_screenshot,
                            url,
                            idx + 1,
                            total_urls,  # Pass total_urls
                            output_dir,
                            gtmetrix_key,
                            gtmetrix_location
                        ): (url, "GTmetrix") for idx, url in enumerate(input_urls)
                    }
                    all_futures = {**psi_futures, **gtm_futures}
                else:
                    all_futures = psi_futures

                # Process results as they complete
                for future in all_futures:
                    url, tool = all_futures[future]
                    try:
                        result = future.result()
                        results.append({
                            "input": url,
                            "tool": tool,
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Error processing {url} with {tool}: {str(e)}")
                        results.append({
                            "input": url,
                            "tool": tool,
                            "result": None
                        })

            # Get screenshot files
            screenshot_files = []
            if os.path.exists(output_dir):
                screenshot_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
                screenshot_files.sort()

            # Prepare file lists for template with improved result tracking
            generated_files = []
            for result in results:
                url = result["input"]
                tool = result["tool"]

                if result["result"]:
                    if tool == "PSI":
                        # Add both desktop and mobile results
                        index = len(generated_files) // 2 + 1
                        generated_files.extend([
                            {
                                "url": url,
                                "name": generate_filename(index * 2 - 1, "gps", url, "desktop"),
                                "success": True,
                                "tool": "PageSpeed Desktop"
                            },
                            {
                                "url": url,
                                "name": generate_filename(index * 2, "gps", url, "mobile"),
                                "success": True,
                                "tool": "PageSpeed Mobile"
                            }
                        ])
                    else:  # GTmetrix
                        generated_files.append({
                            "url": url,
                            "name": os.path.basename(result["result"]),
                            "success": True,
                            "tool": "GTmetrix"
                        })
                else:
                    generated_files.append({
                        "url": url,
                        "name": "Failed",
                        "success": False,
                        "tool": tool
                    })

            # Count actual completed screenshots
            success_count = len(screenshot_files)
            expected_count = len(input_urls)
            if use_gtmetrix:
                expected_count *= 2  # Two screenshots per URL (PSI Desktop/Mobile)
            else:
                expected_count *= 2  # Two screenshots per URL (PSI Desktop/Mobile)
            failed_count = expected_count - success_count

            # Clean up old sessions
            cleanup_old_sessions()

            return render_template("results.html",
                                   session_id=session_id,
                                   input_urls=input_urls,
                                   generated_files=generated_files,
                                   screenshot_files=screenshot_files,
                                   success_count=success_count,
                                   failed_count=failed_count)

        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return f"Error: {error_msg}"

    return render_template("index.html")


# Health check endpoint
@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Start the Flask app
    port = int(os.environ.get("PORT", 5001))
    app.run(host="127.0.0.1", port=port, debug=False)
