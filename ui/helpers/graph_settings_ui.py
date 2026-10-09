from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import QDialog, QGraphicsDropShadowEffect, QColorDialog, QSpinBox, QDoubleSpinBox, QComboBox, \
    QCheckBox
from PyQt6.uic import loadUi

from src.func.general import get_all_os_fonts

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
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

        # Add Transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Add a shadow effect, on the inner frame (drawn in the window's transparent margin). A graphics effect on
        # the window itself leaves the window blank when it is opened again, which blocks the program
        shadow = QGraphicsDropShadowEffect(self.verticalFrame)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 75))  # Black color with some transparency
        self.verticalFrame.setGraphicsEffect(shadow)

    def connect_buttons(self):
        self.qt_button_back.clicked.connect(self.exit)
        self.qt_button_update_graph_styling.clicked.connect(
            self.parent_widget.update_graph_styling
        )

    def exit(self):
        self.close()

    def open_graph_settings(self):
        self.exec()

    def populate_fonts(self):
        font_list = get_all_os_fonts()
        self.qt_combo_font_family.clear()
        self.qt_combo_font_family.addItems(font_list)

    # Values of all settings, by widget name (saved in the project)
    def get_values(self):
        values = {}
        for widget in self.findChildren((QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox)):
            if not widget.objectName().startswith("qt_"):
                continue
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                values[widget.objectName()] = widget.value()
            elif isinstance(widget, QComboBox):
                values[widget.objectName()] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                values[widget.objectName()] = widget.isChecked()

        return values

    # Restore the settings saved in a project (unknown names and values missing from a list are skipped)
    def set_values(self, values):
        for name, value in values.items():
            widget = self.findChild((QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox), name)
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))