@echo off
echo ============================================
echo Facebook Checker - Browser Setup
echo ============================================
echo.
echo This will install Chromium browser for the application.
echo This needs to be done only once.
echo.
pause

echo Installing Playwright browsers...
playwright install chromium

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo You can now run FacebookChecker.exe
echo.
pause

