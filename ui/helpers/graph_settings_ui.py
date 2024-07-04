from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi


# Create a class to handle the graph settings UI

class GraphSettingsUI(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi("ui/graph_settings.ui", self)
        self.setWindowTitle("Graph Settings")
        self.setWindowIcon(QIcon("icon.png"))

    def show_graph_settings(self):
        self.show()

    def close_graph_settings(self):
        self.close()