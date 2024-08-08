from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect
from PyQt5.uic import loadUi


# Create a classes to handle the graph settings UI

class GraphSettingsUI(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi("ui/graph_settings_widget.ui", self)

        # Initial setup
        self.style_window()

        # Varaibles
        self.parent_widget = parent

        # Connect buttons
        self.connect_buttons()

    def style_window(self):
        # Remove the title bar, logo, and exit button
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Add Transparency
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Add a shadow effect
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 75))  # Black color with some transparency
        self.setGraphicsEffect(shadow)

    def connect_buttons(self):
        self.pyqt5_button_back.clicked.connect(self.exit)

    def exit(self):
        self.close()

    def open_graph_settings(self):
        self.exec_()