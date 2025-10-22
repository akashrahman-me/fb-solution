"""
Build script for Facebook Number Checker
Creates a Windows executable using PyInstaller
"""
import os
import sys
import shutil
import subprocess

def clean_build_folders():
    """Remove old build folders"""
    folders_to_clean = ['build', 'dist', '__pycache__']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder)

    # Remove .spec file if exists
    if os.path.exists('FacebookChecker.spec'):
        os.remove('FacebookChecker.spec')

def build_executable():
    """Build the executable using PyInstaller"""
    print("\n" + "="*50)
    print("Building Facebook Number Checker executable...")
    print("="*50 + "\n")

    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=FacebookChecker',
        '--onefile',
        '--windowed',
        '--icon=NONE',
        '--add-data=main.py;.',
        '--add-data=proxy_injector.py;.',
        '--add-data=utils;utils',
        '--hidden-import=customtkinter',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=proxy_injector',
        '--collect-all=customtkinter',
        '--collect-all=playwright',
        'gui.py'
    ]

    try:
        # Run with output capture for better error reporting
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Check if build succeeded by looking for the exe
        exe_path = os.path.abspath('dist/FacebookChecker.exe')
        if os.path.exists(exe_path):
            print("\n" + "="*50)
            print("✓ Build successful!")
            print(f"Executable location: {exe_path}")
            print("="*50)
            return True
        else:
            print("\n" + "="*50)
            print("✗ Build failed - executable not created")
            print("="*50)
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print("\n✗ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("Please run the build script again.")
        return False

if __name__ == "__main__":
    print("Facebook Number Checker - Build Script")
    print("="*50)

    # Build
    success = build_executable()

    if success:
        print("\n✓ Done! You can find the executable in the 'dist' folder.")
        print("\nNext steps:")
        print("1. Test the executable: dist\\FacebookChecker.exe")
        print("2. Create installer (optional): Use Inno Setup with installer_script.iss")

    input("\nPress Enter to exit...")
