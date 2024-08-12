import random



from src.func.general import *

from PyQt5.QtWidgets import QWidget, QPushButton, QColorDialog, QFileDialog, QAbstractScrollArea, QHeaderView, \
    QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

# Create a classes to handle the widget that will be spawn when the user wants to add a curve to the graph
class ScatterWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/scatter_widget.ui", self)

        # Varaibles
        self.parent_widget = None
        self.id = None
        self.disable_table_signals = False
        self.point_styles = ["o", "s", "v", "+", "x", "*"]

        # Some initial setup
        self.collapse(collapse=True)
        self.pyqt5_tablewidget_exp_spectra.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resize_table_height_to_no_rows()

        # Connect buttons
        self.connect_buttons()

    def connect_buttons(self):
        self.pyqt5_checkbox_scatter_visible.clicked.connect(self.toggle_hide)
        self.pyqt5_checkbox_curves_expand.clicked.connect(self.collapse)

        self.pyqt5_spinbox_scatter_size.valueChanged.connect(self.pick_scatter_size)

        self.pyqt5_combo_scatter_point_style.currentIndexChanged.connect(self.pick_scatter_point_style)

        self.pyqt5_entry_scatter_name.textChanged.connect(self.pick_scatter_name)

        self.pyqt5_button_add_scatter_point.clicked.connect(self.add_table_scatter_point)
        self.pyqt5_button_remove_scatter_point.clicked.connect(lambda: self.remove_table_scatter_point(
            self.pyqt5_tablewidget_exp_spectra.currentRow()))
        self.pyqt5_button_pick_scatter_color.clicked.connect(self.pick_curve_color)
        self.pyqt5_button_delete_scatter.clicked.connect(self.delete_self)
        self.pyqt5_button_duplicate_scatter.clicked.connect(lambda: self.parent_widget.generate_new_scatter(
            type="duplicate",
            duplicate_id=self.id))
        self.pyqt5_button_save_scatter.clicked.connect(self.save_self)

        self.pyqt5_tablewidget_exp_spectra.itemSelectionChanged.connect(self.update_button_state)

    def update_button_state(self):
        # Enable the button if any items are selected, otherwise disable it
        if self.pyqt5_tablewidget_exp_spectra.selectedItems():
            self.pyqt5_button_remove_scatter_point.setEnabled(True)
        else:
            self.pyqt5_button_remove_scatter_point.setEnabled(False)

    def connect_buttons_after_setup(self):
        self.pyqt5_tablewidget_exp_spectra.cellChanged.connect(self.get_data_from_table)

    def collapse(self, collapse=True):
        if collapse:
            self.pyqt5_frame_group_parameters.setVisible(False)
        else:
            self.pyqt5_frame_group_parameters.setVisible(True)

    def resize_table_height_to_no_rows(self):
        print(self.pyqt5_tablewidget_exp_spectra.rowCount())
        self.pyqt5_tablewidget_exp_spectra.setFixedHeight((self.pyqt5_tablewidget_exp_spectra.rowCount()) * 35
                                                          + self.pyqt5_tablewidget_exp_spectra.horizontalHeader().height())

    def pick_curve_color(self):
        # Open color picker
        color = QColorDialog.getColor()
        if color.isValid():
            # Set color of button
            self.pyqt5_button_pick_scatter_color.setStyleSheet(f"background-color: {color.name()}")
            # Set color of the curve on the graph
            self.parent_widget.scatter_dict[self.id]["color"] = color.name()
            self.parent_widget.refresh_graph()

    def pick_scatter_point_style(self):
        self.parent_widget.scatter_dict[self.id]["point_style"] = self.point_styles[self.pyqt5_combo_scatter_point_style.currentIndex()]
        self.parent_widget.refresh_graph()

    def pick_scatter_size(self):
        self.parent_widget.scatter_dict[self.id]["point_size"] = self.pyqt5_spinbox_scatter_size.value()
        self.parent_widget.refresh_graph()
        #self.start_focus_curve()

    def pick_scatter_name(self):
        self.parent_widget.scatter_dict[self.id]["name"] = self.pyqt5_entry_scatter_name.text()
        self.parent_widget.refresh_graph()

    def toggle_hide(self):
        if self.pyqt5_checkbox_scatter_visible.isChecked():
            self.parent_widget.scatter_dict[self.id]["visibility"] = True
        else:
            self.parent_widget.scatter_dict[self.id]["visibility"] = False

        self.parent_widget.refresh_graph()

    def delete_self(self):
        self.parent_widget.delete_scatter(self.id)
        self.close()

    def save_self(self):
        # Open file dialog and save curve as a json file with suffix .odc
        filepath, _ = QFileDialog.getSaveFileName(self, "Save curve", "", "OpenDEP Curve (*.ods)")
        self.parent_widget.save_scatter(self.id, filepath)

    def add_table_scatter_point(self):
        # Disable table signals
        self.disable_table_signals = True

        # Get the number of rows
        row_count = self.pyqt5_tablewidget_exp_spectra.rowCount()

        # Insert a new row
        self.pyqt5_tablewidget_exp_spectra.insertRow(row_count)

        # Set the default values
        if row_count == 0:
            self.pyqt5_tablewidget_exp_spectra.setItem(row_count, 0, QTableWidgetItem("1000"))
            self.pyqt5_tablewidget_exp_spectra.setItem(row_count, 1, QTableWidgetItem("0.5"))
            self.pyqt5_tablewidget_exp_spectra.setItem(row_count, 2, QTableWidgetItem("0.05"))

        else:
            self.pyqt5_tablewidget_exp_spectra.setItem(row_count, 0, QTableWidgetItem(
                str(float(self.pyqt5_tablewidget_exp_spectra.item(row_count - 1, 0).text()))))
            self.pyqt5_tablewidget_exp_spectra.setItem(row_count, 1, QTableWidgetItem(
                str(float(self.pyqt5_tablewidget_exp_spectra.item(row_count - 1, 1).text()))))
            self.pyqt5_tablewidget_exp_spectra.setItem(row_count, 2, QTableWidgetItem(
                str(float(self.pyqt5_tablewidget_exp_spectra.item(row_count - 1, 2).text()))))

        # Resize the table
        self.resize_table_height_to_no_rows()

        # Enable table signals
        self.disable_table_signals = False

        # Update the dictionary and graph
        self.get_data_from_table()

    def remove_table_scatter_point(self, row):
        # Disable table signals
        self.disable_table_signals = True

        # Remove the row
        self.pyqt5_tablewidget_exp_spectra.removeRow(row)

        # Resize the table
        self.resize_table_height_to_no_rows()

        # Enable table signals
        self.disable_table_signals = False

        # Update the dictionary and graph
        self.get_data_from_table()

    def clear_table_scatter_points(self):
        self.pyqt5_tablewidget_exp_spectra.clearContents()
        self.pyqt5_tablewidget_exp_spectra.setRowCount(0)

    def set_entries_with_data(self):
        color = self.parent_widget.scatter_dict[self.id]["color"]
        name = self.parent_widget.scatter_dict[self.id]["name"]
        visible = self.parent_widget.scatter_dict[self.id]["visibility"]
        point_style = self.parent_widget.scatter_dict[self.id]["point_style"]
        point_style_index = self.point_styles.index(point_style)
        point_size = self.parent_widget.scatter_dict[self.id]["point_size"]

        self.pyqt5_button_pick_scatter_color.setStyleSheet(f"background-color: {color}")
        self.pyqt5_entry_scatter_name.setText(name)
        self.pyqt5_checkbox_scatter_visible.setChecked(visible)
        self.pyqt5_combo_scatter_point_style.setCurrentIndex(point_style_index)
        self.pyqt5_spinbox_scatter_size.setValue(point_size)

        self.clear_table_scatter_points()
        scatter_data = self.parent_widget.scatter_dict[self.id]["scatter"]

        for i in range(len(scatter_data["frequencies"])):
            # Get the number of rows
            row_count = self.pyqt5_tablewidget_exp_spectra.rowCount()

            # Insert a new row
            self.pyqt5_tablewidget_exp_spectra.insertRow(row_count)

            # Populate the row
            self.pyqt5_tablewidget_exp_spectra.setItem(i, 0, QTableWidgetItem(str(scatter_data["frequencies"][i])))
            self.pyqt5_tablewidget_exp_spectra.setItem(i, 1, QTableWidgetItem(str(scatter_data["recm_values"][i])))
            self.pyqt5_tablewidget_exp_spectra.setItem(i, 2, QTableWidgetItem(str(scatter_data["recm_errors"][i])))

        self.resize_table_height_to_no_rows()

    def get_data_from_table(self):
        if not self.disable_table_signals:
            frequencies = []
            cm_factors = []
            cm_errors = []

            for row in range(self.pyqt5_tablewidget_exp_spectra.rowCount()):
                frequencies.append(float(self.pyqt5_tablewidget_exp_spectra.item(row, 0).text()))
                cm_factors.append(float(self.pyqt5_tablewidget_exp_spectra.item(row, 1).text()))
                cm_errors.append(float(self.pyqt5_tablewidget_exp_spectra.item(row, 2).text()))

            scatter_data = {"frequencies": frequencies,
                            "recm_values": cm_factors,
                            "recm_errors": cm_errors}

            # Scatter data
            self.parent_widget.scatter_dict[self.id]["scatter"] = scatter_data

            # Refresh all graphs with new data
            self.parent_widget.refresh_graph()
