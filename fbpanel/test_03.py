import asyncio, os
from playwright.async_api import async_playwright

CONCURRENCY = 10
SITE = "https://example.com"
PROFILE_ROOT = "./profiles"

os.makedirs(PROFILE_ROOT, exist_ok=True)


async def warm_profile(playwright, profile_dir: str):
    browser = await playwright.chromium.launch_persistent_context(profile_dir, headless=True)
    page = await browser.new_page()
    await page.goto(SITE, wait_until="networkidle")
    await asyncio.sleep(1)
    await browser.close()


async def worker(playwright, profile_dir: str, numbers: list[int]):
    ctx = await playwright.chromium.launch_persistent_context(profile_dir, headless=True)

    # block heavy assets if not needed
    await ctx.route("**/*", lambda route: (
        route.abort() if route.request.resource_type in ["image", "font", "media"] else route.continue_()
    ))

    for number in numbers:
        page = await ctx.new_page()
        try:
            await page.goto(SITE, wait_until="networkidle")

            # example actions
            await page.fill("#phoneInput", str(number))
            await page.click("#validateBtn")
            await page.wait_for_selector("#sendOtpBtn", timeout=5000)
            await page.click("#sendOtpBtn")
            await page.wait_for_load_state("networkidle")

            # clear cookies + localStorage/sessionStorage
            await ctx.clear_cookies()
            await page.evaluate("localStorage.clear(); sessionStorage.clear();")
        except Exception as e:
            print("Error for", number, ":", e)
        finally:
            await page.close()

    await ctx.close()


async def main():
    async with async_playwright() as p:
        # make profile dirs
        for i in range(CONCURRENCY):
            os.makedirs(f"{PROFILE_ROOT}/profile-{i}", exist_ok=True)

        # warm all profiles (only once)
        await asyncio.gather(*[
            warm_profile(p, f"{PROFILE_ROOT}/profile-{i}") for i in range(CONCURRENCY)
        ])
        print("Profiles warmed.")

        # split jobs
        numbers = [8800000000 + i for i in range(100)]
        queues = [numbers[i::CONCURRENCY] for i in range(CONCURRENCY)]

        await asyncio.gather(*[
            worker(p, f"{PROFILE_ROOT}/profile-{i}", queues[i]) for i in range(CONCURRENCY)
        ])

asyncio.run(main())
