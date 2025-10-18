import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime
import json
import random
import string

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global lock removed - no longer needed, was preventing true concurrency

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


class AntiDetection:
    """Comprehensive anti-detection and stealth configuration"""

    # Realistic user agents with various browsers, OS, and versions
    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',

        # Chrome on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',

        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',

        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    ]

    # Realistic viewport sizes (width, height) - common resolutions
    VIEWPORTS = [
        {'width': 1920, 'height': 1080},  # Full HD
        {'width': 1366, 'height': 768},   # Common laptop
        {'width': 1536, 'height': 864},   # HD+
        {'width': 1440, 'height': 900},   # WXGA+
        {'width': 1600, 'height': 900},   # HD+
        {'width': 1680, 'height': 1050},  # WSXGA+
        {'width': 1280, 'height': 720},   # HD
        {'width': 1280, 'height': 1024},  # SXGA
        {'width': 2560, 'height': 1440},  # QHD
    ]

    # Timezones that match US location (for proxy)
    TIMEZONES = [
        'America/New_York',      # EST/EDT
        'America/Chicago',       # CST/CDT
        'America/Denver',        # MST/MDT
        'America/Los_Angeles',   # PST/PDT
        'America/Phoenix',       # MST (no DST)
        'America/Detroit',       # EST/EDT
        'America/Indianapolis',  # EST/EDT
    ]

    # US Locales
    LOCALES = ['en-US']

    @staticmethod
    def get_random_user_agent():
        """Get a random user agent"""
        return random.choice(AntiDetection.USER_AGENTS)

    @staticmethod
    def get_random_viewport():
        """Get a random viewport size"""
        return random.choice(AntiDetection.VIEWPORTS)

    @staticmethod
    def get_random_timezone():
        """Get a random US timezone"""
        return random.choice(AntiDetection.TIMEZONES)

    @staticmethod
    def get_random_locale():
        """Get a random locale"""
        return random.choice(AntiDetection.LOCALES)

    @staticmethod
    def random_delay(min_seconds=0.5, max_seconds=2.0):
        """Generate random delay to simulate human behavior"""
        return random.uniform(min_seconds, max_seconds)

    @staticmethod
    def random_typing_delay():
        """Generate random typing delay (per character)"""
        return random.uniform(0.05, 0.15)

    @staticmethod
    def get_stealth_js():
        """JavaScript to inject for hiding automation and randomizing fingerprints"""
        return """
        // Override the navigator.webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Override plugins to look more realistic
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    name: 'Chrome PDF Plugin',
                    description: 'Portable Document Format',
                    filename: 'internal-pdf-viewer'
                },
                {
                    name: 'Chrome PDF Viewer',
                    description: 'Portable Document Format',
                    filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'
                },
                {
                    name: 'Native Client',
                    description: '',
                    filename: 'internal-nacl-plugin'
                }
            ]
        });
        
        // Override languages to look realistic
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Randomize canvas fingerprint
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, attributes) {
            const context = originalGetContext.call(this, type, attributes);
            if (type === '2d') {
                const originalFillText = context.fillText;
                context.fillText = function(...args) {
                    // Add tiny random noise to canvas fingerprint
                    const noise = Math.random() * 0.0001;
                    if (args[1]) args[1] += noise;
                    if (args[2]) args[2] += noise;
                    return originalFillText.apply(this, args);
                };
            }
            return context;
        };
        
        // Override permissions
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Remove automation-related properties
        delete navigator.__proto__.webdriver;
        
        // Mock chrome runtime
        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {
                connect: () => {},
                sendMessage: () => {}
            };
        }
        
        // Randomize hardware concurrency slightly
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => Math.floor(Math.random() * 4) + 4  // 4-8 cores
        });
        
        // Randomize device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => [4, 8, 16][Math.floor(Math.random() * 3)]
        });
        """

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

        # Anti-detection: Generate random browser profile for this session
        self.user_agent = AntiDetection.get_random_user_agent()
        self.viewport = AntiDetection.get_random_viewport()
        self.timezone = AntiDetection.get_random_timezone()
        self.locale = AntiDetection.get_random_locale()

        logger.info(f"Session initialized with randomized profile:")
        logger.info(f"  - Viewport: {self.viewport['width']}x{self.viewport['height']}")
        logger.info(f"  - Timezone: {self.timezone}")
        logger.info(f"  - User Agent: {self.user_agent[:80]}...")

    def setup_driver(self):
        # Double-check expiration before setup
        expired, message = ExpirationChecker.check_expiration()
        if expired:
            raise Exception(f"SOFTWARE EXPIRED: {message}")

        # Initialize Playwright
        self.playwright = sync_playwright().start()

        # Launch browser with optimizations and anti-detection
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
                f'--window-size={self.viewport["width"]},{self.viewport["height"]}',
            ]
        )

        # Configure  proxy
        proxy_config = {
            'server': 'http://142.111.48.253:7030',
            'username': 'rqsgbzmp',
            'password': 'yag0ewjl9tws'
        }

        # Create context with anti-detection measures and proxy
        self.context = self.browser.new_context(
            viewport=self.viewport,
            user_agent=self.user_agent,
            locale=self.locale,
            timezone_id=self.timezone,
            proxy=proxy_config,
            # Additional anti-detection settings
            device_scale_factor=random.choice([1, 1.25, 1.5, 2]),
            is_mobile=False,
            has_touch=False,
            color_scheme=random.choice(['light', 'dark', 'no-preference']),
            # Permissions
            permissions=[],
            # Geolocation - randomize within US
            geolocation={'latitude': random.uniform(25.0, 49.0), 'longitude': random.uniform(-125.0, -66.0)},
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

        # Inject stealth scripts before any page load
        self.page.add_init_script(AntiDetection.get_stealth_js())

        self.page.on("response", handle_response)

        # Set default timeout
        self.page.set_default_timeout(self.wait_timeout)

        logger.info(f"Browser initialized (headless={self.headless}) with size: {self.viewport['width']}x{self.viewport['height']}")

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

    def human_like_type(self, element, text):
        """Type text with human-like delays between characters"""
        element.click()  # Focus on the element first
        time.sleep(AntiDetection.random_delay(0.1, 0.3))

        for char in text:
            element.type(char)
            time.sleep(AntiDetection.random_typing_delay())

        # Random pause after typing
        time.sleep(AntiDetection.random_delay(0.2, 0.5))

    def human_like_click(self, element):
        """Click with human-like delay before and after"""
        # Small delay before clicking
        time.sleep(AntiDetection.random_delay(0.3, 0.8))

        # Scroll element into view naturally
        element.scroll_into_view_if_needed()
        time.sleep(AntiDetection.random_delay(0.1, 0.3))

        # Click
        element.click()

        # Small delay after clicking
        time.sleep(AntiDetection.random_delay(0.5, 1.5))

    def random_mouse_movement(self):
        """Simulate random mouse movements on the page"""
        try:
            # Move mouse to random positions
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, self.viewport['width'] - 100)
                y = random.randint(100, self.viewport['height'] - 100)
                self.page.mouse.move(x, y)
                time.sleep(AntiDetection.random_delay(0.1, 0.4))
        except:
            pass

    def random_scroll(self):
        """Simulate random scrolling behavior"""
        try:
            # Random small scrolls
            scroll_amount = random.randint(100, 400)
            direction = random.choice([1, -1])

            self.page.evaluate(f"window.scrollBy(0, {scroll_amount * direction})")
            time.sleep(AntiDetection.random_delay(0.3, 0.8))
        except:
            pass

    def search_phone_number(self, phone_number):
        self.current_phone_number = phone_number

        # Add random delay before navigation
        time.sleep(AntiDetection.random_delay(0.5, 1.5))

        self.page.goto("https://www.facebook.com/login/identify/")

        # Simulate reading the page
        time.sleep(AntiDetection.random_delay(1.0, 2.5))

        # Random mouse movements
        self.random_mouse_movement()

    def select_account(self):
        time.sleep(AntiDetection.random_delay(1.0, 2.5))  # Wait before selecting

        first_account_link = self.page.locator("//a[contains(text(), 'This is my account')]").first
        first_account_link.wait_for(state="visible", timeout=self.wait_timeout)

        # Human-like interaction
        self.random_scroll()
        self.human_like_click(first_account_link)

        logger.info("First account selected")

    def continue_send_code(self):
        time.sleep(AntiDetection.random_delay(1.5, 3.0))  # Human-like pause to read options

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
            self.human_like_click(sms_radio_to_click)
            logger.info("SMS radio button clicked")

        continue_button = self.page.locator("//button[@name='reset_action' and @type='submit' and contains(text(), 'Continue')]").first
        continue_button.wait_for(state="visible", timeout=self.wait_timeout)
        self.human_like_click(continue_button)
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
        time.sleep(AntiDetection.random_delay(1.0, 2.0))  # Pause before clicking

        try:
            try_another_way_button = self.page.locator("//a[@name='tryanotherway' and contains(text(), 'Try another way')]").first
            try_another_way_button.wait_for(state="visible", timeout=self.wait_timeout)
            self.human_like_click(try_another_way_button)
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
        time.sleep(AntiDetection.random_delay(1.5, 3.0))  # Human-like pause to read

        try:
            # Click the Continue button to send the verification code
            continue_button = self.page.locator("//button[@type='submit' and contains(text(), 'Continue')]").first
            continue_button.wait_for(state="visible", timeout=self.wait_timeout)
            self.human_like_click(continue_button)
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
                self.human_like_click(element)
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
        time.sleep(AntiDetection.random_delay(0.5, 1.5))  # Pause before accepting cookies

        try:
            allow_cookie = self.page.locator(f"//*[contains(text(), 'Allow all cookies')]").first
            if allow_cookie.count() > 0:
                self.click_clickable_parent(allow_cookie)
        except:
            print("⚠️ No cookie popup found or 'Allow all cookies' not present.")

    def find_account(self):
        time.sleep(AntiDetection.random_delay(1.0, 2.5))  # Pause as if reading the page

        email_input = self.page.locator("#identify_email").first
        email_input.wait_for(state="visible", timeout=self.wait_timeout)

        # Random mouse movement before typing
        self.random_mouse_movement()

        email_input.clear()

        # Human-like typing
        self.human_like_type(email_input, self.current_phone_number)

        # Small pause before clicking search
        time.sleep(AntiDetection.random_delay(0.5, 1.5))

        search_button = self.page.locator("#did_submit").first
        search_button.wait_for(state="visible", timeout=self.wait_timeout)
        self.human_like_click(search_button)
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


if __name__ == "__main__":

    nums = [
        "2250706815570",
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
