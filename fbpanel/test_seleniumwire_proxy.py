from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import time

print("Testing Selenium-Wire with Oxylabs proxy...")
print("=" * 50)

# Proxy configuration
proxy_host = "dc.oxylabs.io"
proxy_port = "8000"
proxy_user = "user-akash_sAIls-country-US"
proxy_pass = "83QcuHmvdK8_yrv"

# Configure proxy options for selenium-wire
seleniumwire_options = {
    'proxy': {
        'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
        'no_proxy': 'localhost,127.0.0.1'
    }
}

# Setup Chrome options
options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

print(f"Proxy configured: {proxy_host}:{proxy_port}")
print(f"Username: {proxy_user}")
print("Starting Chrome with selenium-wire proxy...")

try:
    driver = webdriver.Chrome(
        options=options,
        seleniumwire_options=seleniumwire_options
    )
    print("✓ Chrome started successfully with selenium-wire")

    # Test the proxy by visiting ip check page
    print("\nNavigating to https://ip.oxylabs.io/location...")
    driver.get("https://ip.oxylabs.io/location")

    # Wait for page to load
    print("Waiting for page to load (3 seconds)...")
    time.sleep(3)

    # Get page content
    page_source = driver.page_source

    print("\nPage content preview:")
    print(page_source[:800])

    if "ip" in page_source.lower():
        if '"country":"us"' in page_source.lower() or '"country": "us"' in page_source.lower():
            print("\n✓✓✓ SUCCESS! Proxy is working correctly - US IP detected!")
        else:
            print("\n⚠ Proxy connected but not showing US IP")
            # Extract country if possible
            import json
            try:
                # Find JSON in page source
                start = page_source.find('{')
                end = page_source.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(page_source[start:end])
                    ip = data.get('ip', 'unknown')
                    print(f"   Detected IP: {ip}")
                    providers = data.get('providers', {})
                    for provider, info in providers.items():
                        country = info.get('country', 'unknown')
                        print(f"   {provider}: {country}")
            except Exception as e:
                print(f"   Could not parse JSON: {e}")
    else:
        print("\n✗ Could not verify proxy - page did not load correctly")

    print("\n" + "=" * 50)
    print("Test completed. Browser will remain open for 10 seconds...")
    time.sleep(10)

    driver.quit()
    print("✓ Browser closed")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

