@echo off
echo ============================================
echo Facebook Checker - Direct Build Script
echo ============================================
echo.

REM Clean old builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist FacebookChecker.spec del /q FacebookChecker.spec

REM Preinstall Playwright Chromium into local folder for bundling
set "PLAYWRIGHT_BROWSERS_PATH=%CD%\playwright-browsers"
echo Installing Playwright Chromium into: %PLAYWRIGHT_BROWSERS_PATH%
python -m pip install playwright >nul 2>&1
python -m playwright install chromium

echo Building with PyInstaller...
echo.

python -m PyInstaller --name=FacebookChecker --onedir --windowed --icon=NONE --add-data=main.py;. --add-data=proxy_injector.py;. --add-data=utils;utils --add-data=playwright-browsers;playwright-browsers --hidden-import=customtkinter --hidden-import=PIL._tkinter_finder --hidden-import=proxy_injector --hidden-import=playwright --collect-all=customtkinter --collect-all=playwright --runtime-hook=rthooks/pyi_rth_playwright_browsers.py gui.py

if errorlevel 1 (
    echo.
    echo ============================================
    echo Build FAILED!
    echo ============================================
    pause
    exit /b 1
)

if exist dist\FacebookChecker\FacebookChecker.exe (
    echo.
    echo ============================================
    echo Build SUCCESSFUL!
    echo ============================================
    echo.
    echo Creating launcher script...

    REM Create launcher batch file (fallback first-run setup if needed)
    echo @echo off > dist\FacebookChecker\Launch_FacebookChecker.bat
    echo cd /d "%%~dp0" >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo. >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo REM Prefer bundled browsers; if missing, install locally >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo if not exist "playwright-browsers" ( >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     echo ============================================ >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     echo Facebook Checker - First Time Setup >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     echo ============================================ >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     echo. >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     set "PLAYWRIGHT_BROWSERS_PATH=%%CD%%\playwright-browsers" >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     echo Installing Chromium browser ^(one-time setup^)... >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     python -m pip install playwright >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo     python -m playwright install chromium >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo ^) >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo. >> dist\FacebookChecker\Launch_FacebookChecker.bat
    echo start "" "FacebookChecker.exe" >> dist\FacebookChecker\Launch_FacebookChecker.bat

    echo.
    echo Executable created at: dist\FacebookChecker\FacebookChecker.exe
    echo.
    echo ============================================
    echo IMPORTANT - READ THIS:
    echo ============================================
    echo To run the application:
    echo 1. Go to: dist\FacebookChecker\
    echo 2. Run: FacebookChecker.exe
    echo    ^(If browser doesn't open, try Launch_FacebookChecker.bat once^)
    echo.
    echo Distribute the entire 'FacebookChecker' folder.
    echo ============================================
) else (
    echo.
    echo ============================================
    echo Build FAILED - Executable not created!
    echo ============================================
)

echo.
pause
