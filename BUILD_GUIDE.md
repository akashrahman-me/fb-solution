# 📦 Building Windows Installer (.exe)

Complete guide to build a single Windows installer that includes both frontend and backend.

---

## 🎯 Prerequisites

### 1. Install PyInstaller (for Python backend)

```bash
cd fbpanel
pip install -r requirements-build.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

---

## 🚀 Build Steps

### Option A: Automated Build (Recommended)

From the `client` directory:

```bash
cd client
npm run build:app
```

This will:

1. Build Next.js frontend ✅
2. Build Python backend executable ✅
3. Copy backend to resources ✅
4. Create Windows installer ✅

**Output:** `client/dist/FB OTP Generator-0.1.0-Setup.exe`

---

### Option B: Manual Step-by-Step Build

#### Step 1: Build Python Backend

```bash
cd fbpanel
python build_backend.py
```

Output: `fbpanel/dist/fb-backend.exe`

#### Step 2: Build Frontend & Package

```bash
cd client
npm run build:web
npm run copy:backend
electron-builder --win --x64
```

---

## 📂 Project Structure After Build

```
fb-solution/
├── client/
│   ├── backend/               # Backend executable (copied here)
│   │   └── fb-backend.exe
│   ├── dist/                  # Final installer
│   │   └── FB OTP Generator-0.1.0-Setup.exe
│   └── out/                   # Built Next.js app
└── fbpanel/
    └── dist/
        └── fb-backend.exe     # Python backend executable
```

---

## 🎮 How It Works

1. **Electron app starts** → Automatically launches `fb-backend.exe`
2. **Backend runs on** → http://localhost:8000
3. **Frontend connects** → to backend API
4. **User closes app** → Backend automatically stops

---

## 🧪 Testing the Build

### Test Backend Executable Separately:

```bash
cd fbpanel/dist
./fb-backend.exe
```

Should start server on http://localhost:8000

### Test Full Installer:

1. Run the installer: `FB OTP Generator-0.1.0-Setup.exe`
2. Install the application
3. Launch from desktop shortcut
4. App should work without requiring Python or Node.js installed!

---

## 🔧 Troubleshooting

### Issue: Backend doesn't start

-   Check if port 8000 is already in use
-   Run backend manually to see error messages

### Issue: PyInstaller errors

```bash
# Clean build and try again
cd fbpanel
rm -rf build dist
python build_backend.py
```

### Issue: Playwright not working

```bash
# Reinstall Playwright
playwright install chromium --force
```

---

## 📝 Build Configuration

### Customize App Name/Version

Edit `client/package.json`:

```json
{
    "name": "fb-otp-generator",
    "version": "0.1.0",
    "build": {
        "productName": "FB OTP Generator"
    }
}
```

### Customize Installer

Edit `client/package.json` → `build.nsis` section

---

## ✅ Distribution

The final installer (`FB OTP Generator-0.1.0-Setup.exe`) is:

-   ✅ Self-contained (includes everything)
-   ✅ Works on any Windows machine
-   ✅ No Python/Node.js required
-   ✅ Automatic updates supported (if configured)

Just distribute this single .exe file! 🎉
