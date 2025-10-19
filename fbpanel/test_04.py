from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Set True to hide browser
    page = browser.new_page()
    page.goto("https://www.facebook.com/login/identify")
    browser.close()
