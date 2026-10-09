import random
import re

from PyQt6.QtGui import QDoubleValidator

from src.func.general import *
from src.func import models
from src.func.opendep_files import CURVE_SAVE_FILTER, FIT_SUFFIX
from src.func import links

# Curve parameter -> its entry field (qt_entry_<name>)
PARAMETER_ENTRIES = {
    "buffer_perm": "param_buffer_perm", "buffer_cond": "param_buffer_cond",                     # Buffer
    "core_perm": "param_core_perm", "core_cond": "param_core_cond",                             # Core / particle
    "1st_shell_perm": "param_1st_shell_perm", "1st_shell_cond": "param_1st_shell_cond",         # Membrane
    "2nd_shell_perm": "param_2nd_shell_perm", "2nd_shell_cond": "param_2nd_shell_cond",         # Cell wall
    "core_radius": "param_size", "electric_field": "param_fieldgrad",                           # Radius, field
    "1st_shell_thick": "param_1st_shell_thick", "2nd_shell_thick": "param_2nd_shell_thick",     # Thicknesses
    "core_surface_cond": "param_core_surface_cond",                                             # Surface conductance
    "nucleus_radius": "param_nucleus_radius", "envelope_thick": "param_envelope_thick",         # Nucleus
    "envelope_perm": "param_envelope_perm", "envelope_cond": "param_envelope_cond",
    "nucleoplasm_perm": "param_nucleoplasm_perm", "nucleoplasm_cond": "param_nucleoplasm_cond",
}

from PyQt6.QtWidgets import QWidget, QPushButton, QColorDialog, QFileDialog
from PyQt6.uic import loadUi


