import os
import random
import re

from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QDoubleValidator
from matplotlib.font_manager import findSystemFonts
import numpy as np


def get_random_color_hex():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def format_frequency(value):
    """
    Converts a numeric frequency into a string with the appropriate unit
    (Hz, kHz, or MHz) and two decimal places of precision.

    Args:
        value (float or int): The frequency value to format.

    Returns:
        str: The formatted frequency string.
    """
    if value is None or value == 0:
        # No crossover ("0.00 Hz" would read as a value)
        return "none"
    elif value < 1000:
        # Value is in Hz
        return f"{value:.2f} Hz"
    elif value < 1000000:
        # Value is in kHz
        value_khz = value / 1000
        return f"{value_khz:.2f} kHz"
    else:
        # Value is in MHz
        value_mhz = value / 1000000
        return f"{value_mhz:.2f} MHz"


def get_all_os_fonts():
    """
    Get all available fonts on the system.
    """
    common_fonts = {
        "arial": "Arial",
        "verdana": "Verdana",
        "helvetica": "Helvetica",
        "times": "Times New Roman",
        "cour": "Courier New",
        "georgia": "Georgia",
        "trebuc": "Trebuchet MS",
        "impact": "Impact",
        "segoeui": "Segoe UI",
    }

    fonts = findSystemFonts(fontpaths=None, fontext="ttf")
    font_names_list = []
    for i in fonts:
        font_name = os.path.splitext(os.path.basename(i))[0]
        font_names_list.append(font_name.lower())

    final_font_list = []
    for font in common_fonts.keys():
        if font in font_names_list:
            final_font_list.append(common_fonts[font])

    return final_font_list


# Locale of the number validators: "." as decimal point and no thousands separator. With the system locale,
# Qt 6's validator rewrites a confirmed value as e.g. "9,755.66", which float() cannot read.
def number_locale():
    locale = QLocale.c()
    locale.setNumberOptions(QLocale.NumberOption.OmitGroupSeparator | QLocale.NumberOption.RejectGroupSeparator)
    return locale


# A number typed or shown in a field (thousands separators, if any, ignored)
def parse_number(text):
    return float(str(text).strip().replace(",", ""))


# A typed list of frequencies (Hz): separated by spaces, new lines, "," ";" "/" "_" or "-" ("1000-2000"); a "-" inside
# a number ("5e-1") stays part of it. Raises ValueError naming what cannot be read, or a frequency that is not > 0.
def parse_frequency_list(text):
    parts = [p for p in re.split(r"[\s,;/_]+|(?<![eE])-", str(text)) if p]
    frequencies = []
    for part in parts:
        try:
            value = float(part)
        except ValueError:
            raise ValueError(f'"{part}" is not a frequency: type numbers in Hz (e.g. 1000, 2.5e4, 1e6)') from None
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{part} Hz: frequencies must be greater than 0")
        frequencies.append(value)
    if not frequencies:
        raise ValueError("Type at least one frequency (Hz)")
    return np.array(frequencies)


def lock_entry_to_float(entry):
    validator = QDoubleValidator()
    validator.setLocale(number_locale())
    validator.setNotation(
        QDoubleValidator.Notation.ScientificNotation
    )  # Standard floating-point notation
    validator.setDecimals(1000)  # No limit: a longer value would be rewritten ("fixed up") on Enter
    entry.setValidator(validator)
    entry.setMaxLength(32)  # Allow enough room for scientific notation e.g. -1.23456789e-10


def lock_entry_to_int(entry, min_value=1, max_value=2000, max_length=4):
    validator = QDoubleValidator()
    validator.setLocale(number_locale())
    validator.setRange(min_value, max_value)
    validator.setDecimals(0)  # Disallow decimal points
    entry.setValidator(validator)
    entry.setMaxLength(max_length)  # Limit the number of characters to 10
