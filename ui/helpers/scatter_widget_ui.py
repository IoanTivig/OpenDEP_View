import random

from src.func.general import *

from PyQt5.QtWidgets import QWidget, QPushButton, QColorDialog, QFileDialog, QHeaderView, QLineEdit
from PyQt5.uic import loadUi


# Create a classes to handle the widget that will be spawn when the user wants to add a curve to the graph
class ScatterWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/scatter_widget.ui", self)

        # Varaibles
        self.parent_widget = None
        self.id = None
        self.line_edits_dict = {}

        # Some initial setup
        self.collapse(collapse=True)

        # Connect the buttons to the functions
        self.pyqt5_checkbox_curves_expand.clicked.connect(self.collapse)
        self.pyqt5_checkbox_curves_expand.setChecked(True)

        # Connect the buttons to the functions
        self.pyqt5_button_point_add.clicked.connect(self.spawn_line_edits)

    def collapse(self, collapse=True):
        if collapse:
            self.pyqt5_frame_group_parameters.setVisible(False)
        else:
            self.pyqt5_frame_group_parameters.setVisible(True)

    def spawn_line_edits(self):
        # Create QLineEdit widgets
        frequency_edit = QLineEdit(self)
        re_cm_edit = QLineEdit(self)
        error_edit = QLineEdit(self)

        # Use default_entry.qss style from the ui folder
        frequency_edit.setStyleSheet(open("ui/styles/entries/default_entry.qss").read())
        re_cm_edit.setStyleSheet(open("ui/styles/entries/default_entry.qss").read())
        error_edit.setStyleSheet(open("ui/styles/entries/default_entry.qss").read())

        # Add QLineEdit widgets to the grid layout
        row_position = self.pyqt5_grid_data_points.rowCount()
        self.pyqt5_grid_data_points.addWidget(frequency_edit, row_position, 0)
        self.pyqt5_grid_data_points.addWidget(re_cm_edit, row_position, 1)
        self.pyqt5_grid_data_points.addWidget(error_edit, row_position, 2)

        # Generate a unique id for this set of QLineEdit widgets
        id = row_position

        # Store QLineEdit widgets in a dictionary
        self.line_edits_dict[id] = [frequency_edit, re_cm_edit, error_edit]
