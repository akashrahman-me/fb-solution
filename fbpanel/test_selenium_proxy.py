import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

proxy_host = "dc.oxylabs.io"
proxy_port = "8000"
proxy_user = "user-akash_sAIls-country-US"
proxy_pass = "83QcuHmvdK8_yrv"

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")

# Create a Chrome instance
driver = webdriver.Chrome(options=chrome_options)

# If proxy requires authentication
# Inject credentials using Chrome DevTools (works around popup)
driver.execute_cdp_cmd(
    "Network.enable", {}
)
driver.execute_cdp_cmd(
    "Network.setExtraHTTPHeaders",
    {
        "headers": {
            "Proxy-Authorization": f"Basic {__import__('base64').b64encode(f'{proxy_user}:{proxy_pass}'.encode()).decode()}"
        }
    }
)

# Test the proxy
driver.get("https://httpbin.org/ip")
print(driver.page_source)

time.sleep(999)

driver.quit()
