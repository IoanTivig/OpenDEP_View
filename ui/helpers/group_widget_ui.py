from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QColorDialog, QHeaderView, QTableWidgetItem, QPushButton, QLabel, QFrame, \
    QGridLayout
from PyQt6.uic import loadUi

from src.func import parameters as model_parameters
from src.func import replicates
from src.func.general import format_frequency

POINT_STYLES = ["o", "s", "v", "+", "x", "*"]
LINE_STYLES = ['-', ':', '--', '-.']
REMOVE_BUTTON_STYLE = """QPushButton {
    border: none;
    background: transparent;
    border-radius: 6px;
    padding: 4px;
    image: url(:/ui/qt/resources/buttons/substract_icon.png);
}
QPushButton:hover {
    background: #F1F5F9;
}"""


# A calculated value (replicates.average_scalar) as shown: "mean ± SD" (frequencies in one unit: "29.44 ± 3.93
# kHz"), the mean alone when there is no spread; and the tooltip that says where it comes from
def format_result(stats, unit="", frequency=False):
    if stats is None or stats["kind"] == "none":
        return ("none" if frequency else "–"), "No value"

    if frequency:
        text = format_frequency(stats["mean"])
        if stats["sd"]:
            number, frequency_unit = text.split(" ")
            factor = {"Hz": 1, "kHz": 1e3, "MHz": 1e6}[frequency_unit]
            text = f"{number} ± {stats['sd'] / factor:.2f} {frequency_unit}"
    else:
        text = f"{stats['mean']:.4g}" + (f" ± {stats['sd']:.2g}" if stats["sd"] else "")

    unit_text = f" {unit}" if unit else ""
    if stats["kind"] == "single":
        tip = "From 1 curve"
    elif stats["sd"] == 0:
        tip = "The same in all the curves"
    elif stats["kind"] == "biological":
        tip = f"Mean ± SD over {stats['n_biological']} biological replicates ({stats['n_technical']} curves)"
    else:
        tip = f"Mean ± SD of {stats['n_technical']} technical replicates (1 biological replicate)"
    return text, f"{tip}{unit_text and ', in' + unit_text}"


