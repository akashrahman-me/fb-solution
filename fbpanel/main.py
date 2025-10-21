import time
import os
import tempfile
import queue
import threading
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
import logging
from PIL import Image

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Central configuration for the application"""
    EXPIRATION_DATE = datetime(2025, 10, 21, 23, 59, 59)
    CACHE_DIR = os.path.join(tempfile.gettempdir(), 'fb_checker_cache')
    PROXY_SERVER = "http://127.0.0.1:8080"
    DEFAULT_TIMEOUT = 20  # seconds
    POLL_FREQUENCY = 0.3  # seconds
    PROFILES_DIR = "profiles"  # Directory to store browser profiles

    # Browser arguments
    BROWSER_ARGS = [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-gpu',
        '--log-level=3',
        '--silent',
    ]

    # Facebook URLs
    FB_LOGIN_IDENTIFY_URL = "https://www.facebook.com/login/identify/"

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
        os.makedirs("photo", exist_ok=True)
        os.makedirs("html", exist_ok=True)
        os.makedirs(cls.PROFILES_DIR, exist_ok=True)

    @classmethod
    def get_profile_path(cls, worker_id: int) -> str:
        """Get the profile path for a specific worker"""
        profile_path = os.path.join(cls.PROFILES_DIR, str(worker_id))
        os.makedirs(profile_path, exist_ok=True)
        return profile_path


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CheckResult:
    """Result of a phone number check"""
    phone: str
    status: str  # 'success', 'failed', 'error'
    message: str

    def __str__(self) -> str:
        return f"{self.phone}: {self.status} - {self.message}"


# ============================================================================
# EXPIRATION MANAGEMENT
# ============================================================================

class ExpirationManager:
    """Handles software expiration logic"""
    _warning_shown = False
    _warning_lock = threading.Lock()

    @classmethod
    def check_expiration(cls) -> tuple[bool, str]:
        """
        Check if software has expired.

        Returns:
            tuple: (expired: bool, message: str)
        """
        if Config.EXPIRATION_DATE is None:
            return False, "No expiration set"

        now = datetime.now()

        # Check if expired
        if now > Config.EXPIRATION_DATE:
            days_expired = (now - Config.EXPIRATION_DATE).days
            message = f"This software expired on {Config.EXPIRATION_DATE.strftime('%B %d, %Y')} ({days_expired} days ago)"
            return True, message

        # Calculate remaining time
        days_remaining = (Config.EXPIRATION_DATE - now).days
        hours_remaining = int((Config.EXPIRATION_DATE - now).seconds / 3600)

        # Show warning if expiring soon
        if days_remaining <= 3 and not cls._warning_shown:
            with cls._warning_lock:
                if not cls._warning_shown:  # Double-check after acquiring lock
                    logger.warning(f"Software will expire in {days_remaining} days and {hours_remaining} hours!")
                    cls._warning_shown = True

        message = f"Software expires on {Config.EXPIRATION_DATE.strftime('%B %d, %Y at %I:%M %p')}"
        return False, message

    @classmethod
    def ensure_not_expired(cls):
        """Raise exception if software has expired"""
        expired, message = cls.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")


# ============================================================================
# BROWSER MANAGER
# ============================================================================

class BrowserManager:
    """Manages browser lifecycle and configuration"""

    def __init__(self, headless: bool = False, timeout: int = Config.DEFAULT_TIMEOUT, worker_id: int = 0):
        self.headless = headless
        self.timeout = timeout * 1000  # Convert to milliseconds
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.worker_id = worker_id

    def start(self):
        """Initialize and start the browser"""
        ExpirationManager.ensure_not_expired()

        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()

        # Get the full profile directory path
        profile_path = Config.get_profile_path(self.worker_id)

        # Check if profile exists
        profile_exists = os.path.exists(os.path.join(profile_path, "Default"))

        if profile_exists:
            logger.info(f"Loading existing profile from: {profile_path}")
        else:
            logger.info(f"Creating new profile at: {profile_path}")

        # Launch browser with persistent context (full profile)
        self.context = self.playwright.chromium.launch_persistent_context(
            profile_path,
            headless=self.headless,
            args=Config.BROWSER_ARGS,
            proxy={"server": Config.PROXY_SERVER},
            viewport={"width": 1280, "height": 600}
        )



        # Get the first page (persistent context creates one automatically)
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        logger.info(f"Browser initialized (headless={self.headless}) with full profile at: {profile_path}")

    def close(self):
        """Close browser and cleanup resources"""
        # With persistent context, everything is auto-saved
        if self.context:
            logger.info(f"Saving profile to: {Config.get_profile_path(self.worker_id)}")
            self.context.close()
            logger.info("Profile saved and browser closed")

        if self.playwright:
            self.playwright.stop()

    def get_page(self) -> Page:
        """Get the current page instance"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self.page


