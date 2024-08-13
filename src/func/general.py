import os
import random

from PyQt5.QtGui import QDoubleValidator
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
    if value == None:
        # Return no CO
        return f"0.00 Hz"
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


def lock_entry_to_float(entry):
    validator = QDoubleValidator()
    validator.setNotation(
        QDoubleValidator.ScientificNotation
    )  # Standard floating-point notation
    validator.setDecimals(10)  # Allows up to 6 decimal places (adjust as needed)
    entry.setValidator(validator)
    entry.setMaxLength(12)  # Limit the number of characters to 10


def lock_entry_to_int(entry, min_value=1, max_value=2000, max_length=4):
    validator = QDoubleValidator()
    validator.setRange(min_value, max_value)
    validator.setDecimals(0)  # Disallow decimal points
    entry.setValidator(validator)
    entry.setMaxLength(max_length)  # Limit the number of characters to 10
