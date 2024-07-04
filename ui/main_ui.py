from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.uic import loadUi
from matplotlib.figure import Figure

from ui.resources import graphical_resources
from ui.helpers.graph_settings_ui import GraphSettingsUI

'''
OpenDEP View
    Copyright (C) 2024  Ioan Cristian Tivig

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    You can contact the developer/owner of OpenDEP at "ioan.tivig@gmail.com".
'''

class MainUI(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("ui/main.ui", self)
        self.setWindowTitle("OpenDEP Force Calculator")
        self.setWindowIcon(QIcon("icon.png"))

        self.graph_settings = GraphSettingsUI()

        self.pyqt5_button_save_figure.clicked.connect(self.pyqt5_graph_widget.save_figure)
        self.pyqt5_button_home_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.home)
        self.pyqt5_button_zoom_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.zoom)
        self.pyqt5_button_properties_figure.clicked.connect(self.open_graph_settings)
        self.pyqt5_button_fitspace_figure.clicked.connect(self.pyqt5_graph_widget.set_tight_layout)
        self.pyqt5_button_resize_figure.clicked.connect(self.resize_graph)

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        # Check if self.pyqt5_graph_widget is resized
        if self.pyqt5_graph_widget.size() != event.oldSize():
            self.pyqt5_graph_widget.set_tight_layout()

    def resize_graph(self):
        # Get Height of the graph
        height = int(self.pyqt5_widget_frame.height())
        # Set width of the graph to 16:9 ratio
        width = int(height * 1 / 1)
        # Set current height and width of the graph
        self.pyqt5_widget_frame.resize(width, height)
        self.pyqt5_graph_widget.set_tight_layout()

    def open_graph_settings(self):
        self.graph_settings.show_graph_settings()

