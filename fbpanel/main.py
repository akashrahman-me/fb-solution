from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global lock to prevent concurrent driver initialization
_driver_init_lock = threading.Lock()

# Global bandwidth tracking
_total_bandwidth_lock = threading.Lock()
_global_bandwidth_stats = {
    'total_sent': 0,
    'total_received': 0,
    'total_requests': 0
}

# ============================================
# EXPIRATION CONFIGURATION
# ============================================
# Set the expiration date (YYYY, MM, DD, HH, MM, SS)
# After this date, the software will stop working for all users
# EXPIRATION_DATE = datetime(2025, 10, 17, 23, 59, 59)  # Expires on October 17, 2025 at 11:59:59 PM
EXPIRATION_DATE = datetime(2025, 10, 19, 23, 59, 59)  # Expires on October 17, 2025 at 11:59:59 PM

# Set to None to disable expiration
# EXPIRATION_DATE = None
# ============================================

class ExpirationChecker:
    """Handles software expiration logic"""

    @staticmethod
    def check_expiration():
        """Check if software has expired. Returns (expired, message)"""

        # If no expiration date is set, return not expired
        if EXPIRATION_DATE is None:
            return False, "No expiration set"

        # Check if current date is past expiration date
        now = datetime.now()
        if now > EXPIRATION_DATE:
            days_expired = (now - EXPIRATION_DATE).days
            return True, f"This software expired on {EXPIRATION_DATE.strftime('%B %d, %Y')} ({days_expired} days ago)"
        else:
            days_remaining = (EXPIRATION_DATE - now).days
            hours_remaining = int((EXPIRATION_DATE - now).seconds / 3600)

            # Warn if expiring soon
            if days_remaining <= 3:
                logger.warning(f"Software will expire in {days_remaining} days and {hours_remaining} hours!")

            return False, f"Software expires on {EXPIRATION_DATE.strftime('%B %d, %Y at %I:%M %p')}"


