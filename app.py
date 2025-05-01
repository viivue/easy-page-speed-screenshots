import base64
import logging
import os
import re
import shutil
import time
import traceback
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
from flask import Flask, request, render_template, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
CONFIG = {
    'OUTPUT_DIR': "temp_screenshots",
    'MAX_WORKERS': 1,
    'MAX_SESSIONS_TO_KEEP': 5,
    'SCREENSHOT_TIMEOUT': 30,
    'EXPAND_DELAY': 0.1,
    'LOAD_DELAY': 5,
    'DEBUG': False,
    'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}


# Clean URL for filename
def epss_clean_url_for_filename(url):
    cleaned = re.sub(r'https?://', '', url)
    cleaned = re.sub(r'[^a-zA-Z0-9]', '-', cleaned).strip("-")
    return cleaned


# Generate filename
def epss_generate_filename(index, tool, url, device):
    date_str = datetime.now().strftime("%Y%m%d")
    decoded_url = epss_clean_url_for_filename(url)
    return f"{index}-{tool}-{date_str}-{decoded_url}-{device}"


# Initialize Chrome driver
def epss_init_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1440,1080')
    options.add_argument(f"user-agent={CONFIG['USER_AGENT']}")

    if os.getenv("GOOGLE_CHROME_BIN"):
        options.binary_location = os.getenv("GOOGLE_CHROME_BIN")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    service = Service(os.getenv("CHROMEDRIVER_PATH", ChromeDriverManager().install()))
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd('Page.enable', {})
    driver.set_page_load_timeout(CONFIG['SCREENSHOT_TIMEOUT'])
    return driver


# Expand all sections
def epss_expand_all_sections(driver):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".lh-audit-group__header")
        for element in elements:
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element
                )
                time.sleep(CONFIG['EXPAND_DELAY'])
                if element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                logger.warning(f"Failed to expand element: {e}")
    except Exception as e:
        logger.warning(f"No expandable elements or failed to expand: {e}")


# Take CDP full-page screenshot
def epss_take_cdp_screenshot(driver, output_path):
    try:
        # Disable sticky elements
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

        # Get content dimensions
        metrics = driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
        width = metrics['contentSize']['width']
        height = driver.execute_script("""
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
        """) or metrics['contentSize']['height']

        # Set viewport
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            'mobile': False, 'width': width, 'height': height, 'deviceScaleFactor': 1,
            'screenWidth': width, 'screenHeight': height
        })

        # Capture screenshot
        screenshot_data = driver.execute_cdp_cmd('Page.captureScreenshot', {
            'format': 'png', 'captureBeyondViewport': True, 'fromSurface': True
        })

        # Restore sticky elements
        driver.execute_script("""
            if (window.__originalPositions) {
                for (let i = 0; i < window.__originalPositions.length; i++) {
                    const item = window.__originalPositions[i];
                    item.element.style.position = item.position;
                }
                delete window.__originalPositions;
            }
        """)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(screenshot_data['data']))
        logger.info(f"Screenshot saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return False


# Process a single tab (Desktop or Mobile)
def epss_process_tab(driver, device_type, url, index, output_dir):
    try:
        tab_id = f"{device_type.lower()}_tab"
        tab = driver.find_element(By.ID, tab_id)
        driver.execute_script("arguments[0].click();", tab)

        # Wait for the tab to load
        WebDriverWait(driver, CONFIG['SCREENSHOT_TIMEOUT']).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.PePDG"))
        )
        time.sleep(CONFIG['LOAD_DELAY'])

        epss_expand_all_sections(driver)
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

        file_index = epss_get_psi_index(index, device_type)
        filename = epss_generate_filename(file_index, "gps", url.strip(), device_type.lower())
        return epss_take_cdp_screenshot(driver, os.path.join(output_dir, f"{filename}.png"))
    except Exception as e:
        logger.error(f"Error processing {device_type} tab for {url}: {e}")
        return False


# Run PSI test and screenshot
def epss_run_psi_test_and_screenshot(url, index, total_urls, output_dir):
    driver = None
    try:
        driver = epss_init_driver()
        driver.get("https://pagespeed.web.dev/")
        url_input = driver.find_element(By.CSS_SELECTOR, "input")
        url_input.clear()
        url_input.send_keys(url)
        url_input.submit()

        WebDriverWait(driver, CONFIG['SCREENSHOT_TIMEOUT']).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.PePDG"))
        )
        time.sleep(CONFIG['LOAD_DELAY'])

        desktop_success = epss_process_tab(driver, "Desktop", url, index, output_dir)
        mobile_success = epss_process_tab(driver, "Mobile", url, index, output_dir)

        return url if desktop_success or mobile_success else None
    except Exception as e:
        logger.error(f"Error processing {url} (PSI): {e}\n{traceback.format_exc()}")
        return None
    finally:
        if driver:
            driver.quit()


