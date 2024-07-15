import random

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QListView, QSizePolicy, QColorDialog, QWidget
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from matplotlib.figure import Figure
import numpy as np

from src.func import models
from src.func import general

from ui.helpers.curve_widget_ui import CurveWidgetUI
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

        # Load the main UI
        loadUi("ui/main.ui", self)
        self.setWindowTitle("OpenDEP Force Calculator")
        self.setWindowIcon(QIcon("icon.png"))

        # Create default parameters
        self.default_curve = None
        self.curves_dict = {}
        self.no_curve_points = 100

        # Load the rest of the widgets
        self.graph_settings = GraphSettingsUI()

        # Toolbar buttons
        self.pyqt5_button_save_figure.clicked.connect(self.pyqt5_graph_widget.save_figure)
        self.pyqt5_button_home_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.home)
        self.pyqt5_button_zoom_figure.clicked.connect(self.pyqt5_graph_widget.toolbar.zoom)
        self.pyqt5_button_properties_figure.clicked.connect(self.open_graph_settings)
        self.pyqt5_button_fitspace_figure.clicked.connect(self.pyqt5_graph_widget.set_tight_layout)
        #self.pyqt5_button_resize_figure.clicked.connect(self.resize_graph)

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
    def open_graph_settings(self):
        self.graph_settings.show_graph_settings()

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            print(color.name())

    def generate_new_curve(self):
        # Create a new curve widget
        new_curve_widget = CurveWidgetUI()

        # Create a new parameters list
        generated_parameters = self.create_default_curve_data()

        # Generate the curve data
        curve_data = self.generate_curve_data(generated_parameters[0],
                                              generated_parameters[1],
                                              generated_parameters[2],
                                              float(self.pyqt5_entry_param_fieldgrad.text()))

        # Calculate the cross over frequency
        cross_over_freq_ho = self.get_cross_over_freq(curve_data[0], curve_data[1])
        #print(cross_over_freq_ho)
        cross_over_freq_ss = self.get_cross_over_freq(curve_data[0], curve_data[4])
        #print(cross_over_freq_ss)

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
        new_curve_widget.populate_with_data()

        # Refresh all graphs with new data
        self.refresh_graph()

        # Dock the widget at index 0 from the top
        self.pyqt5_scrollarea_plots_curve_layout.insertWidget(0, new_curve_widget)

    def refresh_graph(self, focus_curve_id=None):
        self.pyqt5_graph_widget.canvas.axes.clear()
        # Some local_vars
        y_index = 0

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
                                                            x_data=self.curves_dict[key]["curves"][0],
                                                            y_data=self.curves_dict[key]["curves"][new_index],
                                                            line_width=self.curves_dict[key]["line_width"])
                        y_index = index
                        break

        # TOoDO - Add the experimental data to the graph

        # Format the graph and draw it
        self.pyqt5_graph_widget.format_graph(y_index=y_index)
        self.pyqt5_graph_widget.canvas.draw()

    def delete_curve(self, id):
        # Remove the curve from the dictionary
        del self.curves_dict[id]

        # Refresh the graph
        self.refresh_graph()

    def create_default_curve_data(self):
        # Details: name, color, visibility, model, gen_data, ss_data, ho_data
        # ss_data: buffer permittivity, buffer conductivity, particle
        gen_data = [78.0, 0.01, 10.0]
        # ss_data: citoplasm permittivity, citoplasm conductivity, membrane permittivity, membrane conductivity, membrane thickness
        ss_data = [random.randint(5,100), 0.1, random.randint(5,100), 0.00001, 6.0]
        # ho_data: permittivity, conductivity
        ho_data = [random.randint(2,100), 0.00001]

        return gen_data, ss_data, ho_data

    def generate_curve_data(self, general_data, ss_model_data, ho_model_data, field_grad):
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

        for freq in frequencies_list:
            # gen_data: buffer permittivity, buffer conductivity, particle size
            # ss_data: citoplasm permittivity, citoplasm conductivity, membrane permittivity, membrane conductivity, membrane thickness
            # ho_data: permittivity, conductivity
            # Generate all lists for homogenous particle
            recm_ho, imcm_ho, depforce_ho = models.homogenous_particle_all(
                                        freq=freq,
                                        fitting_gen_fieldgrad=field_grad,
                                        fitting_hopa_particle_radius=general_data[2],
                                        fitting_hopa_particle_perm=ho_model_data[0],
                                        fitting_hopa_particle_cond=ho_model_data[1],
                                        fitting_gen_buffer_perm=general_data[0],
                                        fitting_gen_buffer_cond=general_data[1])

            recm_ho_list.append(recm_ho)
            imcm_ho_list.append(imcm_ho)
            depforce_ho_list.append(depforce_ho)

            # Generate all lists for single shell particle
            recm_ss, imcm_ss, depforce_ss = models.single_shell_all(
                        freq=freq,
                        fitting_gen_fieldgrad=field_grad,
                        fitting_sish_particle_radius=general_data[2],
                        fitting_sish_membrane_thickness=ss_model_data[4],
                        fitting_sish_membrane_perm=ss_model_data[2],
                        fitting_sish_membrane_cond=ss_model_data[3],
                        fitting_sish_cytoplasm_perm=ss_model_data[0],
                        fitting_sish_cytoplasm_cond=ss_model_data[1],
                        fitting_gen_buffer_perm=general_data[0],
                        fitting_gen_buffer_cond=general_data[1])

            recm_ss_list.append(recm_ss)
            imcm_ss_list.append(imcm_ss)
            depforce_ss_list.append(depforce_ss)

        return frequencies_list, recm_ho_list, imcm_ho_list, depforce_ho_list, recm_ss_list, imcm_ss_list, depforce_ss_list

    def get_cross_over_freq(self, freq_list, recm_list):
        intersections = []
        for i in range(1, len(freq_list)):
            if (freq_list[i - 1] > 0 and freq_list[i] < 0) or (freq_list[i - 1] < 0 and freq_list[i] > 0):
                # Linear interpolation to find the y value where x would be 0
                x1, x2 = freq_list[i - 1], freq_list[i]
                y1, y2 = recm_list[i - 1], recm_list[i]
                y_intersect = y1 + (0 - x1) * (y2 - y1) / (x2 - x1)
                intersections.append(y_intersect)
        return intersections