class FacebookNumberChecker:
    def __init__(self, headless=False, wait_timeout=30):  # Reduced from 60 to 30 seconds
        # Check expiration before initializing
        expired, message = ExpirationChecker.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")

        logger.info(f"Expiration status: {message}")

        self.headless = headless
        self.wait_timeout = wait_timeout
        self.driver = None
        self.wait = None
        self.current_phone_number = None
        self.continuation = True
        self.reached_success = False  # Track if verification page was reached
        self.error_message = None  # Track specific error message

        # Bandwidth tracking for this instance
        self.bandwidth_stats = {
            'bytes_sent': 0,
            'bytes_received': 0,
            'requests_count': 0
        }

    def setup_driver(self):
        # Double-check expiration before setup
        expired, message = ExpirationChecker.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")

        options = Options()

        # Set headless mode properly
        if self.headless:
            options.add_argument('--headless=new')  # Use new headless mode for better performance

        # Performance optimizations
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        # Don't disable logging completely - we need performance logs
        # options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Set page load strategy to 'eager' - don't wait for all resources
        options.page_load_strategy = 'eager'

        # Disable images and other unnecessary resources via preferences
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # Disable images - major speedup
                'plugins': 2,
                'popups': 2,
                'geolocation': 2,
                'notifications': 2,
                'media_stream': 2,
            },
            'profile.managed_default_content_settings.images': 2
        }
        options.add_experimental_option('prefs', prefs)

        # Enable performance logging to capture network data
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        # Use lock to prevent concurrent driver initialization
        with _driver_init_lock:
            self.driver = webdriver.Chrome(options=options)

        # Enable Performance logging to track network activity
        self.driver.execute_cdp_cmd('Network.enable', {})

        # Reduced wait timeout and faster polling
        self.wait = WebDriverWait(self.driver, self.wait_timeout, poll_frequency=0.3)  # Poll every 0.3s instead of default 0.5s

        width = 1200
        height = int(width * 9 / 16)
        self.driver.set_window_size(width, height)

        logger.info(f"Browser initialized (headless={self.headless}) with size: {width}x{height}")

    def get_network_stats(self):
        """Retrieve network statistics from Chrome DevTools Protocol"""
        try:
            # Get performance metrics
            metrics = self.driver.execute_cdp_cmd('Performance.getMetrics', {})

            # Get network data from performance logs
            logs = self.driver.get_log('performance')

            bytes_sent = 0
            bytes_received = 0
            request_count = 0

            for entry in logs:
                try:
                    log_message = json.loads(entry['message'])
                    message = log_message.get('message', {})
                    method = message.get('method', '')

                    # Track response received events
                    if method == 'Network.responseReceived':
                        params = message.get('params', {})
                        response = params.get('response', {})

                        # Get encoded data length (compressed size) or use content length
                        encoded_length = response.get('encodedDataLength', 0)

                        if encoded_length > 0:
                            bytes_received += encoded_length
                            request_count += 1

                    # Track request will be sent events (for upload size)
                    elif method == 'Network.requestWillBeSent':
                        params = message.get('params', {})
                        request = params.get('request', {})

                        # Estimate request size from headers and post data
                        headers = request.get('headers', {})
                        post_data = request.get('postData', '')

                        # Rough estimate of request size
                        header_size = sum(len(str(k)) + len(str(v)) for k, v in headers.items())
                        post_data_size = len(post_data) if post_data else 0

                        bytes_sent += header_size + post_data_size

                except Exception as e:
                    # Skip problematic log entries
                    continue

            return {
                'bytes_sent': bytes_sent,
                'bytes_received': bytes_received,
                'requests_count': request_count
            }

        except Exception as e:
            logger.debug(f"Could not retrieve network stats: {e}")
            return {
                'bytes_sent': 0,
                'bytes_received': 0,
                'requests_count': 0
            }

    def update_bandwidth_stats(self):
        """Update bandwidth statistics for this checker instance"""
        stats = self.get_network_stats()
        self.bandwidth_stats['bytes_sent'] += stats['bytes_sent']
        self.bandwidth_stats['bytes_received'] += stats['bytes_received']
        self.bandwidth_stats['requests_count'] += stats['requests_count']

    @staticmethod
    def format_bytes(bytes_value):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"

    def wait_for_text_and_execute(self, text_actions_map):
        """
        Wait for one of multiple texts to appear and execute corresponding action.
        Checks all texts simultaneously by getting page source once per poll.
        text_actions_map: dict with text as key and action function as value
        """
        def check_all_texts(driver):
            # Get page source once per poll for efficiency
            try:
                page_source = driver.page_source
            except:
                return False

            # Check all texts against the same page source
            for text, action in text_actions_map.items():
                if text in page_source:
                    # Verify with actual element find to ensure it's visible/present
                    try:
                        element = driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
                        if element:
                            return (text, action)
                    except:
                        continue
            return False

        try:
            result = self.wait.until(check_all_texts)
            if result:
                text, action = result
                logger.info(f"Found text: '{text}'")
                action()
                return text
        except:
            pass

        return None

    def search_phone_number(self, phone_number):
        self.current_phone_number = phone_number
        self.driver.get("https://www.facebook.com/login/identify/")

        email_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "identify_email"))
        )

        email_input.clear()
        email_input.send_keys(phone_number)

        search_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "did_submit"))
        )
        search_button.click()
        logger.info(f"Searched for phone number: {phone_number}")

    def select_account(self):
        first_account_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'This is my account')]"))
        )
        first_account_link.click()
        logger.info("First account selected")

    def continue_send_code(self):
        phone_to_match = ''.join(filter(str.isdigit, self.current_phone_number))

        all_radios = self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//input[@type='radio' and @name='recover_method']"))
        )

        sms_radio_to_click = None
        for radio in all_radios:
            try:
                radio_id = radio.get_attribute('id')

                # Only process SMS options
                if not radio_id or not radio_id.startswith('send_sms:'):
                    continue

                # Find the label associated with this radio button
                label = self.driver.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                label_text = label.text

                # Check if it contains "Send code via SMS"
                if "Send code via SMS" not in label_text:
                    continue

                # Extract phone number from the label (it's in the second div)
                phone_in_label = ''.join(filter(str.isdigit, label_text))

                # Match the phone number - look for full match or partial match
                # The phone number appears after "Send code via SMS" text
                if phone_to_match == phone_in_label or phone_to_match in phone_in_label or phone_in_label in phone_to_match:
                    # Check if this is NOT a masked number (masked numbers have asterisks)
                    if '*' not in label_text or phone_to_match in label_text.replace('+', ''):
                        sms_radio_to_click = radio
                        break
            except Exception as e:
                logger.debug(f"Error processing radio button: {e}")
                continue

        if not sms_radio_to_click:
            # No SMS option found - set error and stop
            self.continuation = False
            self.error_message = "Can't find the 'Send code via SMS' option."
            logger.info("SMS verification option not available for this account")
            return

        if not sms_radio_to_click.is_selected():
            sms_radio_to_click.click()
            logger.info("SMS radio button clicked")

        continue_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@name='reset_action' and @type='submit' and contains(text(), 'Continue')]"))
        )
        continue_button.click()
        logger.info("SMS code option selected and Continue clicked")

    def continue_phone_number(self):
        pass

    def on_disabled(self):
        self.continuation = False
        self.error_message = "Account is disabled"
        logger.info("Account is disabled")

    def on_verification_send(self):
        self.continuation = False
        self.reached_success = True  # Set flag when verification code page is reached
        logger.info("Verification code input page reached")

    def no_search_results(self):
        self.continuation = False
        self.error_message = "Facebook account isn't found"
        logger.info("Facebook account isn't found")

    def on_robot_detected(self):
        self.continuation = False
        self.error_message = "Robot detected - CAPTCHA required"
        logger.info("Robot detected")

    def temporary_blocked(self):
        self.continuation = False
        self.error_message = "Temporarily blocked"
        logger.info("Temporarily blocked")

    def try_another_way(self):
        try:
            try_another_way_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[@name='tryanotherway' and contains(text(), 'Try another way')]"))
            )
            try_another_way_button.click()
            logger.info("Clicked 'Try another way' button")
        except Exception as e:
            logger.error(f"Error clicking 'Try another way' button: {e}")
            # Try alternative selector
            try:
                try_another_way_button = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "tryanotherway"))
                )
                try_another_way_button.click()
                logger.info("Clicked 'Try another way' button using alternative selector")
            except Exception as e2:
                logger.error(f"Failed with alternative selector too: {e2}")
                raise

    def reload_page(self):
        self.driver.refresh()

    def direct_code_send(self):
        """Handle the case where Facebook directly offers to send a code to the phone number"""
        try:
            # Click the Continue button to send the verification code
            continue_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(), 'Continue')]"))
            )
            continue_button.click()
            logger.info("Clicked Continue button to send verification code directly")
        except Exception as e:
            logger.error(f"Error clicking Continue button: {e}")
            # Try alternative selector
            try:
                continue_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                continue_button.click()
                logger.info("Clicked Continue button using alternative selector")
            except Exception as e2:
                logger.error(f"Failed with alternative selector too: {e2}")
                raise

    def allow_cookie(self):
        try:
            # Wait for and click the "Allow all cookies" button
            allow_cookie_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Allow all cookies' and @role='button']"))
            )
            allow_cookie_button.click()
            logger.info("Allow all cookies button clicked")
        except Exception as e:
            logger.error(f"Failed to click allow cookies button: {e}")
            raise



    def handle_continuation(self):
        try:
            text_actions = {
                "These accounts matched your search": self.select_account,
                "How do you want to receive the code to reset your password?": self.continue_send_code,
                "How do you want to get the code to reset your password?": self.continue_send_code,
                "Before we send the code, enter these letters and numbers": self.on_robot_detected,
                "Enter security code": self.on_verification_send,
                "Account disabled": self.on_disabled,
                "No search results": self.no_search_results,
                "Log in as": self.try_another_way,
                "Log in to": self.try_another_way,
                "Reload page": self.reload_page,
                "We can send a login code to:": self.direct_code_send,
                "You’re Temporarily Blocked": self.temporary_blocked,
                "Allow the use of cookies from Facebook on this browser?": self.allow_cookie,
            }

            while self.continuation:
                found_text = self.wait_for_text_and_execute(text_actions)

                if not found_text:
                    logger.warning("No expected text found")
                    break

                # Strict mode: remove the executed text action from the map
                if found_text in text_actions:
                    del text_actions[found_text]

                # If all actions are exhausted, break
                if not text_actions:
                    break

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise


    def page_preview(self):
        screenshot_bytes = self.driver.get_screenshot_as_png()
        image = Image.open(BytesIO(screenshot_bytes))
        image.show()
        logger.info("Screenshot preview opened")

    def close(self):
        if self.driver:
            # Get final bandwidth statistics before closing
            self.update_bandwidth_stats()

            # Log per-session bandwidth usage
            total_bandwidth = self.bandwidth_stats['bytes_sent'] + self.bandwidth_stats['bytes_received']
            logger.info(f"Bandwidth for this check: Sent={self.format_bytes(self.bandwidth_stats['bytes_sent'])}, "
                       f"Received={self.format_bytes(self.bandwidth_stats['bytes_received'])}, "
                       f"Total={self.format_bytes(total_bandwidth)}, "
                       f"Requests={self.bandwidth_stats['requests_count']}")

            # Update global bandwidth statistics
            with _total_bandwidth_lock:
                _global_bandwidth_stats['total_sent'] += self.bandwidth_stats['bytes_sent']
                _global_bandwidth_stats['total_received'] += self.bandwidth_stats['bytes_received']
                _global_bandwidth_stats['total_requests'] += self.bandwidth_stats['requests_count']

            self.driver.quit()
            logger.info("Browser closed")

    def check_number(self, phone_number):
        """
        Check a single phone number and return the result
        """
        try:
            self.search_phone_number(phone_number)
            self.handle_continuation()

            # Check if verification page was reached successfully
            if self.reached_success:
                return {
                    'phone': phone_number,
                    'status': 'success',
                    'message': 'Verification code page reached'
                }
            # If we have a specific error message, return it
            elif self.error_message:
                return {
                    'phone': phone_number,
                    'status': 'failed',
                    'message': self.error_message
                }
            # Otherwise, return unknown error
            else:
                return {
                    'phone': phone_number,
                    'status': 'failed',
                    'message': 'Unknown error - didn\'t reach verification page'
                }
        except Exception as e:
            logger.error(f"Error checking {phone_number}: {e}")
            return {
                'phone': phone_number,
                'status': 'error',
                'message': str(e)
            }


