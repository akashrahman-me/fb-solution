# Runtime hook to help Playwright find bundled browser binaries when packaged with PyInstaller
# This sets PLAYWRIGHT_BROWSERS_PATH to the "playwright-browsers" folder next to the executable.

import os
import sys
from pathlib import Path

try:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
except Exception:
    base_dir = Path.cwd()

browsers_dir = base_dir / "playwright-browsers"
if browsers_dir.exists():
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)

