"""
Build script for Facebook Number Checker
Creates a Windows executable using PyInstaller with Playwright support
"""
import os
import sys
import shutil
import subprocess
import pathlib

PLAYWRIGHT_BROWSERS_DIR = "playwright-browsers"


def get_playwright_browsers_path():
    """Get the path where Playwright driver lives (optional add-data)."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "from playwright.driver import compute_driver_executable; print(compute_driver_executable())"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            driver_path = result.stdout.strip()
            playwright_dir = pathlib.Path(driver_path).parent
            return str(playwright_dir)
    except Exception:
        pass

    # Fallback: check common locations
    try:
        import site
        site_packages = site.getsitepackages()[0]
        playwright_path = os.path.join(site_packages, "playwright", "driver")
        if os.path.exists(playwright_path):
            return playwright_path
    except Exception:
        pass

    return None


def install_playwright_browsers(target_dir: str) -> bool:
    """Install Playwright Chromium into target_dir and return True if present."""
    abs_target = os.path.abspath(target_dir)
    os.makedirs(abs_target, exist_ok=True)

    # Set env so playwright installs browsers into our folder
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = abs_target

    print(f"Installing Playwright Chromium into: {abs_target}")
    try:
        # Ensure playwright is installed
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        # Install Chromium browser
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to preinstall Chromium (exit {e.returncode}). The app may try at runtime.")

    # Verify
    has_browsers = any(os.scandir(abs_target))
    print(f"Playwright browsers present: {has_browsers}")
    return has_browsers


def clean_build_folders():
    """Remove old build folders"""
    folders_to_clean = ['build', 'dist', '__pycache__']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            try:
                shutil.rmtree(folder)
            except PermissionError:
                print(f"Warning: Could not delete {folder} (files may be in use)")
                print(f"Please close any running instances and try again.")
                return False

    # Remove .spec file if exists
    if os.path.exists('FacebookChecker.spec'):
        try:
            os.remove('FacebookChecker.spec')
        except PermissionError:
            pass

    return True


def build_executable():
    """Build the executable using PyInstaller"""
    print("\n" + "="*50)
    print("Building Facebook Number Checker executable...")
    print("="*50 + "\n")

    # Preinstall Playwright Chromium into local bundle folder
    browsers_installed = install_playwright_browsers(PLAYWRIGHT_BROWSERS_DIR)

    # Optional driver path add-data
    playwright_path = get_playwright_browsers_path()

    # Use os.pathsep for PyInstaller's --add-data (Windows uses ';')
    sep = ';' if sys.platform == 'win32' else ':'

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=FacebookChecker',
        '--onedir',  # Prefer onedir for Playwright
        '--windowed',
        '--icon=NONE',
        f'--add-data=main.py{sep}.',
        f'--add-data=proxy_injector.py{sep}.',
        f'--add-data=utils{sep}utils',
        '--hidden-import=customtkinter',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=proxy_injector',
        '--hidden-import=playwright',
        '--collect-all=customtkinter',
        '--collect-all=playwright',
        # Runtime hook to point Playwright at bundled browsers
        f'--runtime-hook=rthooks/pyi_rth_playwright_browsers.py',
        'gui.py'
    ]

    # Add bundled browsers folder to data
    if browsers_installed and os.path.isdir(PLAYWRIGHT_BROWSERS_DIR):
        cmd.insert(-1, f'--add-data={PLAYWRIGHT_BROWSERS_DIR}{sep}{PLAYWRIGHT_BROWSERS_DIR}')

    # Add Playwright driver (optional)
    if playwright_path and os.path.exists(playwright_path):
        print(f"Found Playwright driver at: {playwright_path}")
        cmd.insert(-1, f'--add-data={playwright_path}{sep}playwright/driver')

    try:
        # Run PyInstaller using python -m to avoid path issues
        print("Running PyInstaller...")
        cmd_with_python = [sys.executable, '-m', 'PyInstaller'] + cmd[1:]
        result = subprocess.run(cmd_with_python, check=True)

        # Check if build succeeded by looking for the exe
        exe_path = os.path.abspath('dist/FacebookChecker/FacebookChecker.exe')
        if os.path.exists(exe_path):
            print("\n" + "="*50)
            print("✓ Build successful!")
            print(f"Executable location: {exe_path}")
            print("="*50)

            # Create a simple README with instructions
            create_readme(browsers_installed)

            return True
        else:
            print("\n" + "="*50)
            print("✗ Build failed - executable not created")
            print("="*50)
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("\n✗ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("Please run the build script again.")
        return False


def create_readme(browsers_bundled: bool):
    """Create a simple README file with clear setup instructions"""
    if browsers_bundled:
        readme_content = """Facebook Account Checker - Setup Instructions
================================================

The required Chromium browser for Playwright is bundled. No extra setup is needed.

How to run:
1. Open the folder: dist\\FacebookChecker
2. Run: FacebookChecker.exe

Troubleshooting:
- If the browser still does not open, ensure your antivirus did not quarantine any files.
- If needed, you can force reinstall browsers locally:
    python -m playwright install chromium
"""
    else:
        readme_content = """Facebook Account Checker - Setup Instructions
================================================

IMPORTANT: One-time browser setup may be required on first run.

If the browser does not open:
1. Open Command Prompt
2. Run:
    pip install playwright
    python -m playwright install chromium
3. Re-run FacebookChecker.exe
"""

    readme_path = os.path.join("dist", "FacebookChecker", "README.txt")
    os.makedirs(os.path.dirname(readme_path), exist_ok=True)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"Created instructions file: {readme_path}")


if __name__ == "__main__":
    print("Facebook Number Checker - Build Script")
    print("="*50)

    # Clean old builds
    if not clean_build_folders():
        input("\nCould not clean build folders. Please close any running instances and press Enter to exit...")
        sys.exit(1)

    # Build
    success = build_executable()

    if success:
        print("\n✓ Done! Distribution package created in 'dist\\FacebookChecker' folder.")
        print("\nNext steps:")
        print("1. Run dist\\FacebookChecker\\FacebookChecker.exe")
        print("2. Distribute the entire 'FacebookChecker' folder.")

    input("\nPress Enter to exit...")