def check_single_number(phone_number):
    """
    Worker function to check a single phone number
    """
    checker = FacebookNumberChecker(headless=False)
    try:
        checker.setup_driver()
        result = checker.check_number(phone_number)
        logger.info(f"Completed check for {phone_number}: {result['status']}")
        return result
    except Exception as e:
        logger.error(f"Worker error for {phone_number}: {e}")
        return {
            'phone': phone_number,
            'status': 'error',
            'message': str(e)
        }
    finally:
        checker.close()


if __name__ == "__main__":
    #
    # nums = [
    #     "2250708139166", "2250708135432", "2250708136329", "2250708137946", "2250708130149", "2250708132325",
    #     "2250708134921", "2250708131254", "2250708135326", "2250708136921", "2250708138627", "2250708136804",
    #     "2250708133468", "2250708130814", "2250708132680", "2250708131009", "2250708136508", "2250708135640",
    #     "2250708136254", "2250708137888", "2250708130404", "2250708132032", "2250708135700", "2250708136514",
    #     "2250708133330", "2250708137507", "2250708131688", "2250708132191", "2250708134184", "2250708135392",
    #     "2250708135811", "2250708131936", "2250708138942", "2250708130543", "2250708134441", "2250708139822",
    #     "2250708133494", "2250708131958", "2250708130684", "2250708136616", "2250708130337", "2250708131019",
    #     "2250708130369", "2250708137183", "2250708130469", "2250708134024", "2250708133098", "2250708135786",
    #     "2250708131322", "2250708138204", "2250708139499", "2250708138352", "2250708134979", "2250708139512",
    #     "2250708132538", "2250708136979", "2250708136863", "2250708136665", "2250708131689", "2250708138575",
    #     "2250708134924", "2250708130984", "2250708138875", "2250708131727", "2250708136283", "2250708132332",
    #     "2250708132646", "2250708135113", "2250708139954", "2250708132201", "2250708136558", "2250708134414",
    #     "2250708131519", "2250708135538", "2250708130197", "2250708131851", "2250708133530", "2250708130279",
    #     "2250708132252", "2250708135809", "2250708138185", "2250708138513", "2250708139799", "2250708130520",
    #     "2250708138986", "2250708133287", "2250708134147", "2250708131345", "2250708131565", "2250708132120",
    #     "2250708131610", "2250708132501", "2250708139948", "2250708138734", "2250708136500", "2250708130826",
    #     "2250708138855", "2250708139632", "2250708136711", "2250708136905"
    # ]

    nums = [
        "2250708139166"
    ]

    results = []

    logger.info(f"Starting to check {len(nums)} phone numbers with 5 concurrent workers")

    with ThreadPoolExecutor(max_workers=1) as executor:
        # Submit all tasks
        future_to_phone = {executor.submit(check_single_number, phone): phone for phone in nums}

        # Process completed tasks as they finish
        for future in as_completed(future_to_phone):
            phone = future_to_phone[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Progress: {len(results)}/{len(nums)} completed")
            except Exception as e:
                logger.error(f"Exception for {phone}: {e}")
                results.append({
                    'phone': phone,
                    'status': 'error',
                    'message': str(e)
                })

    # Print summary
    logger.info("=" * 50)
    logger.info("FINAL RESULTS:")
    logger.info("=" * 50)

    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')

    logger.info(f"Total checked: {len(results)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Errors: {error_count}")

    logger.info("\nDetailed results:")
    for result in results:
        logger.info(f"{result['phone']}: {result['status']} - {result['message']}")

    # Print total bandwidth usage
    logger.info("=" * 50)
    logger.info("TOTAL BANDWIDTH USAGE:")
    logger.info("=" * 50)
    total_sent = _global_bandwidth_stats['total_sent']
    total_received = _global_bandwidth_stats['total_received']
    total_bandwidth = total_sent + total_received
    total_requests = _global_bandwidth_stats['total_requests']

    logger.info(f"Total Sent: {FacebookNumberChecker.format_bytes(total_sent)}")
    logger.info(f"Total Received: {FacebookNumberChecker.format_bytes(total_received)}")
    logger.info(f"Total Bandwidth: {FacebookNumberChecker.format_bytes(total_bandwidth)}")
    logger.info(f"Total Requests: {total_requests}")

    if len(results) > 0:
        avg_bandwidth_per_check = total_bandwidth / len(results)
        logger.info(f"Average Bandwidth per Check: {FacebookNumberChecker.format_bytes(avg_bandwidth_per_check)}")

    logger.info("=" * 50)
