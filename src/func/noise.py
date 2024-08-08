import numpy as np
import colorednoise as cn


def generate_awgn(signal, std_dev=0.05):
    """
    Additive White Gaussian Noise (AWGN)

    This function adds Additive White Gaussian Noise to the input signal.
    AWGN is characterized by a normal distribution (Gaussian) with a mean of zero
    and a specified standard deviation. It represents random noise that affects
    the signal, simulating electronic or environmental noise.

    Args:
    - signal (np.array): The original signal.
    - std_dev (float): Standard deviation of the Gaussian noise.

    Returns:
    - np.array: Signal with added AWGN.
    """
    noise = np.random.normal(0, std_dev, signal.shape)
    return signal + noise


def generate_pink_noise(signal, std_dev=0.05):
    """
    Pink Noise (1/f Noise)

    This function adds Pink Noise, also known as 1/f noise, to the input signal.
    Pink noise has a power spectral density inversely proportional to its frequency,
    making it more prevalent at lower frequencies. It simulates long-term
    correlations and memory in the data.

    Args:
    - signal (np.array): The original signal.
    - std_dev (float): Standard deviation of the pink noise.

    Returns:
    - np.array: Signal with added pink noise.
    """
    noise = cn.powerlaw_psd_gaussian(1, len(signal)) * std_dev
    return signal + noise


def generate_poisson_noise(signal, scale=1000):
    """
    Poisson Noise (Shot Noise)

    This function adds Poisson noise to the input signal, simulating noise
    that occurs in photon-limited environments or in counting statistics.
    The noise is generated based on a Poisson distribution, which is typically
    used to model random events occurring at a known average rate.

    Args:
    - signal (np.array): The original signal.
    - scale (float): Scaling factor for the signal before applying Poisson noise.

    Returns:
    - np.array: Signal with added Poisson noise.
    """
    # Ensure signal is non-negative and does not contain NaNs
    signal = np.clip(signal, 0, None)  # Replace negative values with 0
    signal = np.nan_to_num(signal, nan=0.0)  # Replace NaNs with 0

    # Generate Poisson noise
    noisy_signal = np.random.poisson(signal * scale) / scale
    return noisy_signal


def generate_speckle_noise(signal, std_dev=0.05):
    """
    Multiplicative Gaussian Noise (Speckle Noise)

    This function adds speckle noise, which is a type of multiplicative Gaussian
    noise, to the input signal. Speckle noise is commonly found in coherent
    imaging systems like radar and ultrasound, where the noise is proportional
    to the local intensity of the signal.

    Args:
    - signal (np.array): The original signal.
    - std_dev (float): Standard deviation of the multiplicative noise.

    Returns:
    - np.array: Signal with added speckle noise.
    """
    noise = np.random.normal(0, std_dev, signal.shape)
    return signal + signal * noise


def generate_frequency_dependent_noise(signal, freqs, scale=0.01):
    """
    Frequency-dependent Noise

    This function adds frequency-dependent noise to the input signal.
    The noise varies with frequency, simulating real-world conditions
    where different frequencies might have different noise characteristics.
    This type of noise is often observed in complex systems where
    measurement uncertainty varies with frequency.

    Args:
    - signal (np.array): The original signal.
    - freqs (np.array): The frequency array corresponding to the signal.
    - scale (float): Scaling factor for the noise relative to frequency.

    Returns:
    - np.array: Signal with added frequency-dependent noise.
    """
    noise = np.random.normal(0, scale * np.log10(freqs + 1), signal.shape)
    return signal + noise
