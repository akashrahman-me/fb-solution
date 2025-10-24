"""
Facebook Account Checker - Simplified Functional Version
A beginner-friendly tool to check if phone numbers are associated with Facebook accounts
"""


import time
import os
import queue
import threading
from datetime import datetime
from playwright.sync_api import sync_playwright
import logging
import shutil
import random

from utils.normalize_text import normalize_text
import proxy_injector

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global configuration
PROXY_SERVER = "http://127.0.0.1:9080"
TIMEOUT = 30000  # milliseconds
POLL_INTERVAL = 0.3  # seconds
PROFILES_DIR = "profiles"
FB_RECOVERY_URL = "https://www.facebook.com/login/identify/"

# Browser arguments
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-gpu',
    '--log-level=3',
    '--silent',
    # Enable disk cache
    '--disk-cache-size=104857600',  # 100MB cache
    '--media-cache-size=104857600',  # 100MB media cache
]

# Proxy server state
_proxy_thread = None
_proxy_started = False
_proxy_lock = threading.Lock()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def start_proxy_server():
    """Start the proxy server in a background thread"""
    global _proxy_thread, _proxy_started

    with _proxy_lock:
        if _proxy_started:
            logger.info("Proxy server already running")
            return

        logger.info("Starting proxy server in background...")
        _proxy_thread = threading.Thread(target=proxy_injector.start_proxy_server, daemon=True)
        _proxy_thread.start()
        _proxy_started = True

        # Give the proxy server a moment to start up
        time.sleep(2)
        logger.info("Proxy server started successfully")


def ensure_directories():
    """Create necessary directories if they don't exist"""

    try:
        shutil.rmtree("photo")
        shutil.rmtree("html")
    except FileNotFoundError:
        pass  # Directory doesn't exist, ignore

    os.makedirs("photo", exist_ok=True)
    os.makedirs("html", exist_ok=True)
    os.makedirs("collection", exist_ok=True)
    os.makedirs(PROFILES_DIR, exist_ok=True)


def get_profile_path(worker_id):
    """Get the browser profile path for a worker"""
    profile_path = os.path.join(PROFILES_DIR, str(worker_id))
    os.makedirs(profile_path, exist_ok=True)
    return profile_path


