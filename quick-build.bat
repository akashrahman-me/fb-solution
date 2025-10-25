@echo off
echo ========================================
echo   FB OTP Generator - Quick Build
echo ========================================
echo.
echo This will build the complete installer.
echo Make sure you have run the backend build first!
echo.
pause

cd client

echo.
echo Building...
call npm run build:app

if errorlevel 1 (
    echo.
    echo ========================================
    echo   BUILD FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD COMPLETE!
echo ========================================
echo.
echo Installer location: client\dist\FB OTP Generator-0.1.0-Setup.exe
echo.
pause
