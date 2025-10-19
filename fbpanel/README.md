# Facebook Number Checker - Build Instructions

## Building the Windows Executable

This guide will help you create a standalone Windows executable (.exe) and installer for the Facebook Number Checker application.

## Prerequisites

1. **Install PyInstaller** (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. **Install Inno Setup** (for creating installer - optional):
   - Download from: https://jrsoftware.org/isdl.php
   - Install the software on your Windows machine

## Method 1: Quick Build (Executable Only)

~~### Step 1: Run the Build Script
Simply run:
```bash
python build_exe.py
```~~

This will:
- Clean old build files (optional)
- Create a standalone executable
- Place it in the `dist` folder

### Step 2: Test the Executable
After building, test the executable:
```bash
dist\FacebookChecker.exe
```

## Method 2: Manual Build

If you prefer manual control:

```bash
pyinstaller --name=FacebookChecker --onefile --windowed --add-data=main.py;. --hidden-import=customtkinter --hidden-import=PIL._tkinter_finder --collect-all=customtkinter gui.py
```

## Method 3: Create Professional Installer

After building the executable, create a professional installer:

### Step 1: Build the Executable First
```bash
python build_exe.py
```

### Step 2: Create the Installer with Inno Setup
1. Open Inno Setup Compiler
2. File → Open → Select `installer_script.iss`
3. Build → Compile
4. Find the installer in `installer_output` folder

The installer will be named: `FacebookChecker_Setup.exe`

## What Gets Created

### Executable Build:
- `dist/FacebookChecker.exe` - Standalone executable (~100-150 MB)
- No Python installation required on target machine
- All dependencies bundled

### Installer Build:
- `installer_output/FacebookChecker_Setup.exe` - Windows installer
- Creates Start Menu shortcuts
- Optional Desktop shortcut
- Proper uninstaller

## Distributing Your Application

### Option 1: Distribute the .exe only
- Share `dist/FacebookChecker.exe`
- Users double-click to run
- No installation needed

### Option 2: Distribute the Installer
- Share `installer_output/FacebookChecker_Setup.exe`
- Users run installer
- Professional installation experience
- Easy uninstallation

## Troubleshooting

### "Module not found" errors:
Add the missing module to PyInstaller command:
```bash
--hidden-import=module_name
```

### Antivirus false positives:
- Common with PyInstaller executables
- Sign your executable with a code signing certificate
- Or add exception in antivirus software

### Large file size:
- Normal for bundled executables
- Contains Python runtime + all dependencies
- To reduce: use `--onedir` instead of `--onefile`

## Testing Checklist

Before distributing:
- [ ] Test on clean Windows machine (without Python)
- [ ] Test all features (number checking, workers, headless mode)
- [ ] Verify Chrome/ChromeDriver works
- [ ] Check if antivirus blocks it
- [ ] Test installer installation/uninstallation

## Notes

- First run may be slower as Chrome driver sets up
- Requires internet connection to access Facebook
- Windows Defender may scan on first run
- Chrome browser will be downloaded automatically if not present

