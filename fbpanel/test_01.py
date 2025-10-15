from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

proxy = "http://user-akash_sAIls-country-US:83QcuHmvdK8_yrv@dc.oxylabs.io:8000"

seleniumwire_options = {
    'proxy': {
        'http': proxy,
        'https': proxy,
        'no_proxy': 'localhost,127.0.0.1'
    }
}

opts = Options()
# add any chrome args you need, e.g. opts.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=opts, seleniumwire_options=seleniumwire_options)

driver.get('https://api.ipify.org?format=json')   # quick IP check
print(driver.page_source)
driver.quit()
