import random


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
