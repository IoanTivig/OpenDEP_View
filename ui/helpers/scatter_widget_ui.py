import random

from src.func.general import *

from PyQt5.QtWidgets import QWidget, QPushButton, QColorDialog, QFileDialog, QHeaderView
from PyQt5.uic import loadUi


# Create a classes to handle the widget that will be spawn when the user wants to add a curve to the graph
class ScatterWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/scatter_widget.ui", self)

        # Varaibles
        self.parent_widget = None
        self.id = None

        # Some initial setup
        self.collapse(collapse=True)
        self.update_table_size()

        # Connect the buttons to the functions
        self.pyqt5_checkbox_curves_expand.clicked.connect(self.collapse)
        self.pyqt5_checkbox_curves_expand.setChecked(True)


    def collapse(self, collapse=True):
        if collapse:
            self.pyqt5_frame_group_parameters.setVisible(False)
        else:
            self.pyqt5_frame_group_parameters.setVisible(True)

    def update_table_size(self):
        self.pyqt5_table_scatter_points.resizeRowsToContents()
