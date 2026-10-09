import os
import sys
from pathlib import Path

'''
OpenDEP View

    python main.py [<files>]          files: a project (.odvproject) or OpenDEP files to add (.odspec, .odcurve, ...)
    python main.py --self-test [--self-test-data=<spectrum file> --self-test-output=<folder>]   (build check)
'''

SELF_TEST = "--self-test" in sys.argv

# Files given on the command line (double-click on a file, OpenDEP Compute's Send to View), as absolute paths:
# the working folder changes below
FILES = [] if SELF_TEST else [str(Path(arg).resolve()) for arg in sys.argv[1:] if not arg.startswith("-")]


def _arg(name):
    return next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{name}=")), None)


SELF_TEST_DATA = _arg("self-test-data")
SELF_TEST_OUTPUT = _arg("self-test-output")
if SELF_TEST_DATA:
    SELF_TEST_DATA = str(Path(SELF_TEST_DATA).resolve())
if SELF_TEST_OUTPUT:
    SELF_TEST_OUTPUT = str(Path(SELF_TEST_OUTPUT).resolve())

# The program reads ui/, docs/ and its icons relative to its own folder, whoever started it (the installed program:
# the folder PyInstaller unpacked them to)
os.chdir(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) if getattr(sys, "frozen", False)
         else Path(__file__).resolve().parent)

from src.func.bug_reports import install_output_buffer

# Keep the last console and log lines in memory for bug reports (Report bug window)
install_output_buffer()

from PyQt6.QtCore import QEvent, QSettings, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QStyleFactory
from src.classes.instance_link import InstanceServer, send_to_running
from ui.main_ui import MainUI, APP_NAME
from ui.helpers.bug_report_widget_ui import install_crash_handler


# Destroy the window while the application still exists: left to the interpreter's exit, Qt objects are destroyed
# in random order and the finished process sometimes crashed (as in OpenDEP Compute and Neuralnet)
def destroy(widget):
    import gc
    widget.deleteLater()
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)
    gc.collect()


# Build check of the installed / frozen program: the window opens; with data and an output folder, a project file is
# created, a spectrum added, the project saved and read back, and the user guide opened. Exit code 0 = it all worked.
def self_test(app):
    import tempfile
    import traceback
    from src.func import project as project_files
    settings = QSettings(str(Path(tempfile.gettempdir()) / "opendep_view_selftest.ini"), QSettings.Format.IniFormat)
    widget = MainUI(settings=settings)
    widget.show()
    app.processEvents()
    try:
        if not SELF_TEST_DATA or not SELF_TEST_OUTPUT:
            QTimer.singleShot(1500, app.quit)
            return app.exec()
        out = Path(SELF_TEST_OUTPUT)
        try:
            out.mkdir(parents=True, exist_ok=True)
            project = project_files.create_project(out / "project")
            widget.clear_workspace()
            widget.set_project(project)
            if widget.open_files([SELF_TEST_DATA]) != [SELF_TEST_DATA]:
                raise RuntimeError(f"{SELF_TEST_DATA} was not added")
            if not widget.save_project():
                raise RuntimeError("the project was not saved")
            again = project_files.read_project(project["path"])
            if len(again["scatters"]) != 1 or again["missing"]:
                raise RuntimeError(f"project read back with {len(again['scatters'])} scatters, missing {again['missing']}")
            widget.show_help()
            app.processEvents()
            if len(widget.help_widget.qt_browser_help.toPlainText()) < 200:
                raise RuntimeError("user guide not found")
            (out / "ok.txt").write_text(f"project with {len(again['scatters'])} scatter", encoding="utf-8")
            return 0
        except Exception:                               # reported to the smoke test, which fails the build
            traceback.print_exc()
            (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            return 1
    finally:
        if widget.help_widget is not None:
            widget.help_widget.close()
        destroy(widget)


def main():
    # Own taskbar entry and icon on Windows (not Python's when run from source)
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("OpenDEP.View")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("OpenDEP")
    app.setWindowIcon(QIcon("icon.png"))
    # Same widget style as under PyQt5 on Windows: Qt 6's default "windows11" style ignores parts of the style sheets
    # (e.g. the combo box lists are drawn empty). Elsewhere (Linux, macOS) Fusion, which follows the style sheets too.
    app.setStyle("windowsvista" if "windowsvista" in QStyleFactory.keys() else "Fusion")
    if SELF_TEST:
        return self_test(app)

    # One View per user: a View that is already running opens the files, this one ends
    if FILES and send_to_running(FILES):
        return 0

    widget = MainUI()
    widget.show()

    # Files sent by a second start of View or by OpenDEP Compute
    instance_server = InstanceServer(app)
    instance_server.files_received.connect(widget.open_files)
    instance_server.start()
    if FILES:
        widget.open_files(FILES)

    # Unhandled errors open the Report bug window with the traceback filled in
    install_crash_handler(widget.show_bug_report_for_error)
    code = app.exec()
    destroy(widget)
    return code


if __name__ == "__main__":
    sys.exit(main())
