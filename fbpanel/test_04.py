from playwright.sync_api import sync_playwright
import time
import psutil


# 1. Record the network stats before the operation
initial_io = psutil.net_io_counters()
initial_bytes_sent = initial_io.bytes_sent
initial_bytes_recv = initial_io.bytes_recv

def run_test():


    with sync_playwright() as p:
        # Launch browser without persistent context (no profile saved)
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            proxy={
                "server": "http://127.0.0.1:8080"
            }
            # proxy={
            #     "server": "http://142.111.48.253:7030",
            #     "username": "lmmwyrac",
            #     "password": "fi17jsine73g"
            # }
        )

        # Create a new page
        page = context.new_page()

        page.set_default_timeout(15000)

        try:
            refresh_times = 1
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
        # Close context and browser
        context.close()
        browser.close()


run_test()


# 3. Record the network stats after the operation
final_io = psutil.net_io_counters()
final_bytes_sent = final_io.bytes_sent
final_bytes_recv = final_io.bytes_recv

# 4. Calculate the difference
bytes_sent_used = final_bytes_sent - initial_bytes_sent
bytes_recv_used = final_bytes_recv - initial_bytes_recv
total_bytes_used = bytes_sent_used + bytes_recv_used


# Convert total bytes to Megabytes (MB)
# Note: 1 MB = 1024 * 1024 bytes (MiB) or 1,000,000 bytes (MB).
# Using 1024*1024 is standard in computing contexts (MiB).
total_mb_used = total_bytes_used / (1024 * 1024)

print("\n--- Network Usage Report ---")
print(f"Bytes Sent: {bytes_sent_used} bytes")
print(f"Bytes Received: {bytes_recv_used} bytes")
print(f"Total Bandwidth Used: {total_bytes_used} bytes")
print(f"Total Bandwidth Used: {total_mb_used:.2f} MB")