import random

from src.func.general import *

from PyQt5.QtWidgets import QWidget, QPushButton, QColorDialog
from PyQt5.uic import loadUi


# Create a class to handle the widget that will be spawn when the user wants to add a curve to the graph
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
        self.pyqt5_combo_curve_line_style.currentIndexChanged.connect(self.pick_curve_line_style)
        self.pyqt5_spinbox_curve_line_width.valueChanged.connect(self.change_curve_thickness)

        # On Header focus


        # Plots menubar, to toggle what is displayed on the plots
        self.pyqt5_model_buttons = [self.pyqt5_button_toggle_homogenous, self.pyqt5_button_toggle_singleshell]
        self.pyqt5_model_tab_widgets = [self.pyqt5_frame_group_homogenous, self.pyqt5_frame_group_singleshell]
        for button in self.pyqt5_model_buttons:
            button.clicked.connect(lambda: self.toggle_tabs(self.pyqt5_model_buttons, self.pyqt5_model_tab_widgets))
        self.pyqt5_model_buttons[0].click()

    def collapse(self, collapse=True):
        if collapse:
            self.pyqt5_frame_group_parameters.setVisible(False)
        else:
            self.pyqt5_frame_group_parameters.setVisible(True)

    def toggle_tabs(self, buttons, tab_widgets):
        sender = self.sender()  # Get the button that was clicked
        for button in buttons:
            button.setProperty("customState", button == sender)
            button.setStyle(button.style())  # Refresh style to apply property

        for i, button in enumerate(buttons):
            tab_widgets[i].setVisible(button == sender)

    def get_random_color_hex(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def populate_with_data(self):
        color = self.parent_widget.curves_dict[self.id]["color"]
        name = self.parent_widget.curves_dict[self.id]["name"]
        visible = self.parent_widget.curves_dict[self.id]["visibility"]
        model = self.parent_widget.curves_dict[self.id]["model"]
        parameters = self.parent_widget.curves_dict[self.id]["parameters"]

        self.pyqt5_button_pick_curve_color.setStyleSheet(f"background-color: {color}")
        self.pyqt5_entry_curve_name.setText(name)
        self.pyqt5_checkbox_curves_visible.setChecked(visible)
        self.pyqt5_model_buttons[model].click()

        # For Homogeneous model
        self.pyqt5_entry_param_ho_buffer_perm.setText(str(parameters[0][0]))
        self.pyqt5_entry_param_ho_buffer_cond.setText(str(parameters[0][1]))

        self.pyqt5_entry_param_ho_part_perm.setText(str(parameters[2][0]))
        self.pyqt5_entry_param_ho_part_cond.setText(str(parameters[2][1]))

        self.pyqt5_entry_param_ho_size.setText(str(parameters[0][2]))

        # For single shell model
        self.pyqt5_entry_param_ss_buffer_perm.setText(str(parameters[0][0]))
        self.pyqt5_entry_param_ss_buffer_cond.setText(str(parameters[0][1]))

        self.pyqt5_entry_param_ss_cito_perm.setText(str(parameters[1][0]))
        self.pyqt5_entry_param_ss_cito_cond.setText(str(parameters[1][1]))

        self.pyqt5_entry_param_ss_membr_perm.setText(str(parameters[1][2]))
        self.pyqt5_entry_param_ss_membr_cond.setText(str(parameters[1][3]))

        self.pyqt5_entry_param_ss_thick.setText(str(parameters[1][4]))
        self.pyqt5_entry_param_ss_size.setText(str(parameters[0][2]))

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
        self.parent_widget.pyqt5_graph_widget.unfocus_curve(self.parent_widget.curves_dict[self.id]["name"])
