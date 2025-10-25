# 🚀 FB Solution - Windows Installer Build Guide

This guide will help you build a complete Windows installer (.exe) that includes both the frontend and backend in a single package.

## 📋 Prerequisites

### 1. Node.js & npm

- Node.js 18+ installed
- Verify: `node --version` and `npm --version`

### 2. Python Environment

- Python 3.8+ installed
- Verify: `python --version`

### 3. Install Python Dependencies

```bash
cd fbpanel
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Install Node Dependencies

```bash
cd client
npm install
```

### 5. Install Playwright Browsers (Backend)

```bash
cd fbpanel
playwright install chromium
```

## 🏗️ Build Process

### Option A: One Command Build (Recommended)

From the `client` directory:

```bash
npm run build:app
```

This single command will:

1. ✅ Build the Next.js frontend
2. ✅ Build the Python backend to executable
3. ✅ Copy backend to resources
4. ✅ Create Windows installer

**Output:** `client/dist/FB OTP Generator-0.1.0-Setup.exe`

---

### Option B: Step-by-Step Build

If you want more control or need to debug:

#### Step 1: Build Frontend

```bash
cd client
npm run build:web
```

- Creates optimized static site in `client/out/`

#### Step 2: Build Python Backend

```bash
cd ../fbpanel
python build_backend.py
```

- Creates `fbpanel/dist/fb-backend.exe` (~100-150 MB)

#### Step 3: Copy Backend to Client

```bash
cd ../client
npm run copy:backend
```

- Copies backend exe to `client/backend/`

#### Step 4: Build Installer

```bash
npm run build:installer
```

- Creates Windows installer in `client/dist/`

---

## 📦 What Gets Built

### Backend Executable (`fb-backend.exe`)

- Standalone FastAPI server
- Playwright browser automation
- All Python dependencies bundled
- Size: ~100-150 MB

### Frontend

- Next.js static site
- Electron wrapper
- Embedded HTTP server
- All Node.js dependencies

### Final Installer (`FB OTP Generator-0.1.0-Setup.exe`)

- NSIS installer format
- Includes both frontend and backend
- Creates desktop shortcut
- Creates start menu entry
- Size: ~150-200 MB

---

## 🎯 Testing the Build

### Test Backend Executable Separately

```bash
cd fbpanel/dist
fb-backend.exe
```

Should see: `API Server ready at http://localhost:8000`

### Test Frontend in Development

```bash
cd client
npm run dev
```

### Test Installer

1. Double-click `FB OTP Generator-0.1.0-Setup.exe`
2. Follow installation wizard
3. Launch from desktop shortcut or start menu

---

## 🔧 Troubleshooting

### Issue: PyInstaller Not Found

```bash
pip install pyinstaller
```

### Issue: Playwright Browsers Missing

```bash
cd fbpanel
playwright install chromium
```

### Issue: Backend Build Fails

- Check all dependencies in `fbpanel/requirements.txt` are installed
- Try deleting `fbpanel/build/` and `fbpanel/dist/` folders
- Run `python build_backend.py` again

### Issue: Frontend Build Fails

- Delete `client/.next/` and `client/out/` folders
- Delete `client/node_modules/` and run `npm install`
- Run `npm run build:web` again

### Issue: Installer Build Fails

- Ensure backend executable exists in `fbpanel/dist/fb-backend.exe`
- Run `npm run copy:backend` to verify backend is copied
- Check Electron Builder logs in `client/dist/`

### Issue: App Crashes on Launch

- Check if backend port 8000 is available
- Check if frontend port 7000 is available
- Look for error logs in AppData folder

---

## 📂 File Locations

```
fb-solution/
├── client/
│   ├── backend/                    # Copied backend exe
│   │   └── fb-backend.exe
│   ├── out/                        # Built frontend
│   ├── dist/                       # Final installer
│   │   └── FB OTP Generator-0.1.0-Setup.exe
│   └── package.json
│
└── fbpanel/
    ├── dist/                       # Backend exe
    │   └── fb-backend.exe
    ├── build/                      # PyInstaller temp files
    └── build_backend.py
```

---

## 🚀 Distribution

### To Distribute Your App:

1. Share `client/dist/FB OTP Generator-0.1.0-Setup.exe`
2. Users run the installer
3. App installs to `C:\Program Files\FB OTP Generator\`
4. Desktop and Start Menu shortcuts created

### System Requirements for End Users:

- Windows 10/11 (64-bit)
- ~500 MB disk space
- No Python or Node.js required!
- Internet connection for Facebook checking

---

## 🔄 Rebuild After Changes

### Frontend Changes Only:

```bash
cd client
npm run build:web
npm run build:installer
```

### Backend Changes Only:

```bash
cd fbpanel
python build_backend.py
cd ../client
npm run copy:backend
npm run build:installer
```

### Both Changed:

```bash
cd client
npm run build:app
```

---

## 📝 Version Management

To change version number:

1. Edit `client/package.json`:

```json
{
    "version": "0.1.0" // Change this
}
```

2. Rebuild installer:

```bash
npm run build:app
```

New installer will be named with new version.

---

## ✅ Pre-Release Checklist

Before distributing:

- [ ] Test backend runs: `fbpanel/dist/fb-backend.exe`
- [ ] Test installer builds without errors
- [ ] Install on a clean Windows machine
- [ ] Verify app launches and connects to backend
- [ ] Test phone number checking functionality
- [ ] Test settings persistence
- [ ] Check proxy configuration works
- [ ] Verify uninstaller works properly
- [ ] Scan with antivirus (may show false positive)

---

## 🎉 Success!

If everything works, you now have a single Windows installer that bundles both your Next.js frontend and Python backend into one easy-to-distribute package!

**Happy Building! 🚀**
