import logging
import sys
import threading

from PyQt6.QtCore import Qt, QUrl, QBuffer, QIODevice, QObject, QSettings, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QWidget, QPushButton, QHeaderView, QTableWidgetItem
from PyQt6.uic import loadUi

from src.func import bug_reports, bug_upload

logger = logging.getLogger(__name__)

# Where the tester's website account is kept (the token, never the password)
SERVER_KEY, USER_KEY, TOKEN_KEY = "bug_reports/server", "bug_reports/username", "bug_reports/token"


# WEBSITE CALLS IN THE BACKGROUND
# Runs one website call in a thread; done (the result) or failed (a message for the tester and the HTTP status, 0
# without one) arrive in the GUI thread, because this object lives there
class NetworkCall(QObject):
    done = pyqtSignal(object)
    failed = pyqtSignal(str, int)

    def __init__(self, function, *args):
        QObject.__init__(self)
        self.function = function
        self.args = args

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        try:
            result = self.function(*self.args)
        except bug_upload.UploadError as e:
            self.failed.emit(str(e), e.status)
        except Exception as e:                       # a background call must never raise unhandled
            logger.exception("Website call failed")
            self.failed.emit(f"Unexpected error: {e}", 0)
        else:
            self.done.emit(result)


# Sign in with the tester account the OpenDEP team created; keeps the website's token, not the password
class BugSignInDialogUI(QDialog):
    def __init__(self, parent, settings):
        QDialog.__init__(self, parent)
        loadUi("ui/widgets/bug_sign_in_dialog.ui", self)
        self.settings = settings
        self.call = None
        self.qt_entry_signin_server.setText(str(settings.value(SERVER_KEY, "") or bug_upload.default_server()))
        self.qt_entry_signin_user.setText(str(settings.value(USER_KEY, "") or ""))
        self.qt_button_signin.clicked.connect(self.sign_in)
        self.qt_button_signin_cancel.clicked.connect(self.reject)
        self.qt_entry_signin_password.returnPressed.connect(self.sign_in)
        if self.qt_entry_signin_user.text():
            self.qt_entry_signin_password.setFocus()

    def sign_in(self):
        server = self.qt_entry_signin_server.text().strip()
        user = self.qt_entry_signin_user.text().strip()
        password = self.qt_entry_signin_password.text()
        if not (server and user and password):
            self.qt_label_signin_status.setText("Fill in the website, your user name and your password.")
            return
        self.qt_button_signin.setEnabled(False)
        self.qt_label_signin_status.setText("Signing in …")
        self.call = NetworkCall(bug_upload.sign_in, server, user, password)
        self.call.done.connect(lambda token: self.signed_in(server, user, token))
        self.call.failed.connect(self.failed)
        self.call.start()

    def signed_in(self, server, user, token):
        self.settings.setValue(SERVER_KEY, server)
        self.settings.setValue(USER_KEY, user)
        self.settings.setValue(TOKEN_KEY, token)
        self.qt_entry_signin_password.clear()
        self.accept()

    def failed(self, message, status=0):
        self.qt_label_signin_status.setText(message)
        self.qt_button_signin.setEnabled(True)


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
    def __init__(self, parent=None, reports_folder=bug_reports.REPORTS_FOLDER, settings=None):
        QWidget.__init__(self, parent, Qt.WindowType.Window)
        loadUi("ui/widgets/bug_report_widget.ui", self)

        # Variables
        self.parent_widget = parent
        self.reports_folder = reports_folder
        self.screenshot = None
        # The tester's website account lives in the program's settings (as the recent projects)
        self.settings = settings or getattr(parent, "settings", None) or QSettings("OpenDEP", "OpenDEP View")
        self.call = None

        # Initial setup
        header = self.qt_table_bug_reports.horizontalHeader()
        for column in (0, 1, 2):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.set_error("")

        # Connect buttons
        self.connect_buttons()
        self.qt_button_bug_tab_new.click()
        self.refresh()
        self.update_account()

    def connect_buttons(self):
        self.qt_tab_buttons = self.qt_frame_tabbar_bug.findChildren(QPushButton)
        for button in self.qt_tab_buttons:
            button.clicked.connect(self.toggle_tabs)
        self.qt_button_bug_send.clicked.connect(self.send)
        self.qt_button_bug_account.clicked.connect(self.toggle_account)
        self.qt_button_bug_save.clicked.connect(self.save)
        self.qt_button_bug_close.clicked.connect(self.close)
        self.qt_button_bug_send_selected.clicked.connect(self.send_selected)
        self.qt_button_bug_send_unsent.clicked.connect(self.send_unsent)
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

        self.clear_form()
        self.qt_label_bug_status.setText(f"Saved as bug_reports/{path.name}. Commit and push it when you finish.")
        self.refresh()
        return path

    def clear_form(self):
        for entry in (self.qt_entry_bug_title, self.qt_text_bug_steps, self.qt_text_bug_expected,
                      self.qt_text_bug_actual):
            entry.clear()
        self.set_error("")
        self.qt_checkbox_bug_screenshot.setChecked(False)

    # SENDING TO THE WEBSITE
    # (website, user name, token) of the signed-in tester; an empty token means not signed in
    def account(self):
        return (str(self.settings.value(SERVER_KEY, "") or ""), str(self.settings.value(USER_KEY, "") or ""),
                str(self.settings.value(TOKEN_KEY, "") or ""))

    def update_account(self):
        server, user, token = self.account()
        if token:
            self.qt_label_bug_account.setText(f"Signed in to the OpenDEP website as {user}")
            self.qt_button_bug_account.setText("Sign out")
        else:
            self.qt_label_bug_account.setText("Not signed in to the OpenDEP website")
            self.qt_button_bug_account.setText("Sign in…")

    # Sign in, or sign out (the token is forgotten at once and revoked on the website)
    def toggle_account(self):
        server, user, token = self.account()
        if token:
            self.settings.remove(TOKEN_KEY)
            threading.Thread(target=bug_upload.sign_out, args=(server, token), daemon=True).start()
            self.update_account()
        else:
            self.sign_in()

    # The sign-in window; True when the tester is signed in afterwards
    def sign_in(self):
        signed_in = BugSignInDialogUI(self, self.settings).exec() == QDialog.DialogCode.Accepted
        self.update_account()
        return signed_in

    # Send the report to the website (signing in first if needed); the form is cleared once it arrived
    def send(self):
        report = self.build_report()
        if not report["title"]:
            self.qt_label_bug_status.setText("Give the report a title first.")
            self.qt_entry_bug_title.setFocus()
            return
        if not self.account()[2] and not self.sign_in():
            return
        server, user, token = self.account()
        self.qt_button_bug_send.setEnabled(False)
        self.qt_label_bug_status.setText("Sending …")
        self.call = NetworkCall(bug_upload.send_report, server, token, report)
        self.call.done.connect(self.sent)
        self.call.failed.connect(self.send_failed)
        self.call.start()

    def sent(self, sent):
        self.qt_button_bug_send.setEnabled(True)
        self.clear_form()
        self.qt_label_bug_status.setText(f"Already on the website as report #{sent.number}: not sent again."
                                         if sent.duplicate else f"Sent as report #{sent.number}. Thank you!")

    def send_failed(self, message, status=0):
        self.qt_button_bug_send.setEnabled(True)
        if status == 401:                            # token revoked by the team: sign in again
            self.forget_token()
        self.qt_label_bug_status.setText(f"Not sent: {message} You can also save the report.")

    def forget_token(self):
        self.settings.remove(TOKEN_KEY)
        self.update_account()

    # SENDING SAVED REPORTS
    def selected_paths(self):
        rows = sorted({index.row() for index in self.qt_table_bug_reports.selectionModel().selectedRows()})
        return [self.qt_table_bug_reports.item(row, 0).data(Qt.ItemDataRole.UserRole) for row in rows]

    # The selected saved reports (those already sent are only confirmed by the website, not stored twice)
    def send_selected(self):
        paths = self.selected_paths()
        if not paths:
            self.qt_label_bug_list_status.setText("Select the reports to send (Ctrl or Shift for several).")
            return
        self.send_saved(paths)

    # Every saved report that has no website number yet
    def send_unsent(self):
        paths = [entry["path"] for entry in bug_reports.list_reports(self.reports_folder) if not entry["sent_as"]]
        if not paths:
            self.qt_label_bug_list_status.setText("Every saved report is already on the OpenDEP website.")
            return
        self.send_saved(paths)

    # Send saved reports one by one in the background (signing in first if needed)
    def send_saved(self, paths):
        if not self.account()[2] and not self.sign_in():
            return
        server, user, token = self.account()
        for button in (self.qt_button_bug_send_selected, self.qt_button_bug_send_unsent):
            button.setEnabled(False)
        self.qt_label_bug_list_status.setText(f"Sending {len(paths)} report{'s' if len(paths) > 1 else ''} …")
        self.call = NetworkCall(bug_upload.send_saved, server, token, paths)
        self.call.done.connect(self.saved_sent)
        self.call.failed.connect(self.saved_failed)
        self.call.start()

    def saved_sent(self, results):
        for button in (self.qt_button_bug_send_selected, self.qt_button_bug_send_unsent):
            button.setEnabled(True)
        if any(result["status"] == 401 for result in results):     # token revoked by the team
            self.forget_token()
        self.refresh()
        if results:
            self.qt_label_bug_list_status.setText(bug_upload.summary(results))

    def saved_failed(self, message, status=0):
        self.saved_sent([])
        self.qt_label_bug_list_status.setText(f"Not sent: {message}")

    # SAVED REPORTS
    def refresh(self):
        entries = bug_reports.list_reports(self.reports_folder)
        self.qt_table_bug_reports.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            date = QTableWidgetItem(entry["date"])
            date.setData(Qt.ItemDataRole.UserRole, str(entry["path"]))
            self.qt_table_bug_reports.setItem(row, 0, date)
            self.qt_table_bug_reports.setItem(row, 1, QTableWidgetItem(entry["status"]))
            self.qt_table_bug_reports.setItem(row, 2, QTableWidgetItem(f"#{entry['sent_as']}" if entry["sent_as"]
                                                                       else ""))
            self.qt_table_bug_reports.setItem(row, 3, QTableWidgetItem(entry["title"]))

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
