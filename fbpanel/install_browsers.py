"""
Install Playwright browsers for the packaged application
Run this script after building the .exe to download browsers to the correct location
"""
import os
import sys
import subprocess

# Set browsers path to be alongside the .exe
if getattr(sys, 'frozen', False):
    # Running as .exe
    BROWSERS_PATH = os.path.join(os.path.dirname(sys.executable), 'playwright-browsers')
else:
    # Running as script
    BROWSERS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'playwright-browsers')

print("="*60)
print("Playwright Browser Installer")
print("="*60)
print(f"Installing browsers to: {BROWSERS_PATH}")
print()

# Set environment variable
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = BROWSERS_PATH

try:
    # Install Chromium only (we don't need Firefox and WebKit)
    print("Installing Chromium browser...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    
    print()
    print("="*60)
    print("✅ Browser installation completed successfully!")
    print(f"📁 Browsers installed in: {BROWSERS_PATH}")
    print("="*60)
except subprocess.CalledProcessError as e:
    print()
    print("="*60)
    print("❌ Browser installation failed!")
    print(f"Error: {e}")
    print("="*60)
    sys.exit(1)
except Exception as e:
    print()
    print("="*60)
    print("❌ Unexpected error during installation!")
    print(f"Error: {e}")
    print("="*60)
    sys.exit(1)
