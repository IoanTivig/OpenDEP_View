import numpy as np
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

from src.func import models, noise


class NoiseWidgetUI(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi("ui/widgets/noise_widget.ui", self)

        # Initial setup
        self.style_window()

        # Varaibles
        self.parent_widget = parent
        self.selected_curve_id = None

        # Connect buttons
        self.connect_buttons()

    def connect_buttons(self):
        self.pyqt5_button_back.clicked.connect(self.exit)
        self.pyqt5_button_generate_scatter.clicked.connect(lambda: self.parent_widget.generate_new_scatter(type="noise"))

    def style_window(self):
        # Remove the title bar, logo, and exit button
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # Add Transparency
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Add a shadow effect
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 75))  # Black color with some transparency
        self.setGraphicsEffect(shadow)

    def exit(self):
        self.close()

    def generate_frequencies(self):
        if self.pyqt5_radio_frequencies_generated.isChecked():
            no_freq = int(self.pyqt5_entry_frequencies_no.text())
            start_freq = float(self.pyqt5_entry_frequencies_start.text())
            stop_freq = float(self.pyqt5_entry_frequencies_stop.text())

            # Generate a log-spaced frequency array
            frequencies = np.logspace(np.log10(start_freq), np.log10(stop_freq), no_freq)

        elif self.pyqt5_radio_frequencies_manual.isChecked():
            string = self.pyqt5_entry_frequencies_manual.toPlainText()
            frequencies = np.array([float(i) for i in string.replace(",", " ").replace("/", " ").replace("-", " ").replace("_", " ").split()])

        return frequencies

    def generate_errors(self, frequencies):
        if self.pyqt5_checkbox_errorbars_generate.isChecked():

            stdev_max = float(self.pyqt5_entry_errorbars_stdev_max.text())
            stdev_min = float(self.pyqt5_entry_errorbars_stdev_min.text())

            errors = np.random.uniform(stdev_min, stdev_max, len(frequencies))

        else:
            errors = np.random.uniform(0, 0, len(frequencies))

        return errors

    def add_noise(self, frequencies, recm):
        scale = float(self.pyqt5_entry_noise_scale.text())
        stdev = float(self.pyqt5_entry_noise_stdev.text())

        if self.pyqt5_radio_noise_awg.isChecked():
            recm_noisy = noise.generate_awgn(recm, std_dev=stdev)
        elif self.pyqt5_radio_noise_speckle.isChecked():
            recm_noisy = noise.generate_speckle_noise(recm, std_dev=stdev)
        elif self.pyqt5_radio_noise_pink.isChecked():
            recm_noisy = noise.generate_pink_noise(recm, std_dev=stdev)
        elif self.pyqt5_radio_noise_poisson.isChecked():
            recm_noisy = noise.generate_poisson_noise(recm, scale=scale)
        elif self.pyqt5_radio_noise_frequency.isChecked():
            recm_noisy = noise.generate_frequency_dependent_noise(recm, freqs=frequencies, scale=scale)

        return recm_noisy

    def generate_recm(self, frequencies):
        parameters = self.parent_widget.curves_dict[self.selected_curve_id]["parameters"]

        recm_ho_list = []
        recm_ss_list = []
        recm_ts_list = []

        for i in frequencies:
            recm_ho, imcm_ho, depforce_ho = models.homogenous_particle_all(
                freq=i,
                fitting_gen_fieldgrad=parameters["electric_field"],
                fitting_hopa_particle_radius=parameters["core_radius"],
                fitting_hopa_particle_perm=parameters["core_perm"],
                fitting_hopa_particle_cond=parameters["core_cond"],
                fitting_gen_buffer_perm=parameters["buffer_perm"],
                fitting_gen_buffer_cond=parameters["buffer_cond"])

            recm_ss, imcm_ss, depforce_ss = models.single_shell_all(
                freq=i,
                fitting_gen_fieldgrad=parameters["electric_field"],
                fitting_sish_particle_radius=parameters["core_radius"],
                fitting_sish_membrane_thickness=parameters["1st_shell_thick"],
                fitting_sish_membrane_perm=parameters["1st_shell_perm"],
                fitting_sish_membrane_cond=parameters["1st_shell_cond"],
                fitting_sish_cytoplasm_perm=parameters["core_perm"],
                fitting_sish_cytoplasm_cond=parameters["core_cond"],
                fitting_gen_buffer_perm=parameters["buffer_perm"],
                fitting_gen_buffer_cond=parameters["buffer_cond"])

            recm_ts, imcm_ts, depforce_ts = models.two_shell_all(
                freq=i,
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

            recm_ho_list.append(recm_ho)
            recm_ss_list.append(recm_ss)
            recm_ts_list.append(recm_ts)

        if self.parent_widget.curves_dict[self.selected_curve_id]["model"] == 0:
            # transform to np.array
            recm_ho_list = np.array(recm_ho_list)
            return recm_ho_list

        elif self.parent_widget.curves_dict[self.selected_curve_id]["model"] == 1:
            recm_ss_list = np.array(recm_ss_list)
            return recm_ss_list

        elif self.parent_widget.curves_dict[self.selected_curve_id]["model"] == 2:
            recm_ts_list = np.array(recm_ts_list)
            return recm_ts_list

    def generate_noise_scatter(self):
        frequencies = self.generate_frequencies()
        errors = self.generate_errors(frequencies=frequencies)
        recm_list = self.generate_recm(frequencies=frequencies)
        recm_noisy_list = self.add_noise(frequencies=frequencies, recm=recm_list)

        frequencies = frequencies.tolist()
        recm_noisy_list = recm_noisy_list.tolist()
        errors = errors.tolist()

        noise_data = {"frequencies": frequencies,
                        "recm_values": recm_noisy_list,
                        "recm_errors": errors}

        return noise_data
