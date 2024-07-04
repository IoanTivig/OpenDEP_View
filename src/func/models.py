import math


def complex_perm(freq, relperm, cond):
    return (relperm * 8.854 * 10 ** (-12)) - 1j * cond / (freq * 2 * math.pi)


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


# Homogenous particle
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
