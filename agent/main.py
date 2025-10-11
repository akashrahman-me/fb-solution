import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from PIL import Image
from io import BytesIO

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class FacebookNumberChecker:
    def __init__(self, headless=False, wait_timeout=10):
        self.headless = headless
        self.wait_timeout = wait_timeout
        self.driver = None
        self.wait = None
        self.current_phone_number = None
        self.continuation = True

    def setup_driver(self):
        options = uc.ChromeOptions()
        options.headless = self.headless
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, self.wait_timeout)

        width = 1200
        height = int(width * 9 / 16)
        self.driver.set_window_size(width, height)

        logger.info(f"Browser initialized with size: {width}x{height}")

    def wait_for_text_and_execute(self, text_actions_map):
        """
        Wait for one of multiple texts to appear and execute corresponding action.
        text_actions_map: dict with text as key and action function as value
        """
        for text, action in text_actions_map.items():
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]"))
                )
                action()
                return text
            except:
                continue
        return None

    def search_phone_number(self, phone_number):
        self.current_phone_number = phone_number
        self.driver.get("https://www.facebook.com/login/identify/")

        email_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "identify_email"))
        )

        email_input.clear()
        email_input.send_keys(phone_number)

        time.sleep(0.5)  # Mimic human behavior

        search_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "did_submit"))
        )
        search_button.click()
        logger.info(f"Searched for phone number: {phone_number}")

    def select_account(self):
        first_account_link = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'This is my account')]"))
        )
        time.sleep(0.5)  # Mimic human behavior
        first_account_link.click()
        logger.info("First account selected")

    def continue_send_code(self):
        phone_to_match = ''.join(filter(str.isdigit, self.current_phone_number))

        time.sleep(1)

        all_radios = self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//input[@type='radio' and @name='recover_method']"))
        )

        sms_radio_to_click = None
        for radio in all_radios:
            try:
                radio_id = radio.get_attribute('id')

                if not radio_id or not radio_id.startswith('send_sms:'):
                    continue

                outer_label = radio.find_element(By.XPATH, "./ancestor::label")
                label_text = outer_label.text

                if "Send code via SMS" not in label_text:
                    continue

                phone_cleaned = ''.join(filter(str.isdigit, label_text))

                if phone_to_match == phone_cleaned or phone_to_match in phone_cleaned or phone_cleaned in phone_to_match:
                    sms_radio_to_click = radio
                    break
            except Exception as e:
                continue

        if not sms_radio_to_click:
            for radio in all_radios:
                try:
                    radio_id = radio.get_attribute('id')
                    if radio_id and radio_id.startswith('send_sms:'):
                        outer_label = radio.find_element(By.XPATH, "./ancestor::label")
                        if "Send code via SMS" in outer_label.text:
                            sms_radio_to_click = radio
                            break
                except Exception as e:
                    continue

        if not sms_radio_to_click:
            raise Exception("Could not find 'Send code via SMS' option")

        if not sms_radio_to_click.is_selected():
            sms_radio_to_click.click()

        time.sleep(0.5)

        continue_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@name='reset_action' and @type='submit' and contains(text(), 'Continue')]"))
        )
        continue_button.click()
        logger.info("SMS code option selected and Continue clicked")

    def continue_phone_number(self):
        pass

    def on_disabled(self):
        self.continuation = False
        logger.info("Account is disabled")

    def on_verification_send(self):
        self.continuation = False
        logger.info("Verification code input page reached")


    def handle_continuation(self):
        try:
            text_actions = {
                "These accounts matched your search": self.select_account,
                "How do you want to receive the code to reset your password?": self.continue_send_code,
                "Enter security code": self.on_verification_send,
                "Account disabled": self.on_disabled,
            }

            while self.continuation:
                found_text = self.wait_for_text_and_execute(text_actions)

                if not found_text:
                    logger.warning("No expected text found")
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
            self.driver.quit()
            logger.info("Browser closed")


if __name__ == "__main__":
    checker = FacebookNumberChecker(headless=True)

    try:
        checker.setup_driver()
        checker.search_phone_number("855716194307")
        checker.handle_continuation()
        time.sleep(10)
        checker.page_preview()
        input("Press Enter to close the browser...")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        input("Press Enter to close the browser...")
    finally:
        checker.close()
