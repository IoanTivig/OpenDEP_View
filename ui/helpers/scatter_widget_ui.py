import random

from src.classes.pyqt import FloatDelegate
from src.func.general import *
from src.func.excel import *
from src.func.opendep_files import SPECTRUM_SAVE_FILTER, after_points_edited

from PyQt6.QtWidgets import QWidget, QPushButton, QColorDialog, QFileDialog, QAbstractScrollArea, QHeaderView, \
    QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUi

# Create a classes to handle the widget that will be spawn when the user wants to add a curve to the graph
class ScatterWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/widgets/scatter_widget.ui", self)

        # Varaibles
        self.parent_widget = None
        self.id = None
        self.disable_table_signals = False
        self.point_styles = ["o", "s", "v", "+", "x", "*"]

        # Some initial setup
        self.collapse(collapse=True)
        self.qt_tablewidget_exp_spectra.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.resize_table_height_to_no_rows()

        # Connect buttons
        self.connect_buttons()

    def connect_buttons(self):
        self.qt_checkbox_scatter_visible.clicked.connect(self.toggle_hide)
        self.qt_checkbox_curves_expand.clicked.connect(self.collapse)

        self.qt_spinbox_scatter_size.valueChanged.connect(self.pick_scatter_size)

        self.qt_combo_scatter_point_style.currentIndexChanged.connect(self.pick_scatter_point_style)

        self.qt_entry_scatter_name.textChanged.connect(self.pick_scatter_name)

        self.qt_button_add_scatter_point.clicked.connect(self.add_table_scatter_point)
        self.qt_button_remove_scatter_point.clicked.connect(lambda: self.remove_table_scatter_point(
            self.qt_tablewidget_exp_spectra.currentRow()))
        self.qt_button_pick_scatter_color.clicked.connect(self.pick_curve_color)
        self.qt_button_delete_scatter.clicked.connect(self.delete_self)
        self.qt_button_duplicate_scatter.clicked.connect(lambda: self.parent_widget.generate_new_scatter(
            type="duplicate",
            duplicate_id=self.id))
        self.qt_button_save_scatter.clicked.connect(self.save_scatter)
        self.qt_button_save_scatter_excel.clicked.connect(self.save_scatter_to_excel)

        self.qt_tablewidget_exp_spectra.itemSelectionChanged.connect(self.update_button_state)

    def update_button_state(self):
        # Enable the button if any items are selected, otherwise disable it
        if self.qt_tablewidget_exp_spectra.selectedItems():
            self.qt_button_remove_scatter_point.setEnabled(True)
        else:
            self.qt_button_remove_scatter_point.setEnabled(False)

    def connect_buttons_after_setup(self):
        self.qt_tablewidget_exp_spectra.cellChanged.connect(self.get_data_from_table)

    def collapse(self, collapse=True):
        if collapse:
            self.qt_frame_group_parameters.setVisible(False)
        else:
            self.qt_frame_group_parameters.setVisible(True)

    # The table shows all its rows (no scroll bar): rows + header + the 1 px border above and below
    def resize_table_height_to_no_rows(self):
        table = self.qt_tablewidget_exp_spectra
        table.setFixedHeight(table.verticalHeader().length() + table.horizontalHeader().height() + 2)

    def pick_curve_color(self):
        # Open color picker
        color = QColorDialog.getColor()
        if color.isValid():
            # Set color of button
            self.qt_button_pick_scatter_color.setStyleSheet(f"background-color: {color.name()}")
            # Set color of the curve on the graph
            self.parent_widget.scatter_dict[self.id]["color"] = color.name()
            self.parent_widget.refresh_graph()

    def pick_scatter_point_style(self):
        self.parent_widget.scatter_dict[self.id]["point_style"] = self.point_styles[self.qt_combo_scatter_point_style.currentIndex()]
        self.parent_widget.refresh_graph()

    def pick_scatter_size(self):
        self.parent_widget.scatter_dict[self.id]["point_size"] = self.qt_spinbox_scatter_size.value()
        self.parent_widget.refresh_graph()
        #self.start_focus_curve()

    def pick_scatter_name(self):
        self.parent_widget.scatter_dict[self.id]["name"] = self.qt_entry_scatter_name.text()
        self.parent_widget.refresh_graph()

    def toggle_hide(self):
        if self.qt_checkbox_scatter_visible.isChecked():
            self.parent_widget.scatter_dict[self.id]["visibility"] = True
        else:
            self.parent_widget.scatter_dict[self.id]["visibility"] = False

        self.parent_widget.refresh_graph()

    def delete_self(self):
        self.parent_widget.delete_scatter(self.id)
        self.close()

    def save_scatter(self):
        # Open file dialog and save the scatter as an OpenDEP Spectrum file (.odspec)
        filepath, _ = QFileDialog.getSaveFileName(self, "Save scatter", "", SPECTRUM_SAVE_FILTER)
        if filepath:
            self.parent_widget.save_scatter(self.id, filepath)

    def save_scatter_to_excel(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Scatter", "", "Excel (*.xlsx)")
        if filepath:
            save_scatter_to_excel(filepath, self.parent_widget.scatter_dict[self.id]['scatter'])

    def add_table_scatter_point(self):
        # Disable table signals
        self.disable_table_signals = True

        # Get the number of rows
        row_count = self.qt_tablewidget_exp_spectra.rowCount()

        # Insert a new row
        self.qt_tablewidget_exp_spectra.insertRow(row_count)

        # Set the default values
        if row_count == 0:
            self.qt_tablewidget_exp_spectra.setItem(row_count, 0, QTableWidgetItem("1000"))
            self.qt_tablewidget_exp_spectra.setItem(row_count, 1, QTableWidgetItem("0.5"))
            self.qt_tablewidget_exp_spectra.setItem(row_count, 2, QTableWidgetItem("0.05"))

        else:
            self.qt_tablewidget_exp_spectra.setItem(row_count, 0, QTableWidgetItem(
                str(parse_number(self.qt_tablewidget_exp_spectra.item(row_count - 1, 0).text()))))
            self.qt_tablewidget_exp_spectra.setItem(row_count, 1, QTableWidgetItem(
                str(parse_number(self.qt_tablewidget_exp_spectra.item(row_count - 1, 1).text()))))
            self.qt_tablewidget_exp_spectra.setItem(row_count, 2, QTableWidgetItem(
                str(parse_number(self.qt_tablewidget_exp_spectra.item(row_count - 1, 2).text()))))

        # Resize the table
        self.resize_table_height_to_no_rows()

        # Enable table signals
        self.disable_table_signals = False

        # Update the dictionary and graph
        self.get_data_from_table(added=True)

        # Lock table items to floats
        delegate = FloatDelegate(self.qt_tablewidget_exp_spectra)
        self.qt_tablewidget_exp_spectra.setItemDelegate(delegate)

    def remove_table_scatter_point(self, row):
        # Disable table signals
        self.disable_table_signals = True

        # Remove the row
        self.qt_tablewidget_exp_spectra.removeRow(row)

        # Resize the table
        self.resize_table_height_to_no_rows()

        # Enable table signals
        self.disable_table_signals = False

        # Update the dictionary and graph
        self.get_data_from_table(removed_row=row)

    def clear_table_scatter_points(self):
        self.qt_tablewidget_exp_spectra.clearContents()
        self.qt_tablewidget_exp_spectra.setRowCount(0)

    def set_entries_with_data(self):
        color = self.parent_widget.scatter_dict[self.id]["color"]
        name = self.parent_widget.scatter_dict[self.id]["name"]
        visible = self.parent_widget.scatter_dict[self.id]["visibility"]
        point_style = self.parent_widget.scatter_dict[self.id]["point_style"]
        point_style_index = self.point_styles.index(point_style)
        point_size = self.parent_widget.scatter_dict[self.id]["point_size"]

        self.qt_button_pick_scatter_color.setStyleSheet(f"background-color: {color}")
        self.qt_entry_scatter_name.setText(name)
        self.qt_checkbox_scatter_visible.setChecked(visible)
        self.qt_combo_scatter_point_style.setCurrentIndex(point_style_index)
        self.qt_spinbox_scatter_size.setValue(point_size)

        self.clear_table_scatter_points()
        scatter_data = self.parent_widget.scatter_dict[self.id]["scatter"]

        for i in range(len(scatter_data["frequencies"])):
            # Get the number of rows
            row_count = self.qt_tablewidget_exp_spectra.rowCount()

            # Insert a new row
            self.qt_tablewidget_exp_spectra.insertRow(row_count)

            # Populate the row
            self.qt_tablewidget_exp_spectra.setItem(i, 0, QTableWidgetItem(str(scatter_data["frequencies"][i])))
            self.qt_tablewidget_exp_spectra.setItem(i, 1, QTableWidgetItem(str(scatter_data["recm_values"][i])))
            self.qt_tablewidget_exp_spectra.setItem(i, 2, QTableWidgetItem(str(scatter_data["recm_errors"][i])))

        self.resize_table_height_to_no_rows()

        # Lock table items to floats
        delegate = FloatDelegate(self.qt_tablewidget_exp_spectra)
        self.qt_tablewidget_exp_spectra.setItemDelegate(delegate)

    # removed_row / added: a point was removed or added (the file's per-point data follows), see after_points_edited
    def get_data_from_table(self, row=None, column=None, removed_row=None, added=False):
        if not self.disable_table_signals:
            frequencies = []
            cm_factors = []
            cm_errors = []

            for row in range(self.qt_tablewidget_exp_spectra.rowCount()):
                frequencies.append(parse_number(self.qt_tablewidget_exp_spectra.item(row, 0).text()))
                cm_factors.append(parse_number(self.qt_tablewidget_exp_spectra.item(row, 1).text()))
                cm_errors.append(parse_number(self.qt_tablewidget_exp_spectra.item(row, 2).text()))

            scatter_data = {"frequencies": frequencies,
                            "recm_values": cm_factors,
                            "recm_errors": cm_errors}

            # Scatter data (per-point data of the file that no longer matches the points is dropped)
            self.parent_widget.scatter_dict[self.id]["scatter"] = scatter_data
            after_points_edited(self.parent_widget.scatter_dict[self.id], removed_row, added)

            # Refresh all graphs with new data
            self.parent_widget.refresh_graph()
