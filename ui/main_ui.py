import random

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QListView, QSizePolicy, QColorDialog, QWidget
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from matplotlib.figure import Figure
import numpy as np
import json

from src.func import models
from src.func import general
from src.classes.numpy_encoder import NumpyEncoder

from ui.helpers.curve_widget_ui import CurveWidgetUI
from ui.helpers.scatter_widget_ui import ScatterWidgetUI
from ui.resources import graphical_resources
from ui.helpers.graph_settings_ui import GraphSettingsUI
from ui.helpers.noise_widget_ui import NoiseWidgetUI

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

        # Load the main UI
        loadUi("ui/main.ui", self)
        self.setWindowTitle("OpenDEP Force Calculator")
        self.setWindowIcon(QIcon("icon.png"))

        # Create default parameters
        self.default_curve = None
        self.curves_dict = {}
        self.scatter_dict = {}
        self.no_curve_points = 100

        # Default styles
        self.point_styles = ["o", "s", "v", "+", "x", "*"]

        # Load the rest of the widgets
        self.graph_settings = GraphSettingsUI(parent=self)
        self.noise_widget = NoiseWidgetUI(parent=self)

        # Toolbar buttons
        self.pyqt5_button_save_figure.clicked.connect(self.pyqt5_graph_widget.save_figure)
        self.pyqt5_button_home_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.home)
        self.pyqt5_button_zoom_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.zoom)
        self.pyqt5_button_properties_figure.clicked.connect(self.graph_settings.open_graph_settings)
        self.pyqt5_button_fitspace_figure.clicked.connect(self.pyqt5_graph_widget.set_tight_layout)
        #self.pyqt5_button_resize_figure.clicked.connect(self.resize_graph)

        # Data buttons
        self.pyqt5_button_curve_load.clicked.connect(self.load_curve)
        self.pyqt5_button_scatter_add.clicked.connect(lambda: self.generate_new_scatter(type="new"))
        self.pyqt5_button_scatter_load.clicked.connect(self.load_scatter)

        # Hide Scrollbars
        self.pyqt5_scrollarea_plots_curve.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.pyqt5_scrollarea_plots_curve.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Graph content menubar, to toggle what is displayed on the graph
        self.pyqt5_graphcontent_buttons = self.pyqt5_frame_toolbar_graphcontent.findChildren(QPushButton)
        for button in self.pyqt5_graphcontent_buttons:
            button.clicked.connect(lambda: self.toggle_active_state(self.pyqt5_graphcontent_buttons))
            button.clicked.connect(self.refresh_graph)
        self.pyqt5_graphcontent_buttons[0].click()

        # Experimental data display menubar, to toggle how the experimental data is displayed
        self.pyqt5_experimentaldisplay_buttons = self.pyqt5_frame_menubar_experimental_display.findChildren(QPushButton)
        for button in self.pyqt5_experimentaldisplay_buttons:
            button.clicked.connect(lambda: self.toggle_active_state(self.pyqt5_experimentaldisplay_buttons))
        self.pyqt5_experimentaldisplay_buttons[0].click()

        # Plots menubar, to toggle what is displayed on the plots
        self.pyqt5_plots_buttons = self.pyqt5_frame_tabbar_plots.findChildren(QPushButton)
        self.pyqt5_plots_tab_widgets = [self.pyqt5_frame_group_curve_plots, self.pyqt5_frame_group_scatter_plots]
        for button in self.pyqt5_plots_buttons:
            button.clicked.connect(lambda: self.toggle_tabs(self.pyqt5_plots_buttons, self.pyqt5_plots_tab_widgets))
        self.pyqt5_plots_buttons[0].click()

        # Graph size lock and size entry - all functionality for resizing the graph
        self.pyqt5_checkbox_graph_size_lock.clicked.connect(self.lock_graph_widget_size)
        self.pyqt5_button_refresh_graph_size.clicked.connect(self.resize_to_entry)
        self.pyqt5_button_refresh_graph_size.setVisible(False)
        self.pyqt5_entry_graph_width.setDisabled(True)
        self.pyqt5_entry_graph_height.setDisabled(True)

        # ScrollArea buttons
        self.pyqt5_button_curves_add.clicked.connect(self.generate_new_curve)

        # Entry fields for the frequency range
        self.pyqt5_entry_param_freq_start.editingFinished.connect(self.modify_all_curves)
        self.pyqt5_entry_param_freq_stop.editingFinished.connect(self.modify_all_curves)
        self.pyqt5_combo_param_freq_start_unit.currentIndexChanged.connect(self.modify_all_curves)
        self.pyqt5_combo_param_freq_stop_unit.currentIndexChanged.connect(self.modify_all_curves)


    # Functionality for the menubar buttons and toggling the tabs
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

    # In Work, Graph Size functionality
    def resizeEvent(self, event=None):
        # Get size of figure in the graph
        new_graph_size = self.pyqt5_graph_widget.get_figure_size()
        QMainWindow.resizeEvent(self, event)
        # Check if self.pyqt5_graph_widget is resized
        if self.pyqt5_graph_widget.size() != event.oldSize():
            self.pyqt5_graph_widget.set_tight_layout()
            self.pyqt5_entry_graph_width.setText(str(int(new_graph_size[0])))
            self.pyqt5_entry_graph_height.setText(str(int(new_graph_size[1])))

    def resize_to_entry(self):
        dpi = int(self.pyqt5_graph_widget.figure.dpi)
        width = int(self.pyqt5_entry_graph_width.text()) / dpi
        height = int(self.pyqt5_entry_graph_height.text()) / dpi
        self.pyqt5_graph_widget.figure.set_size_inches(width, height)
        self.pyqt5_graph_widget.set_tight_layout()
        self.pyqt5_graph_widget.canvas.draw()

    def lock_graph_widget_size(self):
        if self.pyqt5_checkbox_graph_size_lock.isChecked():
            self.pyqt5_entry_graph_width.setDisabled(False)
            self.pyqt5_entry_graph_height.setDisabled(False)
            # Restrict resizing of the graph
            self.pyqt5_graph_widget.setFixedSize(self.pyqt5_graph_widget.size())
            self.pyqt5_graph_widget.set_tight_layout()
            self.pyqt5_button_refresh_graph_size.setVisible(True)

        else:
            self.pyqt5_entry_graph_width.setDisabled(True)
            self.pyqt5_entry_graph_height.setDisabled(True)
            # Allow resizing of the graph
            self.pyqt5_graph_widget.setMinimumSize(0, 0)
            self.pyqt5_graph_widget.setMaximumSize(16777215, 16777215)
            self.pyqt5_graph_widget.set_tight_layout()
            self.pyqt5_button_refresh_graph_size.setVisible(False)

    # Graph settings
    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            print(color.name())

    # Scatter functionality - add, modify, duplicate, delete, save, load
    def generate_new_scatter(self, type="new", duplicate_id=None, file_path=None):
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

            # Generate noise data
            scatter_data = self.noise_widget.generate_noise_scatter()

        # Handle in case a scatter is loaded
        elif type == "duplicate":
            name = self.scatter_dict[duplicate_id]["name"] + " - Copy"
            color = self.scatter_dict[duplicate_id]["color"]
            point_size = self.scatter_dict[duplicate_id]["point_size"]
            point_style = self.scatter_dict[duplicate_id]["point_style"]
            scatter_data = self.scatter_dict[duplicate_id]["scatter"]

        elif type == "load":
            with open(file_path, 'r') as file:
                data = json.load(file)
            name = data["name"]
            color = data["color"]
            point_size = data["point_size"]
            point_style = data["point_style"]
            scatter_data = data["scatter"]

        # Add the curve to the dictionary
        self.scatter_dict[id] = {"name": name,
                                "color": color,
                                "point_size": point_size,
                                "point_style": point_style,
                                "visibility": visibility,
                                "scatter": scatter_data,
                                "widget": scatter_widget}

        # Populate the widget with the data
        scatter_widget.id = id
        scatter_widget.parent_widget = self
        scatter_widget.set_entries_with_data()

        # Connect the buttons after the setup
        scatter_widget.connect_buttons_after_setup()

        # Refresh all graphs with new data
        self.refresh_graph()

        # Dock the widget at index 0 from the top
        self.pyqt5_scrollarea_scatter_curves_layout.insertWidget(0, scatter_widget)

    def delete_scatter(self, id):
        # Remove the curve from the dictionary
        del self.scatter_dict[id]

        # Refresh the graph
        self.refresh_graph()

    def save_scatter(self, id, file_path):
        # save all curve data to a json file from the dictionary
        data = self.scatter_dict[id].copy()
        data["widget"] = None

        with open(file_path, 'w') as file:
            json.dump(data, file, cls=NumpyEncoder)

        file.close()

    def load_scatter(self):
        # load curve data from a json file to the dictionary
        file_path, _ = QFileDialog.getOpenFileName(self, "Load scatter", "", "OpenDEP Scatter (*.ods)")

        if file_path:
            self.generate_new_scatter(type="load", file_path=file_path)

    # Curve functionality - add, modify, duplicate, delete, save, load
    def generate_new_curve(self):
        # Create a new curve widget
        new_curve_widget = CurveWidgetUI()

        # Create a new parameters list
        generated_parameters = self.create_default_curve_data()

        # Generate the curve data
        curve_data = self.generate_curve_data(generated_parameters)

        # Calculate the cross over frequency
        # Homogenous
        first_ho_co, second_ho_co = self.get_cross_over_freq(curve_data["frequencies"], curve_data["recm_homogenous_particle"])
        generated_parameters["1st_cross_over"]["homogenous"] = first_ho_co
        generated_parameters["2nd_cross_over"]["homogenous"] = second_ho_co
        # Single Shell
        first_ss_co, second_ss_co = self.get_cross_over_freq(curve_data["frequencies"], curve_data["recm_single_shell"])
        generated_parameters["1st_cross_over"]["single_shell"] = first_ss_co
        generated_parameters["2nd_cross_over"]["single_shell"] = second_ss_co
        ## TO ADD The Two-Shell model after is implemented fully
        generated_parameters["1st_cross_over"]["two_shell"] = 0.0
        generated_parameters["2nd_cross_over"]["two_shell"] = 0.0

        # Create Random ID which wont be already in the dictionary keys
        id = random.randint(0, 9999)
        while id in self.curves_dict.keys():
            id = random.randint(0, 9999)

        # Create base parameters for the curve
        color = general.get_random_color_hex()
        name = f"Curve {len(self.curves_dict) + 1}"
        visibility = True
        model = random.randint(0,1)
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
                                "widget": new_curve_widget}

        # Populate the widget with the data
        new_curve_widget.id = id
        new_curve_widget.parent_widget = self
        new_curve_widget.set_entries_with_data()

        # Refresh all graphs with new data
        self.refresh_graph()

        # Dock the widget at index 0 from the top
        self.pyqt5_scrollarea_plots_curve_layout.insertWidget(0, new_curve_widget)

    def modify_single_curve(self, id):
        # Update the parameters from entry fields of the widget
        parameters = self.curves_dict[id]["widget"].get_data_from_entries()
        self.curves_dict[id]["parameters"] = parameters

        # Generate the curve data
        curve_data = self.generate_curve_data(self.curves_dict[id]["parameters"])
        self.curves_dict[id]["curves"] = curve_data

        # Calculate the cross over frequency
        # Homogenous
        first_ho_co, second_ho_co = self.get_cross_over_freq(self.curves_dict[id]["curves"]["frequencies"], self.curves_dict[id]["curves"]["recm_homogenous_particle"])
        self.curves_dict[id]["parameters"]["1st_cross_over"]["homogenous"] = first_ho_co
        self.curves_dict[id]["parameters"]["2nd_cross_over"]["homogenous"] = second_ho_co
        # Single Shell
        first_ss_co, second_ss_co = self.get_cross_over_freq(self.curves_dict[id]["curves"]["frequencies"], self.curves_dict[id]["curves"]["recm_single_shell"])
        self.curves_dict[id]["parameters"]["1st_cross_over"]["single_shell"] = first_ss_co
        self.curves_dict[id]["parameters"]["2nd_cross_over"]["single_shell"] = second_ss_co
        ## TO ADD The Two-Shell model after is implemented fully
        first_ts_co, second_ts_co = self.get_cross_over_freq(self.curves_dict[id]["curves"]["frequencies"], self.curves_dict[id]["curves"]["recm_two_shell"])
        self.curves_dict[id]["parameters"]["1st_cross_over"]["two_shell"] = first_ts_co
        self.curves_dict[id]["parameters"]["2nd_cross_over"]["two_shell"] = second_ts_co

        # Refresh all graphs with new data
        self.curves_dict[id]["widget"].update_crossover()
        self.refresh_graph()

    def duplicate_curve(self, id):
        # Create a new curve widget
        new_curve_widget = CurveWidgetUI()

        # Create a new parameters list
        data_copy = self.curves_dict[id].copy()

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

        # Refresh all graphs with new data
        self.modify_all_curves()

        # Dock the widget at index 0 from the top
        self.pyqt5_scrollarea_plots_curve_layout.insertWidget(0, new_curve_widget)

    def delete_curve(self, id):
        # Remove the curve from the dictionary
        del self.curves_dict[id]

        # Refresh the graph
        self.refresh_graph()

    def save_curve(self, id, file_path):
        # save all curve data to a json file from the dictionary
        data = self.curves_dict[id].copy()
        data["widget"] = None

        with open(file_path, 'w') as file:
            json.dump(data, file, cls=NumpyEncoder)

        file.close()

    def load_curve(self):
        # load curve data from a json file to the dictionary
        file_path, _ = QFileDialog.getOpenFileName(self, "Load curve", "", "OpenDEP Curve (*.odc)")

        if file_path:
            with open(file_path, 'r') as file:
                data = json.load(file)
                id = random.randint(0, 9999)
                while id in self.curves_dict.keys():
                    id = random.randint(0, 9999)

            # Create a new curve widget
            new_curve_widget = CurveWidgetUI()

            # Create a new parameters list
            data_copy = data

            # Create Random ID which wont be already in the dictionary keys
            new_id = random.randint(0, 9999)
            while new_id in self.curves_dict.keys():
                new_id = random.randint(0, 9999)

            # Update with the new widget and nwe data
            self.curves_dict[new_id] = data_copy
            self.curves_dict[new_id]["widget"] = new_curve_widget

            # Populate the widget with the data
            new_curve_widget.id = new_id
            new_curve_widget.parent_widget = self
            new_curve_widget.set_entries_with_data()

            # Refresh all graphs with new data
            self.modify_all_curves()

            # Dock the widget at index 0 from the top
            self.pyqt5_scrollarea_plots_curve_layout.insertWidget(0, new_curve_widget)

    # Multiple curve functionality - modify all
    def modify_all_curves(self):
        for key in self.curves_dict.keys():
            self.modify_single_curve(key)

    def refresh_graph(self, focus_curve_id=None):
        self.pyqt5_graph_widget.canvas.axes.clear()
        # Some local_vars
        y_index = 0
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
            "imcm_two_shell"]

        # Add all curves to the graph
        for key in self.curves_dict.keys():
            if self.curves_dict[key]["visibility"]:
                # Get index of the button that is active in type of graph content
                for index, button in enumerate(self.pyqt5_frame_toolbar_graphcontent.findChildren(QPushButton)):
                    if button.property("customState"):
                        # Calculate the index of data depending on selected model and type of graph content
                        new_index = self.curves_dict[key]["model"] * 3 + index + 1
                        self.pyqt5_graph_widget.update_curve(name=self.curves_dict[key]["name"],
                                                            color=self.curves_dict[key]["color"],
                                                            line_style=self.curves_dict[key]["line_style"],
                                                            x_data=self.curves_dict[key]["curves"]["frequencies"],
                                                            y_data=self.curves_dict[key]["curves"][curves[new_index]],
                                                            line_width=self.curves_dict[key]["line_width"])
                        y_index = index
                        break

        if self.pyqt5_button_display_experimental_area.property("customState"):
            self.pyqt5_graph_widget.scatter_style = 'area'
        elif self.pyqt5_button_display_experimental_stdev.property("customState"):
            self.pyqt5_graph_widget.scatter_style = 'scatter'

        for key in self.scatter_dict.keys():
            if self.scatter_dict[key]["visibility"]:
                # Get index of the button that is active in type of graph content
                for index, button in enumerate(self.pyqt5_frame_toolbar_graphcontent.findChildren(QPushButton)):
                    if button.property("customState"):
                        button_index = index
                if button_index == 0:
                    self.pyqt5_graph_widget.update_scatter(name=self.scatter_dict[key]["name"],
                                                        color=self.scatter_dict[key]["color"],
                                                        x_data=self.scatter_dict[key]["scatter"]["frequencies"],
                                                        y_data=self.scatter_dict[key]["scatter"]["recm_values"],
                                                        y_errors=self.scatter_dict[key]["scatter"]["recm_errors"],
                                                        point_style=self.scatter_dict[key]["point_style"],
                                                        point_size=self.scatter_dict[key]["point_size"])

        # Format the graph and draw it
        self.pyqt5_graph_widget.format_graph(y_index=y_index)
        self.pyqt5_graph_widget.canvas.draw()

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
                      "1st_cross_over": {"homogenous": 0.0,
                                         "single_shell": 0.0,
                                         "two_shell": 0.0},
                      "2nd_cross_over": {"homogenous": 0.0,
                                         "single_shell": 0.0,
                                         "two_shell": 0.0}
        }

        return parameters

    # Generate the curve data for the given parameters
    def generate_curve_data(self, parameters):
        # Generate the frequency list
        start = np.log10(float(self.pyqt5_entry_param_freq_start.text())*(1000**self.pyqt5_combo_param_freq_start_unit.currentIndex()))
        stop = np.log10(float(self.pyqt5_entry_param_freq_stop.text())*(1000**self.pyqt5_combo_param_freq_stop_unit.currentIndex()))
        frequencies_list = np.logspace(start=start,
                                       stop=stop,
                                       num=self.no_curve_points,
                                       endpoint=True,
                                       dtype=int)
        #print(frequencies_list)
        # Initialize lists for homogenous particle model
        recm_ho_list = []
        imcm_ho_list = []
        depforce_ho_list = []

        # Initialize lists for single shell particle model
        recm_ss_list = []
        imcm_ss_list = []
        depforce_ss_list = []

        # Initialize lists for two shell particle model
        recm_ts_list = []
        imcm_ts_list = []
        depforce_ts_list = []

        for freq in frequencies_list:
            # Generate all lists for homogenous particle
            recm_ho, imcm_ho, depforce_ho = models.homogenous_particle_all(
                                        freq=freq,
                                        fitting_gen_fieldgrad=parameters["electric_field"],
                                        fitting_hopa_particle_radius=parameters["core_radius"],
                                        fitting_hopa_particle_perm=parameters["core_perm"],
                                        fitting_hopa_particle_cond=parameters["core_cond"],
                                        fitting_gen_buffer_perm=parameters["buffer_perm"],
                                        fitting_gen_buffer_cond=parameters["buffer_cond"])

            recm_ho_list.append(recm_ho)
            imcm_ho_list.append(imcm_ho)
            depforce_ho_list.append(depforce_ho)

            # Generate all lists for single shell particle
            recm_ss, imcm_ss, depforce_ss = models.single_shell_all(
                        freq=freq,
                        fitting_gen_fieldgrad=parameters["electric_field"],
                        fitting_sish_particle_radius=parameters["core_radius"],
                        fitting_sish_membrane_thickness=parameters["1st_shell_thick"],
                        fitting_sish_membrane_perm=parameters["1st_shell_perm"],
                        fitting_sish_membrane_cond=parameters["1st_shell_cond"],
                        fitting_sish_cytoplasm_perm=parameters["core_perm"],
                        fitting_sish_cytoplasm_cond=parameters["core_cond"],
                        fitting_gen_buffer_perm=parameters["buffer_perm"],
                        fitting_gen_buffer_cond=parameters["buffer_cond"])

            recm_ss_list.append(recm_ss)
            imcm_ss_list.append(imcm_ss)
            depforce_ss_list.append(depforce_ss)

            # Generate all lists for two shell particle
            recm_ts, imcm_ts, depforce_ts = models.two_shell_all(
                        freq=freq,
                        field_grad=parameters["electric_field"],
                        core_radius=parameters["core_radius"],
                        inner_shell_thickness=parameters["1st_shell_thick"],
                        inner_shell_perm=parameters["1st_shell_perm"],
                        inner_shell_cond=parameters["1st_shell_cond"],
                        outer_shell_thickness=parameters["2nd_shell_thick"],
                        outer_shell_perm=parameters["2nd_shell_perm"],
                        outer_shell_cond=parameters["2nd_shell_cond"],
                        core_perm=parameters["core_perm"],
                        core_cond=parameters["core_cond"],
                        buffer_perm=parameters["buffer_perm"],
                        buffer_cond=parameters["buffer_cond"])

            recm_ts_list.append(recm_ts)
            imcm_ts_list.append(imcm_ts)
            depforce_ts_list.append(depforce_ts)

        curve_data = {
            "frequencies": frequencies_list,
            "recm_homogenous_particle": recm_ho_list,
            "imcm_homogenous_particle": imcm_ho_list,
            "depforce_homogenous_particle": depforce_ho_list,
            "recm_single_shell": recm_ss_list,
            "imcm_single_shell": imcm_ss_list,
            "depforce_single_shell": depforce_ss_list,
            "recm_two_shell": recm_ts_list,
            "imcm_two_shell": imcm_ts_list,
            "depforce_two_shell": depforce_ts_list
        }

        return curve_data

    # Calculate the cross over frequency
    def get_cross_over_freq(self, freq_list, recm_list):
        intersections = []
        first_co = None
        second_co = None
        for i in range(len(recm_list)-1):
            if recm_list[i] < 0 and recm_list[i+1] > 0:
                first_co = freq_list[i]
                intersections.append(freq_list[i])
            elif recm_list[i] > 0 and recm_list[i+1] < 0:
                second_co = freq_list[i]
                intersections.append(freq_list[i])

        return first_co, second_co