# A replicate group (Group plots): its replicates (a curve with the scatter it is linked to, and the sample = the
# biological replicate), the results calculated from them (mean ± SD of the data, of the crossovers and of the
# parameters of the curves; not editable), and how the group's mean scatter and curve are drawn (one colour)
class GroupWidgetUI(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi("ui/widgets/group_widget.ui", self)

        # Variables
        self.parent_widget = None
        self.id = None
        self.filling = False

        # Initial setup
        header = self.qt_table_group_members.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.qt_table_group_members.setColumnWidth(2, 95)
        self.qt_table_group_members.setColumnWidth(3, 34)
        self.collapse(False)

        # Connect buttons
        self.connect_buttons()

    def connect_buttons(self):
        self.qt_checkbox_group_visible.clicked.connect(self.toggle_hide)
        self.qt_checkbox_group_expand.clicked.connect(lambda checked: self.collapse(not checked))
        self.qt_entry_group_name.editingFinished.connect(self.change_name)
        self.qt_button_pick_group_color.clicked.connect(self.pick_color)
        self.qt_combo_group_point_style.currentIndexChanged.connect(
            lambda index: self.set_style("point_style", POINT_STYLES[index]))
        self.qt_combo_group_line_style.currentIndexChanged.connect(
            lambda index: self.set_style("line_style", LINE_STYLES[index]))
        self.qt_spinbox_group_point_size.valueChanged.connect(lambda value: self.set_style("point_size", value))
        self.qt_spinbox_group_line_width.valueChanged.connect(lambda value: self.set_style("line_width", value))
        self.qt_combo_group_add_scatter.activated.connect(self.add_selected_scatter)
        self.qt_table_group_members.cellChanged.connect(self.member_changed)
        self.qt_button_export_group.clicked.connect(lambda: self.parent_widget.export_group(self.id, kind="opendep"))
        self.qt_button_export_group_table.clicked.connect(lambda: self.parent_widget.export_group(self.id,
                                                                                                  kind="table"))
        self.qt_button_delete_group.clicked.connect(self.delete_self)

    def collapse(self, collapse=True):
        self.qt_frame_group_parameters.setVisible(not collapse)
        self.qt_checkbox_group_expand.setChecked(not collapse)

    def group(self):
        return self.parent_widget.groups_dict[self.id]

    # HEADER: name and style (the only settings of a group)
    def set_entries_with_data(self):
        group = self.group()
        self.filling = True
        self.qt_entry_group_name.setText(group["name"])
        self.qt_checkbox_group_visible.setChecked(group["visibility"])
        self.qt_button_pick_group_color.setStyleSheet(f"background-color: {group['color']};")
        self.qt_combo_group_point_style.setCurrentIndex(POINT_STYLES.index(group["point_style"]))
        self.qt_combo_group_line_style.setCurrentIndex(LINE_STYLES.index(group["line_style"]))
        self.qt_spinbox_group_point_size.setValue(group["point_size"])
        self.qt_spinbox_group_line_width.setValue(group["line_width"])
        self.filling = False
        self.update_members()

    def toggle_hide(self):
        self.group()["visibility"] = self.qt_checkbox_group_visible.isChecked()
        self.parent_widget.refresh_graph()

    def change_name(self):
        self.group()["name"] = self.qt_entry_group_name.text().strip() or "Group"
        self.parent_widget.refresh_graph()

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.group()["color"] = color.name()
            self.qt_button_pick_group_color.setStyleSheet(f"background-color: {color.name()};")
            self.parent_widget.refresh_graph()

    def set_style(self, key, value):
        if not self.filling:
            self.group()[key] = value
            self.parent_widget.refresh_graph()

    def delete_self(self):
        self.parent_widget.delete_group(self.id)
        self.close()

    # REPLICATES
    # Table of the replicates (curve, scatter, sample No.), the summary, the replicates that can be added (a curve
    # with its linked scatter), and the results
    # Each part is rebuilt only when what it shows changed (with many groups, rebuilding them all on every refresh of
    # the graph was slow); force rebuilds everything, e.g. to undo an edit typed in the table
    def update_members(self, force=False):
        main = self.parent_widget
        if main is None or self.id not in main.groups_dict:
            return
        group = self.group()
        members = [m for m in group["members"] if m["scatter"] in main.scatter_dict]
        shown = getattr(self, "shown", {}) if not force else {}
        self.shown = {}

        # 1. Table (rebuilt with its signals off, so filling it is not taken as edits)
        linked = [main.curve_linked_to("scatter", m["scatter"]) for m in members]
        rows = tuple((m["scatter"], main.curves_dict[c]["name"] if c is not None else None,
                      main.scatter_dict[m["scatter"]]["name"], str(m["biological"])) for m, c in zip(members, linked))
        self.shown["rows"] = rows
        if shown.get("rows") != rows:
            self.fill_table(members, linked)

        # 2. What the group is made of
        self.qt_label_group_summary.setText(replicates.summary_text(replicates.group_summary(
            [{"biological": m["biological"]} for m in members])))

        # 3. Replicates that can be added: curves linked to a scatter that is not in the group yet
        in_group = {m["scatter"] for m in members}
        options = tuple((f"{curve['name']} / {main.scatter_dict[link['scatter']]['name']}", link["scatter"])
                        for curve in main.curves_dict.values() for link in [curve.get("link") or {}]
                        if link.get("scatter") in main.scatter_dict and link["scatter"] not in in_group)
        self.shown["options"] = options
        if shown.get("options") != options:
            self.fill_add_combo(options)

        # 4. Results (plain numbers and text, so an unchanged result compares equal)
        result = main.group_result(self.id)
        results = repr((result["average"]["summary"], result["model"], result.get("joint")))
        self.shown["results"] = results
        if shown.get("results") != results:
            self.update_results(result)

    def fill_table(self, members, linked):
        main = self.parent_widget
        table = self.qt_table_group_members
        table.blockSignals(True)
        table.setRowCount(len(members))
        for row, (member, curve_id) in enumerate(zip(members, linked)):
            curve = QTableWidgetItem(main.curves_dict[curve_id]["name"] if curve_id is not None else "–")
            curve.setFlags(Qt.ItemFlag.ItemIsEnabled)
            curve.setToolTip("" if curve_id is not None else
                             "No curve linked to this scatter (any more): it counts in the mean scatter only")
            table.setItem(row, 0, curve)
            scatter = QTableWidgetItem(main.scatter_dict[member["scatter"]]["name"])
            scatter.setFlags(Qt.ItemFlag.ItemIsEnabled)
            scatter.setData(Qt.ItemDataRole.UserRole, member["scatter"])
            table.setItem(row, 1, scatter)
            table.setItem(row, 2, QTableWidgetItem(str(member["biological"])))
            remove = QPushButton()
            remove.setStyleSheet(REMOVE_BUTTON_STYLE)
            remove.setToolTip("Remove from the group (the curve and the scatter stay)")
            remove.clicked.connect(lambda checked=False, sid=member["scatter"]:
                                   main.remove_scatter_from_group(self.id, sid))
            table.setCellWidget(row, 3, remove)
        table.blockSignals(False)
        table.setFixedHeight(max(1, len(members)) * 30 + table.horizontalHeader().height() + 4)

    # Replicates that can be added: (text, scatter id) of the curves linked to a scatter outside the group
    def fill_add_combo(self, options):
        combo = self.qt_combo_group_add_scatter
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Add a replicate…", None)
        for text, scatter_id in options:
            combo.addItem(text, scatter_id)
        # The open list as wide as its longest name, even when the combo itself is narrower
        widest = max(combo.fontMetrics().horizontalAdvance(combo.itemText(i)) for i in range(combo.count()))
        combo.view().setMinimumWidth(widest + 40)
        combo.setEnabled(combo.count() > 1)
        combo.setToolTip("Add a replicate: a curve with the scatter it is linked to" if combo.count() > 1 else
                         "No curve linked to a scatter outside this group: link a curve to its scatter in the "
                         "curve's \"Linked to\" first")
        combo.blockSignals(False)

    def add_selected_scatter(self, index):
        scatter_id = self.qt_combo_group_add_scatter.itemData(index)
        if scatter_id is not None:
            self.parent_widget.add_scatter_to_group(self.id, scatter_id)

    # Sample No. (biological replicate, any label) typed in the table
    def member_changed(self, row, column):
        if column != 2:
            return
        table = self.qt_table_group_members
        scatter_id = table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        text = table.item(row, column).text().strip()
        if text:
            self.parent_widget.set_member_biological(self.id, scatter_id, text)
        else:
            self.update_members(force=True)               # an emptied cell: the table shows the label again

    # RESULTS (calculated, read-only)
    # Samples (biological and technical replicates) with the model, crossovers, and the parameters grouped as in
    # the curve widget
    def update_results(self, result):
        stats = result["model"]
        model = stats["model"]

        # 1. Samples: biological replicates (the n of the SD) and technical replicates (all the scatters)
        summary = result["average"]["summary"]
        n_technical = sum(summary["technical_per_biological"].values())
        self.qt_label_samples.setText(f"{summary['n_biological']} biological · {n_technical} technical"
                                      if n_technical else "none")

        # 2. The model (name and symbol, as in the curve widget), or why there is none
        if model is None:
            self.qt_label_results_model.setText("no model")
            self.qt_label_results_model.setToolTip(stats["warning"])
            self.qt_label_results_model_icon.clear()
        else:
            source = " (joint fit)" if result.get("joint") else ""
            self.qt_label_results_model.setText(f"{model_parameters.MODEL_NAMES[model]}{source}")
            self.qt_label_results_model.setToolTip("Model of the replicates' curves" if not source else
                                                   "One curve fitted to all the replicates together")
            self.qt_label_results_model_icon.setPixmap(QPixmap(model_parameters.MODEL_ICONS[model]))
        self.qt_label_results_model_icon.setVisible(model is not None)

        # 3. Crossovers (one row)
        for label, key in ((self.qt_label_crossover_first, "first_crossover"),
                           (self.qt_label_crossover_second, "second_crossover")):
            text, tip = format_result(stats[key], frequency=True)
            label.setText(text)
            label.setToolTip(tip)

        # 4. Parameters: one card per parameter group, two cards per row, each row "label (unit)  value" as in the
        #    curve widget; a card's content stays at its top when its neighbour in the row is taller
        layout = self.qt_layout_parameter_results
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()
        for row in range(layout.rowCount()):                      # stretch of an earlier model's last row
            layout.setRowStretch(row, 0)
        self.qt_frame_parameter_results.setVisible(model is not None)
        if model is None:
            return
        groups = model_parameters.grouped_parameters(model)
        for position, (title, keys) in enumerate(groups):
            # Sizes as in the curve widget's cards: margins 9, spacing 6, names : values = 5 : 3, values <= 200 px
            card = QFrame()
            card.setProperty("card", True)
            grid = QGridLayout(card)
            grid.setContentsMargins(9, 9, 9, 9)
            grid.setHorizontalSpacing(6)
            grid.setVerticalSpacing(6)
            heading = QLabel(title)
            heading.setProperty("title", True)
            grid.addWidget(heading, 0, 0, 1, 2)
            for row, key in enumerate(keys, 1):
                _, label, unit = model_parameters.PARAMETER_INFO[key]
                text, tip = format_result(stats["parameters"][key], unit)
                name = QLabel(f"{label} ({unit})")
                name.setProperty("parameter", True)
                value = QLabel(text)
                value.setProperty("value", True)
                value.setToolTip(tip)
                value.setMaximumWidth(200)
                value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                grid.addWidget(name, row, 0)
                grid.addWidget(value, row, 1)
            grid.setColumnStretch(0, 5)
            grid.setColumnStretch(1, 3)
            grid.setRowStretch(len(keys) + 1, 1)                    # content at the top
            layout.addWidget(card, position // 2, position % 2)
        layout.setRowStretch((len(groups) + 1) // 2, 1)
