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

from utils.normalize_text import normalize_text

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
EXPIRATION_DATE = datetime(2025, 11, 21, 23, 59, 59)
PROXY_SERVER = "http://127.0.0.1:8080"
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
]

# Thread-safe expiration warning
_expiration_warning_shown = False
_warning_lock = threading.Lock()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_directories():
    """Create necessary directories if they don't exist"""

    try:
        shutil.rmtree("photo")
        shutil.rmtree("html")
    except FileNotFoundError:
        pass  # Directory doesn't exist, ignore

    os.makedirs("photo", exist_ok=True)
    os.makedirs("html", exist_ok=True)
    os.makedirs(PROFILES_DIR, exist_ok=True)


def check_expiration():
    """Check if software has expired"""
    global _expiration_warning_shown

    if EXPIRATION_DATE is None:
        return

    now = datetime.now()

    # Check if expired
    if now > EXPIRATION_DATE:
        days_expired = (now - EXPIRATION_DATE).days
        raise Exception(f"SOFTWARE EXPIRED: This software expired on {EXPIRATION_DATE.strftime('%B %d, %Y')} ({days_expired} days ago)")

    # Show warning if expiring soon
    days_remaining = (EXPIRATION_DATE - now).days
    if days_remaining <= 3 and not _expiration_warning_shown:
        with _warning_lock:
            if not _expiration_warning_shown:
                logger.warning(f"Software will expire in {days_remaining} days!")
                _expiration_warning_shown = True


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


# ============================================================================
# BROWSER MANAGEMENT
# ============================================================================

def create_browser(worker_id, headless=False):
    """Create and return a browser context and page"""
    check_expiration()

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
        args=BROWSER_ARGS,
        proxy={"server": PROXY_SERVER},
        viewport={"width": 1280, "height": 600}
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(TIMEOUT)

    # Set default navigation to not wait for images/stylesheets
    page.set_default_navigation_timeout(TIMEOUT)

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
TEXT_LOG_IN_AS = "Log in as"
TEXT_LOG_IN_TO = "Log in to"
TEXT_SEND_LOGIN_CODE = "We can send a login code to:"
TEXT_RELOAD_PAGE = "Reload page"

def check_phone_number(page, phone_number, worker_id):
    """
    Check a single phone number on Facebook
    Returns: (success: bool, message: str)
    """
    try:
        # Navigate to recovery page (don't wait for all resources to load)
        page.context.clear_cookies()
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
            TEXT_LOG_IN_AS,  # ACTION
            TEXT_LOG_IN_TO,  # ACTION
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
                logger.info("✓ Verification code page reached - SUCCESS! \n\n")
                return True, "Verification code page reached"

            # Check for FAILURES
            if found_text == TEXT_NO_SEARCH_RESULTS:
                return False, "Facebook account not found \n\n"

            if found_text == TEXT_ACCOUNT_DISABLED:
                return False, "Account is disabled \n\n"

            if found_text == TEXT_CAPTCHA_REQUIRED:
                return False, "CAPTCHA required \n\n"

            if found_text == TEXT_TEMPORARILY_BLOCKED:
                return False, "You're temporarily blocked \n\n"

            if found_text == TEXT_TRY_ANOTHER_DEVICE:
                return False, "Try another device to continue \n\n"

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

            # if found_text == TEXT_LOG_IN_AS or found_text == TEXT_LOG_IN_TO:
            #     logger.info("Action: Trying another way")
            #     handle_try_another_way(page)
            #     all_possible_texts.remove(TEXT_LOG_IN_AS)
            #     all_possible_texts.remove(TEXT_LOG_IN_TO)

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

def worker_thread(worker_id, phone_queue, results_list, results_lock, headless):
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

