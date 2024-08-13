import os

import numpy as np
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from PIL import Image

from src.func import general


class CaptureWidgetUI(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi("ui/widgets/capture_widget.ui", self)

        # Initial setup
        self.style_window()

        # Varaibles
        self.parent_widget = parent
        self.selected_curve_id = None

        # Connect buttons
        self.connect_buttons()

        # Set the default path as desktop of user
        self.pyqt5_entry_image_path.setText(os.path.expanduser("~/Desktop"))

        # Lock to integer only
        general.lock_entry_to_int(self.pyqt5_entry_image_width)
        general.lock_entry_to_int(self.pyqt5_entry_image_height)

    def connect_buttons(self):
        self.pyqt5_button_image_close.clicked.connect(self.exit)
        self.pyqt5_button_load_path.clicked.connect(self.load_path)
        self.pyqt5_button_image_save.clicked.connect(self.save_image)

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

    def load_path(self):
        # Open File Dialog
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')

        if folder_path:
            self.pyqt5_entry_image_path.setText(folder_path)

    def save_image(self):
        # Get the path
        path = self.pyqt5_entry_image_path.text()
        # Get the name
        name = self.pyqt5_entry_image_name.text()
        # Get the format
        format = self.pyqt5_combo_image_format.currentText()
        # Get the DPI
        dpi = int(self.pyqt5_combo_image_dpi.currentText())
        # Get the size
        if self.pyqt5_checkbox_size_fixed.isChecked():
            width = int(self.pyqt5_entry_image_width.text())
            height = int(self.pyqt5_entry_image_height.text())
        else:
            width = int(self.parent_widget.pyqt5_entry_graph_width.text())
            height = int(self.parent_widget.pyqt5_entry_graph_height.text())
        # Save the image
        self.parent_widget.pyqt5_graph_widget.figure.savefig(f"{path}/{name}.{format}",
                                                             dpi=dpi,
                                                             bbox_inches='tight')

        image = Image.open(f"{path}/{name}.{format}")
        if self.pyqt5_combo_image_color.currentText() == "Grayscale":
            image = image.convert("L")
        output_size = (width, height)
        image = image.resize(output_size)
        output_dpi = (dpi, dpi)
        image.save(f"{path}/{name}.{format}", dpi=output_dpi)

    def open_widget(self):
        self.exec_()

    def exit(self):
        self.close()
