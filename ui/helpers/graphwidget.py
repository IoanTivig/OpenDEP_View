# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------

### START IMPORTS ###
## PyQt5 imports ##
from PyQt5.QtWidgets import *


## Matplotlib imports ##
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.ticker import StrMethodFormatter
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.patches import Rectangle
### END IMPORTS ###


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.figure = plt.figure(figsize=(10., 10.))
        # Set tight layout
        self.figure.tight_layout()

        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.axes.set_xlabel('Frequency (Hz)', labelpad=5)
        self.canvas.axes.set_ylabel('CM factor', labelpad=5)
        self.canvas.axes.tick_params(labelsize='small')
        self.canvas.axes.grid(which='major', axis='both', color='lightgrey', linestyle='--')
        self.canvas.axes.yaxis.set_major_formatter(StrMethodFormatter('{x:,.3f}'))

        self.setLayout(layout)

    def save_figure(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save figure", "", "PNG (*.png);;JPEG (*.jpeg);;SVG (*.svg);;PDF (*.pdf)")

        if file_path:
            # save the figure at 300 dpi
            self.figure.savefig(file_path, dpi=300)


    def set_tight_layout(self):
        self.figure.tight_layout()
        self.canvas.draw()


    def refresh_UI(self):
        self.canvas.axes.clear()


        self.canvas.draw()
