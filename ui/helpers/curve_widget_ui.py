import random

from src.func.general import *

from PyQt5.QtWidgets import QWidget, QPushButton, QColorDialog, QFileDialog
from PyQt5.uic import loadUi


# Create a classes to handle the widget that will be spawn when the user wants to add a curve to the graph
class CurveWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/curve_widget.ui", self)

        # Varaibles
        self.parent_widget = None
        self.id = None

        # Some initial setup
        self.collapse(collapse=True)

        # Connect the buttons to the functions
        self.pyqt5_checkbox_curves_expand.clicked.connect(self.collapse)
        self.pyqt5_button_pick_curve_color.clicked.connect(self.pick_curve_color)
        self.pyqt5_checkbox_curves_visible.clicked.connect(self.toggle_hide)
        self.pyqt5_entry_curve_name.editingFinished.connect(self.change_curve_name)
        self.pyqt5_button_delete_curve.clicked.connect(self.delete_self)
        self.pyqt5_button_duplicate_curve.clicked.connect(self.duplicate_curve)
        self.pyqt5_button_save_curve.clicked.connect(self.save_curve)

        self.pyqt5_combo_curve_line_style.currentIndexChanged.connect(self.pick_curve_line_style)
        self.pyqt5_spinbox_curve_line_width.valueChanged.connect(self.change_curve_thickness)

        self.pyqt5_button_simulate_curve_noise.clicked.connect(self.open_noise_widget)

        # Model selection
        self.pyqt5_combo_model_selection.currentIndexChanged.connect(lambda:self.change_model(self.pyqt5_combo_model_selection.currentIndex()))
        self.change_model(index=0, init=True)

        # On parameters entry change
        self.parameters_to_modify = [
        "param_buffer_perm", "param_buffer_cond",
        "param_core_perm", "param_core_cond",
        "param_1st_shell_perm", "param_1st_shell_cond",
        "param_2nd_shell_perm", "param_2nd_shell_cond",
        "param_size", "param_fieldgrad",
        "param_1st_shell_thick", "param_2nd_shell_thick"]

        for param in self.parameters_to_modify:
            getattr(self, f"pyqt5_entry_{param}").editingFinished.connect(lambda param=param: self.parent_widget.modify_single_curve(self.id))

    def collapse(self, collapse=True):
        if collapse:
            self.pyqt5_frame_group_parameters.setVisible(False)
        else:
            self.pyqt5_frame_group_parameters.setVisible(True)

    def change_model(self, index=None, init=False):
        for i in self.pyqt5_frame_input_group.findChildren(QWidget):
            i.setVisible(True)
        if index == 0:
            self.pyqt5_frame_size_group.setVisible(False)
            self.pyqt5_frame_1st_shell_group.setVisible(False)
            self.pyqt5_frame_2nd_shell_group.setVisible(False)

            self.pyqt5_frame_group_homogenous_co.setVisible(True)
            self.pyqt5_frame_group_singleshell_co.setVisible(False)
            self.pyqt5_frame_group_twoshell_co.setVisible(False)

            if not init:
                self.parent_widget.curves_dict[self.id]["model"] = 0
                self.parent_widget.modify_single_curve(self.id)
                #self.change_curve_thickness()

        if index == 1:
            self.pyqt5_frame_2nd_thick.setVisible(False)
            self.pyqt5_frame_2nd_shell_group.setVisible(False)

            self.pyqt5_frame_group_homogenous_co.setVisible(False)
            self.pyqt5_frame_group_singleshell_co.setVisible(True)
            self.pyqt5_frame_group_twoshell_co.setVisible(False)

            if not init:
                self.parent_widget.curves_dict[self.id]["model"] = 1
                self.parent_widget.modify_single_curve(self.id)
                #self.change_curve_thickness()

        if index == 2:
            self.pyqt5_frame_group_homogenous_co.setVisible(False)
            self.pyqt5_frame_group_singleshell_co.setVisible(False)
            self.pyqt5_frame_group_twoshell_co.setVisible(True)

            if not init:
                self.parent_widget.curves_dict[self.id]["model"] = 2
                self.parent_widget.modify_single_curve(self.id)
                #self.change_curve_thickness()

    def set_entries_with_data(self):
        color = self.parent_widget.curves_dict[self.id]["color"]
        name = self.parent_widget.curves_dict[self.id]["name"]
        visible = self.parent_widget.curves_dict[self.id]["visibility"]
        model = self.parent_widget.curves_dict[self.id]["model"]
        parameters = self.parent_widget.curves_dict[self.id]["parameters"]

        self.pyqt5_button_pick_curve_color.setStyleSheet(f"background-color: {color}")
        self.pyqt5_entry_curve_name.setText(name)
        self.pyqt5_checkbox_curves_visible.setChecked(visible)

        # Model Selection
        self.pyqt5_combo_model_selection.setCurrentIndex(model)

        self.pyqt5_entry_param_buffer_perm.setText(str(parameters["buffer_perm"]))  # Buffer permittivity
        self.pyqt5_entry_param_buffer_cond.setText(str(parameters["buffer_cond"]))  # Buffer conductivity

        self.pyqt5_entry_param_core_perm.setText(str(parameters["core_perm"]))  # Core permittivity
        self.pyqt5_entry_param_core_cond.setText(str(parameters["core_cond"]))  # Core conductivity

        self.pyqt5_entry_param_1st_shell_perm.setText(str(parameters["1st_shell_perm"]))  # 1st shell permittivity
        self.pyqt5_entry_param_1st_shell_cond.setText(str(parameters["1st_shell_cond"]))  # 1st shell conductivity

        self.pyqt5_entry_param_2nd_shell_perm.setText(str(parameters["2nd_shell_perm"]))  # 2nd shell permittivity
        self.pyqt5_entry_param_2nd_shell_cond.setText(str(parameters["2nd_shell_cond"]))  # 2nd shell conductivity

        self.pyqt5_entry_param_size.setText(str(parameters["core_radius"]))  # Particle radius
        self.pyqt5_entry_param_fieldgrad.setText(str(parameters["electric_field"]))  # Electric Field

        self.pyqt5_entry_param_1st_shell_thick.setText(str(parameters["1st_shell_thick"]))  # 1st shell thickness
        self.pyqt5_entry_param_2nd_shell_thick.setText(str(parameters["2nd_shell_thick"]))  # 2nd shell thickness)

        self.update_crossover()

    def update_crossover(self):
        parameters = self.parent_widget.curves_dict[self.id]["parameters"]

        self.pyqt5_entry_homogenous_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["homogenous"]))  # Homogenous first coross-over
        self.pyqt5_entry_homogenous_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["homogenous"]))  # Homogenous second coross-over

        self.pyqt5_entry_singleshell_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["single_shell"]))  # 1st shell first coross-over
        self.pyqt5_entry_singleshell_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["single_shell"]))  # 2nd shell first coross-over

        self.pyqt5_entry_twoshell_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["two_shell"]))  # 1st shell first coross-over
        self.pyqt5_entry_twoshell_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["two_shell"]))  # 2nd shell first coross-over

    def get_data_from_entries(self):
        parameters = {}

        parameters["buffer_perm"] = float(self.pyqt5_entry_param_buffer_perm.text())  # Buffer permittivity
        parameters["buffer_cond"] = float(self.pyqt5_entry_param_buffer_cond.text())  # Buffer conductivity

        parameters["core_perm"] = float(self.pyqt5_entry_param_core_perm.text())  # Core permittivity
        parameters["core_cond"] = float(self.pyqt5_entry_param_core_cond.text())  # Core conductivity

        parameters["1st_shell_perm"] = float(self.pyqt5_entry_param_1st_shell_perm.text())  # 1st shell permittivity
        parameters["1st_shell_cond"] = float(self.pyqt5_entry_param_1st_shell_cond.text())  # 1st shell conductivity

        parameters["2nd_shell_perm"] = float(self.pyqt5_entry_param_2nd_shell_perm.text())  # 2nd shell permittivity
        parameters["2nd_shell_cond"] = float(self.pyqt5_entry_param_2nd_shell_cond.text())  # 2nd shell conductivity

        parameters["core_radius"] = float(self.pyqt5_entry_param_size.text())  # Particle radius
        parameters["electric_field"] = float(self.pyqt5_entry_param_fieldgrad.text())  # Electric Field

        parameters["1st_shell_thick"] = float(self.pyqt5_entry_param_1st_shell_thick.text())  # 1st shell thickness
        parameters["2nd_shell_thick"] = float(self.pyqt5_entry_param_2nd_shell_thick.text())  # 2nd shell thickness

        parameters["1st_cross_over"] = {"homogenous": 0.0,
                                        "single_shell": 0.0,
                                        "two_shell": 0.0}
        parameters["2nd_cross_over"] = {"homogenous": 0.0,
                                        "single_shell": 0.0,
                                        "two_shell": 0.0}

        return parameters

    def toggle_hide(self):
        if self.pyqt5_checkbox_curves_visible.isChecked():
            self.parent_widget.curves_dict[self.id]["visibility"] = True
        else:
            self.parent_widget.curves_dict[self.id]["visibility"] = False

        self.parent_widget.refresh_graph()

    def pick_curve_color(self):
        # Open color picker
        color = QColorDialog.getColor()
        if color.isValid():
            print(color.name())
            # Set color of button
            self.pyqt5_button_pick_curve_color.setStyleSheet(f"background-color: {color.name()}")
            # Set color of the curve on the graph
            self.parent_widget.curves_dict[self.id]["color"] = color.name()
            self.parent_widget.refresh_graph()

    def pick_curve_line_style(self):
        styles = ['-', ':', '--', '-.']
        self.parent_widget.curves_dict[self.id]["line_style"] = styles[self.pyqt5_combo_curve_line_style.currentIndex()]
        self.parent_widget.refresh_graph()

    def change_curve_thickness(self):
        self.parent_widget.curves_dict[self.id]["line_width"] = self.pyqt5_spinbox_curve_line_width.value()
        self.parent_widget.refresh_graph()
        self.start_focus_curve()

    def change_curve_name(self):
        self.parent_widget.curves_dict[self.id]["name"] = self.pyqt5_entry_curve_name.text()
        self.parent_widget.refresh_graph()

    def delete_self(self):
        self.parent_widget.delete_curve(self.id)
        self.close()

    def enterEvent(self, event):
        self.start_focus_curve()

    def leaveEvent(self, event):
        self.stop_focus_curve()

    def start_focus_curve(self):
        #self.parent_widget.refresh_graph(focus_curve_id=self.id)
        self.parent_widget.pyqt5_graph_widget.focus_curve(self.parent_widget.curves_dict[self.id]["name"])
    def stop_focus_curve(self):
        #self.parent_widget.refresh_graph()
        if self.id in self.parent_widget.curves_dict.keys():
            self.parent_widget.pyqt5_graph_widget.unfocus_curve(self.parent_widget.curves_dict[self.id]["name"])

    def duplicate_curve(self):
        self.parent_widget.duplicate_curve(self.id)
        self.collapse()
        self.pyqt5_checkbox_curves_expand.setChecked(True)

    def save_curve(self):
        # Open file dialog and save curve as a json file with suffix .odc
        filepath, _ = QFileDialog.getSaveFileName(self, "Save curve", "", "OpenDEP Curve (*.odc)")
        self.parent_widget.save_curve(self.id, filepath)

    def open_noise_widget(self):
        self.parent_widget.noise_widget.selected_curve_id = self.id
        self.parent_widget.noise_widget.exec_()
