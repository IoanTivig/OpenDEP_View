from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect, QColorDialog
from PyQt5.uic import loadUi

from src.func.general import get_all_os_fonts
import json

# Create a classes to handle the graph settings UI


class GraphSettingsUI(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi("ui/widgets/graph_settings_widget.ui", self)

        # Initial setup
        self.style_window()

        # Varaibles
        self.parent_widget = parent

        # Populate fonts
        self.populate_fonts()

        # Connect buttons
        self.connect_buttons()

        # Shirk to mainimum size
        self.adjustSize()

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
        self.pyqt5_button_update_graph_styling.clicked.connect(
            self.parent_widget.update_graph_styling
        )

    def exit(self):
        self.close()

    def open_graph_settings(self):
        self.exec_()

    def populate_fonts(self):
        font_list = get_all_os_fonts()
        self.pyqt5_combo_font_family.clear()
        self.pyqt5_combo_font_family.addItems(font_list)

    def save_values(self):
        values = {}

        # Iterate over all child widgets of the main window
        for widget in self.findChildren(QDialog):
            if isinstance(widget, QLineEdit):
                values[widget.objectName()] = widget.text()
            elif isinstance(widget, QComboBox):
                values[widget.objectName()] = widget.currentIndex()
            elif isinstance(widget, QCheckBox):
                values[widget.objectName()] = widget.isChecked()

        # Save values to a JSON file
        with open('widget_values.json', 'w') as file:
            json.dump(values, file)

    def load_values(self):
        try:
            # Load values from a JSON file
            with open('widget_values.json', 'r') as file:
                values = json.load(file)

            # Restore the widget values
            for widget in self.findChildren(QDialog):
                if isinstance(widget, QLineEdit):
                    widget.setText(values.get(widget.objectName(), ''))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(values.get(widget.objectName(), 0))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(values.get(widget.objectName(), False))
        except FileNotFoundError:
            pass  # File doesn't exist yet, nothing to load