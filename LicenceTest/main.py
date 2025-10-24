# client_activate_gui.py
import os, json, base64, datetime, tkinter as tk, tkinter.messagebox as mb
from cryptography.fernet import Fernet
import sys
import uuid as _uuid

# Embed the APP_KEY by reading app.key at build time or paste key bytes here.
# Option A: If you include app.key in build, use:
try:
    with open("app.key","rb") as f:
        APP_KEY = f.read()
except Exception:
    # Option B: paste key literal here if you prefer embedding:
    APP_KEY = b"PASTE_YOUR_APP_KEY_BYTES_HERE"

f = Fernet(APP_KEY)

SAVE_PATH = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "myapp_license.txt")

def get_system_uuid():
    # Try Windows MachineGuid
    try:
        if sys.platform.startswith("win"):
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Cryptography")
            machineguid, _ = winreg.QueryValueEx(key, "MachineGuid")
            return machineguid.strip()
    except Exception:
        pass
    # Try Linux machine-id
    try:
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read().strip()
    except Exception:
        pass
    # Fallback to MAC-based value (not perfect but usable)
    mac = _uuid.getnode()
    return f"{mac:x}"

def verify_token(token):
    try:
        data = json.loads(f.decrypt(token.encode()).decode())
    except Exception as e:
        return False, "invalid token #3984"
    # expiry check
    try:
        if datetime.datetime.now(datetime.timezone.utc) > datetime.datetime.strptime(data["expiry"], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc):
            return False, "invalid token #2934"
    except Exception:
        return False, "invalid token #3984"
    # uuid check
    sys_uuid = get_system_uuid()
    if data.get("uuid") != sys_uuid:
        return False, f"invalid token #9238"

    secure_data = {k: v for k, v in data.items() if k != 'uuid'}
    return True, secure_data

token = input("Enter your license token: ").strip()
print(verify_token(token))

