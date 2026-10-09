import numpy as np
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUi

from src.func import general, models, noise


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
        self.qt_button_back.clicked.connect(self.exit)
        self.qt_button_generate_scatter.clicked.connect(lambda: self.parent_widget.generate_new_scatter(type="noise"))

    def style_window(self):
        # Remove the title bar, logo, and exit button
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

        # Add Transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Add a shadow effect, on the inner frame (drawn in the window's transparent margin). A graphics effect on
        # the window itself leaves the window blank when it is opened again, which blocks the program
        shadow = QGraphicsDropShadowEffect(self.verticalFrame)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 75))  # Black color with some transparency
        self.verticalFrame.setGraphicsEffect(shadow)

    def exit(self):
        self.close()

    def generate_frequencies(self):
        if self.qt_radio_frequencies_generated.isChecked():
            no_freq = int(self.qt_entry_frequencies_no.text())
            start_freq = float(self.qt_entry_frequencies_start.text())
            stop_freq = float(self.qt_entry_frequencies_stop.text())

            # Generate a log-spaced frequency array
            frequencies = np.logspace(np.log10(start_freq), np.log10(stop_freq), no_freq)

        elif self.qt_radio_frequencies_manual.isChecked():
            # Separators , ; / _ - and spaces; "5e-1" stays one number; ValueError (shown) when a value is wrong
            frequencies = general.parse_frequency_list(self.qt_entry_frequencies_manual.toPlainText())

        return frequencies

    def generate_errors(self, frequencies):
        if self.qt_checkbox_errorbars_generate.isChecked():

            stdev_max = float(self.qt_entry_errorbars_stdev_max.text())
            stdev_min = float(self.qt_entry_errorbars_stdev_min.text())

            errors = np.random.uniform(stdev_min, stdev_max, len(frequencies))

        else:
            errors = np.random.uniform(0, 0, len(frequencies))

        return errors

    def add_noise(self, frequencies, recm):
        scale = float(self.qt_entry_noise_scale.text())
        stdev = float(self.qt_entry_noise_stdev.text())

        if self.qt_radio_noise_awg.isChecked():
            recm_noisy = noise.generate_awgn(recm, std_dev=stdev)
        elif self.qt_radio_noise_speckle.isChecked():
            recm_noisy = noise.generate_speckle_noise(recm, std_dev=stdev)
        elif self.qt_radio_noise_pink.isChecked():
            recm_noisy = noise.generate_pink_noise(recm, std_dev=stdev)
        elif self.qt_radio_noise_poisson.isChecked():
            recm_noisy = noise.generate_poisson_noise(recm, scale=scale)
        elif self.qt_radio_noise_frequency.isChecked():
            recm_noisy = noise.generate_frequency_dependent_noise(recm, freqs=frequencies, scale=scale)

        return recm_noisy

    def generate_recm(self, frequencies):
        # Re[CM] of the selected curve's model at the given frequencies
        parameters = self.parent_widget.curves_dict[self.selected_curve_id]["parameters"]
        model = self.parent_widget.curves_dict[self.selected_curve_id]["model"]

        recm, imcm, depforce = models.model_all(model, np.asarray(frequencies, dtype=float), parameters)
        return np.array(recm)

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
