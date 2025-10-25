@echo off
echo ========================================
echo   FB OTP Generator - Build Installer
echo ========================================
echo.

REM Kill any running backend processes
echo Stopping any running backend processes...
taskkill /F /IM fb-backend.exe 2>nul
timeout /t 1 /nobreak >nul

cd C:\WORKSHOP\PRODUCTION\fb-solution

echo [1/4] Installing Python build dependencies...
cd fbpanel
pip install -r requirements-build.txt
if errorlevel 1 (
    echo Failed to install Python dependencies!
    pause
    exit /b 1
)

echo.
echo [2/4] Building Python backend...
python build_backend.py
if errorlevel 1 (
    echo Failed to build backend!
    pause
    exit /b 1
)

cd ..\client

echo.
echo [3/4] Installing Node.js dependencies and building frontend...
if not exist "node_modules" (
    echo Installing npm packages...
    call npm install
    if errorlevel 1 (
        echo Failed to install Node.js dependencies!
        pause
        exit /b 1
    )
)

echo Building frontend...
call npm run build:web
if errorlevel 1 (
    echo Failed to build frontend!
    pause
    exit /b 1
)

echo.
echo [4/4] Copying backend and creating installer...
call npm run copy:backend
if errorlevel 1 (
    echo Failed to copy backend!
    pause
    exit /b 1
)

echo.
echo Building final installer with electron-builder...
call npm run build:installer
if errorlevel 1 (
    echo Failed to create installer!
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
