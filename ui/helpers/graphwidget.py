# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------

### START IMPORTS ###
## PyQt5 imports ##
from PyQt5.QtWidgets import *


## Matplotlib imports ##
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import StrMethodFormatter, ScalarFormatter, LogFormatterMathtext
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.patches import Rectangle

### END IMPORTS ###


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        # some default values
        self.scatter_style = "area"

        # Create figure with tight layout
        self.figure = plt.figure()

        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.axes.set_xlabel("Frequency (Hz)", labelpad=5)
        plt.xscale("log")
        self.canvas.axes.set_ylabel("CM factor", labelpad=5)
        self.canvas.axes.tick_params(labelsize="small")
        self.canvas.axes.yaxis.set_major_formatter(StrMethodFormatter("{x:,.3f}"))

        # Set tight layout
        self.setLayout(layout)

    def get_figure_size(self):
        return self.figure.get_size_inches() * self.figure.dpi

    def set_tight_layout(self):
        self.figure.tight_layout()
        self.canvas.draw()

    def update_curve(self, name, color, x_data, y_data, line_width=1.5, line_style="-"):
        self.canvas.axes.plot(
            x_data,
            y_data,
            label=name,
            color=color,
            linewidth=line_width,
            linestyle=line_style,
        )

    def update_scatter(
        self, name, color, x_data, y_data, y_errors, point_style="o", point_size=5
    ):
        if self.scatter_style == "scatter":
            self.canvas.axes.scatter(
                x_data,
                y_data,
                label=name,
                color=color,
                zorder=2,
                s=point_size,
                marker=point_style,
            )
            # Plot error bars under the scatter points
            self.canvas.axes.errorbar(
                x_data,
                y_data,
                yerr=y_errors,
                fmt="none",
                ecolor="grey",
                zorder=1,
                elinewidth=0.5,
                capsize=2,
            )

        elif self.scatter_style == "area":
            y_min = [y_data - y_errors for y_data, y_errors in zip(y_data, y_errors)]
            y_max = [y_data + y_errors for y_data, y_errors in zip(y_data, y_errors)]

            self.canvas.axes.fill_between(
                x_data, y_min, y_max, color=color, alpha=0.3, label=name
            )

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

    def format_graph(self, y_index=0, style_params=None):
        # Allways available styling
        y_labels = [
            "Re[CM(f)]",
            "DEP force (pN)",
            "Im[CM(f)]",
        ]
        plt.xscale("log")

        # Axis titles formating
        self.canvas.axes.set_xlabel(
            "Frequency (Hz)",
            fontname=style_params["font_family"],
            labelpad=style_params["axis_style"]["labelpad"],
            fontsize=style_params["axis_style"]["fontsize"],
            fontweight=style_params["axis_style"]["fontweight"],
            fontstyle=style_params["axis_style"]["fontstyle"],
            color=style_params["axis_style"]["color"],
        )

        self.canvas.axes.set_ylabel(
            y_labels[y_index],
            fontname=style_params["font_family"],
            labelpad=style_params["axis_style"]["labelpad"],
            fontsize=style_params["axis_style"]["fontsize"],
            fontweight=style_params["axis_style"]["fontweight"],
            fontstyle=style_params["axis_style"]["fontstyle"],
            color=style_params["axis_style"]["color"],
        )

        # Tick labels formating
        self.canvas.axes.set_xticklabels(
            self.canvas.axes.get_xticks(),
            fontname=style_params["font_family"],
            fontsize=style_params["tick_style"]["fontsize"],
            fontweight=style_params["tick_style"]["fontweight"],
            fontstyle=style_params["tick_style"]["fontstyle"],
            color=style_params["tick_style"]["color"],
        )

        self.canvas.axes.set_yticklabels(
            self.canvas.axes.get_yticks(),
            fontname=style_params["font_family"],
            fontsize=style_params["tick_style"]["fontsize"],
            fontweight=style_params["tick_style"]["fontweight"],
            fontstyle=style_params["tick_style"]["fontstyle"],
            color=style_params["tick_style"]["color"],
        )

        # Tick formating
        if style_params["tick_style"]["majortickvisibility"]:
            self.canvas.axes.tick_params(
                which="major",
                pad=style_params["tick_style"]["labelpad"],
                direction=style_params["tick_style"]["majortickdirection"],
                length=style_params["tick_style"]["majorticklength"],
                width=style_params["tick_style"]["majortickwidth"],
            )
        else:
            self.canvas.axes.tick_params(which="major", length=0, width=0)

        if style_params["tick_style"]["minortickvisibility"]:
            self.canvas.axes.tick_params(
                which="minor",
                direction=style_params["tick_style"]["minortickdirection"],
                length=style_params["tick_style"]["minorticklength"],
                width=style_params["tick_style"]["minortickwidth"],
            )
        else:
            self.canvas.axes.tick_params(which="minor", length=0, width=0)

        # Grid formating
        if style_params["grid_style"]["hgridvisibility"]:
            self.canvas.axes.grid(True, axis="x")
            self.canvas.axes.grid(
                axis="x",
                color="black",
                linestyle=style_params["grid_style"]["hgridlinestyle"],
                linewidth=style_params["grid_style"]["hgridlinewidth"],
                alpha=style_params["grid_style"]["hgridalpha"],
                zorder=0,
            )
        else:
            self.canvas.axes.grid(False, axis="x")

        if style_params["grid_style"]["vgridvisibility"]:
            self.canvas.axes.grid(True, axis="y")
            self.canvas.axes.grid(
                axis="y",
                color="black",
                linestyle=style_params["grid_style"]["vgridlinestyle"],
                linewidth=style_params["grid_style"]["vgridlinewidth"],
                alpha=style_params["grid_style"]["vgridalpha"],
                zorder=0,
            )
        else:
            self.canvas.axes.grid(False, axis="y")

        # Legend formating
        font_props = FontProperties(
            family=style_params["font_family"],  # Set font family
            style=style_params["legend_style"]["fontstyle"],  # Set font style
            weight=style_params["legend_style"]["fontweight"],  # Set font weight
            size=style_params["legend_style"]["fontsize"],
        )

        if style_params["legend_style"]["visibility"]:
            self.canvas.axes.legend(
                prop=font_props,
                loc=style_params["legend_style"]["position"],
            )
        else:
            self.canvas.axes.legend().set_visible(False)

        # Figure frame formating
        if style_params["frame_style"]["topvisbility"]:
            self.canvas.axes.spines["top"].set_visible(True)
            self.canvas.axes.spines["top"].set_linewidth(
                style_params["frame_style"]["linewidth"]
            )
        else:
            self.canvas.axes.spines["top"].set_visible(False)

        if style_params["frame_style"]["rightvisbility"]:
            self.canvas.axes.spines["right"].set_visible(True)
            self.canvas.axes.spines["right"].set_linewidth(
                style_params["frame_style"]["linewidth"]
            )
        else:
            self.canvas.axes.spines["right"].set_visible(False)

        if style_params["frame_style"]["bottomvisbility"]:
            self.canvas.axes.spines["bottom"].set_visible(True)
            self.canvas.axes.spines["bottom"].set_linewidth(
                style_params["frame_style"]["linewidth"]
            )
        else:
            self.canvas.axes.spines["bottom"].set_visible(False)

        if style_params["frame_style"]["leftvisbility"]:
            self.canvas.axes.spines["left"].set_visible(True)
            self.canvas.axes.spines["left"].set_linewidth(
                style_params["frame_style"]["linewidth"]
            )
        else:
            self.canvas.axes.spines["left"].set_visible(False)

        # Set number formating for the two axis
        self.canvas.axes.xaxis.set_major_formatter(LogFormatterMathtext())
        self.canvas.axes.yaxis.set_major_formatter(StrMethodFormatter("{x:,.3f}"))

        # Set tight layout
        self.figure.tight_layout()
