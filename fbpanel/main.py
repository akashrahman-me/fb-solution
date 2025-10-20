import time
import os
import tempfile
import queue
import threading
from datetime import datetime
from io import BytesIO

from playwright.sync_api import sync_playwright
import logging
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global bandwidth tracking
_total_bandwidth_lock = threading.Lock()
_global_bandwidth_stats = {'total_sent': 0, 'total_received': 0, 'total_requests': 0}

# Global cache directory
_cache_dir = os.path.join(tempfile.gettempdir(), 'fb_checker_cache')
os.makedirs(_cache_dir, exist_ok=True)

# Expiration configuration
EXPIRATION_DATE = datetime(2025, 10, 21, 23, 59, 59)

class ExpirationChecker:
    """Handles software expiration logic"""
    _warning_shown = False

    @staticmethod
    def check_expiration():
        """Check if software has expired. Returns (expired, message)"""
        if EXPIRATION_DATE is None:
            return False, "No expiration set"

        now = datetime.now()
        if now > EXPIRATION_DATE:
            days_expired = (now - EXPIRATION_DATE).days
            return True, f"This software expired on {EXPIRATION_DATE.strftime('%B %d, %Y')} ({days_expired} days ago)"

        days_remaining = (EXPIRATION_DATE - now).days
        hours_remaining = int((EXPIRATION_DATE - now).seconds / 3600)

        if days_remaining <= 3 and not ExpirationChecker._warning_shown:
            logger.warning(f"Software will expire in {days_remaining} days and {hours_remaining} hours!")
            ExpirationChecker._warning_shown = True

        return False, f"Software expires on {EXPIRATION_DATE.strftime('%B %d, %Y at %I:%M %p')}"


