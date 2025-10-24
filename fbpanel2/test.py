import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import csv
from datetime import datetime

PASSWORD = "#Akash@1234"


cookies_str = "presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1761252645393%2C%22v%22%3A1%7D;fr=0yD3nETUK6whFgIPm.AWdwF8ruZ7Ip8m5bpye1JBXpWNLnomV68ZwjuUrAzfgZgYpZqYM.Bo-pUR..AAA.0.0.Bo-pUh.AWfi9rk2lDIPH1G8exe6-XeqG8U;xs=25%3A7p_v_XNBT4-_xQ%3A2%3A1761252639%3A-1%3A-1;c_user=100076057855613;wd=1904x985;sb=sJH6aGbexE1tDA4s3gyzWRk8;datr=qZH6aAizU0l1xtTkdI3xg5j1"

driver = uc.Chrome()
driver.get(f"https://www.facebook.com")

# Clear all existing cookies before adding new ones
driver.delete_all_cookies()

# Parse and add cookies
cookie_pairs = cookies_str.split(";")
for cookie_pair in cookie_pairs:
    cookie_pair = cookie_pair.strip()
    if "=" in cookie_pair:
        name, value = cookie_pair.split("=", 1)
        driver.add_cookie({
            "name": name.strip(),
            "value": value.strip(),
            "domain": "facebook.com"
        })
print("Cookies loaded")


# Keep browser open
input("Press Enter to close...")
driver.quit()