# Create a classes to handle the widget that will be spawn when the user wants to add a curve to the graph
class CurveWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/widgets/curve_widget.ui", self)

        # Varaibles
        self.parent_widget = None
        self.id = None
        self.filling = False                 # True while set_entries_with_data fills the fields (not an edit)

        # Some initial setup
        self.collapse(collapse=True)

        # Connect the buttons to the functions
        self.qt_checkbox_curves_expand.clicked.connect(self.collapse)
        self.qt_button_pick_curve_color.clicked.connect(self.pick_curve_color)
        self.qt_checkbox_curves_visible.clicked.connect(self.toggle_hide)
        self.qt_entry_curve_name.editingFinished.connect(self.change_curve_name)
        self.qt_button_delete_curve.clicked.connect(self.delete_self)
        self.qt_button_duplicate_curve.clicked.connect(self.duplicate_curve)
        self.qt_button_save_curve.clicked.connect(self.save_curve)

        self.qt_combo_curve_line_style.currentIndexChanged.connect(self.pick_curve_line_style)
        self.qt_spinbox_curve_line_width.valueChanged.connect(self.change_curve_thickness)

        self.qt_button_simulate_curve_noise.clicked.connect(self.open_noise_widget)

        # Model selection
        self.qt_combo_model_selection.currentIndexChanged.connect(lambda:self.change_model(self.qt_combo_model_selection.currentIndex()))
        self.change_model(index=0, init=True)

        # On parameters entry change
        self.parameters_to_modify = [
        "param_buffer_perm", "param_buffer_cond",
        "param_core_perm", "param_core_cond",
        "param_1st_shell_perm", "param_1st_shell_cond",
        "param_2nd_shell_perm", "param_2nd_shell_cond",
        "param_size", "param_fieldgrad",
        "param_1st_shell_thick", "param_2nd_shell_thick",
        "param_core_surface_cond", "param_nucleus_radius",
        "param_envelope_thick", "param_envelope_perm", "param_envelope_cond",
        "param_nucleoplasm_perm", "param_nucleoplasm_cond"]

        for param in self.parameters_to_modify:
            getattr(self, f"qt_entry_{param}").editingFinished.connect(
                lambda param=param: self.parent_widget.modify_single_curve(self.id, edited=True))

        # Link: a scatter or a replicate group
        self.qt_combo_curve_link.activated.connect(self.link_selected)

        # Restrict entries to float
        entries_list = [self.qt_entry_param_buffer_perm,
                        self.qt_entry_param_buffer_cond,
                        self.qt_entry_param_core_perm,
                        self.qt_entry_param_core_cond,
                        self.qt_entry_param_1st_shell_perm,
                        self.qt_entry_param_1st_shell_cond,
                        self.qt_entry_param_1st_shell_thick,
                        self.qt_entry_param_2nd_shell_perm,
                        self.qt_entry_param_2nd_shell_cond,
                        self.qt_entry_param_2nd_shell_thick,
                        self.qt_entry_param_size,
                        self.qt_entry_param_fieldgrad,
                        self.qt_entry_param_core_surface_cond,
                        self.qt_entry_param_nucleus_radius,
                        self.qt_entry_param_envelope_thick,
                        self.qt_entry_param_envelope_perm,
                        self.qt_entry_param_envelope_cond,
                        self.qt_entry_param_nucleoplasm_perm,
                        self.qt_entry_param_nucleoplasm_cond]

        for entry in entries_list:
            lock_entry_to_float(entry)

    def collapse(self, collapse=True):
        if collapse:
            self.qt_frame_group_parameters.setVisible(False)
        else:
            self.qt_frame_group_parameters.setVisible(True)

    def change_model(self, index=None, init=False):
        # Models (as in OpenDEP Compute): 0 homogenous, 1 single-shell, 2 two-shell (cell wall),
        # 3 three-shell (nucleus), 4 four-shell (nucleus + cell wall)
        # Layers: core = cytoplasm (homogenous: the particle), 1st shell = membrane, 2nd shell = cell wall
        for i in self.qt_frame_input_group.findChildren(QWidget):
            i.setVisible(True)

        has_shell = index >= 1
        has_wall = index in (2, 4)
        has_nucleus = index in (3, 4)

        # Parameter groups and rows used by the model
        self.qt_frame_core_surface_cond.setVisible(index == 0)
        self.qt_frame_size_group.setVisible(has_shell)
        self.qt_frame_1st_shell_group.setVisible(has_shell)
        self.qt_frame_2nd_shell_group.setVisible(has_wall)
        self.qt_frame_2nd_thick.setVisible(has_wall)
        self.qt_frame_envelope_thick.setVisible(has_nucleus)
        self.qt_frame_nucleus_radius.setVisible(has_nucleus)
        self.qt_frame_envelope_group.setVisible(has_nucleus)
        self.qt_frame_nucleoplasm_group.setVisible(has_nucleus)

        # Group titles: what each layer is
        self.qt_label_core_group.setText("Particle" if index == 0 else "Cytoplasm")
        self.qt_label_1st_shell_group.setText("Membrane")
        self.qt_label_2nd_shell_group.setText("Cell wall")
        self.qt_label_1st_shell_thick.setText("Membrane thickness (nm)")
        self.qt_label_2nd_shell_thick.setText("Wall thickness (nm)")

        # Place the groups two per row in the order of the layers, the used ones first, so no empty slot is left
        # where a group of another model would be (e.g. the cell wall in the three-shell model)
        groups = [self.qt_frame_buffer_group, self.qt_frame_core_group,
                  self.qt_frame_other_group, self.qt_frame_size_group,
                  self.qt_frame_1st_shell_group, self.qt_frame_2nd_shell_group,
                  self.qt_frame_envelope_group, self.qt_frame_nucleoplasm_group]
        groups = [g for g in groups if not g.isHidden()] + [g for g in groups if g.isHidden()]
        for position, group in enumerate(groups):
            self.qt_group_singleshell.addWidget(group, position // 2, position % 2)

        # Cross-overs of the selected model
        crossover_frames = [self.qt_frame_group_homogenous_co, self.qt_frame_group_singleshell_co,
                            self.qt_frame_group_twoshell_co, self.qt_frame_group_threeshell_co,
                            self.qt_frame_group_fourshell_co]
        for i, frame in enumerate(crossover_frames):
            frame.setVisible(i == index)

        if not init and not self.filling:
            self.parent_widget.curves_dict[self.id]["model"] = index
            self.parent_widget.modify_single_curve(self.id, edited=True)

    def set_entries_with_data(self):
        self.filling = True
        try:
            self.fill_entries()
        finally:
            self.filling = False
        self.update_links()

    def fill_entries(self):
        color = self.parent_widget.curves_dict[self.id]["color"]
        name = self.parent_widget.curves_dict[self.id]["name"]
        visible = self.parent_widget.curves_dict[self.id]["visibility"]
        model = self.parent_widget.curves_dict[self.id]["model"]
        parameters = self.parent_widget.curves_dict[self.id]["parameters"]

        self.qt_button_pick_curve_color.setStyleSheet(f"background-color: {color}")
        self.qt_entry_curve_name.setText(name)
        self.qt_checkbox_curves_visible.setChecked(visible)

        # Model Selection
        self.qt_combo_model_selection.setCurrentIndex(model)

        # Parameter values, shown short so they fit the narrowest field (fitted values have many more digits):
        # 4 significant digits, 2 with an exponent (6.9e-6). The exact value is kept, used as long as the shown
        # text is not changed, and shown in the tooltip
        self.exact_values = {}
        for key, entry_name in PARAMETER_ENTRIES.items():
            entry = getattr(self, f"qt_entry_{entry_name}")
            value = float(parameters[key])
            shown = f"{value:.4g}"
            if "e" in shown:
                shown = re.sub(r"e([+-])0+(\d)", r"e\1\2", f"{value:.2g}")      # 6.889e-06 -> 6.9e-6
            entry.setText(shown)
            entry.setCursorPosition(0)
            entry.setToolTip(f"{value:.10g}" if shown != f"{value:.10g}" else "")
            self.exact_values[key] = (shown, value)

        self.update_crossover()

    def update_crossover(self):
        parameters = self.parent_widget.curves_dict[self.id]["parameters"]

        self.qt_entry_homogenous_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["homogenous"]))  # Homogenous first coross-over
        self.qt_entry_homogenous_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["homogenous"]))  # Homogenous second coross-over

        self.qt_entry_singleshell_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["single_shell"]))  # 1st shell first coross-over
        self.qt_entry_singleshell_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["single_shell"]))  # 2nd shell first coross-over

        self.qt_entry_twoshell_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["two_shell"]))  # 1st shell first coross-over
        self.qt_entry_twoshell_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["two_shell"]))  # 2nd shell first coross-over

        self.qt_entry_threeshell_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["three_shell"]))  # Three-shell first coross-over
        self.qt_entry_threeshell_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["three_shell"]))  # Three-shell second coross-over

        self.qt_entry_fourshell_firstco.setText(
            format_frequency(parameters["1st_cross_over"]["four_shell"]))  # Four-shell first coross-over
        self.qt_entry_fourshell_secondco.setText(
            format_frequency(parameters["2nd_cross_over"]["four_shell"]))  # Four-shell second coross-over

    def get_data_from_entries(self):
        # The exact value while the shown text is unchanged, otherwise the value typed
        parameters = {}
        exact_values = getattr(self, "exact_values", {})
        for key, entry_name in PARAMETER_ENTRIES.items():
            text = getattr(self, f"qt_entry_{entry_name}").text()
            shown, exact = exact_values.get(key, (None, None))
            parameters[key] = exact if text == shown else parse_number(text)

        parameters["1st_cross_over"] = {key: 0.0 for key in models.MODEL_KEYS}
        parameters["2nd_cross_over"] = {key: 0.0 for key in models.MODEL_KEYS}

        return parameters

    def toggle_hide(self):
        if self.qt_checkbox_curves_visible.isChecked():
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
            self.qt_button_pick_curve_color.setStyleSheet(f"background-color: {color.name()}")
            # Set color of the curve on the graph
            self.parent_widget.curves_dict[self.id]["color"] = color.name()
            self.parent_widget.refresh_graph()

    def pick_curve_line_style(self):
        styles = ['-', ':', '--', '-.']
        self.parent_widget.curves_dict[self.id]["line_style"] = styles[self.qt_combo_curve_line_style.currentIndex()]
        self.parent_widget.refresh_graph()

    def change_curve_thickness(self):
        self.parent_widget.curves_dict[self.id]["line_width"] = self.qt_spinbox_curve_line_width.value()
        self.parent_widget.refresh_graph()
        self.start_focus_curve()

    def change_curve_name(self):
        self.parent_widget.curves_dict[self.id]["name"] = self.qt_entry_curve_name.text()
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
        self.parent_widget.qt_graph_widget.focus_curve(self.parent_widget.curves_dict[self.id]["name"])
    def stop_focus_curve(self):
        #self.parent_widget.refresh_graph()
        if self.id in self.parent_widget.curves_dict.keys():
            self.parent_widget.qt_graph_widget.unfocus_curve(self.parent_widget.curves_dict[self.id]["name"])

    def duplicate_curve(self):
        self.parent_widget.duplicate_curve(self.id)
        self.collapse()
        self.qt_checkbox_curves_expand.setChecked(True)

    def save_curve(self):
        # Open file dialog and save the curve as an OpenDEP Curve file (.odcurve), or with its linked scatters as
        # an OpenDEP Fit file (.odfit)
        filepath, selected_filter = QFileDialog.getSaveFileName(self, "Save curve", "", CURVE_SAVE_FILTER)
        if filepath:
            if FIT_SUFFIX in selected_filter and not filepath.lower().endswith(FIT_SUFFIX):
                filepath += FIT_SUFFIX
            self.parent_widget.save_curve(self.id, filepath)

    # LINK - the scatter this curve belongs to (e.g. the data it was fitted to)
    # The "Linked to" list, the group the scatter is in, the fit status
    def update_links(self):
        main = self.parent_widget
        if main is None or self.id not in main.curves_dict:
            return
        curve = main.curves_dict[self.id]
        kind, target_id = links.link_target(curve)

        # 1. Every scatter can be chosen (one linked to another curve moves here)
        combo = self.qt_combo_curve_link
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Nothing", "")
        for scatter_id, scatter in main.scatter_dict.items():
            combo.addItem(scatter["name"], f"scatter:{scatter_id}")
        index = combo.findData(f"{kind}:{target_id}") if kind == "scatter" else 0
        combo.setCurrentIndex(max(index, 0))
        combo.blockSignals(False)

        # 2. The replicate groups the linked scatter is in: this curve's parameters count in their averages
        info = ""
        if kind == "scatter":
            groups = [f"{group['name']} (biological replicate {m['biological']})"
                      for group in main.groups_dict.values() for m in group["members"] if m["scatter"] == target_id]
            if groups:
                info = f"Scatter in group {', '.join(groups)}: this curve's parameters count in its averages"
        self.qt_label_link_info.setText(info)
        self.qt_label_link_info.setToolTip(info)
        self.qt_label_link_info.setVisible(bool(info))                 # no empty line when there is nothing to say

        # 3. Fit from OpenDEP Compute, or changed since
        status = curve.get("fit_status")
        self.qt_label_fit_status.setText({"fitted": "Fitted in OpenDEP Compute",
                                          "edited": "Edited after the fit"}.get(status, ""))
        self.qt_label_fit_status.setToolTip(
            "The values come from a fit in OpenDEP Compute; its results are saved with the curve"
            if status == "fitted" else
            "The values were changed in View after the fit; the fit results are no longer saved"
            if status == "edited" else "")
        self.qt_label_fit_status.setVisible(status in ("fitted", "edited"))

    def link_selected(self, index):
        target = self.qt_combo_curve_link.itemData(index) or ""
        if not target:
            self.parent_widget.set_curve_link(self.id, None, None)
        else:
            kind, target_id = target.split(":")
            self.parent_widget.set_curve_link(self.id, kind, int(target_id))

    def open_noise_widget(self):
        self.parent_widget.noise_widget.selected_curve_id = self.id
        self.parent_widget.noise_widget.exec()
