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

        # somte default values
        self.scatter_style = 'area'

        # Create figure with tight layout
        self.figure = plt.figure()

        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.axes.set_xlabel('Frequency (Hz)', labelpad=5)
        plt.xscale('log')
        self.canvas.axes.set_ylabel('CM factor', labelpad=5)
        self.canvas.axes.tick_params(labelsize='small')
        self.canvas.axes.grid(which='major', axis='both', color='lightgrey', linestyle='--')
        self.canvas.axes.yaxis.set_major_formatter(StrMethodFormatter('{x:,.3f}'))

        # Set tight layout
        self.setLayout(layout)

    def save_figure(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save figure", "", "PNG (*.png);;JPEG (*.jpeg);;SVG (*.svg);;PDF (*.pdf)")

        if file_path:
            # save the figure at 300 dpi
            self.figure.savefig(file_path, dpi=100)

    def get_figure_size(self):
        return self.figure.get_size_inches() * self.figure.dpi

    def set_tight_layout(self):
        self.figure.tight_layout()
        self.canvas.draw()

    def update_curve(self, name, color, x_data, y_data, line_width=1.5, line_style='-'):
        self.canvas.axes.plot(x_data, y_data, label=name, color=color, linewidth=line_width, linestyle=line_style)

    def update_scatter(self, name, color, x_data, y_data, y_errors, point_style='o', point_size=5):
        if self.scatter_style == 'scatter':
            self.canvas.axes.scatter(x_data, y_data, label=name, color=color, s=point_size, marker=point_style)
            # Plot error bars under the scatter points
            self.canvas.axes.errorbar(x_data, y_data, yerr=y_errors, fmt='none', ecolor="black", elinewidth=1, capsize=2)

        elif self.scatter_style == 'area':
            y_min = [y_data-y_errors for y_data, y_errors in zip(y_data, y_errors)]
            y_max = [y_data+y_errors for y_data, y_errors in zip(y_data, y_errors)]

            self.canvas.axes.fill_between(x_data, y_min, y_max, color=color, alpha=0.3, label=name)


    def focus_curve(self, name):
        for line in self.canvas.axes.lines:
            if line.get_label() == name:
                # Get line width
                new_line_width = line.get_linewidth() + 1
                line.set_linewidth(new_line_width)
        self.canvas.draw()

    def unfocus_curve(self, name):
        for line in self.canvas.axes.lines:
            if line.get_label() == name:
                new_line_width = line.get_linewidth() - 1
                line.set_linewidth(new_line_width)
        self.canvas.draw()

    def format_graph(self, y_index=0):
        y_labels = ['Re[CM(f)]', 'DEP force (pN)', 'Im[CM(f)]',]

        plt.xscale('log')
        self.canvas.axes.set_xlabel('Frequency (Hz)', labelpad=5)
        self.canvas.axes.set_ylabel(y_labels[y_index], labelpad=5)
        self.canvas.axes.tick_params(labelsize='small')
        self.canvas.axes.grid(which='major', axis='both', color='lightgrey', linestyle='--')
        self.canvas.axes.yaxis.set_major_formatter(StrMethodFormatter('{x:,.3f}'))
        self.figure.tight_layout()

    # Change Experimental plots to area
    def change_scatter_to_area(self):
        self.canvas.axes.clear()
        self.canvas.draw()

    # Change expermiental plots to scatter with stdev
    def change_area_to_scatter(self):
        self.canvas.axes.clear()
        self.canvas.draw()