# Run GTmetrix test and screenshot
def epss_run_gtmetrix_screenshot(url, index, total_urls, output_dir, api_key, location):
    if not api_key:
        logger.error("GTmetrix API key not provided")
        return None

    headers = {
        'Authorization': f'Basic {base64.b64encode(api_key.encode()).decode()}',
        'Content-Type': 'application/vnd.api+json'
    }
    driver = None

    test_data = {
        "data": {"type": "test", "attributes": {"url": url, "location": location, "browser": 3}}
    }

    try:
        # Add verify=True and handle potential certificate issues
        response = requests.post(
            'https://gtmetrix.com/api/2.0/tests',
            headers=headers,
            json=test_data,
            verify=True  # Explicitly set verify to True
        )
        response.raise_for_status()

        test_id = response.json().get('data', {}).get('id')
        if not test_id:
            logger.error("No test ID in response")
            return None

        logger.info(f"GTmetrix test created with ID: {test_id}")
        report_url = None
        for _ in range(20):
            time.sleep(5)
            # Add verify=True here as well
            status_response = requests.get(
                f'https://gtmetrix.com/api/2.0/tests/{test_id}',
                headers=headers,
                verify=True  # Explicitly set verify to True
            )
            status_response.raise_for_status()
            report_url = status_response.json().get('data', {}).get('links', {}).get('report_url')
            if report_url:
                break

        if not report_url:
            logger.error("Failed to get report URL within timeout")
            return None

        driver = epss_init_driver()
        driver.get(report_url)
        time.sleep(5)

        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1440, total_height)
        gtm_index = epss_get_gtm_index(index, total_urls)
        filename = f"{gtm_index}-gtm-{datetime.now().strftime('%Y%m%d')}-{epss_clean_url_for_filename(url)}.png"
        screenshot_path = os.path.join(output_dir, filename)
        driver.save_screenshot(screenshot_path)
        logger.info(f"GTmetrix screenshot saved: {screenshot_path}")
        return screenshot_path
    except requests.exceptions.SSLError as ssl_err:
        logger.error(f"SSL Error connecting to GTmetrix: {ssl_err}")
        # Handling SSL errors specifically
        logger.info("Attempting to use alternative certificate verification...")
        try:
            # If we're here, we had an SSL error, so let's try with certificate verification disabled
            # Note: This is less secure but can be used as a fallback
            if 'test_id' not in locals():
                # If we failed during the initial test creation
                response = requests.post(
                    'https://gtmetrix.com/api/2.0/tests',
                    headers=headers,
                    json=test_data,
                    verify=False  # Disable certificate verification as a fallback
                )
                response.raise_for_status()
                test_id = response.json().get('data', {}).get('id')

            # Continue with status checks using verify=False
            report_url = None
            for _ in range(20):
                time.sleep(5)
                status_response = requests.get(
                    f'https://gtmetrix.com/api/2.0/tests/{test_id}',
                    headers=headers,
                    verify=False  # Disable certificate verification as a fallback
                )
                status_response.raise_for_status()
                report_url = status_response.json().get('data', {}).get('links', {}).get('report_url')
                if report_url:
                    break

            if not report_url:
                logger.error("Failed to get report URL within timeout (even with SSL verification disabled)")
                return None

            driver = epss_init_driver()
            driver.get(report_url)
            time.sleep(5)

            total_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(1440, total_height)
            gtm_index = epss_get_gtm_index(index, total_urls)
            filename = f"{gtm_index}-gtm-{datetime.now().strftime('%Y%m%d')}-{epss_clean_url_for_filename(url)}.png"
            screenshot_path = os.path.join(output_dir, filename)
            driver.save_screenshot(screenshot_path)
            logger.info(f"GTmetrix screenshot saved (with SSL verification disabled): {screenshot_path}")
            return screenshot_path
        except Exception as fallback_err:
            logger.error(f"Fallback method also failed: {fallback_err}")
            return None
    except Exception as e:
        logger.error(f"Error in GTmetrix screenshot: {e}\n{traceback.format_exc()}")
        return None
    finally:
        if driver and driver.service.is_connectable():
            driver.quit()


# Generate PSI index
def epss_get_psi_index(url_index, device_type):
    base = (url_index - 1) * 2
    return base + (1 if device_type.lower() == "desktop" else 2)


# Generate GTmetrix index
def epss_get_gtm_index(url_index, total_urls):
    return (total_urls * 2) + url_index


