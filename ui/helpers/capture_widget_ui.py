import os

import numpy as np
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QGraphicsDropShadowEffect, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUi

from src.func import general, image_export


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
        self.qt_entry_image_path.setText(os.path.expanduser("~/Desktop"))

        # Lock to integer only
        general.lock_entry_to_int(self.qt_entry_image_width)
        general.lock_entry_to_int(self.qt_entry_image_height)

    def connect_buttons(self):
        self.qt_button_image_close.clicked.connect(self.exit)
        self.qt_button_load_path.clicked.connect(self.load_path)
        self.qt_button_image_save.clicked.connect(self.save_image)

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

    def load_path(self):
        # Open File Dialog
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')

        if folder_path:
            self.qt_entry_image_path.setText(folder_path)

    def save_image(self):
        # Get the path
        path = self.qt_entry_image_path.text()
        # Get the name
        name = self.qt_entry_image_name.text()
        # Get the format
        format = self.qt_combo_image_format.currentText()
        # Get the DPI
        dpi = int(self.qt_combo_image_dpi.currentText())
        # Get the size: a fixed one in pixels, or the graph's own (drawn at the chosen DPI)
        size_px = None
        if self.qt_checkbox_size_fixed.isChecked():
            size_px = (int(self.qt_entry_image_width.text()), int(self.qt_entry_image_height.text()))
        # Save the image, drawn at its final size (see image_export.py)
        graph = self.parent_widget.qt_graph_widget
        try:
            size = image_export.save_figure_image(graph.figure, f"{path}/{name}.{format.lower()}", dpi, size_px,
                                                  grayscale=self.qt_combo_image_color.currentText() == "Grayscale")
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "Save image", f"The image could not be saved:\n{e}")
            return None
        finally:
            graph.canvas.draw()                      # the graph on screen as before
        return size

    def open_widget(self):
        self.exec()

    def exit(self):
        self.close()
