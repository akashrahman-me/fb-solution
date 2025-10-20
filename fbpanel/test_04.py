from playwright.sync_api import sync_playwright
import time


def run_test():


    with sync_playwright() as p:
        # Use persistent context for proper caching with proxy
        user_data_dir = "playwright_user_data"

        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            proxy={
                "server": "http://127.0.0.1:8080"
            }
            # proxy={
            #     "server": "http://142.111.48.253:7030",
            #     "username": "lmmwyrac",
            #     "password": "fi17jsine73g"
            # }
        )

        # Use the default page from persistent context
        page = context.pages[0] if context.pages else context.new_page()

        page.set_default_timeout(15000)

        try:
            refresh_times = 5
            print("🧪 Testing Facebook with CUSTOM CACHE (refresh_times iterations)\n")

            for i in range(refresh_times):
                print(f"[{i+1}/{refresh_times}] ", end="", flush=True)

                # Visit Facebook
                if i == 0:
                    page.goto("https://www.facebook.com/login/identify/?ctx=recover&ars=facebook_login&from_login_screen=0", wait_until="domcontentloaded")

                else:
                    page.reload(wait_until="domcontentloaded")

                time.sleep(3)
            print("\n" + "="*70)
            print(f"✅ All {refresh_times} tests completed successfully!")

        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

        time.sleep(5)
        # Close the persistent context (crucial for saving cache)
        context.close()


run_test()