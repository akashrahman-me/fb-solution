# generate_license.py
import json, datetime
from cryptography.fernet import Fernet

# read your secret app key
with open("app.key","rb") as f:
    APP_KEY = f.read()
f = Fernet(APP_KEY)

def create_license(name, target_uuid, days_valid=30):
    payload = {
        "name": name,
        "uuid": target_uuid,
        "expiry": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_valid)).strftime("%Y-%m-%d")
    }
    token = f.encrypt(json.dumps(payload).encode()).decode()
    return token

if __name__ == "__main__":
    # Example: run and paste values
    name = input("Customer name: ").strip()
    target_uuid = input("Customer system uuid (ask them to provide): ").strip()
    days = input("Days valid [30]: ").strip()
    days = int(days) if days else 30
    token = create_license(name, target_uuid, days)
    print("\nGive this token to the customer (single line):\n")
    print(token)