def process_phone_numbers(phone_numbers, num_workers=1, headless=False):
    """
    Process multiple phone numbers using worker threads

    Args:
        phone_numbers: List of phone numbers to check
        num_workers: Number of parallel workers
        headless: Run browsers in headless mode

    Returns:
        List of results dictionaries
    """
    ensure_directories()
    check_expiration()

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
            args=(i, phone_queue, results_list, results_lock, headless)
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
2290149422329
2290149424024
2290149421786
2290149423307
2290149421132
2290149429104
2290149428652
2290149420218
2290149425131
2290149424342
2290149423956
2290149428713
2290149424775
2290149422988
2290149424373
2290149423195
2290149425573
2290149420986
2290149425403
2290149425630
2290149427107
2290149420160
2290149420931
2290149423899
2290149427927
2290149428429
2290149428045
2290149424699
2290149423314
2290149427494
2290149421689
2290149426307
2290149421460
2290149421607
2290149424722
2290149429037
2290149427341
2290149421123
2290149423428
2290149425374
2290149421058
2290149427848
2290149421945
2290149428800
2290149423436
2290149427760
2290149427305
2290149428664
2290149428160
2290149425326
2290149428270
2290149424421
2290149425491
2290149422072
2290149425051
2290149425322
2290149422289
2290149429739
2290149427569
2290149421390
2290149427714
2290149421669
243891356221
243891355390
243891356849
243891351699
243891356439
243891358589
243891353213
243891352349
243891351892
243891350176
243891357506
243891357701
243891359761
243891353066
243891357635
243891350929
243891356378
243891352199
243891355306
243891351729
243891350102
243891356155
243891356706
243891356054
243891357986
243891356874
243891358383
243891359313
243891352374
243891354695
243891358611
243891352686
243891351040
243891350554
243891355601
243891359307
243891357890
243891356422
243891359402
243891350372
243891357157
243891357840
243891355999
243891358779
243891352984
243891356498
243891359577
243891356690
243891357090
243891358156
243891357679
243891352316
243891356471
243891358764
243891350549
243891352971
243891358890
243891357017
243891356575
243891359671
243891355183
243891355077
243891359266
243891352586
243891353615
243891358413
243891354608
243891352221
243891359462
243891351439
243891357306
243891356684
243891356335
243891356955
243891350244
243891354312
243891352959
243891357675
243891359297
243891358482
243891358052
243891359633
243891356829
243891354835
243891352784
243891358346
243891354023
243891352277
243891350293
243891356215
243891356590
243891353014
243891358028
243891356111
243891353893
243891359857
243891354120
243891356535
243891350354
243891351191
243842447216
243842442956
243842448475
243842448200
243842443585
243842442189
243842442782
243842440794
243842446035
243842447969
243842441224
243842445813
243842449244
243842444490
243842448978
243842447592
243842443200
243842445454
243842449022
243842444983
243842445580
243842448273
243842448533
243842447244
243842445054
243842447400
243842445498
243842443248
243842442020
243842442617
243842441008
243842440277
243842449239
243842440414
243842443478
243842448563
243842446006
243842442238
243842446587
243842446100
243842441864
243842448192
243842445709
243842445196
243842442097
243842440040
243842445847
243842442041
243842445798
243842441213
243842442210
243842440060
243842449326
243842448820
243842442718
243842447303
243842441994
243842440234
243842446907
243842443893
243842444721
243842440133
243842446396
243842448517
243842442253
243842440787
243842448299
243842448397
243842449139
243842448330
243842440064
243842440914
243842442416
243842446372
243842444501
243842443677
243842448150
243842448322
243842449799
243842441820
243842447182
243842442169
243842443725
243842440323
243842442303
243842446230
243842448938
243842447289
243842446675
243842449641
243842443619
243842444156
243842448924
243842444880
243842447533
243842448301
243842443424
243842445641
243842441835
243842447837
251906957107
251906957697
251906959884
251906956416
251906957364
251906951511
251906957774
251906957753
251906951182
251906953652
251906953208
251906954352
251906956171
251906950920
251906956440
251906952924
251906951048
251906952206
251906958816
251906952758
251906952317
251906954223
251906952246
251906951227
251906955412
251906953599
251906956328
251906955757
251906954144
251906959980
251906956204
251906955488
251906951387
251906950429
251906954955
251906953504
251906950067
251906952511
251906954009
251906954103
251906954690
251906957998
251906959487
251906957362
251906950469
251906957087
251906951806
251906950169
251906952530
251906959077
251906957202
251906955415
251906950963
251906959333
251906950702
251906951505
251906955491
251906954881
251906958877
251906956498
251906953627
251906955120
251906950426
251906950141
251906950966
251906956304
251906952856
251906952227
251906957323
251906953625
251906951949
251906952281
251906958425
251906953773
251906954678
251906954407
251906957208
251906955594
251906957076
251906953264
251906953786
251906950478
251906959301
251906955677
251906950606
251906950747
251906956074
251906957693
251906955352
251906952024
251906958617
251906958615
251906958810
251906956417
251906953847
251906952885
251906952586
251906959600
251906951310
251906951593
959674085673
959674085771
959674080744
959674082738
959674084209
959674082910
959674083096
959674088906
959674082238
959674089166
959674081681
959674088985
959674089343
959674089220
959674085215
959674087286
959674086283
959674084727
959674082762
959674088612
959674089578
959674081542
959674083060
959674083583
959674081576
959674083153
959674088105
959674089271
959674083323
959674082898
959674086493
959674082653
959674082696
959674081930
959674087608
959674086242
959674085177
959674089169
959674086737
959674081686
959674080639
959674086679
959674084941
959674087858
959674085655
959674083316
959674080045
959674082319
959674086480
959674080081
959674086073
959674080953
959674084181
959674082675
959674084131
959674086489
959674089465
959674083000
959674083307
959674081732
959674086724
959674083672
959674080709
959674080502
959674084660
959674085572
959674086961
959674080091
959674085920
959674081935
959674087618
959674081369
959674080617
959674086290
959674087417
959674088608
959674085536
959674089520
959674081339
959674085832
959674082377
959674084457
959674085360
959674084099
959674084584
959674084635
959674083217
959674083688
959674087756
959674085022
959674085950
959674087842
959674087720
959674080374
959674087106
959674086247
959674081216
959674084009
959674084510
959674087585
959688929019
959688923930
959688928676
959688928530
959688920834
959688928650
959688921202
959688926351
959688922743
959688928977
959688925394
959688925828
959688928979
959688920181
959688922661
959688924577
959688922294
959688929581
959688929023
959688921585
959688923292
959688929499
959688923458
959688927018
959688926138
959688925703
959688926452
959688929477
959688926952
959688924391
959688928164
959688929099
959688924727
959688926979
959688922017
959688921204
959688922375
959688923290
959688921388
959688927077
959688926990
959688927749
959688927567
959688927956
959688920022
959688926383
959688920645
959688925727
959688929508
959688929154
959688928018
959688925919
959688921904
959688922368
959688929066
959688926174
959688929011
959688929867
959688926763
959688927449
959688925810
959688927466
959688926007
959688927668
959688925433
959688929676
959688924935
959688928961
959688929774
959688921323
959688920343
959688923293
959688925560
959688924895
959688923879
959688926438
959688922926
959688921312
959688927126
959688923905
959688920266
959688928587
959688925898
959688926063
959688923446
959688922761
959688928715
959688922690
959688927634
959688925858
959688922387
959688923169
959688923180
959688920911
959688920338
959688924460
959688928108
959688921872
959688922126
959688922866
959694340345
959694343778
959694346412
959694340869
959694346761
959694340820
959694345406
959694343803
959694348057
959694349187
959694347901
959694348994
959694348461
959694344935
959694348382
959694345800
959694341115
959694344883
959694342360
959694342814
959694345396
959694348235
959694346158
959694349966
959694343895
959694346104
959694341686
959694347227
959694343241
959694340685
959694341427
959694344974
959694340361
959694345556
959694345247
959694344894
959694349530
959694348416
959694347580
959694341879
959694344954
959694348983
959694348183
959694347353
959694344795
959694341163
959694346423
959694349990
959694340037
959694349350
959694344850
959694341214
959694343218
959694343606
959694346219
959694342637
959694344405
959694343062
959694343700
959694345061
959694344056
959694345383
959694346811
959694341757
959694345886
959694348932
959694342707
959694344944
959694340478
959694341947
959694348243
959694342467
959694347030
959694341746
959694349097
959694343932
959694340915
959694343677
959694344501
959694348408
959694347686
959694347842
959694346643
959694349652
959694342193
959694343277
959694346595
959694341526
959694347602
959694340344
959694346111
959694346264
959694340186
959694348509
959694344780
959694344623
959694344778
959694345428
959694344472
959694345665
959650771628
959650772613
959650773906
959650772841
959650776228
959650777085
959650770906
959650773677
959650772340
959650770845
959650773727
959650777195
959650778004
959650772358
959650779355
959650776304
959650770448
959650774328
959650771074
959650777895
959650771898
959650772584
959650774971
959650777569
959650779980
959650779447
959650779684
959650770023
959650770199
959650779150
959650779663
959650772725
959650776086
959650779656
959650774602
959650774929
959650777001
959650775487
959650773807
959650777644
959650777923
959650778448
959650778622
959650770081
959650770975
959650776567
959650770536
959650777466
959650772901
959650778020
959650779242
959650770155
959650774515
959650770989
959650779876
959650778833
959650775290
959650777634
959650779767
959650776167
959650770502
959650771727
959650774179
959650772272
959650777720
959650776221
959650776664
959650771448
959650773681
959650776287
959650777899
959650776597
959650775952
959650771668
959650772408
959650774097
959650774173
959650772679
959650770031
959650776716
959650778247
959650770788
959650770424
959650775112
959650774509
959650778390
959650771227
959650777203
959650770142
959650773925
959650770815
959650777112
959650771347
959650773017
959650778087
959650770054
959650775204
959650774254
959650773682
959650778113
9779764548236
9779764546117
9779764544878
9779764548206
9779764549716
9779764548466
9779764549342
9779764549629
9779764544761
9779764545081
9779764543054
9779764546539
9779764546471
9779764546812
9779764546843
9779764547023
9779764548901
9779764546455
9779764542800
9779764540477
9779764543341
9779764541576
9779764540432
9779764549546
9779764541887
9779764541670
9779764544030
9779764545688
9779764545116
9779764549882
9779764540185
9779764544886
9779764541340
9779764549689
9779764542913
9779764541444
9779764540330
9779764544285
9779764546213
9779764546707
9779764540337
9779764549178
9779764543355
9779764543029
9779764540373
9779764546905
9779764542295
9779764541681
9779764548303
9779764546821
9779764540013
9779764547954
9779764541130
9779764543169
9779764542285
9779764542302
9779764540381
9779764542631
9779764547799
9779764542110
9779764546534
9779764544627
9779764540796
9779764546406
9779764543255
9779764544503
9779764548014
9779764541403
9779764547349
9779764540680
9779764548249
9779764541035
9779764541663
9779764545954
9779764545188
9779764546064
9779764542216
9779764548583
9779764544189
9779764543812
9779764546119
9779764546380
9779764549810
9779764540327
9779764542954
9779764546456
9779764543992
9779764549878
9779764549748
9779764542731
9779764540355
9779764541664
9779764548141
9779764548617
9779764544269
9779764545331
9779764543650
9779764540968
9779764543701
9779764546868
998992381341
998992380771
998992389750
998992389126
998992380469
998992388038
998992384276
998992385248
998992380792
998992387253
998992388062
998992381451
998992384932
998992388582
998992381467
998992389574
998992389770
998992385746
998992382567
998992380364
998992382813
998992383222
998992389108
998992387963
998992387655
998992385821
998992381033
998992386661
998992381652
998992382448
998992382483
998992388911
998992387701
998992380852
998992387773
998992381554
998992386517
998992388389
998992387152
998992388014
998992380583
998992381049
998992380300
998992384453
998992386667
998992388121
998992381019
998992387292
998992382594
998992382826
998992385678
998992388956
998992384227
998992387086
998992382331
998992384066
998992384086
998992383152
998992387922
998992381935
998992387818
998992386618
998992388369
998992383148
998992383428
998992387682
998992387423
998992386838
998992386221
998992381448
998992386094
998992387428
998992387336
998992388645
998992388490
998992381539
998992385901
998992385697
998992384097
998992382396
998992389711
998992388299
998992385301
998992381897
998992389138
998992386753
998992380875
998992388784
998992389004
998992384515
998992388176
998992382506
998992384556
998992380671
998992385074
998992387448
998992388839
998992382046
998992385622
998992387528
    """

    # Parse phone numbers (remove empty lines and spaces)
    phone_numbers = [num.strip() for num in phone_numbers_text.split('\n') if num.strip()]

    # Process phone numbers with 5 workers
    results = process_phone_numbers(
        phone_numbers=phone_numbers,
        num_workers=20,
        headless=True
    )

    # Display results
    print_results(results)


if __name__ == "__main__":
    main()
