# 🎯 Quick Build Guide

## One-Command Build

Double-click: **`build-installer.bat`**

OR run in terminal:

```bash
build-installer.bat
```

That's it! 🎉

---

## What It Does

1. ✅ Installs PyInstaller
2. ✅ Builds Python backend → `fb-backend.exe`
3. ✅ Builds Next.js frontend
4. ✅ Copies backend to resources
5. ✅ Creates Windows installer

**Output:** `client/dist/FB OTP Generator-0.1.0-Setup.exe`

---

## First Time Setup

```bash
# Install Python dependencies
cd fbpanel
pip install -r requirements.txt
playwright install chromium

# Install Node.js dependencies
cd ../client
npm install
```

---

## Manual Build (Alternative)

```bash
cd client
npm run build:app
```

---

## Distribution

Share the installer:

-   **File:** `client/dist/FB OTP Generator-0.1.0-Setup.exe`
-   **Size:** ~200-300 MB (includes everything)
-   **Requirements:** Windows 10/11 (no Python/Node needed!)

Users just run the installer and start using the app! 🚀