def save_debug_info(page, phone_number, worker_id):
    """Save screenshot and HTML for debugging"""
    try:
        filename = f"{phone_number}_worker{worker_id}"
        page.screenshot(path=f"photo/{filename}.png")
        with open(f"html/{filename}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        logger.info(f"Debug info saved for {phone_number}")
    except Exception as e:
        logger.error(f"Error saving debug info: {e}")


def random_user_agent():
    """Generate a random user agent"""
    user_agents = [
        # Windows Chrome (v141)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        # Windows Chrome (v140)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        # Windows Edge (v141)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.3537.85",
        # Windows Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
        # macOS Chrome (v141) - Note: macOS version is often "frozen" at 10_15_7 for privacy
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        # macOS Safari (v26) - Note: Uses the modern macOS version (e.g., 15_7)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
        # Android Chrome (v141 on Android 14)
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
        # Android Chrome (v141, "frozen" Android 10 string for privacy)
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
    ]
    return random.choice(user_agents)


def random_viewport():
    """Generate a random viewport size"""
    viewports = [
        {"width": 1920, "height": 1080},  # Full HD
        {"width": 1366, "height": 768},   # Common laptop
        {"width": 1536, "height": 864},   # Common laptop
        {"width": 1440, "height": 900},   # MacBook
        {"width": 1280, "height": 720},   # HD
        {"width": 2560, "height": 1440},  # 2K
    ]
    return random.choice(viewports)


# ============================================================================
# BROWSER MANAGEMENT
# ============================================================================

def create_browser(worker_id, headless=False):
    """Create and return a browser context and page"""
    profile_path = get_profile_path(worker_id)
    profile_exists = os.path.exists(os.path.join(profile_path, "Default"))

    if profile_exists:
        logger.info(f"Worker {worker_id}: Loading existing profile")
    else:
        logger.info(f"Worker {worker_id}: Creating new profile")

    playwright = sync_playwright().start()

    context = playwright.chromium.launch_persistent_context(
        profile_path,
        headless=headless,
        args=BROWSER_ARGS + [
            '--disable-blink-features=AutomationControlled',
            '--exclude-switches=enable-automation',
            '--disable-infobars',
        ],
        proxy={"server": PROXY_SERVER},
        viewport=random_viewport()
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(TIMEOUT)

    # Set default navigation to not wait for images/stylesheets
    page.set_default_navigation_timeout(TIMEOUT)

    # Comprehensive stealth scripts to hide automation
    user_agent = random_user_agent()

    stealth_script = f"""
        // Override navigator properties
        Object.defineProperty(navigator, 'userAgent', {{
            get: () => '{user_agent}'
        }});
        
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined
        }});
        
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [1, 2, 3, 4, 5]
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['en-US', 'en']
        }});
        
        // Remove automation traces
        window.navigator.chrome = {{
            runtime: {{}}
        }};
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        
        // Hide webdriver property
        delete navigator.__proto__.webdriver;
    """

    page.add_init_script(stealth_script)
    logger.info(f"Worker {worker_id}: User agent set to {user_agent}")
    logger.info(f"Worker {worker_id}: Stealth mode enabled")

    logger.info(f"Worker {worker_id}: Browser initialized")

    return playwright, context, page


def close_browser(playwright, context):
    """Close browser and save profile"""
    if context:
        context.close()
    if playwright:
        playwright.stop()


# ============================================================================
# PAGE INTERACTION FUNCTIONS
# ============================================================================

def click_element(page, selector, description):
    """Click an element on the page"""
    try:
        element = page.locator(selector).first
        element.wait_for(state="visible", timeout=TIMEOUT)
        element.click()
        logger.info(f"Clicked: {description}")
        return True
    except Exception as e:
        logger.error(f"Error clicking {description}: {e}")
        return False


def type_text(page, selector, text, description):
    """Type text into an input field"""
    try:
        element = page.locator(selector).first
        element.wait_for(state="visible", timeout=TIMEOUT)
        element.clear()
        element.type(text)
        logger.info(f"Typed into: {description}")
        return True
    except Exception as e:
        logger.error(f"Error typing into {description}: {e}")
        return False


def click_clickable_parent(element):
    """Recursively find and click the first clickable parent element"""
    try:
        if element.is_visible() and element.is_enabled():
            element.click()
            return True
        parent = element.locator("xpath=..").first
        if parent.evaluate("el => el.tagName").lower() == "html":
            return False
        return click_clickable_parent(parent)
    except:
        return False


def wait_for_any_text(page, text_list, max_time):
    """Wait for any text from a list to appear on the page"""
    start_time = time.time()

    while time.time() - start_time < max_time:
        try:
            page_content = page.content()
            for text in text_list:
                if normalize_text(text.lower())  in normalize_text(page_content.lower()):
                    logger.info(f"Searched “{text}”")
                    return text
            time.sleep(POLL_INTERVAL)
        except:
            time.sleep(POLL_INTERVAL)

    return None


# ============================================================================
# FLOW HANDLERS
# ============================================================================

def handle_cookie_consent(page):
    """Handle cookie consent popup"""
    try:
        cookie_element = page.locator("//*[contains(text(), 'Allow all cookies')]").first
        if cookie_element.count() > 0:
            click_clickable_parent(cookie_element)
            logger.info("Cookie consent handled")
    except:
        logger.debug("No cookie popup found")


def handle_find_account(page, phone_number):
    """Enter phone number and search for account"""
    type_text(page, "#identify_email", phone_number, "phone number field")
    time.sleep(0.5)
    click_element(page, "#did_submit", "search button")
    logger.info(f"Searched for: {phone_number}")


def handle_select_account(page):
    """Select the account from search results"""
    click_element(page, "//a[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'this is my account')]", "account confirmation")


def handle_recovery_method(page, phone_number):
    """Select SMS recovery method"""
    phone_digits = ''.join(filter(str.isdigit, phone_number))
    all_radios = page.locator("//input[@type='radio' and @name='recover_method']").all()

    sms_radio = None
    for radio in all_radios:
        try:
            radio_id = radio.get_attribute('id')
            if not radio_id or not radio_id.startswith('send_sms:'):
                continue

            label = page.locator(f"//label[@for='{radio_id}']").first
            label_text = label.text_content()

            if "Send code via SMS" not in label_text:
                continue

            phone_in_label = ''.join(filter(str.isdigit, label_text))
            if (phone_digits == phone_in_label or
                phone_digits in phone_in_label or
                phone_in_label in phone_digits):
                sms_radio = radio
                break
        except Exception as e:
            logger.debug(f"Error processing radio button: {e}")

    if not sms_radio:
        return False, "Can't find the 'Send code via SMS' option"

    if not sms_radio.is_checked():
        sms_radio.click()
        logger.info("SMS radio button selected")

    click_element(page, "//button[@name='reset_action' and @type='submit' and contains(text(), 'Continue')]", "Continue button")
    return True, None


def handle_try_another_way(page):
    """Click 'Try another way' link"""
    click_element(page, "//a[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'try another way')]", "Try another way")


def handle_continue_button(page):
    """Click Continue button"""
    if not click_element(page, "//button[@type='submit' and contains(text(), 'Continue')]", "Continue button"):
        click_element(page, "//button[@type='submit']", "Continue button (alt)")


# ============================================================================
# MAIN CHECKING LOGIC
# ============================================================================

# Text constants for Facebook page detection
TEXT_ENTER_SECURITY_CODE = "Enter security code"
TEXT_NO_SEARCH_RESULTS = "No search results"
TEXT_ACCOUNT_DISABLED = "Account disabled"
TEXT_CAPTCHA_REQUIRED = "Before we send the code, enter these letters and numbers"
TEXT_TEMPORARILY_BLOCKED = "You're Temporarily Blocked"
TEXT_TRY_ANOTHER_DEVICE = "Try another device to continue"
TEXT_TRY_ANOTHER_WAY = "Try another way"
TEXT_COOKIE_CONSENT = "Allow the use of cookies from Facebook on this browser?"
TEXT_FIND_YOUR_ACCOUNT = "Find Your Account"
TEXT_ACCOUNTS_MATCHED = "These accounts matched your search"
TEXT_RECEIVE_CODE_RESET = "How do you want to receive the code to reset your password?"
TEXT_GET_CODE_RESET = "How do you want to get the code to reset your password?"
TEXT_SEND_LOGIN_CODE = "We can send a login code to:"
TEXT_RELOAD_PAGE = "Reload page"

def check_phone_number(page, phone_number, worker_id, clear_cache=False):
    """
    Check a single phone number on Facebook
    Returns: (success: bool, message: str)

    Args:
        page: Playwright page object
        phone_number: Phone number to check
        worker_id: Worker ID for debugging
        clear_cache: If True, clears cookies/storage (default: False to keep cache)
    """
    try:
        # Clear cookies and storage only if requested (to appear as new user)
        # NOTE: Setting clear_cache=False preserves HTTP cache for bandwidth saving
        if clear_cache:
            page.context.clear_cookies()

            # Clear localStorage and sessionStorage
            try:
                page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            except:
                pass

        # Navigate to recovery page (don't wait for all resources to load)
        page.goto(FB_RECOVERY_URL, wait_until="domcontentloaded")

        # List of all possible texts we might encounter
        all_possible_texts = [
            TEXT_ENTER_SECURITY_CODE,  # SUCCESS
            TEXT_NO_SEARCH_RESULTS,  # FAILURE
            TEXT_ACCOUNT_DISABLED,  # FAILURE
            TEXT_CAPTCHA_REQUIRED,  # FAILURE - CAPTCHA
            TEXT_TEMPORARILY_BLOCKED,  # FAILURE
            TEXT_TRY_ANOTHER_DEVICE,  # FAILURE
            TEXT_COOKIE_CONSENT,  # ACTION
            TEXT_FIND_YOUR_ACCOUNT,  # ACTION
            TEXT_ACCOUNTS_MATCHED,  # ACTION
            TEXT_RECEIVE_CODE_RESET,  # ACTION
            TEXT_GET_CODE_RESET,  # ACTION
            TEXT_SEND_LOGIN_CODE,  # ACTION
            TEXT_RELOAD_PAGE,  # ACTION
            TEXT_TRY_ANOTHER_WAY,  # ACTION
        ]

        # Process flow - maximum 20 attempts
        while True:
            # Wait for any expected text to appear (smart waiting)
            found_text = wait_for_any_text(page, all_possible_texts, TIMEOUT / 1000)

            # If nothing found, something is wrong
            if not found_text:
                logger.warning(f"No expected content found")
                save_debug_info(page, phone_number, worker_id)
                return False, "Unexpected page state"

            # Check for SUCCESS
            if found_text == TEXT_ENTER_SECURITY_CODE:
                logger.info("✓ Verification code page reached - SUCCESS!")

                # Save current URL to txt file
                current_url = page.url

                # Get cookies and format them as name=value;name2=value2
                cookies = page.context.cookies()
                cookie_string = ";".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

                # Save URL and cookies to txt file
                os.makedirs("collection", exist_ok=True)
                with open(f"collection/{phone_number}.txt", "w", encoding="utf-8") as f:
                    f.write(current_url + "\n")
                    f.write(cookie_string)
                logger.info(f"URL and cookies saved to collection/{phone_number}.txt")
                logger.info(f"URL: {current_url}")
                logger.info(f"Cookies: {len(cookies)} cookies saved")

                return True, "Verification code page reached"

            # Check for FAILURES
            if found_text == TEXT_NO_SEARCH_RESULTS:
                return False, "Facebook account not found"

            if found_text == TEXT_ACCOUNT_DISABLED:
                return False, "Account is disabled"

            if found_text == TEXT_CAPTCHA_REQUIRED:
                return False, "CAPTCHA required"

            if found_text == TEXT_TEMPORARILY_BLOCKED:
                return False, "You're temporarily blocked"

            if found_text == TEXT_TRY_ANOTHER_DEVICE:
                return False, "Try another device to continue"

            # Handle ACTIONS based on what we found
            if found_text == TEXT_COOKIE_CONSENT:
                logger.info("Action: Handling cookie consent")
                handle_cookie_consent(page)
                all_possible_texts.remove(TEXT_COOKIE_CONSENT)

            if found_text == TEXT_FIND_YOUR_ACCOUNT:
                logger.info("Action: Entering phone number")
                handle_find_account(page, phone_number)
                all_possible_texts.remove(TEXT_FIND_YOUR_ACCOUNT)

            if found_text == TEXT_ACCOUNTS_MATCHED:
                logger.info("Action: Selecting account")
                handle_select_account(page)
                all_possible_texts.remove(TEXT_ACCOUNTS_MATCHED)

            if found_text == TEXT_RECEIVE_CODE_RESET or found_text == TEXT_GET_CODE_RESET:
                logger.info("Action: Selecting SMS recovery method")
                success, error_msg = handle_recovery_method(page, phone_number)
                if not success:
                    return False, error_msg
                all_possible_texts.remove(TEXT_RECEIVE_CODE_RESET)
                all_possible_texts.remove(TEXT_GET_CODE_RESET)

            if found_text == TEXT_TRY_ANOTHER_WAY:
                logger.info("Action: Trying another way")
                handle_try_another_way(page)
                all_possible_texts.remove(TEXT_TRY_ANOTHER_WAY)


            if found_text == TEXT_SEND_LOGIN_CODE:
                logger.info("Action: Clicking continue")
                handle_continue_button(page)
                all_possible_texts.remove(TEXT_SEND_LOGIN_CODE)

            if found_text == TEXT_RELOAD_PAGE:
                logger.info("Action: Reloading page")
                page.reload(wait_until="domcontentloaded")
                time.sleep(0.5)
                all_possible_texts.remove(TEXT_RELOAD_PAGE)

        # Reached maximum iterations without result
        save_debug_info(page, phone_number, worker_id)
        return False, "Maximum iterations reached"

    except Exception as e:
        logger.error(f"Error checking {phone_number}: {e}")
        return False, f"Error: {str(e)}"


# ============================================================================
# WORKER THREAD
# ============================================================================

def worker_thread(worker_id, phone_queue, results_list, results_lock, headless, callback=None):
    """Worker function that processes phone numbers from queue"""
    playwright = None
    context = None
    page = None
    phones_processed = 0

    try:
        # Setup browser once
        playwright, context, page = create_browser(worker_id, headless)
        logger.info(f"Worker {worker_id} ready")

        while True:
            try:
                # Get phone number from queue
                phone_number = phone_queue.get(timeout=1)
                logger.info(f"Worker {worker_id} checking: {phone_number}")

                # Check the phone number
                try:
                    success, message = check_phone_number(page, phone_number, worker_id)
                    status = 'success' if success else 'failed'
                except Exception as check_error:
                    logger.error(f"Worker {worker_id} error: {check_error}")
                    status = 'error'
                    message = str(check_error)

                phones_processed += 1

                # Store result thread-safely
                result = {
                    'phone': phone_number,
                    'status': status,
                    'message': message
                }

                with results_lock:
                    results_list.append(result)
                    total = phone_queue.qsize() + len(results_list)
                    logger.info(f"Progress: {len(results_list)}/{total} - {phone_number}: {status}")

                # Call callback if provided (for real-time GUI updates)
                if callback:
                    try:
                        callback(result)
                    except Exception as callback_error:
                        logger.error(f"Callback error: {callback_error}")

                phone_queue.task_done()

            except queue.Empty:
                logger.info(f"Worker {worker_id} finished - processed {phones_processed} numbers")
                break

    except Exception as e:
        logger.error(f"Worker {worker_id} fatal error: {e}")

    finally:
        # Close browser
        if playwright and context:
            close_browser(playwright, context)
            logger.info(f"Worker {worker_id} closed")


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def process_phone_numbers(phone_numbers, num_workers=1, headless=False, callback=None):
    """
    Process multiple phone numbers using worker threads

    Args:
        phone_numbers: List of phone numbers to check
        num_workers: Number of parallel workers
        headless: Run browsers in headless mode
        callback: Optional callback function called for each result: callback(result_dict)

    Returns:
        List of results dictionaries
    """
    # Start proxy server in background
    start_proxy_server()

    ensure_directories()

    # Create queue and add phone numbers
    phone_queue = queue.Queue()
    for number in phone_numbers:
        phone_queue.put(number)

    results_list = []
    results_lock = threading.Lock()

    logger.info(f"Starting to check {len(phone_numbers)} phone numbers with {num_workers} workers")

    # Create and start worker threads
    workers = []
    for i in range(num_workers):
        thread = threading.Thread(
            target=worker_thread,
            args=(i, phone_queue, results_list, results_lock, headless, callback)
        )
        workers.append(thread)
        thread.start()

    # Wait for all workers to complete
    for thread in workers:
        thread.join()

    logger.info("All workers completed")
    return results_list


def check_single_number(phone_number, headless=False):
    """
    Check a single phone number (convenience function)

    Args:
        phone_number: Phone number to check
        headless: Run browser in headless mode

    Returns:
        Result dictionary
    """
    results = process_phone_numbers([phone_number], num_workers=1, headless=headless)
    return results[0] if results else None


# ============================================================================
# RESULTS DISPLAY
# ============================================================================

def print_results(results):
    """Print results summary"""
    logger.info("=" * 70)
    logger.info("RESULTS:")
    logger.info("=" * 70)

    for result in results:
        logger.info(f"{result['phone']}: {result['status']} - {result['message']}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main function - entry point of the program"""

    # Sample phone numbers for testing
    phone_numbers_text = """
        998992608371
998992603001
998992607726
998992604633
998992606010
    """

    # Parse phone numbers (remove empty lines and spaces)
    phone_numbers = [num.strip() for num in phone_numbers_text.split('\n') if num.strip()]

    # Process phone numbers with 5 workers
    results = process_phone_numbers(
        phone_numbers=phone_numbers,
        num_workers=1,
        headless=False
    )

    # Display results
    print_results(results)


if __name__ == "__main__":
    main()
