import math
import numpy as np


# General functions #
def complex_perm(freq, relperm, cond):
    # Ensure inputs are of a higher precision data type
    relperm = np.array(relperm, dtype=np.float64)
    cond = np.array(cond, dtype=np.float64)
    freq = np.array(freq, dtype=np.float64)

    # Perform calculation, explicitly using complex numbers
    result = (relperm * 8.854e-12) - 1j * cond / (freq * 2 * np.pi)

    # Ensure the result is of complex type to handle imaginary parts correctly
    return np.array(result, dtype=np.complex128)


# Single-shell model #
# Single-Shell Models composed of a cytoplasm surrounded by a cell membrane
# Calculate the equivalent complex permittivity for a single-shell model
def single_shell_equivalent_complex_permittivity(
    freq,
    fitting_sish_particle_radius,
    fitting_sish_membrane_thickness,
    fitting_sish_membrane_perm,
    fitting_sish_membrane_cond,
    fitting_sish_cytoplasm_perm,
    fitting_sish_cytoplasm_cond,
):
    # Calculate complex permittivity for membrane and cytoplasm
    complex_perm_membrane = complex_perm(
        freq, fitting_sish_membrane_perm, fitting_sish_membrane_cond
    )
    complex_perm_cytoplasm = complex_perm(
        freq, fitting_sish_cytoplasm_perm, fitting_sish_cytoplasm_cond
    )

    # Calculate radius ratio
    radius_ratio = fitting_sish_particle_radius / (
        fitting_sish_particle_radius - 0.001 * fitting_sish_membrane_thickness
    )
    radius_ratio_cubed = radius_ratio**3

    # Calculate permittivity difference and sum
    perm_diff = complex_perm_cytoplasm - complex_perm_membrane
    perm_sum = complex_perm_cytoplasm + 2 * complex_perm_membrane

    # Calculate the numerator and denominator for the main fraction
    numerator = radius_ratio_cubed + 2 * (perm_diff / perm_sum)
    denominator = radius_ratio_cubed - (perm_diff / perm_sum)

    # Return the final result
    return complex_perm_membrane * (numerator / denominator)


