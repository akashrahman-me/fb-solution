import requests

# Local proxy configuration
LOCAL_PROXY = "http://127.0.0.1:8080"

proxies = {
    "http": LOCAL_PROXY,
    "https": LOCAL_PROXY
}

try:
    print("Testing proxy connection...")
    print(f"Using proxy: {LOCAL_PROXY}")
    print("-" * 50)

    # Make request through the local proxy
    response = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)

    if response.status_code == 200:
        print("✓ Proxy is working!")
        print("\nIP Information:")
        print(response.text)
    else:
        print(f"✗ Error: Status code {response.status_code}")
        print(response.text)

except requests.exceptions.ProxyError as e:
    print(f"✗ Proxy connection failed: {e}")
except requests.exceptions.Timeout as e:
    print(f"✗ Request timed out: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
