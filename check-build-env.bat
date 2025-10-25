@echo off
REM Quick verification script to check if everything is ready for building

echo ========================================
echo   Build Environment Check
echo ========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found!
    goto :error
)
echo [OK] Python found
echo.

echo Checking pip...
pip --version
if errorlevel 1 (
    echo [ERROR] pip not found!
    goto :error
)
echo [OK] pip found
echo.

echo Checking Node.js...
node --version
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    goto :error
)
echo [OK] Node.js found
echo.

echo Checking npm...
npm --version
if errorlevel 1 (
    echo [ERROR] npm not found!
    goto :error
)
echo [OK] npm found
echo.

cd C:\WORKSHOP\PRODUCTION\fb-solution

echo Checking Python dependencies...
cd fbpanel
python -c "import fastapi; import uvicorn; import playwright; import pyinstaller; print('[OK] All Python packages installed')" 2>nul
if errorlevel 1 (
    echo [WARNING] Some Python packages missing. Installing...
    pip install -r requirements.txt
    pip install -r requirements-build.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python packages!
        goto :error
    )
)
echo.

echo Checking Playwright browsers...
python -c "import os; browsers = 'playwright-browsers'; print(f'[OK] Playwright browsers folder exists' if os.path.exists(browsers) else '[WARNING] Run: playwright install chromium')"
echo.

cd ..\client

echo Checking Node dependencies...
if not exist "node_modules" (
    echo [WARNING] node_modules not found. Run: npm install
) else (
    echo [OK] node_modules exists
)
echo.

echo Checking if backend is built...
if exist "..\fbpanel\dist\fb-backend.exe" (
    echo [OK] Backend executable exists
) else (
    echo [WARNING] Backend not built. Will build during installer creation.
)
echo.

echo Checking if frontend is built...
if exist "out" (
    echo [OK] Frontend build exists
) else (
    echo [WARNING] Frontend not built. Will build during installer creation.
)
echo.

echo ========================================
echo   All Checks Complete!
echo ========================================
echo.
echo Ready to build? Run: build-installer.bat
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo   Setup Incomplete!
echo ========================================
echo Please install missing dependencies and try again.
pause
exit /b 1
