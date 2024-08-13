import random
import numpy as np
import json

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QListView, QSizePolicy, QColorDialog, QWidget
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from matplotlib.figure import Figure

from src.func import models
from src.func import general
from src.func import excel
from src.classes.numpy_encoder import NumpyEncoder

from ui.helpers.curve_widget_ui import CurveWidgetUI
from ui.helpers.scatter_widget_ui import ScatterWidgetUI
from ui.resources import graphical_resources
from ui.helpers.graph_settings_ui import GraphSettingsUI
from ui.helpers.noise_widget_ui import NoiseWidgetUI
from ui.helpers.capture_widget_ui import CaptureWidgetUI

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
        self.graph_y_index = 0

        # Default styles
        self.point_styles = ["o", "s", "v", "+", "x", "*"]
        self.graph_style_parameters = None

        # Load the rest of the widgets
        self.graph_settings = GraphSettingsUI(parent=self)
        self.noise_widget = NoiseWidgetUI(parent=self)
        self.capture_widget = CaptureWidgetUI(parent=self)

        # Toolbar buttons
        self.pyqt5_button_save_figure.clicked.connect(self.capture_widget.open_widget)
        self.pyqt5_button_home_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.home)
        self.pyqt5_button_zoom_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.zoom)
        self.pyqt5_button_properties_figure.clicked.connect(self.graph_settings.open_graph_settings)
        self.pyqt5_button_fitspace_figure.clicked.connect(self.pyqt5_graph_widget.set_tight_layout)
        #self.pyqt5_button_resize_figure.clicked.connect(self.resize_graph)

        # Data buttons
        self.pyqt5_button_curve_load.clicked.connect(lambda: self.load_curve(file_type="OpenDEP"))
        self.pyqt5_button_scatter_add.clicked.connect(lambda: self.generate_new_scatter(type="new"))
        self.pyqt5_button_scatter_load.clicked.connect(self.load_scatter)
        self.pyqt5_button_scatter_load_excel.clicked.connect(self.load_excel_scatter)
        self.pyqt5_button_curve_load_excel.clicked.connect(lambda: self.load_curve(file_type="Excel"))


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
        self.pyqt5_entry_graph_height.editingFinished.connect(self.resize_to_entry)
        self.pyqt5_entry_graph_width.editingFinished.connect(self.resize_to_entry)
        self.pyqt5_entry_graph_width.setDisabled(True)
        self.pyqt5_entry_graph_height.setDisabled(True)

        # ScrollArea buttons
        self.pyqt5_button_curves_add.clicked.connect(self.generate_new_curve)

        # Entry fields for the frequency range
        self.pyqt5_entry_param_freq_start.editingFinished.connect(self.modify_all_curves)
        self.pyqt5_entry_param_freq_stop.editingFinished.connect(self.modify_all_curves)
        self.pyqt5_combo_param_freq_start_unit.currentIndexChanged.connect(self.modify_all_curves)
        self.pyqt5_combo_param_freq_stop_unit.currentIndexChanged.connect(self.modify_all_curves)

        # Visibility checkboxes
        self.pyqt5_checkbox_curves_visibility.clicked.connect(self.refresh_graph)
        self.pyqt5_checkbox_scatters_visibility.clicked.connect(self.refresh_graph)

        # Hide future buttons
        self.pyqt5_button_cruves_load_cloud.setVisible(False)
        self.pyqt5_button_fitspace_figure.setVisible(False)

        # Lock entries to integers
        entries_to_int = [self.pyqt5_entry_graph_width,
                          self.pyqt5_entry_graph_height,
                          self.pyqt5_entry_param_freq_start,
                          self.pyqt5_entry_param_freq_stop
                          ]
        for entry in entries_to_int:
            general.lock_entry_to_int(entry, min_value=1, max_value=2000, max_length=4)

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

    # Delete scatter from the dictionary and refresh the graph
    def delete_scatter(self, id):
        # Remove the curve from the dictionary
        del self.scatter_dict[id]

        # Refresh the graph
        self.refresh_graph()

    # Save scatter to file
    def save_scatter(self, id, file_path):
        # save all curve data to a json file from the dictionary
        data = self.scatter_dict[id].copy()
        data["widget"] = None

        with open(file_path, 'w') as file:
            json.dump(data, file, cls=NumpyEncoder)

        file.close()

    # Load scatter from file
    def load_scatter(self):
        # load curve data from a json file to the dictionary
        file_path, _ = QFileDialog.getOpenFileName(self, "Load scatter", "", "OpenDEP Scatter (*.ods)")

        if file_path:
            self.generate_new_scatter(type="load", file_path=file_path)

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

    # Modify single curve from the dictionary and refresh the graph
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

    # Duplicate curve from the dictionary and refresh the graph
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

    # Delete curve from the dictionary and refresh the graph
    def delete_curve(self, id):
        # Remove the curve from the dictionary
        del self.curves_dict[id]

        # Refresh the graph
        self.refresh_graph()

    # Save curve to file
    def save_curve(self, id, file_path):
        # save all curve data to a json file from the dictionary
        data = self.curves_dict[id].copy()
        data["widget"] = None

        with open(file_path, 'w') as file:
            json.dump(data, file, cls=NumpyEncoder)

        file.close()

    # Load curve from file
    def load_curve(self, file_type="OpenDEP"):
        # load curve data from a json file to the dictionary
        if file_type == "OpenDEP":
            file_path, _ = QFileDialog.getOpenFileName(self, "Load curve", "", "OpenDEP Curve (*.odc)")
        elif file_type == "Excel":
            file_path, _ = QFileDialog.getOpenFileName(self, "Load curve", "", "Excel Curve (*.xlsx)")

        if file_path:
            # Create a new curve widget
            new_curve_widget = CurveWidgetUI()

            # Create a new parameters list
            if file_type == "OpenDEP":
                with open(file_path, 'r') as file:
                    data = json.load(file)
                data_copy = data

            elif file_type == "Excel":
                parameters, model = excel.load_curve_from_excel(file_path)
                if not parameters == None:
                    data_copy = {"name": file_path.split("/")[-1].split(".")[0],
                                 "color": general.get_random_color_hex(),
                                 "line_style": '-',
                                 "line_width": 1.5,
                                 "visibility": True,
                                 "model": model,
                                 "parameters": parameters,
                                 "curves": self.generate_curve_data(parameters),
                                 "widget": new_curve_widget}
                else:
                    return


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

    # GRAPH METHODS
    # Get the styling of the graph
    def get_graph_styling(self):
        graph_style_parameters = {
            'font_family': self.graph_settings.pyqt5_combo_font_family.currentText().lower(),
            'axis_style': {'fontsize': self.graph_settings.pyqt5_spinbox_axis_title_size.value(),
                           'fontweight': self.graph_settings.pyqt5_combo_axis_font_weight.currentText().lower(),
                           'fontstyle': self.graph_settings.pyqt5_combo_axis_font_style.currentText().lower(),
                           'color': '#000000',
                           'labelpad': self.graph_settings.pyqt5_spinbox_axis_title_padding.value()
                           },
            'tick_style': {'fontsize': self.graph_settings.pyqt5_spinbox_tick_size.value(),
                           'fontweight': self.graph_settings.pyqt5_combo_tick_font_weight.currentText().lower(),
                           'fontstyle': self.graph_settings.pyqt5_combo_tick_font_style.currentText().lower(),
                           'color': '#000000',
                           'labelpad': self.graph_settings.pyqt5_spinbox_tick_label_padding.value(),
                           'majortickvisibility': self.graph_settings.pyqt5_checkbox_major_tick_visibility.isChecked(),
                           'majortickdirection': self.graph_settings.pyqt5_combo_major_tick_direction.currentText().lower(),
                           'majorticklength': self.graph_settings.pyqt5_spinbox_major_tick_length.value(),
                           'majortickwidth': self.graph_settings.pyqt5_spinbox_major_tick_width.value(),
                           'minortickvisibility': self.graph_settings.pyqt5_checkbox_minor_tick_visibility.isChecked(),
                           'minortickdirection': self.graph_settings.pyqt5_combo_minor_tick_direction.currentText().lower(),
                           'minorticklength': self.graph_settings.pyqt5_spinbox_minor_tick_length.value(),
                           'minortickwidth': self.graph_settings.pyqt5_spinbox_minor_tick_width.value()
                           },
            'grid_style': {'hgridvisibility': self.graph_settings.pyqt5_checkbox_h_grid_visibility.isChecked(),
                           'hgridlinestyle': self.graph_settings.pyqt5_combo_h_grid_style.currentText().lower(),
                           'hgridlinewidth': self.graph_settings.pyqt5_spinbox_h_grid_width.value(),
                           'hgridalpha': self.graph_settings.pyqt5_spinbox_h_grid_transparency.value(),
                           'vgridvisibility': self.graph_settings.pyqt5_checkbox_v_grid_visibility.isChecked(),
                           'vgridlinestyle': self.graph_settings.pyqt5_combo_v_grid_style.currentText().lower(),
                           'vgridlinewidth': self.graph_settings.pyqt5_spinbox_v_grid_width.value(),
                            'vgridalpha': self.graph_settings.pyqt5_spinbox_v_grid_transparency.value()
                           },
            'legend_style': {'visibility': self.graph_settings.pyqt5_checkbox_legend_visibility.isChecked(),
                             'fontsize': self.graph_settings.pyqt5_spinbox_legend_font_size.value(),
                             'fontweight': self.graph_settings.pyqt5_combo_legend_font_weight.currentText().lower(),
                             'fontstyle': self.graph_settings.pyqt5_combo_legend_font_style.currentText().lower(),
                             'position': self.graph_settings.pyqt5_combo_legend_position.currentText().lower(),
                             },
            'frame_style': {'linewidth': self.graph_settings.pyqt5_spinbox_frame_width.value(),
                            'topvisbility': self.graph_settings.pyqt5_checkbox_frame_top_visibility.isChecked(),
                            'bottomvisbility': self.graph_settings.pyqt5_checkbox_frame_bottom_visibility.isChecked(),
                            'leftvisbility': self.graph_settings.pyqt5_checkbox_frame_left_visibility.isChecked(),
                            'rightvisbility': self.graph_settings.pyqt5_checkbox_frame_right_visibility.isChecked()
                            }
            }

        return graph_style_parameters

    # Update the styling of the graph
    def update_graph_styling(self):
        self.graph_style_parameters = self.get_graph_styling()
        self.pyqt5_graph_widget.format_graph(y_index=self.graph_y_index, style_params=self.graph_style_parameters)
        self.pyqt5_graph_widget.canvas.draw()

    # Refresh the graph with new data
    def refresh_graph(self, focus_curve_id=None):
        self.pyqt5_graph_widget.canvas.axes.clear()
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
            "imcm_two_shell"]

        # Add all curves to the graph
        if self.pyqt5_checkbox_curves_visibility.isChecked():
            for key in self.curves_dict.keys():
                self.curves_dict[key]["widget"].setEnabled(True)
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
                            self.graph_y_index = index
                            break
        else:
            for key in self.curves_dict.keys():
                self.curves_dict[key]["widget"].setEnabled(False)

        if self.pyqt5_button_display_experimental_area.property("customState"):
            self.pyqt5_graph_widget.scatter_style = 'area'
        elif self.pyqt5_button_display_experimental_stdev.property("customState"):
            self.pyqt5_graph_widget.scatter_style = 'scatter'

        if self.pyqt5_checkbox_scatters_visibility.isChecked():
            for key in self.scatter_dict.keys():
                self.scatter_dict[key]["widget"].setEnabled(True)
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

        else:
            for key in self.scatter_dict.keys():
                self.scatter_dict[key]["widget"].setEnabled(False)

        # Format the graph and draw it
        self.update_graph_styling()

    # When the window is resized, resize the graph
    def resizeEvent(self, event=None):
        # Get size of figure in the graph
        new_graph_size = self.pyqt5_graph_widget.get_figure_size()
        QMainWindow.resizeEvent(self, event)
        # Check if self.pyqt5_graph_widget is resized
        if self.pyqt5_graph_widget.size() != event.oldSize():
            self.pyqt5_graph_widget.set_tight_layout()
            if not self.pyqt5_entry_graph_width.isEnabled():
                self.pyqt5_entry_graph_width.setText(str(int(new_graph_size[0])))
            if not self.pyqt5_entry_graph_height.isEnabled():
                self.pyqt5_entry_graph_height.setText(str(int(new_graph_size[1])))

    # Resize the graph to the values in the entry fields
    def resize_to_entry(self):
        # Get current DPI and size of the figure
        graph_dpi = self.pyqt5_graph_widget.figure.get_dpi()
        graph_width = self.pyqt5_graph_widget.figure.get_size_inches()[0] * graph_dpi
        graph_height = self.pyqt5_graph_widget.figure.get_size_inches()[1] * graph_dpi

        # Calculate the size difference between the window and the graph
        old_graph_size = [graph_width, graph_height]
        old_window_size = [self.width(), self.height()]
        remaining_space = [old_window_size[0] - old_graph_size[0], old_window_size[1] - old_graph_size[1]]

        # Get the new desired graph size from entries
        new_graph_size_pixels = [int(self.pyqt5_entry_graph_width.text()), int(self.pyqt5_entry_graph_height.text())]
        new_graph_size_inches = [new_graph_size_pixels[0] / graph_dpi, new_graph_size_pixels[1] / graph_dpi]

        # Set the new size for the Matplotlib figure
        self.pyqt5_graph_widget.figure.set_size_inches(new_graph_size_inches[0], new_graph_size_inches[1])

        # Update the widget and window size
        new_window_size = [new_graph_size_pixels[0] + remaining_space[0], new_graph_size_pixels[1] + remaining_space[1]]
        self.resize(int(new_window_size[0]), int(new_window_size[1]))

        # Set the size of the widget containing the figure
        self.pyqt5_graph_widget.setFixedSize(new_graph_size_pixels[0], new_graph_size_pixels[1])

        # Apply tight layout if needed and redraw the canvas
        self.pyqt5_graph_widget.set_tight_layout()
        self.pyqt5_graph_widget.canvas.draw()

        print("Resized")

    # Lock the graph widget size
    def lock_graph_widget_size(self):
        if self.pyqt5_checkbox_graph_size_lock.isChecked():
            self.pyqt5_entry_graph_width.setDisabled(False)
            self.pyqt5_entry_graph_height.setDisabled(False)
            # Restrict resizing of the graph
            self.pyqt5_graph_widget.setFixedSize(self.pyqt5_graph_widget.size())
            self.pyqt5_graph_widget.set_tight_layout()

        else:
            self.pyqt5_entry_graph_width.setDisabled(True)
            self.pyqt5_entry_graph_height.setDisabled(True)
            # Allow resizing of the graph
            self.pyqt5_graph_widget.setMinimumSize(0, 0)
            self.pyqt5_graph_widget.setMaximumSize(16777215, 16777215)
            self.pyqt5_graph_widget.set_tight_layout()
