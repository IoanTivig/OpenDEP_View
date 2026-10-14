import copy
import csv
import random
import numpy as np
import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSize, QSettings
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QPushButton, QListView, QSizePolicy, QColorDialog, QWidget, \
    QMessageBox, QApplication
from PyQt6.uic import loadUi
from PyQt6 import QtCore
from matplotlib.figure import Figure

from src.func import models
from src.func import general
from src.func import excel
from src.func import project as project_files
from src.func import opendep_files
from src.func import links
from src.func import replicates
from src.func import parameters as model_parameters
from src.func import separation
from src.func import sorting
from src.func import group_statistics
from src.func import statistics_report
from src.func.general import format_frequency
from ui.helpers.report_pdf import write_pdf
from src.classes.numpy_encoder import NumpyEncoder
from src.classes.pyqt import NoWheelChangeFilter

from ui.helpers.curve_widget_ui import CurveWidgetUI
from ui.helpers.scatter_widget_ui import ScatterWidgetUI
from ui.resources import graphical_resources
from ui.helpers.graph_settings_ui import GraphSettingsUI
from ui.helpers.noise_widget_ui import NoiseWidgetUI
from ui.helpers.capture_widget_ui import CaptureWidgetUI
from ui.helpers.welcome_widget_ui import WelcomeWidgetUI, set_logo
from ui.helpers.bug_report_widget_ui import BugReportWidgetUI
from ui.helpers.help_widget_ui import HelpWidgetUI, HELP_PAGES
from ui.helpers.group_widget_ui import GroupWidgetUI
from ui.helpers import separation_help

APP_NAME = "OpenDEP View"
PROJECT_FILTER = (f"OpenDEP View project (*{project_files.PROJECT_SUFFIX});;"
                  "Project folder of an older version (project.json)")

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

    You can contact the developer/owner of OpenDEP at "ioan.tivig@gmail.com" or "ioan.tivig@umfcd.ro".
