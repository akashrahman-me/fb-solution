import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
    def __init__(self, headless=False, wait_timeout=120):
        # Check expiration before initializing
        expired, message = ExpirationChecker.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")

        logger.info(f"Expiration status: {message}")

        self.headless = headless
        self.wait_timeout = wait_timeout * 1000  # Convert to milliseconds for Playwright
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
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
        self.network_requests = []

        logger.info(f"Session initialized")

    def setup_driver(self):
        # Double-check expiration before setup
        expired, message = ExpirationChecker.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")

        # Initialize Playwright
        self.playwright = sync_playwright().start()

        # Launch browser with optimizations
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-popup-blocking',
                '--disable-notifications',
                '--disable-infobars',
                '--log-level=3',
                '--silent',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )

        # Configure  proxy
        proxy_config = {
            'server': 'http://142.111.48.253:7030',
            'username': 'rqsgbzmp',
            'password': 'yag0ewjl9tws'
        }

        # Create context with proxy
        self.context = self.browser.new_context(
            proxy=proxy_config,
        )

        # Block images, media, and JavaScript files for bandwidth optimization
        self.context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "media"]
            else route.continue_()
        ))

        # Track network requests for bandwidth monitoring
        def handle_response(response):
            try:
                request = response.request
                headers = response.headers

                # Estimate sizes
                response_size = int(headers.get('content-length', 0)) if 'content-length' in headers else 0
                request_headers_size = sum(len(str(k)) + len(str(v)) for k, v in request.headers.items())

                self.network_requests.append({
                    'bytes_sent': request_headers_size,
                    'bytes_received': response_size,
                })
            except:
                pass

        self.page = self.context.new_page()

        # Set default timeout
        self.page.set_default_timeout(self.wait_timeout)

        logger.info(f"Browser initialized (headless={self.headless})")

    def get_network_stats(self):
        """Retrieve network statistics from tracked requests"""
        try:
            bytes_sent = sum(req['bytes_sent'] for req in self.network_requests)
            bytes_received = sum(req['bytes_received'] for req in self.network_requests)
            request_count = len(self.network_requests)

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
        poll_frequency = 0.3  # Poll every 0.3 seconds (same as Selenium implementation)
        max_time = self.wait_timeout / 1000  # Convert milliseconds to seconds
        start_time = time.time()

        while time.time() - start_time < max_time:
            try:
                # Get page content
                page_source = self.page.content()

                # Check all texts against the page source
                for text, action in text_actions_map.items():
                    if text in page_source:
                        # Verify with actual element find to ensure it's visible/present
                        try:
                            element = self.page.locator(f"//*[contains(text(), '{text}')]").first
                            if element.count() > 0:
                                logger.info(f"Found text: '{text}'")
                                action()
                                return text
                        except:
                            continue

                # Wait before next poll
                time.sleep(poll_frequency)

            except:
                # Wait before retry on error
                time.sleep(poll_frequency)
                continue

        # Timeout reached - no text found
        return None

    def search_phone_number(self, phone_number):
        self.current_phone_number = phone_number
        self.page.goto("https://www.facebook.com/login/identify/")

    def select_account(self):
        first_account_link = self.page.locator("//a[contains(text(), 'This is my account')]").first
        first_account_link.wait_for(state="visible", timeout=self.wait_timeout)
        first_account_link.click()
        logger.info("First account selected")

    def continue_send_code(self):
        phone_to_match = ''.join(filter(str.isdigit, self.current_phone_number))

        all_radios = self.page.locator("//input[@type='radio' and @name='recover_method']").all()

        sms_radio_to_click = None
        for radio in all_radios:
            try:
                radio_id = radio.get_attribute('id')

                # Only process SMS options
                if not radio_id or not radio_id.startswith('send_sms:'):
                    continue

                # Find the label associated with this radio button
                label = self.page.locator(f"//label[@for='{radio_id}']").first
                label_text = label.text_content()

                # Check if it contains "Send code via SMS"
                if "Send code via SMS" not in label_text:
                    continue

                # Extract phone number from the label (it's in the second div)
                phone_in_label = ''.join(filter(str.isdigit, label_text))

                # Match the phone number - look for full match or partial match
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

        if not sms_radio_to_click.is_checked():
            sms_radio_to_click.click()
            logger.info("SMS radio button clicked")

        continue_button = self.page.locator("//button[@name='reset_action' and @type='submit' and contains(text(), 'Continue')]").first
        continue_button.wait_for(state="visible", timeout=self.wait_timeout)
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
        self.error_message = "You’re Temporarily Blocked"
        logger.info("You’re Temporarily Blocked")

    def try_another_way(self):
        try:
            try_another_way_button = self.page.locator("//a[@name='tryanotherway' and contains(text(), 'Try another way')]").first
            try_another_way_button.wait_for(state="visible", timeout=self.wait_timeout)
            try_another_way_button.click()
            logger.info("Clicked 'Try another way' button")
        except Exception as e:
            logger.error(f"Error clicking 'Try another way' button: {e}")
            # Try alternative selector
            try:
                try_another_way_button = self.page.locator("[name='tryanotherway']").first
                try_another_way_button.wait_for(state="visible", timeout=self.wait_timeout)
                try_another_way_button.click()
                logger.info("Clicked 'Try another way' button using alternative selector")
            except Exception as e2:
                logger.error(f"Failed with alternative selector too: {e2}")
                raise

    def reload_page(self):
        self.page.reload()

    def direct_code_send(self):
        """Handle the case where Facebook directly offers to send a code to the phone number"""
        try:
            # Click the Continue button to send the verification code
            continue_button = self.page.locator("//button[@type='submit' and contains(text(), 'Continue')]").first
            continue_button.wait_for(state="visible", timeout=self.wait_timeout)
            continue_button.click()
            logger.info("Clicked Continue button to send verification code directly")
        except Exception as e:
            logger.error(f"Error clicking Continue button: {e}")
            # Try alternative selector
            try:
                continue_button = self.page.locator("//button[@type='submit']").first
                continue_button.wait_for(state="visible", timeout=self.wait_timeout)
                continue_button.click()
                logger.info("Clicked Continue button using alternative selector")
            except Exception as e2:
                logger.error(f"Failed with alternative selector too: {e2}")
                raise

    def click_clickable_parent(self, element):
        """Tries to click the element; if not clickable, moves up until a clickable parent is found."""
        try:
            if element.is_visible() and element.is_enabled():
                element.click()
                return True
            else:
                parent = element.locator("xpath=..").first
                parent_tag = parent.evaluate("el => el.tagName").lower()
                if parent_tag == "html":
                    return False
                return self.click_clickable_parent(parent)
        except:
            return False

    def allow_cookie(self):
        try:
            allow_cookie = self.page.locator(f"//*[contains(text(), 'Allow all cookies')]").first
            if allow_cookie.count() > 0:
                self.click_clickable_parent(allow_cookie)
        except:
            print("⚠️ No cookie popup found or 'Allow all cookies' not present.")

    def find_account(self):
        email_input = self.page.locator("#identify_email").first
        email_input.wait_for(state="visible", timeout=self.wait_timeout)
        email_input.clear()
        email_input.type(self.current_phone_number)

        search_button = self.page.locator("#did_submit").first
        search_button.wait_for(state="visible", timeout=self.wait_timeout)
        search_button.click()
        logger.info(f"Searched for phone number: {self.current_phone_number}")

    def handle_continuation(self):
        try:
            text_actions = {
                "Allow the use of cookies from Facebook on this browser?": self.allow_cookie,
                "Find Your Account": self.find_account,
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
                "You're Temporarily Blocked": self.temporary_blocked,
                "You’re Temporarily Blocked": self.temporary_blocked,
            }

            while self.continuation:
                found_text = self.wait_for_text_and_execute(text_actions)

                if not found_text:
                    logger.warning("No expected text found")
                    if self.current_phone_number:
                        self.page.screenshot(path=f"photo/{self.current_phone_number}.png")
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
        screenshot_bytes = self.page.screenshot()
        image = Image.open(BytesIO(screenshot_bytes))
        image.show()
        logger.info("Screenshot preview opened")

    def close(self):
        if self.page:
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

            # Close browser resources
            self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed")

    def check_number(self, phone_number):
        """
        Check a single phone number and return the result
        """
        self.current_phone_number = phone_number
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