class FacebookNumberChecker:
    def __init__(self, headless=False, wait_timeout=20):
        expired, message = ExpirationChecker.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")

        self.headless = headless
        self.wait_timeout = wait_timeout * 1000
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        self.current_phone_number = None
        self.continuation = True
        self.reached_success = False
        self.error_message = None
        self.network_requests = []
        self.cdp_session = None

        logger.info("Session initialized")

    def setup_driver(self):
        expired, message = ExpirationChecker.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--log-level=3',
                '--silent',
            ]
        )
        #
        proxy_config = {
            "server": "http://127.0.0.1:8080"
        }

        # Create a context with proxy enabled for proper caching and proxy support
        self.context = self.browser.new_context(
            proxy = proxy_config
        )
        self.page = self.context.new_page()

        # Use CDP to accurately track network bandwidth
        self.cdp_session = self.context.new_cdp_session(self.page)
        self.cdp_session.send('Network.enable')

        # Listen to CDP Network events for accurate tracking
        self.cdp_session.on('Network.responseReceived', self._on_cdp_response)
        self.cdp_session.on('Network.loadingFinished', self._on_cdp_loading_finished)

        # Store request IDs and their info
        self.pending_requests = {}

        self.page.set_default_timeout(self.wait_timeout)

        logger.info(f"Browser initialized (headless={self.headless}) with proxy")

    def _on_cdp_response(self, params):
        """Handle CDP Network.responseReceived event"""
        try:
            request_id = params.get('requestId')
            response = params.get('response', {})

            # Check if response was served from cache
            from_disk_cache = response.get('fromDiskCache', False)
            from_service_worker = response.get('fromServiceWorker', False)
            from_prefetch_cache = response.get('fromPrefetchCache', False)

            # Skip cached resources
            if from_disk_cache or from_service_worker or from_prefetch_cache:
                return

            # Store info for this request
            self.pending_requests[request_id] = {
                'url': response.get('url', ''),
                'status': response.get('status', 0),
                'headers': response.get('headers', {}),
                'encoded_data_length': 0
            }
        except:
            pass

    def _on_cdp_loading_finished(self, params):
        """Handle CDP Network.loadingFinished event"""
        try:
            request_id = params.get('requestId')
            encoded_data_length = params.get('encodedDataLength', 0)

            if request_id in self.pending_requests:
                request_info = self.pending_requests[request_id]

                # Skip data URLs
                url = request_info['url']
                if url.startswith('data:') or url.startswith('blob:'):
                    del self.pending_requests[request_id]
                    return

                # Calculate actual bandwidth
                # encodedDataLength includes headers + body as received over network
                if encoded_data_length > 0:
                    self.network_requests.append({
                        'bytes_sent': 0,  # Request size is minimal (headers only)
                        'bytes_received': encoded_data_length,
                        'url': url,
                        'status': request_info['status']
                    })

                # Clean up
                del self.pending_requests[request_id]
        except:
            pass

    def get_network_stats(self):
        """Retrieve network statistics"""
        return {
            'bytes_sent': sum(req['bytes_sent'] for req in self.network_requests),
            'bytes_received': sum(req['bytes_received'] for req in self.network_requests),
            'requests_count': len(self.network_requests)
        }

    @staticmethod
    def format_bytes(bytes_value):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"

    def _click_element(self, selector, description, use_alt=False):
        """Helper to click element with fallback"""
        try:
            element = self.page.locator(selector).first
            element.wait_for(state="visible", timeout=self.wait_timeout)
            element.click()
            logger.info(f"Clicked {description}")
        except Exception as e:
            if use_alt:
                raise
            logger.error(f"Error clicking {description}: {e}")

    def _stop_with_error(self, error_msg):
        """Helper to stop continuation with error message"""
        self.continuation = False
        self.error_message = error_msg
        logger.info(error_msg)

    def wait_for_text_and_execute(self, text_actions_map):
        """Wait for text to appear and execute corresponding action"""
        poll_frequency = 0.3
        max_time = self.wait_timeout / 1000
        start_time = time.time()

        while time.time() - start_time < max_time:
            try:
                page_source = self.page.content()
                for text, action in text_actions_map.items():
                    if text in page_source:
                        element = self.page.locator(f"//*[contains(text(), '{text}')]").first
                        if element.count() > 0:
                            logger.info(f"Found text: '{text}'")
                            action()
                            return text
                time.sleep(poll_frequency)
            except:
                time.sleep(poll_frequency)
        return None

    def search_phone_number(self, phone_number):
        self.current_phone_number = phone_number
        self.page.goto("https://www.facebook.com/login/identify/")

    def select_account(self):
        self._click_element("//a[contains(text(), 'This is my account')]", "first account")

    def continue_send_code(self):
        phone_to_match = ''.join(filter(str.isdigit, self.current_phone_number))
        all_radios = self.page.locator("//input[@type='radio' and @name='recover_method']").all()

        sms_radio = None
        for radio in all_radios:
            try:
                radio_id = radio.get_attribute('id')
                if not radio_id or not radio_id.startswith('send_sms:'):
                    continue

                label = self.page.locator(f"//label[@for='{radio_id}']").first
                label_text = label.text_content()

                if "Send code via SMS" not in label_text:
                    continue

                phone_in_label = ''.join(filter(str.isdigit, label_text))
                if (phone_to_match == phone_in_label or phone_to_match in phone_in_label or
                    phone_in_label in phone_to_match):
                    if '*' not in label_text or phone_to_match in label_text.replace('+', ''):
                        sms_radio = radio
                        break
            except Exception as e:
                logger.debug(f"Error processing radio button: {e}")

        if not sms_radio:
            self._stop_with_error("Can't find the 'Send code via SMS' option.")
            return

        if not sms_radio.is_checked():
            sms_radio.click()
            logger.info("SMS radio button clicked")

        self._click_element("//button[@name='reset_action' and @type='submit' and contains(text(), 'Continue')]",
                           "Continue button")

    def on_disabled(self):
        self._stop_with_error("Account is disabled")

    def on_verification_send(self):
        self.continuation = False
        self.reached_success = True
        logger.info("Verification code input page reached")

    def no_search_results(self):
        self._stop_with_error("Facebook account isn't found")

    def on_robot_detected(self):
        self._stop_with_error("Robot detected - CAPTCHA required")

    def temporary_blocked(self):
        self._stop_with_error("You're Temporarily Blocked")

    def try_another_way(self):
        try:
            self._click_element("//a[@name='tryanotherway' and contains(text(), 'Try another way')]",
                               "Try another way")
        except:
            try:
                self._click_element("[name='tryanotherway']", "Try another way (alt)", use_alt=True)
            except Exception as e:
                logger.error(f"Failed to click 'Try another way': {e}")
                raise

    def reload_page(self):
        self.page.reload()

    def direct_code_send(self):
        """Handle direct code send option"""
        try:
            self._click_element("//button[@type='submit' and contains(text(), 'Continue')]", "Continue")
        except:
            try:
                self._click_element("//button[@type='submit']", "Continue (alt)", use_alt=True)
            except Exception as e:
                logger.error(f"Failed to click Continue: {e}")
                raise

    def click_clickable_parent(self, element):
        """Recursively find and click clickable parent"""
        try:
            if element.is_visible() and element.is_enabled():
                element.click()
                return True
            parent = element.locator("xpath=..").first
            if parent.evaluate("el => el.tagName").lower() == "html":
                return False
            return self.click_clickable_parent(parent)
        except:
            return False

    def allow_cookie(self):
        try:
            cookie_element = self.page.locator("//*[contains(text(), 'Allow all cookies')]").first
            if cookie_element.count() > 0:
                self.click_clickable_parent(cookie_element)
        except:
            logger.debug("No cookie popup found")

    def find_account(self):
        email_input = self.page.locator("#identify_email").first
        email_input.wait_for(state="visible", timeout=self.wait_timeout)
        email_input.clear()
        email_input.type(self.current_phone_number)
        self._click_element("#did_submit", "search button")
        logger.info(f"Searched for phone number: {self.current_phone_number}")

    def try_another_device(self):
        self._stop_with_error("Try another device to continue")

    def _save_debug_info(self):
        """Save screenshot and HTML for debugging"""
        if self.current_phone_number:
            self.page.screenshot(path=f"photo/{self.current_phone_number}.png")
            os.makedirs("html", exist_ok=True)
            with open(f"html/{self.current_phone_number}.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())

    def handle_continuation(self):
        """Main flow handler"""
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
            "Try another device to continue": self.try_another_device,
        }

        try:
            while self.continuation:
                found_text = self.wait_for_text_and_execute(text_actions)

                if not found_text:
                    logger.warning("No expected text found")
                    self._save_debug_info()
                    break

                if found_text in text_actions:
                    del text_actions[found_text]

                if not text_actions:
                    break
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

    def page_preview(self):
        """Show screenshot preview"""
        screenshot_bytes = self.page.screenshot()
        Image.open(BytesIO(screenshot_bytes)).show()
        logger.info("Screenshot preview opened")

    def _log_bandwidth(self, stats):
        """Log bandwidth usage"""
        total = stats['bytes_sent'] + stats['bytes_received']
        logger.info(f"Bandwidth: Sent={self.format_bytes(stats['bytes_sent'])}, "
                   f"Received={self.format_bytes(stats['bytes_received'])}, "
                   f"Total={self.format_bytes(total)}, Requests={stats['requests_count']}")

    def _update_global_bandwidth(self, stats):
        """Update global bandwidth statistics"""
        with _total_bandwidth_lock:
            _global_bandwidth_stats['total_sent'] += stats['bytes_sent']
            _global_bandwidth_stats['total_received'] += stats['bytes_received']
            _global_bandwidth_stats['total_requests'] += stats['requests_count']

    def close(self):
        """Clean up resources"""
        if self.page:
            stats = self.get_network_stats()
            self._log_bandwidth(stats)
            self._update_global_bandwidth(stats)

            input("Enter to close")

            self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed")

    def check_number(self, phone_number):
        """Check a single phone number"""
        self.current_phone_number = phone_number
        try:
            self.search_phone_number(phone_number)
            self.handle_continuation()

            if self.reached_success:
                return {'phone': phone_number, 'status': 'success', 'message': 'Verification code page reached'}
            elif self.error_message:
                return {'phone': phone_number, 'status': 'failed', 'message': self.error_message}
            else:
                return {'phone': phone_number, 'status': 'failed', 'message': 'Unknown error - didn\'t reach verification page'}
        except Exception as e:
            logger.error(f"Error checking {phone_number}: {e}")
            return {'phone': phone_number, 'status': 'error', 'message': str(e)}