# Clean up old sessions
def epss_cleanup_old_sessions():
    try:
        if not os.path.exists(CONFIG['OUTPUT_DIR']):
            return
        sessions = [d for d in os.listdir(CONFIG['OUTPUT_DIR']) if os.path.isdir(os.path.join(CONFIG['OUTPUT_DIR'], d))]
        sessions.sort(key=lambda x: os.path.getctime(os.path.join(CONFIG['OUTPUT_DIR'], x)))
        for old_session in sessions[:-CONFIG['MAX_SESSIONS_TO_KEEP']]:
            shutil.rmtree(os.path.join(CONFIG['OUTPUT_DIR'], old_session), ignore_errors=True)
            logger.info(f"Cleaned up old session: {old_session}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Download ZIP file
@app.route("/download/<session_id>")
def epss_download_results(session_id):
    zip_path = f"screenshots_{session_id}.zip"
    session_dir = os.path.join(CONFIG['OUTPUT_DIR'], session_id)

    try:
        if not os.path.exists(session_dir):
            return "Session not found", 404

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(session_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = file_path.replace(CONFIG['OUTPUT_DIR'], "screenshots")
                    zipf.write(file_path, arcname)

        return send_file(zip_path, as_attachment=True, download_name=f"screenshots_{session_id}.zip")
    except Exception as e:
        logger.error(f"Error creating ZIP file: {e}\n{traceback.format_exc()}")
        return f"Error: {e}", 500
    finally:
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except:
                pass


# Web Interface
@app.route("/", methods=["GET", "POST"])
def epss_index():
    if request.method == "POST":
        try:
            input_urls = [url.strip() for url in request.form.get("urls", "").splitlines() if url.strip()]
            total_urls = len(input_urls)
            use_gtmetrix = request.form.get("use_gtmetrix") == "on"
            gtmetrix_key = request.form.get("gtmetrix_key", "").strip()

            if not input_urls:
                return "Error: Please enter at least one URL."
            if use_gtmetrix and not gtmetrix_key:
                return "Error: GTmetrix API key is required when using GTmetrix."

            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(CONFIG['OUTPUT_DIR'], session_id)
            os.makedirs(output_dir, exist_ok=True)

            results = []
            with ThreadPoolExecutor(max_workers=CONFIG['MAX_WORKERS']) as executor:
                psi_futures = {
                    executor.submit(epss_run_psi_test_and_screenshot, url, idx + 1, total_urls, output_dir): (url,
                                                                                                              "PSI")
                    for idx, url in enumerate(input_urls)
                }
                if use_gtmetrix:
                    gtmetrix_location = request.form.get("gtmetrix_location")
                    gtm_futures = {
                        executor.submit(epss_run_gtmetrix_screenshot, url, idx + 1, total_urls, output_dir,
                                        gtmetrix_key, gtmetrix_location): (url, "GTmetrix")
                        for idx, url in enumerate(input_urls)
                    }
                    all_futures = {**psi_futures, **gtm_futures}
                else:
                    all_futures = psi_futures

                for future in all_futures:
                    url, tool = all_futures[future]
                    try:
                        result = future.result()
                        results.append({"input": url, "tool": tool, "result": result})
                    except Exception as e:
                        logger.error(f"Error processing {url} with {tool}: {e}")
                        results.append({"input": url, "tool": tool, "result": None})

            screenshot_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')]) if os.path.exists(
                output_dir) else []
            generated_files = []
            for result in results:
                url, tool = result["input"], result["tool"]
                if result["result"]:
                    if tool == "PSI":
                        index = len(generated_files) // 2 + 1
                        generated_files.extend([
                            {"url": url, "name": epss_generate_filename(index * 2 - 1, "gps", url, "desktop"),
                             "success": True, "tool": "PageSpeed Desktop"},
                            {"url": url, "name": epss_generate_filename(index * 2, "gps", url, "mobile"),
                             "success": True, "tool": "PageSpeed Mobile"}
                        ])
                    else:
                        generated_files.append({"url": url, "name": os.path.basename(result["result"]), "success": True,
                                                "tool": "GTmetrix"})
                else:
                    generated_files.append({"url": url, "name": "Failed", "success": False, "tool": tool})

            success_count = len(screenshot_files)
            expected_count = len(input_urls) * (3 if use_gtmetrix else 2)
            failed_count = expected_count - success_count

            epss_cleanup_old_sessions()
            return render_template("results.html", session_id=session_id, input_urls=input_urls,
                                   generated_files=generated_files, screenshot_files=screenshot_files,
                                   success_count=success_count, failed_count=failed_count)
        except Exception as e:
            logger.error(f"Error during processing: {e}\n{traceback.format_exc()}")
            return f"Error: {e}"

    return render_template("index.html")


if __name__ == "__main__":
    os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5001)), debug=CONFIG['DEBUG'])