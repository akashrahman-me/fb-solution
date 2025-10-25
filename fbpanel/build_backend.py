#!/usr/bin/env python3
"""
Build script to create standalone Python backend executable
"""
import os
import sys
import shutil
import subprocess
import time

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ PyInstaller found: {result.stdout.strip()}")
            return True
    except Exception:
        pass
    
    print("❌ PyInstaller not found!")
    print("\nPlease install it with:")
    print(f"  {sys.executable} -m pip install pyinstaller")
    return False

def main():
    print("🔨 Building Python Backend Executable...")
    print()
    
    # Check PyInstaller
    if not check_pyinstaller():
        sys.exit(1)
    
    print()
    
    # Kill any running fb-backend processes
    print("🛑 Checking for running backend processes...")
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "fb-backend.exe"],
            capture_output=True,
            timeout=5
        )
        print("✓ Stopped running backend processes")
    except:
        pass  # No processes to kill or taskkill not available
    
    # Clean previous builds
    if os.path.exists("dist"):
        print("🧹 Cleaning old dist/")
        try:
            shutil.rmtree("dist")
        except PermissionError:
            print("⚠️  Could not delete dist folder (file in use). Trying to continue...")
            time.sleep(2)
            try:
                shutil.rmtree("dist")
            except:
                print("❌ Failed to clean dist folder. Please close any running fb-backend.exe")
                sys.exit(1)
                
    if os.path.exists("build"):
        print("🧹 Cleaning old build/")
        try:
            shutil.rmtree("build")
        except:
            pass  # Build folder is less critical
    
    print()
    
    # Create directories if they don't exist
    os.makedirs("cookies", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # Check if Playwright browsers are installed
    print("🌐 Checking Playwright browsers...")
    playwright_browsers_path = os.path.join(os.getcwd(), 'playwright-browsers')
    chromium_path = os.path.join(playwright_browsers_path, 'chromium-1187')  # Adjust version as needed
    
    if not os.path.exists(playwright_browsers_path) or not os.listdir(playwright_browsers_path):
        print("📥 Playwright browsers not found. Installing...")
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = playwright_browsers_path
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            print("✅ Chromium installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Chromium: {e}")
            print("Please run: python -m playwright install chromium")
            sys.exit(1)
    else:
        print(f"✅ Playwright browsers found at: {playwright_browsers_path}")
    
    print()
    
    # PyInstaller command with all necessary imports
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=fb-backend",
        "--onefile",
        "--console",
        "--add-data=cookies;cookies",
        "--add-data=results;results",
        f"--add-data={playwright_browsers_path};playwright-browsers",  # Include browsers in the exe
        # Main modules
        "--hidden-import=main",
        "--hidden-import=server",
        "--hidden-import=proxy_injector",
        "--hidden-import=PhoneNumberFilter",
        # Utils package
        "--hidden-import=utils",
        "--hidden-import=utils.normalize_text",
        "--hidden-import=utils.parse_ip_data",
        # Playwright
        "--hidden-import=playwright",
        "--hidden-import=playwright.sync_api",
        "--hidden-import=playwright._impl._driver",
        "--collect-all=playwright",
        # FastAPI and dependencies
        "--hidden-import=fastapi",
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=pydantic",
        "--hidden-import=starlette",
        # Other dependencies
        "--hidden-import=cryptography",
        "--hidden-import=cryptography.fernet",
        "--collect-submodules=uvicorn",
        "--collect-submodules=fastapi",
        "--collect-submodules=starlette",
        # Entry point
        "server.py"
    ]
    
    print("🔧 Building executable...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    print()
    if result.returncode == 0:
        exe_path = os.path.abspath("dist/fb-backend.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print("=" * 50)
            print("✅ Backend executable built successfully!")
            print(f"📦 Location: {exe_path}")
            print(f"📊 Size: {size_mb:.1f} MB")
            print("=" * 50)
            print()
            print("⚠️  IMPORTANT: Playwright Browser Installation Required")
            print("=" * 50)
            print("Before running the .exe, you must install Playwright browsers.")
            print("Run this command:")
            print()
            print("    python install_browsers.py")
            print()
            print("This will download Chromium browser to the correct location.")
            print("The browsers will be installed in: playwright-browsers/")
            print("=" * 50)
        else:
            print("❌ Build completed but executable not found!")
            sys.exit(1)
    else:
        print("=" * 50)
        print("❌ Build failed!")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