def check_single_number(phone_number):
    """Worker function to check a single phone number"""
    checker = FacebookNumberChecker(headless=False)
    try:
        checker.setup_driver()
        result = checker.check_number(phone_number)
        logger.info(f"Completed check for {phone_number}: {result['status']}")
        return result
    except Exception as e:
        logger.error(f"Worker error for {phone_number}: {e}")
        return {'phone': phone_number, 'status': 'error', 'message': str(e)}
    finally:
        checker.close()


def string_to_number_array(data_str):
    """Convert multi-line string of numbers to list"""
    return [num.strip() for num in data_str.split('\n') if num.strip()]


def worker_process_numbers(worker_id, phone_queue, results_list, results_lock):
    """Worker that processes multiple phone numbers with one browser instance"""
    checker = FacebookNumberChecker(headless=False)
    phones_processed = 0

    try:
        checker.setup_driver()
        logger.info(f"Worker {worker_id} browser ready")

        while True:
            try:
                phone_number = phone_queue.get(timeout=1)

                # Reset state
                checker.continuation = True
                checker.reached_success = False
                checker.error_message = None
                checker.network_requests = []

                logger.info(f"Worker {worker_id} checking: {phone_number}")
                result = checker.check_number(phone_number)
                phones_processed += 1

                # Log and update bandwidth
                stats = checker.get_network_stats()
                checker._log_bandwidth(stats)
                checker._update_global_bandwidth(stats)

                # Store result
                with results_lock:
                    results_list.append(result)
                    logger.info(f"Progress: {len(results_list)}/{phone_queue.qsize() + len(results_list)} completed")

                phone_queue.task_done()

            except queue.Empty:
                logger.info(f"Worker {worker_id} finished - processed {phones_processed} numbers")
                break

    except Exception as e:
        logger.error(f"Worker {worker_id} error: {e}")
    finally:
        input("Enter to finally close")
        if checker.page:
            checker.page.close()
        if checker.browser:
            checker.browser.close()
        if checker.playwright:
            checker.playwright.stop()
        logger.info(f"Worker {worker_id} browser closed")


