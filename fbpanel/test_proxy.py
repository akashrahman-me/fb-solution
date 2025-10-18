import requests
import json

# Proxy configuration
proxy_host = "142.111.48.253"
proxy_port = "7030"
proxy_user = "rqsgbzmp"
proxy_pass = "yag0ewjl9tws"

# Format proxy URL with authentication
proxies = {
    'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
    'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
}

print("Testing proxy connection...")
print(f"Proxy: {proxy_host}:{proxy_port}")
print("-" * 50)

try:
    # Make request through proxy
    response = requests.get('https://ip.oxylabs.io/location', proxies=proxies, timeout=10)

    # Print response with 4-space indent
    if response.status_code == 200:
        data = response.json()
        print("✓ Proxy connection successful!")
        print("\nResponse JSON:")
        print(json.dumps(data, indent=4))
    else:
        print(f"✗ Request failed with status code: {response.status_code}")
        print(response.text)

except requests.exceptions.ProxyError as e:
    print(f"✗ Proxy error: {e}")
except requests.exceptions.Timeout as e:
    print(f"✗ Timeout error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

