import requests
import json

def test_proxy():
    """Test the proxy configuration"""
    proxy = {
        "http": "http://user-akash_sAIls-country-US:83QcuHmvdK8_yrv@dc.oxylabs.io:8000",
        "https": "http://user-akash_sAIls-country-US:83QcuHmvdK8_yrv@dc.oxylabs.io:8000"
    }
    url = "https://ip.oxylabs.io/location"

    try:
        print("Testing proxy connection...")
        response = requests.get(url, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("\n✓ Proxy is working!")
        print("\nYour IP Location Info:")
        print(json.dumps(data, indent=4))
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Proxy connection failed: {e}")
        return False

if __name__ == "__main__":
    test_proxy()
