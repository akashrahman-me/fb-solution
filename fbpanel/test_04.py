import undetected_chromedriver as uc
import time

# Test opening Google website with undetected Chrome driver
print("Initializing undetected Chrome driver...")

# Create Chrome options
options = uc.ChromeOptions()
# options.add_argument('--headless')  # Uncomment for headless mode

# Initialize the undetected Chrome driver
driver = uc.Chrome(options=options)

try:
    driver.get('https://www.ivasms.com/portal/live/my_sms')

    print(f"Page title: {driver.title}")
    print(f"Current URL: {driver.current_url}")

except Exception as e:
    print(f"Error occurred: {e}")

finally:
    input("Press Enter to close the browser...")
    driver.quit()