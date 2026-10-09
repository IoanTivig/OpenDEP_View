from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QListWidgetItem
from PyQt6.uic import loadUi

LOGO = ":/ui/qt/resources/logos/opendep_symbol_crop.png"


# Logo of the OpenDEP symbol, sharp on high-DPI screens
def set_logo(label, height):
    ratio = label.devicePixelRatioF() or 1.0
    pixmap = QPixmap(LOGO).scaledToHeight(round(height * ratio), Qt.TransformationMode.SmoothTransformation)
    pixmap.setDevicePixelRatio(ratio)
    label.setPixmap(pixmap)


# Welcome screen shown while no project is open: create, open or reopen a recent project
class WelcomeWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/widgets/welcome_widget.ui", self)

        # Variables
        self.parent_widget = parent

        set_logo(self.qt_label_welcome_logo, 48)

        # Connect buttons
        self.connect_buttons()

    def connect_buttons(self):
        self.qt_button_welcome_create.clicked.connect(self.parent_widget.new_project)
        self.qt_button_welcome_open.clicked.connect(self.parent_widget.open_project_dialog)
        self.qt_list_recent_projects.itemActivated.connect(
            lambda item: self.parent_widget.open_project(item.data(Qt.ItemDataRole.UserRole)))

    def set_recent_projects(self, paths):
        self.qt_list_recent_projects.clear()
        for path in paths:
            item = QListWidgetItem(f"{Path(path).name}   —   {path}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.qt_list_recent_projects.addItem(item)

        self.qt_list_recent_projects.setVisible(len(paths) > 0)
        self.qt_label_welcome_no_recent.setVisible(len(paths) == 0)