# Claussius-Mossotti Factor calculation
def single_shell_CMfactor_complex(
    freq,
    fitting_sish_particle_radius,
    fitting_sish_membrane_thickness,
    fitting_sish_membrane_perm,
    fitting_sish_membrane_cond,
    fitting_sish_cytoplasm_perm,
    fitting_sish_cytoplasm_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    # Calculate SS_model and complex_perm
    ss_model_result = single_shell_equivalent_complex_permittivity(
        freq,
        fitting_sish_particle_radius,
        fitting_sish_membrane_thickness,
        fitting_sish_membrane_perm,
        fitting_sish_membrane_cond,
        fitting_sish_cytoplasm_perm,
        fitting_sish_cytoplasm_cond,
    )

    buffer_complex_perm = complex_perm(
        freq, fitting_gen_buffer_perm, fitting_gen_buffer_cond
    )

    # Calculate the numerator and denominator for the main fraction
    numerator = ss_model_result - buffer_complex_perm
    denominator = ss_model_result + 2 * buffer_complex_perm

    # Return the final result
    return (numerator / denominator).real


# Claussius-Mossotti Factor calculation - real part only
def single_shell_CMfactor_real(
    freq,
    fitting_sish_particle_radius,
    fitting_sish_membrane_thickness,
    fitting_sish_membrane_perm,
    fitting_sish_membrane_cond,
    fitting_sish_cytoplasm_perm,
    fitting_sish_cytoplasm_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    return single_shell_CMfactor_complex(
        freq,
        fitting_sish_particle_radius,
        fitting_sish_membrane_thickness,
        fitting_sish_membrane_perm,
        fitting_sish_membrane_cond,
        fitting_sish_cytoplasm_perm,
        fitting_sish_cytoplasm_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    ).real


# Claussius-Mossotti Factor calculation - imaginary part only
def single_shell_CMfactor_imag(
    freq,
    fitting_sish_particle_radius,
    fitting_sish_membrane_thickness,
    fitting_sish_membrane_perm,
    fitting_sish_membrane_cond,
    fitting_sish_cytoplasm_perm,
    fitting_sish_cytoplasm_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    return single_shell_CMfactor_complex(
        freq,
        fitting_sish_particle_radius,
        fitting_sish_membrane_thickness,
        fitting_sish_membrane_perm,
        fitting_sish_membrane_cond,
        fitting_sish_cytoplasm_perm,
        fitting_sish_cytoplasm_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    ).imag


# Single-shell DEP Force calculation
def single_shell_DEP_force(
    freq,
    fitting_gen_fieldgrad,
    fitting_sish_particle_radius,
    fitting_sish_membrane_thickness,
    fitting_sish_membrane_perm,
    fitting_sish_membrane_cond,
    fitting_sish_cytoplasm_perm,
    fitting_sish_cytoplasm_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    # Calculate the real part of the CM factor
    cm_factor_real = single_shell_CMfactor_real(
        freq,
        fitting_sish_particle_radius,
        fitting_sish_membrane_thickness,
        fitting_sish_membrane_perm,
        fitting_sish_membrane_cond,
        fitting_sish_cytoplasm_perm,
        fitting_sish_cytoplasm_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )

    # Calculate the buffer permittivity
    buffer_perm = fitting_gen_buffer_perm * 8.854 * 10 ** (-6)

    # Calculate the particle radius cubed
    particle_radius_cubed = fitting_sish_particle_radius**3

    # Calculate the final result
    result = (
        2.0
        * math.pi
        * buffer_perm
        * particle_radius_cubed
        * cm_factor_real
        * fitting_gen_fieldgrad
    )

    return result


def single_shell_all(
    freq,
    fitting_gen_fieldgrad,
    fitting_sish_particle_radius,
    fitting_sish_membrane_thickness,
    fitting_sish_membrane_perm,
    fitting_sish_membrane_cond,
    fitting_sish_cytoplasm_perm,
    fitting_sish_cytoplasm_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    cm_factor_real = single_shell_CMfactor_real(
        freq,
        fitting_sish_particle_radius,
        fitting_sish_membrane_thickness,
        fitting_sish_membrane_perm,
        fitting_sish_membrane_cond,
        fitting_sish_cytoplasm_perm,
        fitting_sish_cytoplasm_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )

    cm_factor_imag = single_shell_CMfactor_imag(
        freq,
        fitting_sish_particle_radius,
        fitting_sish_membrane_thickness,
        fitting_sish_membrane_perm,
        fitting_sish_membrane_cond,
        fitting_sish_cytoplasm_perm,
        fitting_sish_cytoplasm_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )

    dep_force = single_shell_DEP_force(
        freq,
        fitting_gen_fieldgrad,
        fitting_sish_particle_radius,
        fitting_sish_membrane_thickness,
        fitting_sish_membrane_perm,
        fitting_sish_membrane_cond,
        fitting_sish_cytoplasm_perm,
        fitting_sish_cytoplasm_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )
    return cm_factor_real, cm_factor_imag, dep_force


# Homogenous particle #
# Calculate Complex Claussius-Mossotti Factor
def homogenous_particle_CMfactor_complex(
    freq,
    fitting_hopa_particle_perm,
    fitting_hopa_particle_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    # Calculate complex permittivity for particle and buffer
    complex_perm_particle = complex_perm(
        freq, fitting_hopa_particle_perm, fitting_hopa_particle_cond
    )
    complex_perm_buffer = complex_perm(
        freq, fitting_gen_buffer_perm, fitting_gen_buffer_cond
    )

    # Calculate the numerator and denominator for the main fraction
    numerator = complex_perm_particle - complex_perm_buffer
    denominator = complex_perm_particle + 2 * complex_perm_buffer

    # Return the final result
    return numerator / denominator


# Claussius-Mossotti Factor calculation - real part only
def homogenous_particle_CMfactor_real(
    freq,
    fitting_hopa_particle_perm,
    fitting_hopa_particle_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    return homogenous_particle_CMfactor_complex(
        freq,
        fitting_hopa_particle_perm,
        fitting_hopa_particle_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    ).real


# Claussius-Mossotti Factor calculation - imaginary part only
def homogenous_particle_CMfactor_imag(
    freq,
    fitting_hopa_particle_perm,
    fitting_hopa_particle_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    return homogenous_particle_CMfactor_complex(
        freq,
        fitting_hopa_particle_perm,
        fitting_hopa_particle_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    ).imag


# Homogenous particle DEP Force calculation
def homogenous_particle_DEP_force(
    freq,
    fitting_gen_fieldgrad,
    fitting_hopa_particle_radius,
    fitting_hopa_particle_perm,
    fitting_hopa_particle_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    # Calculate the real part of the CM factor
    cm_factor_real = homogenous_particle_CMfactor_real(
        freq,
        fitting_hopa_particle_perm,
        fitting_hopa_particle_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )

    # Calculate the buffer permittivity
    buffer_perm = fitting_gen_buffer_perm * 8.854 * 10 ** (-6)

    # Calculate the particle radius cubed
    particle_radius_cubed = fitting_hopa_particle_radius**3

    # Calculate the final result
    result = (
        2.0
        * math.pi
        * buffer_perm
        * particle_radius_cubed
        * cm_factor_real
        * fitting_gen_fieldgrad
    )

    return result


def homogenous_particle_all(
    freq,
    fitting_gen_fieldgrad,
    fitting_hopa_particle_radius,
    fitting_hopa_particle_perm,
    fitting_hopa_particle_cond,
    fitting_gen_buffer_perm,
    fitting_gen_buffer_cond,
):
    cm_factor_real = homogenous_particle_CMfactor_real(
        freq,
        fitting_hopa_particle_perm,
        fitting_hopa_particle_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )

    cm_factor_imag = homogenous_particle_CMfactor_imag(
        freq,
        fitting_hopa_particle_perm,
        fitting_hopa_particle_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )

    dep_force = homogenous_particle_DEP_force(
        freq,
        fitting_gen_fieldgrad,
        fitting_hopa_particle_radius,
        fitting_hopa_particle_perm,
        fitting_hopa_particle_cond,
        fitting_gen_buffer_perm,
        fitting_gen_buffer_cond,
    )

    return cm_factor_real, cm_factor_imag, dep_force


# Two-shell model #
def complex_perm(freq, relperm, cond):
    # Ensure inputs are of a higher precision data type
    relperm = np.array(relperm, dtype=np.float64)
    cond = np.array(cond, dtype=np.float64)
    freq = np.array(freq, dtype=np.float64)

    # Perform calculation, explicitly using complex numbers
    result = (relperm * 8.854e-12) - 1j * cond / (freq * 2 * np.pi)

    # Ensure the result is of complex type to handle imaginary parts correctly
    return np.array(result, dtype=np.complex128)


# Two-Shell Models composed of a core, inner shell, and outer shell
# Calculate the equivalent complex permittivity for a two-shell model
def two_shell_equivalent_complex_permittivity(
    freq,
    core_radius,
    inner_shell_thickness,
    outer_shell_thickness,
    core_perm,
    core_cond,
    inner_shell_perm,
    inner_shell_cond,
    outer_shell_perm,
    outer_shell_cond,
):
    # Calculate complex permittivity for core, inner shell, and outer shell
    complex_perm_core = complex_perm(freq, core_perm, core_cond)
    complex_perm_inner_shell = complex_perm(freq, inner_shell_perm, inner_shell_cond)
    complex_perm_outer_shell = complex_perm(freq, outer_shell_perm, outer_shell_cond)

    # Calculate radius ratios
    inner_radius = core_radius + 0.001 * inner_shell_thickness
    outer_radius = inner_radius + 0.001 * outer_shell_thickness

    radius_ratio_inner = inner_radius / core_radius
    radius_ratio_outer = outer_radius / inner_radius

    # Calculate complex permittivity differences and sums
    perm_diff_inner = complex_perm_core - complex_perm_inner_shell
    perm_sum_inner = complex_perm_core + 2 * complex_perm_inner_shell

    perm_diff_outer = complex_perm_inner_shell - complex_perm_outer_shell
    perm_sum_outer = complex_perm_inner_shell + 2 * complex_perm_outer_shell

    # Calculate the numerator and denominator for the main fraction
    numerator_inner = radius_ratio_inner**3 + 2 * (perm_diff_inner / perm_sum_inner)
    denominator_inner = radius_ratio_inner**3 - (perm_diff_inner / perm_sum_inner)

    numerator_outer = radius_ratio_outer**3 + 2 * (perm_diff_outer / perm_sum_outer)
    denominator_outer = radius_ratio_outer**3 - (perm_diff_outer / perm_sum_outer)

    # Calculate equivalent permittivity for inner shell
    equiv_perm_inner = complex_perm_inner_shell * (numerator_inner / denominator_inner)

    # Calculate equivalent permittivity for outer shell
    numerator_combined = numerator_outer * equiv_perm_inner
    denominator_combined = denominator_outer * complex_perm_outer_shell

    return complex_perm_outer_shell * (numerator_combined / denominator_combined)


# Claussius-Mossotti Factor calculation for two-shell model
def two_shell_CMfactor_complex(
    freq,
    core_radius,
    inner_shell_thickness,
    outer_shell_thickness,
    core_perm,
    core_cond,
    inner_shell_perm,
    inner_shell_cond,
    outer_shell_perm,
    outer_shell_cond,
    buffer_perm,
    buffer_cond,
):
    # Calculate two-shell model and complex permittivity for buffer
    ts_model_result = two_shell_equivalent_complex_permittivity(
        freq,
        core_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
    )

    buffer_complex_perm = complex_perm(freq, buffer_perm, buffer_cond)

    # Calculate the numerator and denominator for the main fraction
    numerator = ts_model_result - buffer_complex_perm
    denominator = ts_model_result + 2 * buffer_complex_perm

    # Return the final result
    return (numerator / denominator).real


# Claussius-Mossotti Factor calculation - real part only for two-shell model
def two_shell_CMfactor_real(
    freq,
    core_radius,
    inner_shell_thickness,
    outer_shell_thickness,
    core_perm,
    core_cond,
    inner_shell_perm,
    inner_shell_cond,
    outer_shell_perm,
    outer_shell_cond,
    buffer_perm,
    buffer_cond,
):
    return two_shell_CMfactor_complex(
        freq,
        core_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
        buffer_perm,
        buffer_cond,
    ).real


# Claussius-Mossotti Factor calculation - imaginary part only for two-shell model
def two_shell_CMfactor_imag(
    freq,
    core_radius,
    inner_shell_thickness,
    outer_shell_thickness,
    core_perm,
    core_cond,
    inner_shell_perm,
    inner_shell_cond,
    outer_shell_perm,
    outer_shell_cond,
    buffer_perm,
    buffer_cond,
):
    return two_shell_CMfactor_complex(
        freq,
        core_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
        buffer_perm,
        buffer_cond,
    ).imag


# Two-shell DEP Force calculation
def two_shell_DEP_force(
    freq,
    field_grad,
    core_radius,
    inner_shell_thickness,
    outer_shell_thickness,
    core_perm,
    core_cond,
    inner_shell_perm,
    inner_shell_cond,
    outer_shell_perm,
    outer_shell_cond,
    buffer_perm,
    buffer_cond,
):
    # Calculate the real part of the CM factor
    cm_factor_real = two_shell_CMfactor_real(
        freq,
        core_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
        buffer_perm,
        buffer_cond,
    )

    # Calculate the buffer permittivity
    buffer_perm_value = buffer_perm * 8.854 * 10 ** (-6)

    # Calculate the particle radius cubed
    outer_radius = core_radius + 0.001 * (inner_shell_thickness + outer_shell_thickness)
    particle_radius_cubed = outer_radius**3

    # Calculate the final result
    result = (
        2.0
        * math.pi
        * buffer_perm_value
        * particle_radius_cubed
        * cm_factor_real
        * field_grad
    )

    return result


def two_shell_all(
    freq,
    field_grad,
    core_radius,
    inner_shell_thickness,
    outer_shell_thickness,
    core_perm,
    core_cond,
    inner_shell_perm,
    inner_shell_cond,
    outer_shell_perm,
    outer_shell_cond,
    buffer_perm,
    buffer_cond,
):
    cm_factor_real = two_shell_CMfactor_real(
        freq,
        core_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
        buffer_perm,
        buffer_cond,
    )

    cm_factor_imag = two_shell_CMfactor_imag(
        freq,
        core_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
        buffer_perm,
        buffer_cond,
    )

    dep_force = two_shell_DEP_force(
        freq,
        field_grad,
        core_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
        buffer_perm,
        buffer_cond,
    )

    return cm_factor_real, cm_factor_imag, dep_force
