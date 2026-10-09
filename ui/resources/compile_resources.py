import re
import subprocess
import sys
from pathlib import Path

'''
Compile graphical_resources.qrc into graphical_resources.py (icons and images used by the .ui files as ":/...").

PyQt6 has no pyrcc anymore, so Qt's own resource compiler is used, as shipped with PySide6
(pip install PySide6-Essentials, in any environment - not needed to run OpenDEP View).
The generated module only registers the resource data in Qt, so swapping its PySide6 import for PyQt6 is enough.

Usage (from the project root):
    python ui/resources/compile_resources.py [path/to/pyside6-rcc]
Run it again every time graphical_resources.qrc or one of its images changes.
'''

# Paths
RESOURCES_FOLDER = Path(__file__).resolve().parent
QRC_FILE = RESOURCES_FOLDER / "graphical_resources.qrc"
PY_FILE = RESOURCES_FOLDER / "graphical_resources.py"


def compile_resources(rcc="pyside6-rcc"):
    # Run Qt's resource compiler, Python output
    result = subprocess.run([rcc, "-g", "python", str(QRC_FILE)], capture_output=True, text=True, cwd=RESOURCES_FOLDER)
    if result.returncode != 0:
        sys.exit(f"rcc failed: {result.stderr}")

    # Use PyQt6 instead of PySide6 for the registration of the resources
    code = re.sub(r"^from PySide6 import QtCore$", "from PyQt6 import QtCore", result.stdout, flags=re.MULTILINE)
    if "from PyQt6 import QtCore" not in code:
        sys.exit("Unexpected rcc output: the PySide6 import was not found")

    PY_FILE.write_text(code, encoding="utf-8")
    print(f"Written {PY_FILE.name} ({len(code) / 1e6:.1f} MB)")


if __name__ == "__main__":
    compile_resources(sys.argv[1] if len(sys.argv) > 1 else "pyside6-rcc")
