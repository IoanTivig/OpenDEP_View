import logging
import sys
import threading

from PyQt6.QtCore import Qt, QUrl, QBuffer, QIODevice, QObject, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QPushButton, QHeaderView, QTableWidgetItem
from PyQt6.uic import loadUi

from src.func import bug_reports

logger = logging.getLogger(__name__)


# PNG bytes of a widget as currently drawn (None if it cannot be grabbed)
def widget_png(widget):
    pixmap = widget.grab()
    if pixmap.isNull():
        return None
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(buffer.data())


# Report Bug window: a form for a new report and the list of saved reports (as in OpenDEP Control).
# Not modal, so it can stay open while the problem is reproduced.
class BugReportWidgetUI(QWidget):
    def __init__(self, parent=None, reports_folder=bug_reports.REPORTS_FOLDER):
        QWidget.__init__(self, parent, Qt.WindowType.Window)
        loadUi("ui/widgets/bug_report_widget.ui", self)

        # Variables
        self.parent_widget = parent
        self.reports_folder = reports_folder
        self.screenshot = None

        # Initial setup
        header = self.qt_table_bug_reports.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.set_error("")

        # Connect buttons
        self.connect_buttons()
        self.qt_button_bug_tab_new.click()
        self.refresh()

    def connect_buttons(self):
        self.qt_tab_buttons = self.qt_frame_tabbar_bug.findChildren(QPushButton)
        for button in self.qt_tab_buttons:
            button.clicked.connect(self.toggle_tabs)
        self.qt_button_bug_save.clicked.connect(self.save)
        self.qt_button_bug_close.clicked.connect(self.close)
        self.qt_button_bug_open.clicked.connect(self.open_selected)
        self.qt_button_bug_folder.clicked.connect(self.open_folder)
        self.qt_button_bug_refresh.clicked.connect(self.refresh)
        self.qt_table_bug_reports.itemDoubleClicked.connect(lambda item: self.open_selected())

    def toggle_tabs(self):
        sender = self.sender()
        for button in self.qt_tab_buttons:
            button.setProperty("customState", button == sender)
            button.setStyle(button.style())  # Refresh style to apply property
        self.qt_frame_bug_new.setVisible(sender == self.qt_button_bug_tab_new)
        self.qt_frame_bug_list.setVisible(sender == self.qt_button_bug_tab_list)

    # NEW REPORT
    # Show an empty form (with the error, if any); the screenshot is taken now, before the window covers anything
    def start_report(self, error=""):
        self.screenshot = widget_png(self.parent_widget) if self.parent_widget is not None else None
        self.set_error(error or bug_reports.last_error())
        self.qt_label_bug_status.setText("")
        self.qt_button_bug_tab_new.click()
        self.show()
        self.raise_()
        self.activateWindow()
        self.qt_entry_bug_title.setFocus()

    # A crash while the window is already open: update the error, keep what was typed
    def show_error(self, error):
        if not self.isVisible():
            self.start_report(error)
            return
        self.set_error(error)
        self.qt_button_bug_tab_new.click()
        self.raise_()

    def set_error(self, error):
        self.qt_text_bug_error.setPlainText(error.strip())
        has_error = bool(error.strip())
        self.qt_label_bug_error.setVisible(has_error)
        self.qt_text_bug_error.setVisible(has_error)
        if has_error and not self.qt_entry_bug_title.text().strip():
            self.qt_entry_bug_title.setText(f"Crash: {error.strip().splitlines()[-1]}"[:100])

    # Where the program was when the bug was reported (written in the report header)
    def get_context(self):
        main = self.parent_widget
        if main is None or not hasattr(main, "get_bug_report_context"):
            return {}
        try:
            return main.get_bug_report_context()
        except Exception as e:                       # the report must be saved even if this fails
            return {"context_error": repr(e)}

    def build_report(self):
        attach_output = self.qt_checkbox_bug_output.isChecked()
        return {"title": self.qt_entry_bug_title.text().strip(),
                "steps": self.qt_text_bug_steps.toPlainText(),
                "expected": self.qt_text_bug_expected.toPlainText(),
                "actual": self.qt_text_bug_actual.toPlainText(),
                "error": self.qt_text_bug_error.toPlainText(),
                "output": bug_reports.recent_output() if attach_output else "",
                "context": {key: str(value) for key, value in self.get_context().items()},
                "screenshot_png": self.screenshot if self.qt_checkbox_bug_screenshot.isChecked() else None}

    # Save the report and clear the form for the next one
    def save(self):
        report = self.build_report()
        if not report["title"]:
            self.qt_label_bug_status.setText("Give the report a title first.")
            self.qt_entry_bug_title.setFocus()
            return None

        try:
            path = bug_reports.save_report(report, self.reports_folder)
        except OSError as e:
            logger.error("Could not save the bug report: %s", e)
            self.qt_label_bug_status.setText(f"Could not save the report: {e}")
            return None

        for entry in (self.qt_entry_bug_title, self.qt_text_bug_steps, self.qt_text_bug_expected,
                      self.qt_text_bug_actual):
            entry.clear()
        self.set_error("")
        self.qt_checkbox_bug_screenshot.setChecked(False)
        self.qt_label_bug_status.setText(f"Saved as bug_reports/{path.name}. Commit and push it when you finish.")
        self.refresh()
        return path

    # SAVED REPORTS
    def refresh(self):
        entries = bug_reports.list_reports(self.reports_folder)
        self.qt_table_bug_reports.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            date = QTableWidgetItem(entry["date"])
            date.setData(Qt.ItemDataRole.UserRole, str(entry["path"]))
            self.qt_table_bug_reports.setItem(row, 0, date)
            self.qt_table_bug_reports.setItem(row, 1, QTableWidgetItem(entry["status"]))
            self.qt_table_bug_reports.setItem(row, 2, QTableWidgetItem(entry["title"]))

        n_open = sum(entry["status"] == "open" for entry in entries)
        noun = "report" if len(entries) == 1 else "reports"
        self.qt_label_bug_summary.setText(f"{len(entries)} {noun}, {n_open} open   ·   {self.reports_folder}"
                                          if entries else f"No reports yet   ·   {self.reports_folder}")
        self.qt_button_bug_tab_list.setText(f"Reports ({n_open} open)" if n_open else "Reports")

    def open_selected(self):
        row = self.qt_table_bug_reports.currentRow()
        item = self.qt_table_bug_reports.item(row, 0) if row >= 0 else None
        if item is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(item.data(Qt.ItemDataRole.UserRole)))

    def open_folder(self):
        self.reports_folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.reports_folder)))


# UNHANDLED ERRORS -> report window
# Carries unhandled errors from any thread to the GUI thread
class CrashNotifier(QObject):
    crashed = pyqtSignal(str)


crash_notifier = None


# Record unhandled exceptions and pass them to on_crash (call in the GUI thread, after QApplication exists)
def install_crash_handler(on_crash):
    global crash_notifier
    crash_notifier = CrashNotifier()
    crash_notifier.crashed.connect(on_crash)

    def handle(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        try:
            text = bug_reports.record_error(exc_type, exc_value, exc_tb)
            crash_notifier.crashed.emit(text)
        except Exception:                            # the handler itself must never raise
            pass
        # Also print it (terminal, and the console lines attached to reports)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = handle
    threading.excepthook = lambda args: handle(args.exc_type, args.exc_value, args.exc_traceback)
    return crash_notifier