# ============================================================================
# PAGE INTERACTION HELPER
# ============================================================================

class PageInteractor:
    """Handles all page interactions and element operations"""

    def __init__(self, page: Page, timeout: int, worker_id: int = 0):
        self.page = page
        self.timeout = timeout
        self.worker_id = worker_id

    def click_element(self, selector: str, description: str, use_alt: bool = False):
        """
        Click an element with proper waiting and error handling

        Args:
            selector: CSS or XPath selector
            description: Human-readable description for logging
            use_alt: If True, raise exception on error instead of logging
        """
        try:
            element = self.page.locator(selector).first
            element.wait_for(state="visible", timeout=self.timeout)
            element.click()
            logger.info(f"Clicked {description}")
        except Exception as e:
            if use_alt:
                raise
            logger.error(f"Error clicking {description}: {e}")

    def click_clickable_parent(self, element) -> bool:
        """Recursively find and click clickable parent element"""
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

    def type_text(self, selector: str, text: str, description: str):
        """Type text into an input field"""
        element = self.page.locator(selector).first
        element.wait_for(state="visible", timeout=self.timeout)
        element.clear()
        element.type(text)
        logger.info(f"Typed into {description}")

    def wait_for_text_and_execute(self, text_actions_map: Dict[str, Callable],
                                   max_time: float) -> Optional[str]:
        """
        Wait for any text to appear and execute corresponding action

        Args:
            text_actions_map: Dictionary mapping text to action functions
            max_time: Maximum time to wait in seconds

        Returns:
            The text that was found, or None if timeout
        """
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
                time.sleep(Config.POLL_FREQUENCY)
            except:
                time.sleep(Config.POLL_FREQUENCY)
        return None

    def save_debug_info(self, phone_number: str):
        """Save screenshot and HTML for debugging"""
        try:
            # Add worker_id to filename to prevent race conditions
            filename = f"{phone_number}_worker{self.worker_id}"
            self.page.screenshot(path=f"photo/{filename}.png")
            with open(f"html/{filename}.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            logger.info(f"Debug info saved for {phone_number}")
        except Exception as e:
            logger.error(f"Error saving debug info: {e}")

    def show_preview(self):
        """Show screenshot preview"""
        screenshot_bytes = self.page.screenshot()
        Image.open(BytesIO(screenshot_bytes)).show()
        logger.info("Screenshot preview opened")


# ============================================================================
# FACEBOOK ACCOUNT CHECKER
# ============================================================================

class FacebookAccountChecker:
    """Main class for checking Facebook accounts"""

    def __init__(self, headless: bool = False, wait_timeout: int = Config.DEFAULT_TIMEOUT, worker_id: int = 0):
        ExpirationManager.ensure_not_expired()

        self.browser_manager = BrowserManager(headless, wait_timeout, worker_id)
        self.page_interactor: Optional[PageInteractor] = None
        self.current_phone_number: Optional[str] = None
        self.continuation = True
        self.reached_success = False
        self.error_message: Optional[str] = None
        self.worker_id = worker_id

        logger.info(f"FacebookAccountChecker initialized for worker {worker_id}")

    def setup(self):
        """Setup browser and page interactor"""
        self.browser_manager.start()
        page = self.browser_manager.get_page()
        self.page_interactor = PageInteractor(page, self.browser_manager.timeout, self.worker_id)

    def close(self):
        """Cleanup resources"""
        if self.browser_manager:
            self.browser_manager.close()

    def check_number(self, phone_number: str) -> CheckResult:
        """
        Check a single phone number

        Args:
            phone_number: Phone number to check

        Returns:
            CheckResult with status and message
        """
        self.current_phone_number = phone_number
        self._reset_state()

        try:
            self._navigate_to_recovery()
            self._handle_flow()

            if self.reached_success:
                return CheckResult(phone_number, 'success', 'Verification code page reached')
            elif self.error_message:
                return CheckResult(phone_number, 'failed', self.error_message)
            else:
                return CheckResult(phone_number, 'failed', 'An unexpected error occurred')

        except Exception as e:
            logger.error(f"Error checking {phone_number}: {e}")
            return CheckResult(phone_number, 'error', str(e))

    def _reset_state(self):
        """Reset checker state for new check"""
        self.continuation = True
        self.reached_success = False
        self.error_message = None

    def _navigate_to_recovery(self):
        """Navigate to Facebook account recovery page"""
        page = self.browser_manager.get_page()
        context = self.browser_manager.context

        # Clear only cookies before navigation
        context.clear_cookies()
        logger.info("Cleared cookies")

        page.goto(Config.FB_LOGIN_IDENTIFY_URL)

    def _handle_flow(self):
        """Handle the main flow of checking account"""
        text_actions = {
            "Allow the use of cookies from Facebook on this browser?": self._handle_cookie_consent,
            "Find Your Account": self._handle_find_account,
            "These accounts matched your search": self._handle_select_account,
            "How do you want to receive the code to reset your password?": self._handle_recovery_method,
            "How do you want to get the code to reset your password?": self._handle_recovery_method,
            "Before we send the code, enter these letters and numbers": self._handle_robot_detected,
            "Enter security code": self._handle_verification_sent,
            "Account disabled": self._handle_disabled,
            "No search results": self._handle_no_results,
            "Log in as": self._handle_try_another_way,
            "Log in to": self._handle_try_another_way,
            "Reload page": self._handle_reload,
            "We can send a login code to:": self._handle_direct_code,
            "You're Temporarily Blocked": self._handle_blocked,
            "Try another device to continue": self._handle_another_device,
        }

        try:
            while self.continuation:
                max_time = self.browser_manager.timeout / 1000
                found_text = self.page_interactor.wait_for_text_and_execute(text_actions, max_time)

                if not found_text:
                    logger.warning("No expected text found")
                    self.page_interactor.save_debug_info(self.current_phone_number)
                    break

                # Remove handled action to avoid re-execution
                if found_text in text_actions:
                    del text_actions[found_text]

                if not text_actions:
                    break

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

    def _stop_with_error(self, error_msg: str):
        """Stop continuation with error message"""
        self.continuation = False
        self.error_message = error_msg
        logger.info(error_msg)

    # ========================================================================
    # FLOW HANDLERS
    # ========================================================================

    def _handle_cookie_consent(self):
        """Handle cookie consent popup"""
        try:
            page = self.browser_manager.get_page()
            cookie_element = page.locator("//*[contains(text(), 'Allow all cookies')]").first
            if cookie_element.count() > 0:
                self.page_interactor.click_clickable_parent(cookie_element)
                logger.info("Cookie consent handled")
        except:
            logger.debug("No cookie popup found")

    def _handle_find_account(self):
        """Handle account search"""
        self.page_interactor.type_text(
            "#identify_email",
            self.current_phone_number,
            "phone number field"
        )
        self.page_interactor.click_element("#did_submit", "search button")
        logger.info(f"Searched for phone number: {self.current_phone_number}")

    def _handle_select_account(self):
        """Handle account selection"""
        self.page_interactor.click_element(
            "//a[contains(text(), 'This is my account')]",
            "account confirmation"
        )

    def _handle_recovery_method(self):
        """Handle recovery method selection (SMS)"""
        phone_to_match = ''.join(filter(str.isdigit, self.current_phone_number))
        page = self.browser_manager.get_page()
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
                if (phone_to_match == phone_in_label or
                    phone_to_match in phone_in_label or
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
            logger.info("SMS radio button selected")

        self.page_interactor.click_element(
            "//button[@name='reset_action' and @type='submit' and contains(text(), 'Continue')]",
            "Continue button"
        )

    def _handle_verification_sent(self):
        """Handle verification code page reached"""
        self.continuation = False
        self.reached_success = True
        logger.info("Verification code input page reached")

    def _handle_disabled(self):
        """Handle disabled account"""
        self._stop_with_error("Account is disabled")

    def _handle_no_results(self):
        """Handle no search results"""
        self._stop_with_error("Facebook account isn't found")

    def _handle_robot_detected(self):
        """Handle CAPTCHA/robot detection"""
        self._stop_with_error("Robot detected - CAPTCHA required")

    def _handle_blocked(self):
        """Handle temporary block"""
        self._stop_with_error("You're Temporarily Blocked")

    def _handle_another_device(self):
        """Handle another device required"""
        self._stop_with_error("Try another device to continue")

    def _handle_try_another_way(self):
        """Handle try another way option"""
        try:
            self.page_interactor.click_element(
                "//a[@name='tryanotherway' and contains(text(), 'Try another way')]",
                "Try another way"
            )
        except:
            try:
                self.page_interactor.click_element(
                    "[name='tryanotherway']",
                    "Try another way (alt)",
                    use_alt=True
                )
            except Exception as e:
                logger.error(f"Failed to click 'Try another way': {e}")
                raise

    def _handle_reload(self):
        """Handle page reload"""
        page = self.browser_manager.get_page()
        page.reload()
        logger.info("Page reloaded")

    def _handle_direct_code(self):
        """Handle direct code send option"""
        try:
            self.page_interactor.click_element(
                "//button[@type='submit' and contains(text(), 'Continue')]",
                "Continue button"
            )
        except:
            try:
                self.page_interactor.click_element(
                    "//button[@type='submit']",
                    "Continue button (alt)",
                    use_alt=True
                )
            except Exception as e:
                logger.error(f"Failed to click Continue: {e}")
                raise


# ============================================================================
# WORKER MANAGEMENT
# ============================================================================

class CheckerWorker:
    """Worker that processes phone numbers"""

    def __init__(self, worker_id: int, headless: bool = False):
        self.worker_id = worker_id
        self.headless = headless
        self.checker: Optional[FacebookAccountChecker] = None
        self.phones_processed = 0

    def process_queue(self, phone_queue: queue.Queue,
                     results_list: List[CheckResult],
                     results_lock: threading.Lock):
        """
        Process phone numbers from queue

        Args:
            phone_queue: Queue containing phone numbers to check
            results_list: Shared list to store results
            results_lock: Lock for thread-safe results access
        """
        self.checker = FacebookAccountChecker(headless=self.headless, worker_id=self.worker_id)

        try:
            # Setup browser ONCE for the entire worker session
            self.checker.setup()
            logger.info(f"Worker {self.worker_id} browser ready with profile: profiles/{self.worker_id}")

            while True:
                try:
                    phone_number = phone_queue.get(timeout=1)

                    logger.info(f"Worker {self.worker_id} checking: {phone_number}")

                    # Wrap check_number in try-except to prevent worker crash
                    try:
                        result = self.checker.check_number(phone_number)
                    except Exception as check_error:
                        logger.error(f"Worker {self.worker_id} error checking {phone_number}: {check_error}")
                        result = CheckResult(phone_number, 'error', f'Check failed: {str(check_error)}')

                    self.phones_processed += 1

                    # Store result thread-safely
                    with results_lock:
                        results_list.append(result)
                        total = phone_queue.qsize() + len(results_list)
                        logger.info(f"Progress: {len(results_list)}/{total} completed")

                    phone_queue.task_done()

                except queue.Empty:
                    logger.info(f"Worker {self.worker_id} finished - processed {self.phones_processed} numbers")
                    break

        except Exception as e:
            logger.error(f"Worker {self.worker_id} fatal error during setup: {e}")
        finally:
            # Close browser ONCE at the end
            if self.checker:
                try:
                    logger.info(f"Worker {self.worker_id} closing browser after processing {self.phones_processed} numbers")
                    self.checker.close()
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} error closing browser: {e}")



# ============================================================================
# BATCH PROCESSOR
# ============================================================================

class BatchProcessor:
    """Handles batch processing of phone numbers"""

    def __init__(self, num_workers: int = 1, headless: bool = False):
        self.num_workers = num_workers
        self.headless = headless
        self.results: List[CheckResult] = []
        self.results_lock = threading.Lock()

    def process_numbers(self, phone_numbers: List[str]) -> List[CheckResult]:
        """
        Process a list of phone numbers

        Args:
            phone_numbers: List of phone numbers to check

        Returns:
            List of CheckResult objects
        """
        # Create queue and populate
        phone_queue = queue.Queue()
        for number in phone_numbers:
            phone_queue.put(number)

        logger.info(f"Starting to check {len(phone_numbers)} phone numbers with {self.num_workers} workers")

        # Create and start workers
        workers = []
        for i in range(self.num_workers):
            worker_thread = threading.Thread(
                target=CheckerWorker.run_worker,
                args=(i, phone_queue, self.results, self.results_lock, self.headless)
            )
            workers.append(worker_thread)
            worker_thread.start()

        # Wait for all workers to complete
        for worker in workers:
            worker.join()

        logger.info("All workers completed")
        return self.results


# ============================================================================
# RESULTS REPORTER
# ============================================================================

class ResultsReporter:
    """Handles reporting and display of results"""


    @staticmethod
    def print_summary(results: List[CheckResult]):
        """Print a summary of all results"""
        logger.info("=" * 50)
        logger.info("FINAL RESULTS:")
        logger.info("=" * 50)

        success_count = sum(1 for r in results if r.status == 'success')
        failed_count = sum(1 for r in results if r.status == 'failed')
        error_count = sum(1 for r in results if r.status == 'error')

        logger.info(f"Total checked: {len(results)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Errors: {error_count}")

        logger.info("\nDetailed results:")
        for result in results:
            logger.info(str(result))

    @staticmethod
    def save_to_file(results: List[CheckResult], filename: str = "results.txt"):
        """Save results to a file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Facebook Account Check Results\n")
                f.write("=" * 50 + "\n\n")
                for result in results:
                    f.write(f"{result}\n")
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_phone_numbers(data_str: str) -> List[str]:
    """Parse phone numbers from multi-line string"""
    return [num.strip() for num in data_str.split('\n') if num.strip()]


def check_single_number(phone_number: str, headless: bool = False) -> CheckResult:
    """
    Convenience function to check a single phone number

    Args:
        phone_number: Phone number to check
        headless: Whether to run browser in headless mode

    Returns:
        CheckResult
    """
    checker = FacebookAccountChecker(headless=headless)
    try:
        checker.setup()
        result = checker.check_number(phone_number)
        logger.info(f"Completed check for {phone_number}: {result.status}")
        return result
    except Exception as e:
        logger.error(f"Error checking {phone_number}: {e}")
        return CheckResult(phone_number, 'error', str(e))
    finally:
        checker.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the application"""
    # Ensure required directories exist
    Config.ensure_directories()

    # Sample phone numbers for testing
    nums_str = """
2250715774457
2250715776049
2250715777573
2250715773443
2250715773725
2250715779203
2250715779821
2250715773140
2250715777761
2250715770618
2250715779038
2250715772866
2250715778684
2250715774608
2250715778171
2250715772758
2250715771858
2250715779267
2250715777338
2250715774450
2250715771945
2250715773345
2250715776450
2250715772022
2250715772378
2250715770521
2250715777429
2250715774921
2250715776943
2250715773983
2250715778643
2250715779619
2250715773959
2250715778952
2250715770236
2250715772775
2250715775410
2250715774263
2250715776536
2250715775787
2250715776233
2250715779156
2250715774888
2250715777180
2250715770026
2250715770266
2250715777970
2250715776042
2250715776175
2250715779608
2250715772206
2250715778048
2250715777090
2250715777733
2250715773737
2250715778343
2250715776566
2250715771466
2250715779233
2250715778030
2250715775240
2250715778962
2250715776835
2250715770546
2250715771302
2250715774878
2250715772568
2250715776014
2250715770393
2250715771863
2250715778539
2250715777700
2250715773193
2250715775874
2250715774882
2250715774341
2250715771975
2250715777196
2250715779588
2250715777909
2250715777259
2250715779813
2250715775464
2250715771412
2250715770859
2250715771824
2250715779686
2250715778074
2250715779989
2250715777835
2250715770605
2250715776589
2250715774123
2250715779730
2250715776431
2250715776679
2250715777047
2250715779318
2250715774674
2250715770601
    """

    # Parse phone numbers
    phone_numbers = parse_phone_numbers(nums_str)

    # Process numbers
    processor = BatchProcessor(num_workers=5, headless=False)
    results = processor.process_numbers(phone_numbers)

    # Report results
    ResultsReporter.print_summary(results)
    # ResultsReporter.save_to_file(results)  # Optionally save to file


if __name__ == "__main__":
    main()