def print_summary(results):
    """Print final summary of results"""
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


def print_bandwidth_summary(num_results):
    """Print total bandwidth usage"""
    logger.info("=" * 50)
    logger.info("TOTAL BANDWIDTH USAGE:")
    logger.info("=" * 50)

    total_sent = _global_bandwidth_stats['total_sent']
    total_received = _global_bandwidth_stats['total_received']
    total_bandwidth = total_sent + total_received

    logger.info(f"Total Sent: {FacebookNumberChecker.format_bytes(total_sent)}")
    logger.info(f"Total Received: {FacebookNumberChecker.format_bytes(total_received)}")
    logger.info(f"Total Bandwidth: {FacebookNumberChecker.format_bytes(total_bandwidth)}")
    logger.info(f"Total Requests: {_global_bandwidth_stats['total_requests']}")

    if num_results > 0:
        avg = total_bandwidth / num_results
        logger.info(f"Average Bandwidth per Check: {FacebookNumberChecker.format_bytes(avg)}")

    logger.info("=" * 50)


if __name__ == "__main__":
    nums_str = """
2250779359702
2250779356403
2250779354097
2250779355845
2250779354549
2250779352567
2250779350481
2250779357023
2250779354188
2250779355447
    """

    nums = string_to_number_array(nums_str)
    phone_queue = queue.Queue()
    for num in nums:
        phone_queue.put(num)

    results = []
    results_lock = threading.Lock()
    num_workers = 1

    logger.info(f"Starting to check {len(nums)} phone numbers with {num_workers} concurrent workers")

    # Create and start workers
    workers = [
        threading.Thread(target=worker_process_numbers, args=(i, phone_queue, results, results_lock))
        for i in range(num_workers)
    ]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    print_summary(results)
    print_bandwidth_summary(len(results))
