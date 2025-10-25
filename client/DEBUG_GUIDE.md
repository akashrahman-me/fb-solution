# 🐛 Debugging White Screen Issues

## Common Causes & Solutions

### 1. **Static Files Not Found**

The most common issue is that the `out` folder is missing or not included in the build.

**Solution:** Rebuild everything:

```bash
cd client
npm run build:app
```

### 2. **Backend Not Starting**

The Python backend might not be starting, causing API calls to fail.

**Check:** Look for `fb-backend.exe` in the installation directory.

### 3. **Port Conflicts**

Ports 7000 (frontend) or 8000 (backend) might be in use.

**Solution:** Close other apps using these ports or restart your computer.

---

## 📋 How to View Logs

### Method 1: Run from Command Prompt (Recommended)

1. Open Command Prompt (cmd)
2. Navigate to installation folder:
    ```cmd
    cd "C:\Program Files\FB OTP Generator"
    ```
3. Run the executable:
    ```cmd
    "FB OTP Generator.exe"
    ```
4. Logs will appear in the command prompt window

### Method 2: View Electron Logs

Electron stores logs in AppData. View them with:

**Windows:**

```
%APPDATA%\fb-otp-generator\logs
```

Or open in File Explorer:

1. Press `Win + R`
2. Type: `%APPDATA%\fb-otp-generator`
3. Look for log files

### Method 3: Enable DevTools in Production

I've enabled DevTools in the updated code. When the white screen appears:

1. Press `Ctrl+Shift+I` (or `F12`) to open DevTools
2. Check the Console tab for errors
3. Check the Network tab to see if files are loading

---

## 🔍 What to Look For in Logs

### Good Signs (App should work):

```
✅ Frontend server running on http://127.0.0.1:7000
✅ Backend found
✅ Backend started
✅ DOM Ready
✅ Page Finished Loading
```

### Bad Signs (Problems to fix):

```
❌ Static path does not exist
❌ Backend not found at: ...
❌ Failed to load: ...
❌ Backend Process Error
```

---

## 🛠️ Step-by-Step Troubleshooting

### Step 1: Check if Out Folder Exists

```bash
cd client
dir out
```

Should show: `index.html`, `_next` folder, etc.

**If missing:** Run `npm run build:web`

### Step 2: Check if Backend is Built

```bash
cd fbpanel\dist
dir
```

Should show: `fb-backend.exe`

**If missing:** Run `python build_backend.py`

### Step 3: Check if Backend is Copied

```bash
cd client\backend
dir
```

Should show: `fb-backend.exe`

**If missing:** Run `npm run copy:backend`

### Step 4: Test Backend Manually

```bash
cd fbpanel\dist
fb-backend.exe
```

Should see: `API Server ready at http://localhost:8000`

### Step 5: Rebuild Installer

```bash
cd client
npm run build:installer
```

---

## 🔄 Complete Clean Rebuild

If nothing works, do a complete clean rebuild:

```bash
# Clean frontend
cd client
rm -rf out
rm -rf dist
rm -rf .next

# Clean backend
cd ../fbpanel
rm -rf dist
rm -rf build

# Rebuild everything
cd ../client
npm run build:app
```

---

## 🚨 Emergency Debug Version

Create a debug version that shows more info:

1. Open `client/main.js`
2. Find line: `mainWindow.webContents.openDevTools();`
3. Make sure it's NOT commented out
4. Rebuild: `npm run build:installer`
5. Install and run - DevTools will open automatically

---

## 📞 Still Having Issues?

Check these files in the built app:

1. **Installation Directory:**

    ```
    C:\Program Files\FB OTP Generator\
    ```

2. **Resources folder should contain:**
    - `resources\app.asar` (contains frontend)
    - `resources\backend\fb-backend.exe`

3. **Extract app.asar to verify contents:**
    ```bash
    npm install -g asar
    asar extract "C:\Program Files\FB OTP Generator\resources\app.asar" extracted
    dir extracted\out
    ```

---

## ✅ Quick Checklist

Before reporting issues, verify:

- [ ] `client/out` folder exists with files
- [ ] `fbpanel/dist/fb-backend.exe` exists
- [ ] `client/backend/fb-backend.exe` exists
- [ ] No errors during `npm run build:app`
- [ ] Ports 7000 and 8000 are free
- [ ] Windows Firewall allows the app
- [ ] Antivirus didn't block/delete files
- [ ] Ran installer as Administrator
- [ ] Installed to default location

---

## 🎯 Expected Startup Sequence

```
1. App starts
2. Electron logs: "FB OTP Generator Starting..."
3. Checks static path (out folder)
4. Starts frontend HTTP server on port 7000
5. Checks backend path
6. Starts backend process (fb-backend.exe)
7. Backend starts API server on port 8000
8. Creates window
9. Loads http://127.0.0.1:7000
10. Window shows with UI
```

If any step fails, you'll see an error in the logs!
