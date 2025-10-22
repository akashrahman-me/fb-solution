import time
import os
import queue
import threading
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# ============================================================================
# LOGGING
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
    EXPIRATION_DATE = datetime(2025, 11, 21, 23, 59, 59)
    PROXY_SERVER = "http://127.0.0.1:8080"
    TIMEOUT = 20
    POLL_INTERVAL = 0.1
    PROFILES_DIR = "profiles"
    FB_RECOVERY_URL = "https://www.facebook.com/login/identify/"

    @classmethod
    def ensure_dirs(cls):
        os.makedirs("photo", exist_ok=True)
        os.makedirs("html", exist_ok=True)
        os.makedirs(cls.PROFILES_DIR, exist_ok=True)


# ============================================================================
# MODELS
# ============================================================================

@dataclass
class CheckResult:
    phone: str
    status: str
    message: str


# ============================================================================
# EXPIRATION CHECK
# ============================================================================

def check_expired():
    if datetime.now() > Config.EXPIRATION_DATE:
        raise Exception(f"Software expired on {Config.EXPIRATION_DATE.strftime('%B %d, %Y')}")


# ============================================================================
# FACEBOOK CHECKER
# ============================================================================

class FacebookChecker:
    def __init__(self, worker_id: int = 0, headless: bool = False):
        check_expired()
        self.worker_id = worker_id
        self.headless = headless
        self.driver = None
        logger.info(f"Worker {worker_id} initialized")

    def start_browser(self):
        """Start browser with profile"""
        profile_path = os.path.abspath(os.path.join(Config.PROFILES_DIR, str(self.worker_id)))
        os.makedirs(profile_path, exist_ok=True)

        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--remote-debugging-port={9222 + self.worker_id}')
        options.add_argument(f'--proxy-server={Config.PROXY_SERVER}')

        if self.headless:
            options.add_argument('--headless=new')

        self.driver = uc.Chrome(
            options=options,
            user_data_dir=profile_path,
            headless=self.headless,
            use_subprocess=False
        )

        if not self.headless:
            self.driver.set_window_size(1280, 720)

        self.driver.set_page_load_timeout(Config.TIMEOUT)
        logger.info(f"Worker {self.worker_id} browser started")

    def close_browser(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info(f"Worker {self.worker_id} browser closed")
            except:
                pass

    def check_phone(self, phone: str) -> CheckResult:
        """Check a single phone number"""
        try:
            # Navigate and clear cookies
            self.driver.get(Config.FB_RECOVERY_URL)
            try:
                self.driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
                self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
                self.driver.refresh()
            except:
                pass

            # Wait for page and enter phone
            result = self._process_flow(phone)
            return result

        except Exception as e:
            logger.error(f"Error checking {phone}: {e}")
            return CheckResult(phone, 'error', str(e))

    def _process_flow(self, phone: str) -> CheckResult:
        """Process the Facebook recovery flow"""

        # Step 1: Find account page
        if not self._wait_for_text("Find Your Account", 10):
            return CheckResult(phone, 'error', 'Find account page not loaded')

        # Enter phone number
        try:
            input_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#identify_email"))
            )
            input_field.clear()
            input_field.send_keys(phone)

            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "#did_submit")
            submit_btn.click()
            logger.info(f"Searched for: {phone}")
        except Exception as e:
            return CheckResult(phone, 'error', f'Failed to enter phone: {e}')

        # Step 2: Check results
        time.sleep(2)  # Brief wait for response

        page_text = self.driver.page_source

        # Check for various outcomes
        if "No search results" in page_text:
            return CheckResult(phone, 'failed', 'Account not found')

        if "Account disabled" in page_text:
            return CheckResult(phone, 'failed', 'Account disabled')

        if "You're Temporarily Blocked" in page_text:
            return CheckResult(phone, 'failed', 'Temporarily blocked')

        if "Try another device" in page_text:
            return CheckResult(phone, 'failed', 'Device verification required')

        if "captcha" in page_text.lower() or "enter these letters" in page_text.lower():
            return CheckResult(phone, 'failed', 'CAPTCHA detected')

        # Step 3: Recovery method selection
        if "How do you want to" in page_text and "code" in page_text:
            if not self._select_sms_option(phone):
                return CheckResult(phone, 'failed', 'SMS option not available')

            # Click continue
            try:
                continue_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(., 'Continue')]"))
                )
                continue_btn.click()
                time.sleep(2)
            except:
                pass

        # Step 4: Check for verification code page
        if self._wait_for_text("Enter security code", 10):
            return CheckResult(phone, 'success', 'Verification code page reached')

        # Step 5: Handle "Log in as" / "Try another way"
        if "Log in as" in self.driver.page_source or "Log in to" in self.driver.page_source:
            try:
                another_way = self.driver.find_element(By.CSS_SELECTOR, "[name='tryanotherway']")
                another_way.click()
                time.sleep(2)

                # Try again after clicking another way
                if "How do you want to" in self.driver.page_source:
                    if self._select_sms_option(phone):
                        try:
                            continue_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                            continue_btn.click()
                            time.sleep(2)
                            if self._wait_for_text("Enter security code", 10):
                                return CheckResult(phone, 'success', 'Verification code page reached')
                        except:
                            pass
            except:
                pass

        # Check one more time for success
        if "Enter security code" in self.driver.page_source or "enter the code" in self.driver.page_source.lower():
            return CheckResult(phone, 'success', 'Verification code page reached')

        # Save debug info
        self._save_debug(phone)
        return CheckResult(phone, 'failed', 'Unexpected page state')

    def _wait_for_text(self, text: str, timeout: int) -> bool:
        """Wait for text to appear on page"""
        start = time.time()
        while time.time() - start < timeout:
            if text in self.driver.page_source:
                return True
            time.sleep(Config.POLL_INTERVAL)
        return False

    def _select_sms_option(self, phone: str) -> bool:
        """Select SMS recovery option"""
        try:
            phone_digits = ''.join(filter(str.isdigit, phone))
            radios = self.driver.find_elements(By.XPATH, "//input[@type='radio' and @name='recover_method']")

            for radio in radios:
                try:
                    radio_id = radio.get_attribute('id')
                    if not radio_id or not radio_id.startswith('send_sms:'):
                        continue

                    label = self.driver.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                    label_text = label.text

                    if "SMS" not in label_text:
                        continue

                    label_digits = ''.join(filter(str.isdigit, label_text))
                    if phone_digits in label_digits or label_digits in phone_digits:
                        if not radio.is_selected():
                            radio.click()
                        logger.info("SMS option selected")
                        return True
                except:
                    continue

            logger.warning("SMS option not found")
            return False
        except Exception as e:
            logger.error(f"Error selecting SMS: {e}")
            return False

    def _save_debug(self, phone: str):
        """Save screenshot and HTML"""
        try:
            filename = f"{phone}_worker{self.worker_id}"
            self.driver.save_screenshot(f"photo/{filename}.png")
            with open(f"html/{filename}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        except:
            pass


# ============================================================================
# BATCH PROCESSOR
# ============================================================================

class BatchProcessor:
    def __init__(self, num_workers: int = 1, headless: bool = False):
        self.num_workers = num_workers
        self.headless = headless

    def process(self, phone_numbers: List[str]) -> List[CheckResult]:
        """Process phone numbers with multiple workers"""
        phone_queue = queue.Queue()
        for num in phone_numbers:
            phone_queue.put(num)

        results = []
        results_lock = threading.Lock()

        def worker_func(worker_id: int):
            checker = FacebookChecker(worker_id, self.headless)
            try:
                checker.start_browser()

                while True:
                    try:
                        phone = phone_queue.get(timeout=1)
                        result = checker.check_phone(phone)

                        with results_lock:
                            results.append(result)
                            logger.info(f"Progress: {len(results)}/{len(phone_numbers)}")

                        phone_queue.task_done()
                    except queue.Empty:
                        break
            finally:
                checker.close_browser()

        # Start workers
        threads = []
        for i in range(self.num_workers):
            t = threading.Thread(target=worker_func, args=(i,), daemon=True)
            t.start()
            threads.append(t)

        # Wait for completion
        for t in threads:
            t.join()

        return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_phones(text: str) -> List[str]:
    """Parse phone numbers from text"""
    return [line.strip() for line in text.strip().split('\n') if line.strip()]


def print_results(results: List[CheckResult]):
    """Print summary of results"""
    success = sum(1 for r in results if r.status == 'success')
    failed = sum(1 for r in results if r.status == 'failed')
    error = sum(1 for r in results if r.status == 'error')

    logger.info("=" * 50)
    logger.info(f"RESULTS: Total={len(results)}, Success={success}, Failed={failed}, Errors={error}")
    logger.info("=" * 50)

    for r in results:
        logger.info(f"{r.phone}: {r.status} - {r.message}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    Config.ensure_dirs()

    nums = """
        2250715774457
        2250715776049
    """

    phone_numbers = parse_phones(nums)
    processor = BatchProcessor(num_workers=2, headless=False)
    results = processor.process(phone_numbers)
    print_results(results)


if __name__ == "__main__":
    main()