'''

class MainUI(QMainWindow):
    def __init__(self, settings=None):
        QMainWindow.__init__(self)

        # The mouse wheel scrolls; it does not change spin boxes or drop-down lists (in all windows)
        self.no_wheel_change_filter = NoWheelChangeFilter(self)
        QApplication.instance().installEventFilter(self.no_wheel_change_filter)

        # Load the main UI
        loadUi("ui/main.ui", self)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon("icon.png"))

        # Create default parameters
        self.default_curve = None
        self.curves_dict = {}
        self.scatter_dict = {}
        self.groups_dict = {}                  # replicate groups (Group plots)
        self.no_curve_points = 100
        self.curve_keys = ["homogenous_particle", "single_shell", "two_shell", "three_shell", "four_shell"]
        self.graph_y_index = 0

        # Sort drop-downs of the plot lists (see sort_plot_list): a list waiting to be sorted until the user leaves it
        self.sort_pending = set()
        for kind, (_, combo, _, _) in self.plot_lists().items():
            for key, label in sorting.SORT_OPTIONS[kind]:
                combo.addItem(label, key)
            combo.currentIndexChanged.connect(lambda index, kind=kind: self.sort_plot_list(kind))
        QApplication.instance().focusChanged.connect(self.sort_pending_lists)

        # Project: the open project file, the saved state (to detect unsaved changes), the recent projects
        self.settings = settings or QSettings("OpenDEP", APP_NAME)
        self.project = None
        self.saved_state = None
        self.loading = False

        # Default styles
        self.point_styles = ["o", "s", "v", "+", "x", "*"]
        self.graph_style_parameters = None

        # Load the rest of the widgets
        self.graph_settings = GraphSettingsUI(parent=self)
        self.noise_widget = NoiseWidgetUI(parent=self)
        self.capture_widget = CaptureWidgetUI(parent=self)

        # Toolbar buttons
        self.qt_button_save_figure.clicked.connect(self.capture_widget.open_widget)
        self.qt_button_home_figure.clicked.connect(self.qt_graph_widget.toolbar.home)
        self.qt_button_zoom_figure.clicked.connect(self.qt_graph_widget.toolbar.zoom)
        self.qt_button_properties_figure.clicked.connect(self.graph_settings.open_graph_settings)
        self.qt_button_fitspace_figure.clicked.connect(self.qt_graph_widget.set_tight_layout)
        #self.qt_button_resize_figure.clicked.connect(self.resize_graph)

        # Data buttons
        self.qt_button_curve_load.clicked.connect(lambda: self.load_curve(file_type="OpenDEP"))
        self.qt_button_scatter_add.clicked.connect(lambda: self.generate_new_scatter(type="new"))
        self.qt_button_scatter_load.clicked.connect(self.load_scatter)
        self.qt_button_scatter_load_excel.clicked.connect(self.load_excel_scatter)
        self.qt_button_curve_load_excel.clicked.connect(lambda: self.load_curve(file_type="Excel"))


        # Plot lists: no horizontal scroll bar (the vertical one is the slim styled bar of main.ui, shown when needed)
        self.qt_scrollarea_plots_curve.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Splitter between the graph and the parameters, the graph takes the extra space when the window grows
        self.qt_splitter_main.setStretchFactor(0, 1)
        self.qt_splitter_main.setStretchFactor(1, 0)

        # Graph content menubar, to toggle what is displayed on the graph
        self.qt_graphcontent_buttons = self.qt_frame_toolbar_graphcontent.findChildren(QPushButton)
        for button in self.qt_graphcontent_buttons:
            button.clicked.connect(lambda: self.toggle_active_state(self.qt_graphcontent_buttons))
            button.clicked.connect(self.refresh_graph)
        self.qt_graphcontent_buttons[0].click()

        # Experimental data display menubar, to toggle how the experimental data is displayed
        self.qt_experimentaldisplay_buttons = self.qt_frame_menubar_experimental_display.findChildren(QPushButton)
        for button in self.qt_experimentaldisplay_buttons:
            button.clicked.connect(lambda: self.toggle_active_state(self.qt_experimentaldisplay_buttons))
        self.qt_experimentaldisplay_buttons[0].click()

        # Plots menubar, to toggle what is displayed on the plots. Group plots also changes the graph: it shows the
        # replicate groups (mean ± SD and their curves) instead of the individual curves and scatters
        self.qt_plots_buttons = self.qt_frame_tabbar_plots.findChildren(QPushButton)
        self.qt_plots_tab_widgets = [self.qt_frame_group_curve_plots, self.qt_frame_group_scatter_plots,
                                     self.qt_frame_group_group_plots]
        for button in self.qt_plots_buttons:
            button.clicked.connect(lambda: self.toggle_tabs(self.qt_plots_buttons, self.qt_plots_tab_widgets))
            button.clicked.connect(self.refresh_graph)
        self.qt_plots_buttons[0].click()
        self.qt_button_group_add.clicked.connect(lambda: self.generate_new_group())
        self.qt_button_statistics_report.clicked.connect(lambda: self.statistics_report())
        self.qt_checkbox_group_single_points.clicked.connect(self.refresh_graph)

        # Best separation: what the pairs are ranked by, and what each entry means (tooltips)
        self.separation_rank = "score"
        self.qt_separation_rank_buttons = {"score": self.qt_button_separation_rank_score,
                                           "ratio": self.qt_button_separation_rank_ratio,
                                           "contrast": self.qt_button_separation_rank_contrast}
        for key, button in self.qt_separation_rank_buttons.items():
            button.setToolTip(separation_help.HELP[f"rank_{key}"])
            button.clicked.connect(lambda checked=False, key=key: self.set_separation_rank(key))
        for label, key in ((self.qt_label_separation_title, "title"), (self.qt_label_separation_rank, "title"),
                           (self.qt_label_separation_pair, "pair"),
                           (self.qt_label_separation_frequency_title, "frequency"),
                           (self.qt_label_separation_score_title, "score"),
                           (self.qt_label_separation_ratio_title, "ratio"),
                           (self.qt_label_separation_contrast_title, "contrast"),
                           (self.qt_label_separation_second_title, "second")):
            label.setToolTip(separation_help.HELP[key])
        self.set_separation_rank("score")

        # Graph size lock and size entry - all functionality for resizing the graph
        self.qt_checkbox_graph_size_lock.clicked.connect(self.lock_graph_widget_size)
        self.qt_entry_graph_height.editingFinished.connect(self.resize_to_entry)
        self.qt_entry_graph_width.editingFinished.connect(self.resize_to_entry)
        self.qt_entry_graph_width.setDisabled(True)
        self.qt_entry_graph_height.setDisabled(True)

        # ScrollArea buttons
        self.qt_button_curves_add.clicked.connect(self.generate_new_curve)

        # Entry fields for the frequency range (all curves recalculated only when the range really changed)
        self.last_frequency_range = None
        self.qt_entry_param_freq_start.editingFinished.connect(self.frequency_range_changed)
        self.qt_entry_param_freq_stop.editingFinished.connect(self.frequency_range_changed)
        self.qt_combo_param_freq_start_unit.currentIndexChanged.connect(self.frequency_range_changed)
        self.qt_combo_param_freq_stop_unit.currentIndexChanged.connect(self.frequency_range_changed)

        # Visibility checkboxes
        self.qt_checkbox_curves_visibility.clicked.connect(self.refresh_graph)
        self.qt_checkbox_scatters_visibility.clicked.connect(self.refresh_graph)

        # Hide future buttons
        self.qt_button_cruves_load_cloud.setVisible(False)
        self.qt_button_fitspace_figure.setVisible(False)

        # Lock entries to integers
        entries_to_int = [self.qt_entry_graph_width,
                          self.qt_entry_graph_height,
                          self.qt_entry_param_freq_start,
                          self.qt_entry_param_freq_stop
                          ]
        for entry in entries_to_int:
            general.lock_entry_to_int(entry, min_value=1, max_value=2000, max_length=4)

        # Header and welcome screen
        set_logo(self.qt_label_header_logo, 22)
        self.welcome_widget = WelcomeWidgetUI(parent=self)
        self.qt_page_welcome_layout.addWidget(self.welcome_widget)
        self.qt_button_project_new.clicked.connect(self.new_project)
        self.qt_button_project_open.clicked.connect(self.open_project_dialog)
        self.qt_button_project_save.clicked.connect(self.save_project)
        self.qt_button_report_bug.clicked.connect(self.show_bug_report)
        self.bug_report_widget = None
        self.qt_button_help.clicked.connect(lambda: self.show_help())
        self.help_widget = None
        self.pending_files = []                        # files from outside waiting for a project (open_files)
        self.setAcceptDrops(True)
        QShortcut(QKeySequence("F1"), self, lambda: self.show_help())
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_project)
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_project_dialog)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_project)
        self.update_project_display()

    # UI METHODS
    def toggle_tabs(self, buttons, tab_widgets):
        sender = self.sender()  # Get the button that was clicked
        for button in buttons:
            button.setProperty("customState", button == sender)
            button.setStyle(button.style())  # Refresh style to apply property

        for i, button in enumerate(buttons):
            tab_widgets[i].setVisible(button == sender)

    def toggle_active_state(self, buttons):
        sender = self.sender()  # Get the button that was clicked
        for button in buttons:
            button.setProperty("customState", button == sender)
            button.setStyle(button.style())  # Refresh style to apply property

        self.refresh_graph()

    # SCATTER METHODS - add, modify, duplicate, delete, save, load
    # Generate new scatter with default parameters
    def generate_new_scatter(self, type="new", duplicate_id=None, file_path=None, data=None):
        # Create a new scatter widget
        scatter_widget = ScatterWidgetUI()

        # Create Random ID which wont be already in the dictionary keys
        id = random.randint(0, 9999)
        while id in self.scatter_dict.keys():
            id = random.randint(0, 9999)

        # Create parameters for the curve
        point_style = 'o'
        point_size = 50
        visibility = True
        extra = {}                             # keys of the file View does not use, kept as read (see below)

        # Handle in case a new scatter is generated
        if type == "new":
            color = general.get_random_color_hex()
            name = f"Scatter {len(self.scatter_dict) + 1}"


            # Create scatter data
            scatter_data = {"frequencies": [1000.0, 2500.0, 5000.0, 7500.0, 10000.0],
                            "recm_values": [-0.4, -0.3, -0.33, -0.11, 0.0],
                            "recm_errors": [0.01, 0.015, 0.005, 0.02, 0.01]}

        # Handle in case a scatter based on noise is generated
        elif type == "noise":
            color = self.curves_dict[self.noise_widget.selected_curve_id]["color"]
            name = self.curves_dict[self.noise_widget.selected_curve_id]["name"] + " - Noise"

            # Generate noise data (a typed frequency or setting that cannot be read: say which, add nothing)
            try:
                scatter_data = self.noise_widget.generate_noise_scatter()
            except ValueError as e:
                QMessageBox.warning(self.noise_widget, APP_NAME, str(e))
                return None

        # Handle in case a scatter is loaded
        elif type == "duplicate":
            name = self.scatter_dict[duplicate_id]["name"] + " - Copy"
            color = self.scatter_dict[duplicate_id]["color"]
            point_size = self.scatter_dict[duplicate_id]["point_size"]
            point_style = self.scatter_dict[duplicate_id]["point_style"]
            extra = copy.deepcopy(opendep_files.extra_spectrum_keys(self.scatter_dict[duplicate_id]))
            scatter_data = copy.deepcopy(self.scatter_dict[duplicate_id]["scatter"])

        # Handle in case a scatter is loaded from a file, or its data is given (scatters of a project). Files from
        # OpenDEP Control and Compute carry more than View uses (quantity, raw values, normalisation, per-point data,
        # known parameters, source): it is kept, and written again when the scatter is saved.
        elif type == "load":
            if data is None:
                with open(file_path, 'r', encoding="utf-8") as file:
                    data = json.load(file)
            if float(data.get("scale_factor", 1.0)) != 1.0:      # project of 2026-10-08 with a View scale factor
                data = {**data, **opendep_files.scaled_to_cm_factor(data, data["scale_factor"])}
            name = data.get("name") or "Scatter"
            color = data.get("color") or general.get_random_color_hex()
            point_size = data.get("point_size", 50)
            point_style = data.get("point_style", "o") if data.get("point_style", "o") in self.point_styles else "o"
            visibility = data.get("visibility", True)
            extra = copy.deepcopy(opendep_files.extra_spectrum_keys(data))
            scatter_data = copy.deepcopy(data["scatter"])

        elif type == "load_excel":
            data = excel.load_scatter_from_excel(file_path)

            if data is None:
                scatter_data = scatter_data = {"frequencies": [1000.0],
                            "recm_values": [0.0],
                            "recm_errors": [0.0]}
            else:
                scatter_data = data

            color = general.get_random_color_hex()
            name = file_path.split("/")[-1].split(".")[0]

        # Add the curve to the dictionary
        self.scatter_dict[id] = {"name": name,
                                "color": color,
                                "point_size": point_size,
                                "point_style": point_style,
                                "visibility": visibility,
                                "scatter": scatter_data,
                                **extra,
                                "widget": scatter_widget}

        # Populate the widget with the data
        scatter_widget.id = id
        scatter_widget.parent_widget = self
        scatter_widget.set_entries_with_data()

        # Connect the buttons after the setup
        scatter_widget.connect_buttons_after_setup()

        # Dock the widget at index 0 from the top (the refresh puts the list in the chosen order)
        self.qt_scrollarea_scatter_curves_layout.insertWidget(0, scatter_widget)

        # Refresh all graphs with new data
        self.refresh_graph()
        return id

    # Delete scatter from the dictionary and refresh the graph
    def delete_scatter(self, id):
        # Remove the scatter from the dictionary, its link to a curve, and the groups it was in
        del self.scatter_dict[id]
        links.remove_target(self.curves_dict, "scatter", id)
        for group in self.groups_dict.values():
            group["members"] = [m for m in group["members"] if m["scatter"] != id]

        # Refresh the graph
        self.refresh_graph()

    # Save scatter to an OpenDEP Spectrum file (.odspec)
    def save_scatter(self, id, file_path):
        file_path = opendep_files.with_suffix(file_path, (opendep_files.SPECTRUM_SUFFIX,
                                                          opendep_files.LEGACY_SPECTRUM_SUFFIX))
        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(opendep_files.spectrum_file_data(self.scatter_dict[id]), file, cls=NumpyEncoder)

    # Load scatter from an OpenDEP Spectrum file (.odspec, or .ods from before 2026-10)
    def load_scatter(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load scatter", "", opendep_files.SPECTRUM_OPEN_FILTER)
        if not file_path:
            return

        try:
            kind, data = opendep_files.read_opendep_file(file_path)
        except (opendep_files.OpenDEPFileError, OSError) as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return
        if kind == "curve":
            self.add_curve(data)
        elif kind == "fit":
            self.add_fit(data)
        else:
            self.generate_new_scatter(type="load", data=data)

    def load_excel_scatter(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load scatter", "", "Excel Scatter (*.xlsx)")
        if file_path:
            self.generate_new_scatter(type="load_excel", file_path=file_path)

    # CURVE METHODS - add, modify, duplicate, delete, save, load
    # Generate new curve with default parameters
    def generate_new_curve(self):
        # Create a new curve widget
        new_curve_widget = CurveWidgetUI()

        # Create a new parameters list
        generated_parameters = self.create_default_curve_data()

        # Generate the curve data
        curve_data = self.generate_curve_data(generated_parameters)

        # Calculate the cross over frequencies of all models
        self.update_cross_overs(generated_parameters, curve_data)

        # Create Random ID which wont be already in the dictionary keys
        id = random.randint(0, 9999)
        while id in self.curves_dict.keys():
            id = random.randint(0, 9999)

        # Create base parameters for the curve
        color = general.get_random_color_hex()
        name = f"Curve {len(self.curves_dict) + 1}"
        visibility = True
        model = 1                                      # single-shell: the model of most cells
        line_style = '-'
        line_width = 1.5

        # Add the curve to the dictionary
        self.curves_dict[id] = {"name": name,
                                "color": color,
                                "line_style": line_style,
                                "line_width": line_width,
                                "visibility": visibility,
                                "model": model,
                                "parameters": generated_parameters,
                                "curves": curve_data,
                                "link": None,
                                "widget": new_curve_widget}

        # Populate the widget with the data
        new_curve_widget.id = id
        new_curve_widget.parent_widget = self
        new_curve_widget.set_entries_with_data()

        # Dock the widget at index 0 from the top (the refresh puts the list in the chosen order)
        self.qt_scrollarea_plots_curve_layout.insertWidget(0, new_curve_widget)

        # Refresh all graphs with new data
        self.refresh_graph()

    # Modify single curve from the dictionary and refresh the graph. edited: the user changed a value or the model
    # (not a recalculation); a curve fitted in OpenDEP Compute then loses its fit results
    def modify_single_curve(self, id, edited=False, redraw=True):
        curve = self.curves_dict[id]
        before = links.defining_values(curve) if edited else None

        # Update the parameters from entry fields of the widget
        parameters = curve["widget"].get_data_from_entries()
        self.curves_dict[id]["parameters"] = parameters

        if edited and curve.get("fit") and links.defining_values(curve) != before:
            del curve["fit"]
            curve["fit_status"] = "edited"
            curve["widget"].update_links()

        # Generate the curve data
        curve_data = self.generate_curve_data(self.curves_dict[id]["parameters"])
        self.curves_dict[id]["curves"] = curve_data

        # Calculate the cross over frequencies of all models
        self.update_cross_overs(self.curves_dict[id]["parameters"], self.curves_dict[id]["curves"])

        # Refresh all graphs with new data
        self.curves_dict[id]["widget"].update_crossover()
        if redraw:
            self.refresh_graph()

    # Duplicate curve from the dictionary and refresh the graph
    def duplicate_curve(self, id):
        # Create a new curve widget
        new_curve_widget = CurveWidgetUI()

        # Create a new parameters list (a scatter or group is linked to one curve, so the copy has no link)
        data_copy = self.curves_dict[id].copy()
        data_copy["parameters"] = dict(data_copy["parameters"])
        data_copy["link"] = None

        # Create Random ID which wont be already in the dictionary keys
        new_id = random.randint(0, 9999)
        while new_id in self.curves_dict.keys():
            new_id = random.randint(0, 9999)

        # Create new name
        name = f"{self.curves_dict[id]['name']} - Copy"

        self.curves_dict[new_id] = data_copy
        self.curves_dict[new_id]["widget"] = new_curve_widget
        self.curves_dict[new_id]["name"] = name

        # Populate the widget with the data
        new_curve_widget.id = new_id
        new_curve_widget.parent_widget = self
        new_curve_widget.set_entries_with_data()

        # Dock the widget at index 0 from the top (the refresh puts the list in the chosen order)
        self.qt_scrollarea_plots_curve_layout.insertWidget(0, new_curve_widget)

        # Refresh all graphs with new data
        self.modify_all_curves()

    # Delete curve from the dictionary and refresh the graph
    def delete_curve(self, id):
        # Remove the curve from the dictionary (and as a group's joint fit)
        del self.curves_dict[id]
        for group in self.groups_dict.values():
            if group.get("joint_curve") == id:
                del group["joint_curve"]

        # Refresh the graph
        self.refresh_graph()

    # Save curve to an OpenDEP Curve file (.odcurve), or with its linked scatter to an OpenDEP Fit file (.odfit).
    # The particle radius ("core_radius") is the outer radius for every model (see complete_curve_parameters)
    def save_curve(self, id, file_path):
        curve = self.curves_dict[id]
        if file_path.lower().endswith(opendep_files.FIT_SUFFIX):
            kind, target_id = links.link_target(curve)
            if kind != "scatter":
                QMessageBox.warning(self, APP_NAME, "An OpenDEP Fit file holds a curve with its scatter: link a "
                                                    "scatter to the curve first, or save it as an OpenDEP Curve.")
                return None
            data = opendep_files.fit_file_data(curve["name"], [self.scatter_dict[target_id]], curve)
        else:
            file_path = opendep_files.with_suffix(file_path, (opendep_files.CURVE_SUFFIX,
                                                              opendep_files.LEGACY_CURVE_SUFFIX))
            data = opendep_files.curve_file_data(curve)
        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(data, file, cls=NumpyEncoder)
        return file_path

    # Load curve from an OpenDEP Curve file (.odcurve, or .odc from before 2026-10) or an Excel file
    def load_curve(self, file_type="OpenDEP"):
        if file_type == "OpenDEP":
            file_path, _ = QFileDialog.getOpenFileName(self, "Load curve", "", opendep_files.CURVE_OPEN_FILTER)
        elif file_type == "Excel":
            file_path, _ = QFileDialog.getOpenFileName(self, "Load curve", "", "Excel Curve (*.xlsx)")

        if file_path:
            # Create a new parameters list
            if file_type == "OpenDEP":
                try:
                    kind, data = opendep_files.read_opendep_file(file_path)
                except (opendep_files.OpenDEPFileError, OSError) as e:
                    QMessageBox.warning(self, APP_NAME, str(e))
                    return
                if kind == "spectrum":
                    self.generate_new_scatter(type="load", data=data)
                    return
                if kind == "fit":
                    self.add_fit(data)
                    return

            elif file_type == "Excel":
                parameters, model = excel.load_curve_from_excel(file_path)
                if not parameters == None:
                    data = {"name": file_path.split("/")[-1].split(".")[0],
                            "color": general.get_random_color_hex(),
                            "line_style": '-',
                            "line_width": 1.5,
                            "visibility": True,
                            "model": model,
                            "parameters": parameters,
                            "radius_convention": "outer"}
                else:
                    return

            self.add_curve(data)

    # Add a curve from its saved data (OpenDEP Curve file, Excel file or project)
    def add_curve(self, data):
        # Create a new curve widget
        new_curve_widget = CurveWidgetUI()

        data["parameters"] = self.complete_curve_parameters(data["parameters"], data["model"],
                                                            data.pop("radius_convention", None))

        # Create Random ID which wont be already in the dictionary keys
        new_id = random.randint(0, 9999)
        while new_id in self.curves_dict.keys():
            new_id = random.randint(0, 9999)

        # Update with the new widget and nwe data
        self.curves_dict[new_id] = data
        self.curves_dict[new_id]["widget"] = new_curve_widget
        self.curves_dict[new_id]["link"] = None

        # Populate the widget with the data
        new_curve_widget.id = new_id
        new_curve_widget.parent_widget = self
        new_curve_widget.set_entries_with_data()

        # Dock the widget at index 0 from the top (the refresh puts the list in the chosen order)
        self.qt_scrollarea_plots_curve_layout.insertWidget(0, new_curve_widget)

        # Curve data for the current frequency range, then refresh the graph
        self.modify_single_curve(new_id)
        return new_id

    # Add an OpenDEP Fit (.odfit): its spectra as scatters (on the CM-factor scale) and its curve(s).
    #   one spectrum                      the curve is linked to the scatter
    #   several spectra (replicates)      a replicate group; each replicate's own curve (files from View) is linked
    #                                     to its scatter; a curve fitted to all of them together (OpenDEP Compute)
    #                                     is kept as the group's joint fit
    def add_fit(self, data):
        refreshing = self.loading
        self.loading = True                            # draw once, at the end
        try:
            # 1. Scatters on the CM-factor scale: each spectrum ÷ the scale factor the fit found for it (the values
            #    as measured and the factor are kept in the scatter's data)
            spectra_links = {int(link["spectrum"]): link for link in data.get("links", [])}
            scatter_ids = []
            for i, spectrum in enumerate(data["spectra"]):
                link = spectra_links.get(i, {})
                if float(link.get("scale", 1.0)) != 1.0:
                    spectrum = {**spectrum, **opendep_files.scaled_to_cm_factor(spectrum, link["scale"],
                                                                               link.get("scale_error"))}
                scatter_ids.append(self.generate_new_scatter(type="load", data=spectrum))

            # 2. The curve of a single spectrum, with the fit results, linked to it
            group_info = data.get("group") or {}
            is_group = len(scatter_ids) > 1 or bool(group_info) or \
                any("biological" in link for link in spectra_links.values())
            curve_id = None
            if data.get("curve") and not group_info.get("member_curves"):
                curve = dict(data["curve"])
                if data.get("fit"):
                    curve["fit"] = data["fit"]
                    curve["fit_status"] = "fitted"
                curve_id = self.add_curve(curve)
                if not is_group:
                    links.set_link(self.curves_dict, curve_id, "scatter", scatter_ids[0])
            if not is_group:
                return curve_id

            # 3. A group of the replicates (each spectrum its own biological replicate unless the file says
            #    otherwise), with each replicate's curve linked to its scatter
            for scatter_id, member_curve in zip(scatter_ids, group_info.get("member_curves") or []):
                if member_curve:
                    links.set_link(self.curves_dict, self.add_curve(dict(member_curve)), "scatter", scatter_id)
            name = (group_info.get("name") or next((l["sample"] for l in spectra_links.values() if l.get("sample")),
                                                   "") or data.get("name") or "Group")
            members = [{"scatter": sid, "biological": str(spectra_links.get(i, {}).get("biological", i + 1))}
                       for i, sid in enumerate(scatter_ids)]
            style = {"color": (data.get("curve") or {}).get("color") or self.scatter_dict[scatter_ids[0]]["color"],
                     **group_info}
            group_id = self.generate_new_group(name, members, style)
            if curve_id is not None:                       # a curve fitted to all the replicates together
                self.groups_dict[group_id]["joint_curve"] = curve_id
            return group_id
        finally:
            self.loading = refreshing
            self.refresh_graph()

    # LINKS - a curve and the scatter it belongs to (e.g. the data it was fitted to)
    # Link a curve to a scatter (kind None: unlink). A curve linked by hand to a scatter takes its colour.
    def set_curve_link(self, curve_id, kind, target_id):
        curve = self.curves_dict[curve_id]
        if kind == "scatter" and links.link_target(curve) == (None, None):
            curve["color"] = self.scatter_dict[target_id]["color"]
            curve["widget"].qt_button_pick_curve_color.setStyleSheet(f"background-color: {curve['color']}")
        links.set_link(self.curves_dict, curve_id, kind, target_id)
        self.refresh_graph()

    def curve_linked_to(self, kind, target_id):
        return links.linked_curve(self.curves_dict, kind, target_id)

    # GROUP METHODS - replicate groups (Group plots)
    # New group; members: [{"scatter": id, "biological": label}]
    # style: {"color" (mean scatter and curve), "point_style", "point_size", "line_style", "line_width", "visibility"}
    def generate_new_group(self, name=None, members=None, style=None):
        style = {key: value for key, value in (style or {}).items() if value is not None}
        # One colour for the group (exports of 2026-10-09 had a point and a curve colour: the point colour is used)
        color = style.get("color") or style.get("point_color") or general.get_random_color_hex()
        group_widget = GroupWidgetUI()
        group_id = random.randint(0, 9999)
        while group_id in self.groups_dict:
            group_id = random.randint(0, 9999)

        self.groups_dict[group_id] = {"name": name or f"Group {len(self.groups_dict) + 1}",
                                      "visibility": style.get("visibility", True),
                                      "color": color,
                                      "point_style": style.get("point_style", "o"),
                                      "point_size": style.get("point_size", 50),
                                      "line_style": style.get("line_style", "-"),
                                      "line_width": style.get("line_width", 1.5),
                                      "members": [dict(m) for m in members or []],
                                      "widget": group_widget}
        group_widget.id = group_id
        group_widget.parent_widget = self
        group_widget.set_entries_with_data()
        self.qt_scrollarea_groups_layout.insertWidget(0, group_widget)
        self.refresh_graph()
        return group_id

    def delete_group(self, group_id):
        del self.groups_dict[group_id]
        self.refresh_graph()

    # A scatter joins a group as a new biological replicate (the next free number)
    def add_scatter_to_group(self, group_id, scatter_id):
        members = self.groups_dict[group_id]["members"]
        numbers = [int(m["biological"]) for m in members if str(m["biological"]).isdigit()]
        label = str(max(numbers) + 1) if numbers else str(len(members) + 1)
        members.append({"scatter": scatter_id, "biological": label})
        self.refresh_graph()

    def remove_scatter_from_group(self, group_id, scatter_id):
        group = self.groups_dict[group_id]
        group["members"] = [m for m in group["members"] if m["scatter"] != scatter_id]
        self.refresh_graph()

    # Biological replicate of a scatter in a group (scatters with the same label are technical replicates)
    def set_member_biological(self, group_id, scatter_id, label):
        for member in self.groups_dict[group_id]["members"]:
            if member["scatter"] == scatter_id:
                member["biological"] = str(label)
        self.refresh_graph()

    # Everything calculated for a group (kept until the next refresh of the graph):
    #   "average"     mean ± SD of the scatters (replicates.average_group)
    #   "model"       mean ± SD of the parameters and crossovers of the curves linked to its scatters
    #                 (replicates.average_curves); a joint fit when only that exists ("joint": True)
    #   "mean_curve"  the curve of the mean parameters: {"name", "model", "parameters", "curves"}, or None
    def group_result(self, group_id):
        cache = getattr(self, "group_results", {})
        if group_id in cache:
            return cache[group_id]

        group = self.groups_dict[group_id]
        members = [m for m in group["members"] if m["scatter"] in self.scatter_dict]
        average = replicates.average_group([
            {"biological": m["biological"], "frequencies": self.scatter_dict[m["scatter"]]["scatter"]["frequencies"],
             "values": self.scatter_dict[m["scatter"]]["scatter"]["recm_values"],
             "errors": self.scatter_dict[m["scatter"]]["scatter"]["recm_errors"]} for m in members])

        # The replicates' curves (or the joint fit when no replicate has its own curve)
        curves = []
        for member in members:
            curve_id = self.curve_linked_to("scatter", member["scatter"])
            if curve_id is not None:
                curves.append((member["biological"], self.curves_dict[curve_id]))
        joint = not curves and group.get("joint_curve") in self.curves_dict
        if joint:
            curves = [("joint fit", self.curves_dict[group["joint_curve"]])]
        model = replicates.average_curves(
            [{"biological": biological, "model": curve["model"], "parameters": curve["parameters"],
              "crossovers": (curve["parameters"]["1st_cross_over"].get(models.MODEL_KEYS[curve["model"]]),
                             curve["parameters"]["2nd_cross_over"].get(models.MODEL_KEYS[curve["model"]]))}
             for biological, curve in curves], model_parameters.MODEL_PARAMETERS, model_parameters.MODEL_NAMES,
            model_parameters.LINEAR_SCALE)

        # The curve of the mean parameters (the model's parameters averaged: geometric means, so it crosses at the
        # geometric-mean crossover, see replicates.average_scalar; the others as in the first curve)
        mean_curve = None
        if model["model"] is not None:
            mean_parameters = {**copy.deepcopy(curves[0][1]["parameters"]),
                               **{key: stats["mean"] for key, stats in model["parameters"].items()
                                  if stats["mean"] is not None},
                               "1st_cross_over": {key: None for key in models.MODEL_KEYS},
                               "2nd_cross_over": {key: None for key in models.MODEL_KEYS}}
            curve_data = self.generate_curve_data(mean_parameters)
            self.update_cross_overs(mean_parameters, curve_data)
            mean_curve = {"name": f"{group['name']} (mean parameters)", "model": model["model"],
                          "parameters": mean_parameters, "curves": curve_data}

        # Each replicate's curve: its model, parameters and crossovers (separation and statistics)
        curve_items = [{"biological": biological, "model": curve["model"], "parameters": curve["parameters"],
                        "first": curve["parameters"]["1st_cross_over"].get(models.MODEL_KEYS[curve["model"]]),
                        "second": curve["parameters"]["2nd_cross_over"].get(models.MODEL_KEYS[curve["model"]])}
                       for biological, curve in curves]
        result = {"average": average, "model": model, "mean_curve": mean_curve, "joint": joint,
                  "curves": curve_items,
                  "member_curves": [self.curve_linked_to("scatter", m["scatter"]) for m in members]}
        if hasattr(self, "group_results"):
            self.group_results[group_id] = result
        return result

    def group_average(self, group_id):
        return self.group_result(group_id)["average"]

    # OpenDEP Fit document of a group: its scatters (CM factor) with their biological replicates, each one's curve,
    # the curve of the mean parameters, and the results (mean ± SD of the data, parameters and crossovers)
    def group_fit_file_data(self, group_id):
        group = self.groups_dict[group_id]
        result = self.group_result(group_id)
        members = [m for m in group["members"] if m["scatter"] in self.scatter_dict]
        mean_curve = None
        if result["mean_curve"] is not None:
            mean_curve = {**result["mean_curve"], "color": group["color"], "line_style": group["line_style"],
                          "line_width": group["line_width"], "visibility": True}
        style = {key: group[key] for key in ("name", "color", "point_style", "point_size",
                                             "line_style", "line_width")}
        member_curves = [opendep_files.curve_file_data(self.curves_dict[curve_id]) if curve_id is not None else None
                         for curve_id in result["member_curves"]]
        return opendep_files.fit_file_data(group["name"], [self.scatter_dict[m["scatter"]] for m in members],
                                           mean_curve, [m["biological"] for m in members],
                                           {**style, "average": result["average"], "results": result["model"],
                                            "member_curves": member_curves})

    # Export a group. kind "opendep": OpenDEP Fit (.odfit) or its mean as an OpenDEP Spectrum (.odspec);
    # kind "table": Excel (.xlsx) or CSV (.csv). A file_path given (tests) may have any of the four extensions.
    def export_group(self, group_id, file_path=None, selected_filter="", kind=None):
        group = self.groups_dict[group_id]
        if not group["members"]:
            QMessageBox.warning(self, APP_NAME, "The group has no scatters yet.")
            return None
        opendep = {opendep_files.FIT_SUFFIX: "OpenDEP Fit: replicates, curves and results (*.odfit)",
                   opendep_files.SPECTRUM_SUFFIX: "OpenDEP Spectrum: the mean ± SD (*.odspec)"}
        tables = {".xlsx": "Excel: mean, parameters and replicates (*.xlsx)",
                  ".csv": "CSV: the mean (*.csv)"}
        filters = opendep if kind == "opendep" else tables if kind == "table" else {**opendep, **tables}
        if file_path is None:
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "Export group", project_files.safe_file_name(group["name"]), ";;".join(filters.values()))
            if not file_path:
                return None
        suffix = next((s for s in filters if file_path.lower().endswith(s)), None) or \
            next((s for s, f in filters.items() if f == selected_filter), next(iter(filters)))
        if not file_path.lower().endswith(suffix):
            file_path += suffix

        result = self.group_result(group_id)
        average = result["average"]
        members = [m for m in group["members"] if m["scatter"] in self.scatter_dict]
        try:
            if suffix == opendep_files.FIT_SUFFIX:
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(self.group_fit_file_data(group_id), file, cls=NumpyEncoder)
            elif suffix == opendep_files.SPECTRUM_SUFFIX:
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(opendep_files.average_file_data(group["name"], group["color"], average), file,
                              cls=NumpyEncoder)
            elif suffix == ".xlsx":
                excel.save_group_to_excel(file_path, group["name"], average, [
                    {"name": self.scatter_dict[m["scatter"]]["name"], "biological": m["biological"],
                     "scatter": self.scatter_dict[m["scatter"]]["scatter"]} for m in members],
                    result["model"], model_parameters)
            else:
                with open(file_path, "w", encoding="utf-8", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Frequency (Hz)", "Mean CM factor", "Error (SD)", "Biological replicates (n)",
                                     "Technical replicates", "Error from"])
                    writer.writerows(zip(average["frequencies"], average["values"], average["errors"],
                                         average["n_biological"], average["n_technical"], average["kind"]))
        except OSError as e:
            QMessageBox.warning(self, APP_NAME, f"The group could not be exported:\n{e}")
            return None
        return file_path

    # Multiple curve functionality - modify all
    # Frequency range edited: leaving the field without a change (editingFinished) recalculates nothing
    def frequency_range_changed(self):
        frequency_range = (self.qt_entry_param_freq_start.text(), self.qt_combo_param_freq_start_unit.currentIndex(),
                           self.qt_entry_param_freq_stop.text(), self.qt_combo_param_freq_stop_unit.currentIndex())
        if frequency_range != self.last_frequency_range:
            self.last_frequency_range = frequency_range
            self.modify_all_curves()

    # All curves recalculated (e.g. a new frequency range), the graph redrawn once at the end
    def modify_all_curves(self):
        for key in self.curves_dict.keys():
            self.modify_single_curve(key, redraw=False)
        self.refresh_graph()


    # Place holder parameters and data for when adding new curve
    def create_default_curve_data(self):
        # Details: name, color, visibility, model, gen_data, ss_data, ho_data
        # ss_data: buffer permittivity, buffer conductivity, particle
        parameters = {"buffer_perm":78,
                      "buffer_cond":0.01,
                      "core_perm":random.randint(5,100),
                      "core_cond":0.1,
                      "core_radius": 10.0,
                      "1st_shell_perm":random.randint(5,100),
                      "1st_shell_cond":0.00001,
                      "1st_shell_thick":6.0,
                      "2nd_shell_perm":random.randint(5,100),
                      "2nd_shell_cond":0.00001,
                      "2nd_shell_thick": 6.0,
                      "electric_field":1.0,
                      # Homogenous particle: surface conductance (nS)
                      "core_surface_cond": 0.0,
                      # Nucleus of the three- and four-shell models (same defaults as OpenDEP Compute)
                      "nucleus_radius": 3.0,
                      "envelope_thick": 40.0,
                      "envelope_perm": 30.0,
                      "envelope_cond": 0.001,
                      "nucleoplasm_perm": 50.0,
                      "nucleoplasm_cond": 1.0,
                      "1st_cross_over": {key: 0.0 for key in models.MODEL_KEYS},
                      "2nd_cross_over": {key: 0.0 for key in models.MODEL_KEYS}
        }

        return parameters

    # Parameters of a curve loaded from a file: older files miss the newer parameters and cross-overs, and their
    # two-shell radius was the core radius (now the outer radius, as for the other models and in OpenDEP Compute)
    def complete_curve_parameters(self, parameters, model, radius_convention=None):
        defaults = self.create_default_curve_data()
        for key, value in defaults.items():
            if key not in parameters:
                parameters[key] = value
        for key in ("1st_cross_over", "2nd_cross_over"):
            parameters[key] = {**defaults[key], **parameters[key]}

        if model == 2 and radius_convention != "outer":
            parameters["core_radius"] = parameters["core_radius"] + 0.001 * (parameters["1st_shell_thick"] +
                                                                             parameters["2nd_shell_thick"])
        return parameters

    # Generate the curve data for the given parameters
    def generate_curve_data(self, parameters):
        # Generate the frequency list
        start = np.log10(float(self.qt_entry_param_freq_start.text())*(1000**self.qt_combo_param_freq_start_unit.currentIndex()))
        stop = np.log10(float(self.qt_entry_param_freq_stop.text())*(1000**self.qt_combo_param_freq_stop_unit.currentIndex()))
        frequencies_list = np.logspace(start=start,
                                       stop=stop,
                                       num=self.no_curve_points,
                                       endpoint=True)

        # Re[CM], Im[CM] and DEP force of every model
        curve_data = {"frequencies": frequencies_list}
        for model, key in enumerate(self.curve_keys):
            recm, imcm, depforce = models.model_all(model, frequencies_list, parameters)
            curve_data[f"recm_{key}"] = list(recm)
            curve_data[f"imcm_{key}"] = list(imcm)
            curve_data[f"depforce_{key}"] = list(depforce)

        return curve_data

    # Cross over frequencies of all models of a curve (exact: refined on the model, see models.crossover_frequencies)
    def update_cross_overs(self, parameters, curve_data):
        for model, key in enumerate(models.MODEL_KEYS):
            first_co, second_co = models.crossover_frequencies(model, parameters, curve_data["frequencies"],
                                                               curve_data[f"recm_{self.curve_keys[model]}"])
            parameters["1st_cross_over"][key] = first_co
            parameters["2nd_cross_over"][key] = second_co

    # GRAPH METHODS
    # Get the styling of the graph
    def get_graph_styling(self):
        graph_style_parameters = {
            'font_family': self.graph_settings.qt_combo_font_family.currentText().lower(),
            'axis_style': {'fontsize': self.graph_settings.qt_spinbox_axis_title_size.value(),
                           'fontweight': self.graph_settings.qt_combo_axis_font_weight.currentText().lower(),
                           'fontstyle': self.graph_settings.qt_combo_axis_font_style.currentText().lower(),
                           'color': '#000000',
                           'labelpad': self.graph_settings.qt_spinbox_axis_title_padding.value()
                           },
            'tick_style': {'fontsize': self.graph_settings.qt_spinbox_tick_size.value(),
                           'fontweight': self.graph_settings.qt_combo_tick_font_weight.currentText().lower(),
                           'fontstyle': self.graph_settings.qt_combo_tick_font_style.currentText().lower(),
                           'color': '#000000',
                           'labelpad': self.graph_settings.qt_spinbox_tick_label_padding.value(),
                           'majortickvisibility': self.graph_settings.qt_checkbox_major_tick_visibility.isChecked(),
                           'majortickdirection': self.graph_settings.qt_combo_major_tick_direction.currentText().lower(),
                           'majorticklength': self.graph_settings.qt_spinbox_major_tick_length.value(),
                           'majortickwidth': self.graph_settings.qt_spinbox_major_tick_width.value(),
                           'minortickvisibility': self.graph_settings.qt_checkbox_minor_tick_visibility.isChecked(),
                           'minortickdirection': self.graph_settings.qt_combo_minor_tick_direction.currentText().lower(),
                           'minorticklength': self.graph_settings.qt_spinbox_minor_tick_length.value(),
                           'minortickwidth': self.graph_settings.qt_spinbox_minor_tick_width.value()
                           },
            'grid_style': {'hgridvisibility': self.graph_settings.qt_checkbox_h_grid_visibility.isChecked(),
                           'hgridlinestyle': self.graph_settings.qt_combo_h_grid_style.currentText().lower(),
                           'hgridlinewidth': self.graph_settings.qt_spinbox_h_grid_width.value(),
                           'hgridalpha': self.graph_settings.qt_spinbox_h_grid_transparency.value(),
                           'vgridvisibility': self.graph_settings.qt_checkbox_v_grid_visibility.isChecked(),
                           'vgridlinestyle': self.graph_settings.qt_combo_v_grid_style.currentText().lower(),
                           'vgridlinewidth': self.graph_settings.qt_spinbox_v_grid_width.value(),
                            'vgridalpha': self.graph_settings.qt_spinbox_v_grid_transparency.value()
                           },
            'legend_style': {'visibility': self.graph_settings.qt_checkbox_legend_visibility.isChecked(),
                             'fontsize': self.graph_settings.qt_spinbox_legend_font_size.value(),
                             'fontweight': self.graph_settings.qt_combo_legend_font_weight.currentText().lower(),
                             'fontstyle': self.graph_settings.qt_combo_legend_font_style.currentText().lower(),
                             'position': self.graph_settings.qt_combo_legend_position.currentText().lower(),
                             },
            'frame_style': {'linewidth': self.graph_settings.qt_spinbox_frame_width.value(),
                            'topvisbility': self.graph_settings.qt_checkbox_frame_top_visibility.isChecked(),
                            'bottomvisbility': self.graph_settings.qt_checkbox_frame_bottom_visibility.isChecked(),
                            'leftvisbility': self.graph_settings.qt_checkbox_frame_left_visibility.isChecked(),
                            'rightvisbility': self.graph_settings.qt_checkbox_frame_right_visibility.isChecked()
                            }
            }

        return graph_style_parameters

    # Update the styling of the graph
    def update_graph_styling(self):
        self.graph_style_parameters = self.get_graph_styling()
        self.qt_graph_widget.format_graph(y_index=self.graph_y_index, style_params=self.graph_style_parameters)
        self.qt_graph_widget.canvas.draw()

    # Refresh the graph with new data
    def refresh_graph(self, focus_curve_id=None):
        # While a project is loaded, the graph is drawn once at the end
        if self.loading:
            return

        # Group results are calculated once per refresh (widgets and graph share them)
        self.group_results = {}

        self.qt_graph_widget.canvas.axes.clear()
        # Some local_vars
        self.graph_y_index = 0
        curves = [
            "frequencies",
            "recm_homogenous_particle",
            "depforce_homogenous_particle",
            "imcm_homogenous_particle",
            "recm_single_shell",
            "depforce_single_shell",
            "imcm_single_shell",
            "recm_two_shell",
            "depforce_two_shell",
            "imcm_two_shell",
            "recm_three_shell",
            "depforce_three_shell",
            "imcm_three_shell",
            "recm_four_shell",
            "depforce_four_shell",
            "imcm_four_shell"]

        if self.qt_button_display_experimental_area.property("customState"):
            self.qt_graph_widget.scatter_style = 'area'
        elif self.qt_button_display_experimental_stdev.property("customState"):
            self.qt_graph_widget.scatter_style = 'scatter'

        # Group plots: only the replicate groups (mean ± SD) and the curves linked to them
        if self.active_plots_tab() == 2:
            self.draw_groups(curves)
            self.sort_plot_list("groups")
            self.update_link_widgets()
            self.update_separation()
            self.update_graph_styling()
            return

        # Add all curves to the graph
        if self.qt_checkbox_curves_visibility.isChecked():
            for key in self.curves_dict.keys():
                self.curves_dict[key]["widget"].setEnabled(True)
                if self.curves_dict[key]["visibility"]:
                    # Get index of the button that is active in type of graph content
                    for index, button in enumerate(self.qt_frame_toolbar_graphcontent.findChildren(QPushButton)):
                        if button.property("customState"):
                            # Calculate the index of data depending on selected model and type of graph content
                            new_index = self.curves_dict[key]["model"] * 3 + index + 1
                            self.qt_graph_widget.update_curve(name=self.curves_dict[key]["name"],
                                                                color=self.curves_dict[key]["color"],
                                                                line_style=self.curves_dict[key]["line_style"],
                                                                x_data=self.curves_dict[key]["curves"]["frequencies"],
                                                                y_data=self.curves_dict[key]["curves"][curves[new_index]],
                                                                line_width=self.curves_dict[key]["line_width"])
                            self.graph_y_index = index
                            break
        else:
            for key in self.curves_dict.keys():
                self.curves_dict[key]["widget"].setEnabled(False)

        if self.qt_checkbox_scatters_visibility.isChecked():
            for key in self.scatter_dict.keys():
                self.scatter_dict[key]["widget"].setEnabled(True)
                # A scatter linked to a curve is hidden with the curve
                linked_curve = links.linked_curve(self.curves_dict, "scatter", key)
                hidden_with_curve = linked_curve is not None and not self.curves_dict[linked_curve]["visibility"]
                if self.scatter_dict[key]["visibility"] and not hidden_with_curve:
                    # Get index of the button that is active in type of graph content
                    for index, button in enumerate(self.qt_frame_toolbar_graphcontent.findChildren(QPushButton)):
                        if button.property("customState"):
                            button_index = index
                    if button_index == 0:
                        drawn = self.scatter_dict[key]["scatter"]
                        self.qt_graph_widget.update_scatter(name=self.scatter_dict[key]["name"],
                                                            color=self.scatter_dict[key]["color"],
                                                            x_data=drawn["frequencies"],
                                                            y_data=drawn["recm_values"],
                                                            y_errors=drawn["recm_errors"],
                                                            point_style=self.scatter_dict[key]["point_style"],
                                                            point_size=self.scatter_dict[key]["point_size"])

        else:
            for key in self.scatter_dict.keys():
                self.scatter_dict[key]["widget"].setEnabled(False)

        self.sort_plot_list(["curves", "scatters"][self.active_plots_tab()])
        self.update_link_widgets()

        # Format the graph and draw it
        self.update_graph_styling()

    # Index of the plots tab in use: 0 Curve plots, 1 Scatter plots, 2 Group plots
    def active_plots_tab(self):
        buttons = getattr(self, "qt_plots_buttons", [])        # not set yet while the window is built
        return next((i for i, b in enumerate(buttons) if b.property("customState")), 0)

    # SORTING - the order of the cards in the plot lists (Sort drop-down of each list, see src/func/sorting.py)
    # Each list: its items, Sort drop-down, scroll area and the layout of its cards
    def plot_lists(self):
        return {"curves": (self.curves_dict, self.qt_combo_curves_sort, self.qt_scrollarea_plots_curve,
                           self.qt_scrollarea_plots_curve_layout),
                "scatters": (self.scatter_dict, self.qt_combo_scatters_sort, self.qt_scrollarea_scatter_curves,
                             self.qt_scrollarea_scatter_curves_layout),
                "groups": (self.groups_dict, self.qt_combo_groups_sort, self.qt_scrollarea_groups,
                           self.qt_scrollarea_groups_layout)}

    # Put the cards of a list in the chosen order. Only the list of the visible plots tab is sorted at each refresh of
    # the graph (switching tabs refreshes it). Nothing moves while the user works in a card of the list (the keyboard
    # focus is in it, e.g. typing a name or a value): the list is sorted when the focus leaves it
    def sort_plot_list(self, kind):
        items, combo, area, layout = self.plot_lists()[kind]
        focus = QApplication.focusWidget()
        if focus is not None and area.isAncestorOf(focus):
            self.sort_pending.add(kind)
            return
        self.sort_pending.discard(kind)

        mode = combo.currentData()
        order = sorting.sort_ids(items, mode, lambda i: items[i]["name"], self.sort_value(kind, mode))
        wanted = [items[i]["widget"] for i in order if layout.indexOf(items[i]["widget"]) >= 0]
        current = [layout.itemAt(i).widget() for i in range(layout.count())]
        if [card for card in current if card in wanted] == wanted:
            return
        for card in wanted:                            # deleted cards (closed) and the spacers stay at the end
            layout.removeWidget(card)
        for index, card in enumerate(wanted):
            layout.insertWidget(index, card)

    def sort_pending_lists(self, old=None, new=None):
        for kind in list(self.sort_pending):
            self.sort_plot_list(kind)

    # What a list is sorted on besides newest / oldest / name: a function of the id, or None (no such order)
    def sort_value(self, kind, mode):
        if kind == "curves" and mode == "model":
            return lambda i: self.curves_dict[i]["model"]
        if kind == "curves" and mode in ("first_crossover", "second_crossover"):
            return lambda i: self.curve_crossover(self.curves_dict[i], mode)
        if kind == "scatters" and mode == "first_crossover":
            return self.scatter_crossover
        if kind == "scatters" and mode == "group":
            return self.scatter_group_key
        if kind == "groups" and mode in ("first_crossover", "second_crossover"):
            return lambda i: self.group_crossover(i, mode)
        return None

    # Crossover frequency of a curve's model, None when it has none
    def curve_crossover(self, curve, which="first_crossover"):
        key = "1st_cross_over" if which == "first_crossover" else "2nd_cross_over"
        return sorting.frequency_or_none(curve["parameters"][key].get(models.MODEL_KEYS[curve["model"]]))

    # 1st crossover of a scatter: that of its linked curve, or else where its measured values change sign
    def scatter_crossover(self, scatter_id):
        curve_id = self.curve_linked_to("scatter", scatter_id)
        crossover = self.curve_crossover(self.curves_dict[curve_id]) if curve_id is not None else None
        if crossover is None:
            data = self.scatter_dict[scatter_id]["scatter"]
            crossover = next(iter(sorting.data_crossovers(data["frequencies"], data["recm_values"])), None)
        return crossover

    # Groups of a scatter, by name: the first one (None when it is in no group)
    def scatter_group_key(self, scatter_id):
        return min((sorting.natural_key(group["name"]) for group in self.groups_dict.values()
                    if any(m["scatter"] == scatter_id for m in group["members"])), default=None)

    # Mean crossover of a group's replicate curves, or else where its mean changes sign
    def group_crossover(self, group_id, which):
        result = self.group_result(group_id)
        stats = result["model"][which]
        crossover = sorting.frequency_or_none(stats["mean"]) if stats else None
        if crossover is None:
            crossovers = sorting.data_crossovers(result["average"]["frequencies"], result["average"]["values"])
            index = 0 if which == "first_crossover" else 1
            crossover = crossovers[index] if len(crossovers) > index else None
        return crossover

    # Names, links and group make-up shown on the curve and group widgets. Only the widgets of the visible plots tab are
    # updated (with many groups, rebuilding the hidden ones made every refresh slow); a tab's widgets are brought up
    # to date when it is shown, since switching tabs refreshes the graph
    def update_link_widgets(self):
        tab = self.active_plots_tab()
        if tab == 0:
            for curve in self.curves_dict.values():
                curve["widget"].update_links()
        elif tab == 2:
            for group in self.groups_dict.values():
                group["widget"].update_members()

    # Group plots: per visible group one scatter, the mean ± SD of its replicates (frequencies measured once as open
    # markers), and one curve, that of the mean parameters of the replicates' curves, each in its own style
    def draw_groups(self, curve_keys):
        content = next((i for i, b in enumerate(self.qt_graphcontent_buttons) if b.property("customState")), 0)
        self.graph_y_index = content
        for group_id, group in self.groups_dict.items():
            if not group["visibility"]:
                continue
            result = self.group_result(group_id)
            mean_curve = result["mean_curve"]
            if mean_curve is not None:
                self.qt_graph_widget.update_curve(
                    name=mean_curve["name"], color=group["color"], line_style=group["line_style"],
                    x_data=mean_curve["curves"]["frequencies"],
                    y_data=mean_curve["curves"][curve_keys[mean_curve["model"] * 3 + content + 1]],
                    line_width=group["line_width"])
            if content != 0 or not group["members"]:
                continue                                     # measured points are Re[CM] values
            average = result["average"]
            averaged = [i for i, kind in enumerate(average["kind"]) if kind != "single"]
            single = [i for i, kind in enumerate(average["kind"]) if kind == "single"]
            if averaged:
                self.qt_graph_widget.update_scatter(
                    name=group["name"], color=group["color"],
                    x_data=[average["frequencies"][i] for i in averaged],
                    y_data=[average["values"][i] for i in averaged],
                    y_errors=[average["errors"][i] for i in averaged],
                    point_style=group["point_style"], point_size=group["point_size"])
            if single and self.qt_checkbox_group_single_points.isChecked():
                self.qt_graph_widget.update_points(
                    name=f"{group['name']} (measured once)", color=group["color"],
                    x_data=[average["frequencies"][i] for i in single],
                    y_data=[average["values"][i] for i in single],
                    point_style=group["point_style"], point_size=group["point_size"])

    # Best separation (bottom of Group plots): of the visible groups, the pair ranked first by the chosen criterion
    # (Rank by: separation score, crossover ratio or ΔRe[CM]; see separation.py); the other pairs are listed in the
    # card's tooltip, each entry explains itself in its own
    def update_separation(self):
        groups = [self.separation_input(group_id) for group_id, group in self.groups_dict.items()
                  if group["visibility"]]
        pairs = separation.rank_pairs(groups, self.separation_rank)

        values = {"frequency": self.qt_label_separation_frequency, "score": self.qt_label_separation_score,
                  "ratio": self.qt_label_separation_ratio, "contrast": self.qt_label_separation_contrast,
                  "second": self.qt_label_separation_second}
        for key, tip in separation_help.value_tooltips(pairs[0] if pairs else None).items():
            values[key].setToolTip(tip)
        if not pairs:
            usable = sum(1 for g in groups if g["samples"])
            self.qt_label_separation_pair.setText(f"needs 2 groups with crossovers ({usable} now)")
            for label in values.values():
                label.setText("–")
            self.qt_frame_separation.setToolTip("Needs two visible groups whose curves have a first crossover, "
                                                "measured over a common frequency range")
            return

        # Each group with how many of its samples are on its side at the best frequency (why the pair scores so)
        def name(group, kind, on_side, samples):
            return f"<span style='color:{group['color']}'>●</span> {group['name']} <span style='color:#64748B'>" \
                   f"{kind} {on_side}/{samples}</span>"

        best = pairs[0]
        (pdep_in, pdep_out), (ndep_in, ndep_out) = best["pdep_samples"], best["ndep_samples"]
        self.qt_label_separation_pair.setText(f"{name(best['pdep'], 'pDEP', pdep_in, pdep_in + pdep_out)} "
                                              f"&nbsp;·&nbsp; {name(best['ndep'], 'nDEP', ndep_out, ndep_in + ndep_out)}")
        self.qt_label_separation_frequency.setText(format_frequency(best["frequency"]))
        self.qt_label_separation_score.setText(f"{best['score']:.2f}")
        self.qt_label_separation_ratio.setText(f"{best['ratio']:.2f}×" if best["ratio"] else "–")
        self.qt_label_separation_contrast.setText(
            f"{best['contrast']:.2f} ({best['recm_pdep']:+.2f} / {best['recm_ndep']:+.2f})"
            if best["contrast"] is not None else "–")
        second = best["second"]
        self.qt_label_separation_second.setText(
            f"{second['score']:.2f} at {format_frequency(second['frequency'])}   ({second['pdep']['name']} pDEP)"
            if second else "– (second crossovers not both in the measured range)")
        others = [f"{rank}. {p['pdep']['name']} + {p['ndep']['name']}: score {p['score']:.2f}, ratio "
                  + (f"{p['ratio']:.2f}×" if p["ratio"] else "–") + ", ΔRe[CM] "
                  + (f"{p['contrast']:.2f}" if p["contrast"] is not None else "–")
                  + f" at {format_frequency(p['frequency'])} (pDEP {p['pdep_samples'][0]}/{sum(p['pdep_samples'])},"
                  f" nDEP {p['ndep_samples'][1]}/{sum(p['ndep_samples'])})" for rank, p in enumerate(pairs[1:], 2)]
        self.qt_frame_separation.setToolTip(f"Other pairs, ranked by {separation.RANKINGS[self.separation_rank]}:\n"
                                            + "\n".join(others) if others else "")

    # Rank the pairs of Best separation by "score", "ratio" or "contrast" (separation.RANKINGS; kept in the project)
    def set_separation_rank(self, key):
        self.separation_rank = key if key in separation.RANKINGS else "score"
        for name, button in self.qt_separation_rank_buttons.items():
            button.setProperty("customState", name == self.separation_rank)
            button.setStyle(button.style())                   # refresh style to apply property
        if not self.loading and self.active_plots_tab() == 2:
            self.update_separation()

    # A group as separation.py needs it: its samples' crossovers, mean first crossover, the frequency range its
    # scatters were measured over and the Re[CM] of its mean-parameter curve
    def separation_input(self, group_id):
        group = self.groups_dict[group_id]
        result = self.group_result(group_id)
        mean_curve = result["mean_curve"]
        recm = None
        if mean_curve is not None:
            recm = (lambda f, c=mean_curve: models.model_all(c["model"], np.atleast_1d(np.asarray(f, dtype=float)),
                                                             c["parameters"])[0])
        measured = [float(f) for m in group["members"] if m["scatter"] in self.scatter_dict
                    for f in self.scatter_dict[m["scatter"]]["scatter"]["frequencies"] if float(f) > 0]
        first = result["model"]["first_crossover"]
        return {"name": group["name"], "color": group["color"], "samples": separation.samples(result["curves"]),
                "recm": recm, "first_crossover": first["mean"] if first else None,
                "range": (min(measured), max(measured)) if measured else (None, None)}

    # Statistics report of the visible groups: every pair ranked by separation, descriptive statistics, normality
    # and pairwise tests of the crossovers and parameters (see group_statistics.py), as PDF and / or Excel
    def statistics_report(self, file_path=None, selected_filter=""):
        group_ids = [i for i, g in self.groups_dict.items() if g["visibility"] and g["members"]]
        if len(group_ids) < 2:
            QMessageBox.warning(self, APP_NAME, "The statistics report compares groups: it needs at least two "
                                                "visible groups with replicates.")
            return None
        filters = {"both": "PDF report and Excel workbook (*.pdf)", ".pdf": "PDF report (*.pdf)",
                   ".xlsx": "Excel workbook, also for LibreOffice Calc (*.xlsx)"}
        if file_path is None:
            folder = Path(self.project["path"]).parent if self.project else Path.home()
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "Save statistics report", str(Path(folder) / "statistics_report.pdf"),
                ";;".join(filters.values()))
            if not file_path:
                return None
        kind = next((k for k, f in filters.items() if f == selected_filter), None)
        path = Path(file_path)
        if kind is None:
            kind = ".xlsx" if path.suffix.lower() == ".xlsx" else ".pdf"
        if kind in ("both", ".pdf"):
            path = path.with_suffix(".pdf")
        else:
            path = path.with_suffix(".xlsx")

        groups = []
        for group_id in group_ids:
            group = self.groups_dict[group_id]
            result = self.group_result(group_id)
            summary = result["average"]["summary"]
            groups.append({"name": group["name"], "color": group["color"], "model": result["model"]["model"],
                           "curves": result["curves"], "n_biological": summary["n_biological"],
                           "n_technical": sum(summary["technical_per_biological"].values()),
                           "separation": self.separation_input(group_id)})
        report = group_statistics.build_report(groups, self.separation_rank)
        project_name = self.project["name"] if self.project else ""

        written = []
        try:
            if kind in ("both", ".pdf"):
                plots = []
                for group_id in group_ids:
                    group, result = self.groups_dict[group_id], self.group_result(group_id)
                    mean_curve, average = result["mean_curve"], result["average"]
                    plots.append({"name": group["name"], "color": group["color"],
                                  "curve": (mean_curve["curves"]["frequencies"],
                                            mean_curve["curves"][f"recm_{self.curve_keys[mean_curve['model']]}"])
                                  if mean_curve is not None else None,
                                  "points": (average["frequencies"], average["values"], average["errors"])
                                  if average["frequencies"] else None})
                best = next((p for p in report["pairs"] if p["score"] is not None), None)
                figure = statistics_report.report_figure(
                    plots, best["frequency"] if best else None,
                    f"best separation: {best['a']} / {best['b']}" if best else "")
                html = statistics_report.report_html(report, project_name, image="groups.png")
                write_pdf(html, path, {"groups.png": figure}, title=statistics_report.TITLE)
                written.append(path)
            if kind in ("both", ".xlsx"):
                statistics_report.write_xlsx(report, path.with_suffix(".xlsx"), project_name)
                written.append(path.with_suffix(".xlsx"))
        except OSError as error:
            QMessageBox.warning(self, APP_NAME, f"Could not write the report:\n{error}")
            return None
        return written

    # When the window is resized, resize the graph
    def resizeEvent(self, event=None):
        # Get size of figure in the graph
        new_graph_size = self.qt_graph_widget.get_figure_size()
        QMainWindow.resizeEvent(self, event)
        # Check if self.qt_graph_widget is resized
        if self.qt_graph_widget.size() != event.oldSize():
            self.qt_graph_widget.set_tight_layout()
            if not self.qt_entry_graph_width.isEnabled():
                self.qt_entry_graph_width.setText(str(int(new_graph_size[0])))
            if not self.qt_entry_graph_height.isEnabled():
                self.qt_entry_graph_height.setText(str(int(new_graph_size[1])))

    # Resize the graph to the values in the entry fields
    def resize_to_entry(self):
        # Get current DPI and size of the figure
        graph_dpi = self.qt_graph_widget.figure.get_dpi()
        graph_width = self.qt_graph_widget.figure.get_size_inches()[0] * graph_dpi
        graph_height = self.qt_graph_widget.figure.get_size_inches()[1] * graph_dpi

        # Calculate the size difference between the window and the graph
        old_graph_size = [graph_width, graph_height]
        old_window_size = [self.width(), self.height()]
        remaining_space = [old_window_size[0] - old_graph_size[0], old_window_size[1] - old_graph_size[1]]

        # Get the new desired graph size from entries
        new_graph_size_pixels = [int(self.qt_entry_graph_width.text()), int(self.qt_entry_graph_height.text())]
        new_graph_size_inches = [new_graph_size_pixels[0] / graph_dpi, new_graph_size_pixels[1] / graph_dpi]

        # Set the new size for the Matplotlib figure
        self.qt_graph_widget.figure.set_size_inches(new_graph_size_inches[0], new_graph_size_inches[1])

        # Update the widget and window size
        new_window_size = [new_graph_size_pixels[0] + remaining_space[0], new_graph_size_pixels[1] + remaining_space[1]]
        self.resize(int(new_window_size[0]), int(new_window_size[1]))

        # Set the size of the widget containing the figure
        self.qt_graph_widget.setFixedSize(new_graph_size_pixels[0], new_graph_size_pixels[1])

        # Apply tight layout if needed and redraw the canvas
        self.qt_graph_widget.set_tight_layout()
        self.qt_graph_widget.canvas.draw()

        print("Resized")

    # Lock the graph widget size
    def lock_graph_widget_size(self):
        if self.qt_checkbox_graph_size_lock.isChecked():
            self.qt_entry_graph_width.setDisabled(False)
            self.qt_entry_graph_height.setDisabled(False)
            # Restrict resizing of the graph
            self.qt_graph_widget.setFixedSize(self.qt_graph_widget.size())
            self.qt_graph_widget.set_tight_layout()

        else:
            self.qt_entry_graph_width.setDisabled(True)
            self.qt_entry_graph_height.setDisabled(True)
            # Allow resizing of the graph
            self.qt_graph_widget.setMinimumSize(0, 0)
            self.qt_graph_widget.setMaximumSize(16777215, 16777215)
            self.qt_graph_widget.set_tight_layout()

    # PROJECT METHODS - new, open, save, recent projects
    # Everything a project saves: the scatters and curves (in creation order) and the view settings
    def get_project_state(self):
        scatters = [opendep_files.spectrum_file_data(item) for item in self.scatter_dict.values()]
        curves = [opendep_files.curve_file_data(item) for item in self.curves_dict.values()]
        active = lambda buttons: next((i for i, b in enumerate(buttons) if b.property("customState")), 0)
        settings = {"graph_content": active(self.qt_graphcontent_buttons),
                    "experimental_display": active(self.qt_experimentaldisplay_buttons),
                    "frequency_range": {"start": self.qt_entry_param_freq_start.text(),
                                        "start_unit": self.qt_combo_param_freq_start_unit.currentIndex(),
                                        "stop": self.qt_entry_param_freq_stop.text(),
                                        "stop_unit": self.qt_combo_param_freq_stop_unit.currentIndex()},
                    "curves_visible": self.qt_checkbox_curves_visibility.isChecked(),
                    "scatters_visible": self.qt_checkbox_scatters_visibility.isChecked(),
                    "graph_settings": self.graph_settings.get_values()}

        settings["plots_tab"] = self.active_plots_tab()
        settings["group_single_points"] = self.qt_checkbox_group_single_points.isChecked()
        settings["sort"] = {kind: combo.currentData() for kind, (_, combo, _, _) in self.plot_lists().items()}
        settings["separation_rank"] = self.separation_rank
        scatter_index = {scatter_id: i for i, scatter_id in enumerate(self.scatter_dict)}
        curve_index = {curve_id: i for i, curve_id in enumerate(self.curves_dict)}
        groups = []
        for group in self.groups_dict.values():
            saved = {key: value for key, value in group.items() if key not in ("widget", "members", "joint_curve")}
            saved["members"] = [{"scatter": scatter_index[m["scatter"]], "biological": m["biological"]}
                                for m in group["members"] if m["scatter"] in scatter_index]
            if group.get("joint_curve") in curve_index:
                saved["joint_curve"] = curve_index[group["joint_curve"]]
            groups.append(saved)
        curve_links = links.links_to_indices(self.curves_dict, list(self.curves_dict), list(self.scatter_dict),
                                             list(self.groups_dict))
        return {"scatters": scatters, "curves": curves, "groups": groups, "links": curve_links,
                "settings": settings}

    # Compact text of the project state, compared with the saved one to find unsaved changes
    def get_state_snapshot(self):
        return json.dumps(self.get_project_state(), cls=NumpyEncoder, sort_keys=True)

    def has_unsaved_changes(self):
        return self.project is not None and self.get_state_snapshot() != self.saved_state

    # Remove all scatters and curves
    def clear_workspace(self):
        for items in (self.scatter_dict, self.curves_dict, self.groups_dict):
            for item in items.values():
                item["widget"].close()
                item["widget"].deleteLater()
            items.clear()

    # Put the settings of a project back on the widgets
    def apply_project_settings(self, settings):
        frequency_range = settings.get("frequency_range")
        if frequency_range:
            self.qt_entry_param_freq_start.setText(str(frequency_range["start"]))
            self.qt_combo_param_freq_start_unit.setCurrentIndex(frequency_range["start_unit"])
            self.qt_entry_param_freq_stop.setText(str(frequency_range["stop"]))
            self.qt_combo_param_freq_stop_unit.setCurrentIndex(frequency_range["stop_unit"])

        self.graph_settings.set_values(settings.get("graph_settings", {}))
        self.qt_checkbox_curves_visibility.setChecked(settings.get("curves_visible", True))
        self.qt_checkbox_scatters_visibility.setChecked(settings.get("scatters_visible", True))

        self.qt_checkbox_group_single_points.setChecked(settings.get("group_single_points", True))
        for kind, (_, combo, _, _) in self.plot_lists().items():
            index = combo.findData((settings.get("sort") or {}).get(kind, sorting.DEFAULT_SORT))
            combo.setCurrentIndex(max(index, 0))
        self.set_separation_rank(settings.get("separation_rank", "score"))

        for buttons, key in ((self.qt_graphcontent_buttons, "graph_content"),
                             (self.qt_experimentaldisplay_buttons, "experimental_display"),
                             (self.qt_plots_buttons, "plots_tab")):
            index = settings.get(key, 0)
            buttons[index if 0 <= index < len(buttons) else 0].click()

    # Show the open project in the header, the workspace or the welcome screen, and the recent projects
    def update_project_display(self):
        if self.project:
            saved = f"   ·   Saved {self.project['saved']}" if "saved" in self.project else ""
            self.qt_label_header_project.setText(f"{self.project['name']}   ·   {self.project['path']}{saved}")
            self.qt_label_header_project.setToolTip(self.project["path"])
            self.setWindowTitle(f"{self.project['name']} - {APP_NAME}")
        else:
            self.qt_label_header_project.setText("No project open")
            self.setWindowTitle(APP_NAME)

        self.qt_stack_main.setCurrentWidget(self.qt_page_workspace if self.project else self.qt_page_welcome)
        self.qt_button_project_save.setEnabled(self.project is not None)
        self.welcome_widget.set_recent_projects(self.get_recent_projects())

    def get_recent_projects(self):
        value = self.settings.value("recent_projects", [])
        items = [value] if isinstance(value, str) else list(value or [])
        return [path for path in items if project_files.is_project(path)]

    def remember_project(self, path):
        self.settings.setValue("recent_projects", project_files.update_recent(self.get_recent_projects(), path))

    # Where the project dialogs start: the folder of the last project
    def project_dialog_folder(self):
        recent = self.get_recent_projects()
        return Path(recent[0]).parent if recent else Path.home()

    # Ask to save the changes of the open project; False when the user cancels
    def confirm_discard(self):
        if not self.has_unsaved_changes():
            return True

        answer = QMessageBox.question(self, APP_NAME, f"Save the changes to the project {self.project['name']}?",
                                      QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
                                      | QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            return self.save_project()
        return answer == QMessageBox.StandardButton.Discard

    # New project: an empty workspace, saved as a new project file (the view settings in use are kept)
    def new_project(self):
        if not self.confirm_discard():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "New project", str(self.project_dialog_folder() / f"New project{project_files.PROJECT_SUFFIX}"),
            PROJECT_FILTER.split(";;")[0])
        if not path:
            return

        try:
            project = project_files.create_project(path)
        except (project_files.ProjectError, OSError) as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return

        self.clear_workspace()
        self.refresh_graph()
        self.set_project(project)

    def open_project_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open project", str(self.project_dialog_folder()), PROJECT_FILTER)
        if path:
            self.open_project(path)

    # Open a project file (or an older project folder); tell what could not be read or was converted
    def open_project(self, path):
        if self.project and Path(path).absolute() == Path(self.project["path"]):
            return
        if not self.confirm_discard():
            return

        try:
            project = project_files.read_project(path)
        except project_files.ProjectError as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return

        # Load everything with the graph frozen, then draw once
        self.loading = True
        try:
            self.clear_workspace()
            self.apply_project_settings(project["settings"])
            scatter_ids = [self.generate_new_scatter(type="load", data=data) for data in project["scatters"]]
            curve_ids = [self.add_curve(data) for data in project["curves"]]
            group_ids = []
            for group in project["groups"]:
                group_ids.append(self.generate_new_group(
                    group["name"], [{"scatter": scatter_ids[m["scatter"]], "biological": m["biological"]}
                                    for m in group["members"]], group))
                if isinstance(group.get("joint_curve"), int) and 0 <= group["joint_curve"] < len(curve_ids):
                    self.groups_dict[group_ids[-1]]["joint_curve"] = curve_ids[group["joint_curve"]]
            links.links_from_indices(self.curves_dict, self.scatter_dict, project["links"], curve_ids, scatter_ids,
                                     group_ids)
        finally:
            self.loading = False
        self.refresh_graph()

        self.set_project(project)
        if project.get("converted_from"):
            self.saved_state = None                    # unsaved: closing asks to save the new file
            QMessageBox.information(self, APP_NAME, f"This is a project folder of an older version. Save writes it "
                                                    f"as one file:\n\n{project['path']}\n\nThe folder is left as "
                                                    f"it is; you can delete it once the new file is saved.")
        if project["missing"]:
            QMessageBox.warning(self, APP_NAME, "The project opened, but these parts could not be read and are left "
                                                "out (saving now removes them; the .bak file keeps the previous "
                                                "version):\n" + "\n".join(project["missing"]))

    # Save the project; False when it could not be written
    def save_project(self):
        if self.project is None:
            return False

        state = self.get_project_state()
        try:
            project_files.write_project({**self.project, **state})
        except OSError as e:
            QMessageBox.warning(self, APP_NAME, f"The project could not be saved:\n{e}")
            return False

        self.saved_state = self.get_state_snapshot()
        self.project["saved"] = datetime.now().strftime("%H:%M")
        self.update_project_display()
        return True

    def set_project(self, project):
        self.project = {"name": project["name"], "path": project["path"]}
        self.saved_state = self.get_state_snapshot()
        self.remember_project(project["path"])
        self.update_project_display()

        # Files that came while no project was open (see open_files)
        if self.pending_files:
            files, self.pending_files = self.pending_files, []
            self.open_files(files)

    # FILES FROM OUTSIDE - command line, a second start of View, OpenDEP Compute's Send to View, drag and drop
    # OpenDEP files are added to the open project (like Open file); without a project they wait until one is created
    # or opened. Returns the paths that were added.
    def open_files(self, paths):
        # A project file (double-click, a second start of View) opens as the project
        projects = [str(p) for p in paths if Path(p).suffix.lower() == project_files.PROJECT_SUFFIX]
        if projects:
            self.bring_to_front()
            self.open_project(projects[0])
        paths = [str(p) for p in paths if Path(p).suffix.lower() in opendep_files.OPEN_SUFFIXES]
        if not paths:
            return []
        self.bring_to_front()
        if self.project is None:
            self.pending_files.extend(p for p in paths if p not in self.pending_files)
            names = ", ".join(Path(p).name for p in self.pending_files)
            QMessageBox.information(self, APP_NAME, f"Create or open a project to add {names}: the files are added "
                                                    "as soon as a project is open.")
            return []

        added, problems = [], []
        self.loading = True                            # draw once, at the end
        try:
            for path in paths:
                try:
                    kind, data = opendep_files.read_opendep_file(path)
                except (opendep_files.OpenDEPFileError, OSError) as e:
                    problems.append(f"{Path(path).name}: {e}")
                    continue
                if kind == "curve":
                    self.add_curve(data)
                elif kind == "fit":
                    self.add_fit(data)
                else:
                    self.generate_new_scatter(type="load", data=data)
                added.append(path)
        finally:
            self.loading = False
        self.refresh_graph()
        if problems:
            QMessageBox.warning(self, APP_NAME, "These files could not be opened:\n" + "\n".join(problems))
        return added

    # Show the window in front (files sent from another program)
    def bring_to_front(self):
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(Path(url.toLocalFile()).suffix.lower() in opendep_files.OPEN_SUFFIXES for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.open_files([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()

    # HELP - Help button and F1: the user guide (docs/) at the page of the place in use
    def help_page(self):
        if self.qt_stack_main.currentWidget() is self.qt_page_welcome:
            return HELP_PAGES["welcome"]
        return HELP_PAGES[["Curve plots", "Scatter plots", "Group plots"][self.active_plots_tab()]]

    def show_help(self, page=None):
        if self.help_widget is None:
            self.help_widget = HelpWidgetUI(parent=self)
        self.help_widget.show_page(page or self.help_page())
        return self.help_widget

    # BUG REPORTS - Report bug button, unhandled errors
    # The Report bug window, created on first use
    def get_bug_report_widget(self):
        if self.bug_report_widget is None:
            self.bug_report_widget = BugReportWidgetUI(parent=self)
        return self.bug_report_widget

    def show_bug_report(self):
        self.get_bug_report_widget().start_report()

    # Unhandled error: open the Report bug window with the traceback filled in
    def show_bug_report_for_error(self, error):
        self.get_bug_report_widget().show_error(error)

    # Where the program was when the bug was reported (written in the report header)
    def get_bug_report_context(self):
        graph_content = next((b.text() for b in self.qt_graphcontent_buttons if b.property("customState")), "")
        return {"screen": "workspace" if self.project else "welcome screen",
                "project": self.project["path"] if self.project else "none",
                "unsaved_changes": self.has_unsaved_changes(),
                "scatters": len(self.scatter_dict),
                "groups": ", ".join(f"{g['name']} ({len(g['members'])} scatters)" for g in self.groups_dict.values())
                          or "none",
                "plots_tab": ["Curve plots", "Scatter plots", "Group plots"][self.active_plots_tab()],
                "curves": ", ".join(f"{c['name']} ({self.curve_keys[c['model']]})" for c in self.curves_dict.values())
                          or "none",
                "graph": graph_content,
                "frequency_range": f"{self.qt_entry_param_freq_start.text()} "
                                   f"{self.qt_combo_param_freq_start_unit.currentText()} - "
                                   f"{self.qt_entry_param_freq_stop.text()} "
                                   f"{self.qt_combo_param_freq_stop_unit.currentText()}"}

    def closeEvent(self, event):
        if self.confirm_discard():
            event.accept()
        else:
            event.ignore()