def string_to_number_array(data_str):
    """
    Converts a multi-line string of numbers into a list of integers.

    :param data_str: The input string where each number is on a new line.
    :return: A list of integers.
    """
    # Split the string by newline, filter out any empty strings,
    # and convert the remaining non-empty strings to integers.
    number_array = [num_str.strip() for num_str in data_str.split('\n') if num_str.strip()]
    return number_array


if __name__ == "__main__":
    nums_str = """
    2250720090666
    2250720093506
    2250720091783
    2250720093644
    2250720091803
    2250720093238
    2250720092529
    2250720097722
    2250720091417
    2250720096645
    2250720097932
    2250720092604
    2250720096754
    2250720099074
    2250720092741
    2250720097048
    2250720093780
    2250720096837
    2250720095658
    2250720094631
    2250720092380
    2250720096050
    2250720091012
    2250720097381
    2250720095957
    2250720096373
    2250720090591
    2250720094143
    2250720099690
    2250720095090
    2250720098872
    2250720098676
    2250720099898
    2250720097371
    2250720097114
    2250720091786
    2250720093991
    2250720093137
    2250720090985
    2250720092022
    2250720096221
    2250720095219
    2250720093273
    2250720091574
    2250720097361
    2250720092607
    2250720093871
    2250720092882
    2250720099569
    2250720092267
    2250720093954
    2250720090050
    2250720093578
    2250720095482
    2250720095184
    2250720092433
    2250720096967
    2250720095491
    2250720091289
    2250720098348
    2250720096947
    2250720093786
    2250720090628
    2250720091913
    2250720097703
    2250720091189
    2250720098197
    2250720096909
    2250720094050
    2250720092640
    2250720096641
    2250720094115
    2250720092910
    2250720099068
    2250720091922
    2250720096081
    2250720091582
    2250720091493
    2250720092266
    2250720097767
    2250720096966
    2250720092577
    2250720091770
    2250720095950
    2250720096246
    2250720091518
    2250720092589
    2250720093916
    2250720094090
    2250720098137
    2250720091884
    2250720097621
    2250720097790
    2250720096472
    2250720095730
    2250720093750
    2250720097035
    2250720095035
    2250720095937
    2250720097304
    """

    nums = string_to_number_array(nums_str)

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
