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
    return numerator / denominator


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
    fitting_hopa_particle_surface_cond=0.0,
):
    # Surface conductance K_s (nS) adds 2 K_s / r to the bulk conductivity (latex beads), radius in um
    fitting_hopa_particle_cond = fitting_hopa_particle_cond + 2 * fitting_hopa_particle_surface_cond * 1e-9 / (
        fitting_hopa_particle_radius * 1e-6)

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


# Shell functions #
# Equivalent complex permittivity of a sphere (inner_radius) covered by one shell (up to outer_radius)
# Same formula as the single-shell model, used for every layer of the multi-shell models
def shell_equivalent_complex_permittivity(
    complex_perm_inner,
    complex_perm_shell,
    inner_radius,
    outer_radius,
):
    # Calculate radius ratio
    radius_ratio_cubed = (outer_radius / inner_radius) ** 3

    # Calculate permittivity contrast between the inner sphere and the shell
    perm_contrast = (complex_perm_inner - complex_perm_shell) / (complex_perm_inner + 2 * complex_perm_shell)

    # Return the equivalent permittivity of sphere + shell
    return complex_perm_shell * (radius_ratio_cubed + 2 * perm_contrast) / (radius_ratio_cubed - perm_contrast)


# Claussius-Mossotti Factor of a particle with a known equivalent complex permittivity
def particle_CMfactor_complex(freq, particle_complex_perm, buffer_perm, buffer_cond):
    buffer_complex_perm = complex_perm(freq, buffer_perm, buffer_cond)
    return (particle_complex_perm - buffer_complex_perm) / (particle_complex_perm + 2 * buffer_complex_perm)


# DEP Force from the real part of the CM factor (same units as the other models: radius in um, force in pN)
def particle_DEP_force(cm_factor_real, field_grad, particle_radius, buffer_perm):
    return 2.0 * math.pi * buffer_perm * 8.854 * 10 ** (-6) * particle_radius**3 * cm_factor_real * field_grad


# Two-shell model #
# Two-Shell Models composed of a core (cytoplasm), an inner shell (membrane) and an outer shell (cell wall)
# The particle radius is the outer radius of the whole particle (outer shell included), as for the single-shell
# model, OpenDEP Compute and MyDEP; the core radius is particle radius - both shell thicknesses
# Calculate the equivalent complex permittivity for a two-shell model
def two_shell_equivalent_complex_permittivity(
    freq,
    particle_radius,
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

    # Calculate radii (um), thicknesses are in nm
    inner_shell_radius = particle_radius - 0.001 * outer_shell_thickness
    core_radius = inner_shell_radius - 0.001 * inner_shell_thickness

    # Core + inner shell, then the outer shell around the result
    equiv_perm_inner = shell_equivalent_complex_permittivity(
        complex_perm_core, complex_perm_inner_shell, core_radius, inner_shell_radius)

    return shell_equivalent_complex_permittivity(
        equiv_perm_inner, complex_perm_outer_shell, inner_shell_radius, particle_radius)


# Claussius-Mossotti Factor calculation for two-shell model
def two_shell_CMfactor_complex(
    freq,
    particle_radius,
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
        particle_radius,
        inner_shell_thickness,
        outer_shell_thickness,
        core_perm,
        core_cond,
        inner_shell_perm,
        inner_shell_cond,
        outer_shell_perm,
        outer_shell_cond,
    )

    return particle_CMfactor_complex(freq, ts_model_result, buffer_perm, buffer_cond)


# Claussius-Mossotti Factor calculation - real part only for two-shell model
def two_shell_CMfactor_real(
    freq,
    particle_radius,
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
        particle_radius,
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
    particle_radius,
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
        particle_radius,
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
    particle_radius,
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
        particle_radius,
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

    return particle_DEP_force(cm_factor_real, field_grad, particle_radius, buffer_perm)


def two_shell_all(
    freq,
    field_grad,
    particle_radius,
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
    cm_factor = two_shell_CMfactor_complex(
        freq,
        particle_radius,
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

    dep_force = particle_DEP_force(cm_factor.real, field_grad, particle_radius, buffer_perm)

    return cm_factor.real, cm_factor.imag, dep_force


# Three-shell model #
# Three-Shell Models: nucleus (nucleoplasm + nuclear envelope), cytoplasm and membrane (as in OpenDEP Compute / MyDEP)
# The particle radius is the outer radius of the cell, the nucleus radius includes the nuclear envelope
# Calculate the equivalent complex permittivity for a three-shell model
def three_shell_equivalent_complex_permittivity(
    freq,
    particle_radius,
    membrane_thickness,
    membrane_perm,
    membrane_cond,
    cytoplasm_perm,
    cytoplasm_cond,
    nucleus_radius,
    envelope_thickness,
    envelope_perm,
    envelope_cond,
    nucleoplasm_perm,
    nucleoplasm_cond,
):
    # Calculate complex permittivity for every layer
    complex_perm_nucleoplasm = complex_perm(freq, nucleoplasm_perm, nucleoplasm_cond)
    complex_perm_envelope = complex_perm(freq, envelope_perm, envelope_cond)
    complex_perm_cytoplasm = complex_perm(freq, cytoplasm_perm, cytoplasm_cond)
    complex_perm_membrane = complex_perm(freq, membrane_perm, membrane_cond)

    # Calculate radii (um), thicknesses are in nm
    nucleoplasm_radius = nucleus_radius - 0.001 * envelope_thickness
    cytoplasm_radius = particle_radius - 0.001 * membrane_thickness

    # 1. Nucleus: nucleoplasm + envelope
    equiv_perm = shell_equivalent_complex_permittivity(
        complex_perm_nucleoplasm, complex_perm_envelope, nucleoplasm_radius, nucleus_radius)

    # 2. Cytoplasm around the nucleus
    equiv_perm = shell_equivalent_complex_permittivity(
        equiv_perm, complex_perm_cytoplasm, nucleus_radius, cytoplasm_radius)

    # 3. Membrane around the cytoplasm
    return shell_equivalent_complex_permittivity(
        equiv_perm, complex_perm_membrane, cytoplasm_radius, particle_radius)


# Claussius-Mossotti Factor calculation for three-shell model
def three_shell_CMfactor_complex(
    freq,
    particle_radius,
    membrane_thickness,
    membrane_perm,
    membrane_cond,
    cytoplasm_perm,
    cytoplasm_cond,
    nucleus_radius,
    envelope_thickness,
    envelope_perm,
    envelope_cond,
    nucleoplasm_perm,
    nucleoplasm_cond,
    buffer_perm,
    buffer_cond,
):
    ths_model_result = three_shell_equivalent_complex_permittivity(
        freq,
        particle_radius,
        membrane_thickness,
        membrane_perm,
        membrane_cond,
        cytoplasm_perm,
        cytoplasm_cond,
        nucleus_radius,
        envelope_thickness,
        envelope_perm,
        envelope_cond,
        nucleoplasm_perm,
        nucleoplasm_cond,
    )

    return particle_CMfactor_complex(freq, ths_model_result, buffer_perm, buffer_cond)


def three_shell_all(
    freq,
    field_grad,
    particle_radius,
    membrane_thickness,
    membrane_perm,
    membrane_cond,
    cytoplasm_perm,
    cytoplasm_cond,
    nucleus_radius,
    envelope_thickness,
    envelope_perm,
    envelope_cond,
    nucleoplasm_perm,
    nucleoplasm_cond,
    buffer_perm,
    buffer_cond,
):
    cm_factor = three_shell_CMfactor_complex(
        freq,
        particle_radius,
        membrane_thickness,
        membrane_perm,
        membrane_cond,
        cytoplasm_perm,
        cytoplasm_cond,
        nucleus_radius,
        envelope_thickness,
        envelope_perm,
        envelope_cond,
        nucleoplasm_perm,
        nucleoplasm_cond,
        buffer_perm,
        buffer_cond,
    )

    dep_force = particle_DEP_force(cm_factor.real, field_grad, particle_radius, buffer_perm)

    return cm_factor.real, cm_factor.imag, dep_force


# Four-shell model #
# Four-Shell Models: the three-shell cell (nucleus, cytoplasm, membrane) inside a cell wall
# The particle radius is the outer radius of the whole particle (cell wall included)
# Calculate the equivalent complex permittivity for a four-shell model
def four_shell_equivalent_complex_permittivity(
    freq,
    particle_radius,
    wall_thickness,
    wall_perm,
    wall_cond,
    membrane_thickness,
    membrane_perm,
    membrane_cond,
    cytoplasm_perm,
    cytoplasm_cond,
    nucleus_radius,
    envelope_thickness,
    envelope_perm,
    envelope_cond,
    nucleoplasm_perm,
    nucleoplasm_cond,
):
    # Calculate radii (um), thicknesses are in nm
    membrane_radius = particle_radius - 0.001 * wall_thickness

    # 1. The three-shell cell inside the wall (its outer radius is the outer radius of the membrane)
    equiv_perm = three_shell_equivalent_complex_permittivity(
        freq,
        membrane_radius,
        membrane_thickness,
        membrane_perm,
        membrane_cond,
        cytoplasm_perm,
        cytoplasm_cond,
        nucleus_radius,
        envelope_thickness,
        envelope_perm,
        envelope_cond,
        nucleoplasm_perm,
        nucleoplasm_cond,
    )

    # 2. Cell wall around the cell
    return shell_equivalent_complex_permittivity(
        equiv_perm, complex_perm(freq, wall_perm, wall_cond), membrane_radius, particle_radius)


# Claussius-Mossotti Factor calculation for four-shell model
def four_shell_CMfactor_complex(
    freq,
    particle_radius,
    wall_thickness,
    wall_perm,
    wall_cond,
    membrane_thickness,
    membrane_perm,
    membrane_cond,
    cytoplasm_perm,
    cytoplasm_cond,
    nucleus_radius,
    envelope_thickness,
    envelope_perm,
    envelope_cond,
    nucleoplasm_perm,
    nucleoplasm_cond,
    buffer_perm,
    buffer_cond,
):
    fs_model_result = four_shell_equivalent_complex_permittivity(
        freq,
        particle_radius,
        wall_thickness,
        wall_perm,
        wall_cond,
        membrane_thickness,
        membrane_perm,
        membrane_cond,
        cytoplasm_perm,
        cytoplasm_cond,
        nucleus_radius,
        envelope_thickness,
        envelope_perm,
        envelope_cond,
        nucleoplasm_perm,
        nucleoplasm_cond,
    )

    return particle_CMfactor_complex(freq, fs_model_result, buffer_perm, buffer_cond)


def four_shell_all(
    freq,
    field_grad,
    particle_radius,
    wall_thickness,
    wall_perm,
    wall_cond,
    membrane_thickness,
    membrane_perm,
    membrane_cond,
    cytoplasm_perm,
    cytoplasm_cond,
    nucleus_radius,
    envelope_thickness,
    envelope_perm,
    envelope_cond,
    nucleoplasm_perm,
    nucleoplasm_cond,
    buffer_perm,
    buffer_cond,
):
    cm_factor = four_shell_CMfactor_complex(
        freq,
        particle_radius,
        wall_thickness,
        wall_perm,
        wall_cond,
        membrane_thickness,
        membrane_perm,
        membrane_cond,
        cytoplasm_perm,
        cytoplasm_cond,
        nucleus_radius,
        envelope_thickness,
        envelope_perm,
        envelope_cond,
        nucleoplasm_perm,
        nucleoplasm_cond,
        buffer_perm,
        buffer_cond,
    )

    dep_force = particle_DEP_force(cm_factor.real, field_grad, particle_radius, buffer_perm)

    return cm_factor.real, cm_factor.imag, dep_force


# All models #
# Model index as stored in the curves ("model") and in the OpenDEP Curve files (.odcurve), and its key in the curve data / cross-overs
MODEL_KEYS = ["homogenous", "single_shell", "two_shell", "three_shell", "four_shell"]


# Crossover frequencies of a model: the first rising (Re[CM] from negative to positive) and the first falling one,
# None when there is none. Bracketed on the sampled curve, then refined on the model in log frequency, so the result
# does not depend on how densely the curve is sampled. Each round evaluates the model once on a grid of `points`
# across the bracket and keeps the sub-interval where the sign changes: 4 rounds of 200 narrow the bracket
# 200^4 = 1.6e9 times (finer than 30 bisection steps) in 4 model calls instead of one call per step.
def crossover_frequencies(model, parameters, frequencies, recm, rounds=4, points=200):
    crossovers = {"rising": None, "falling": None}
    for i in range(len(recm) - 1):
        a, b = recm[i], recm[i + 1]
        kind = "rising" if a < 0 <= b else "falling" if a > 0 >= b else None
        if kind is None or crossovers[kind] is not None:
            continue
        low, high = np.log10(float(frequencies[i])), np.log10(float(frequencies[i + 1]))
        negative_low = a < 0
        for _ in range(rounds):
            grid = np.linspace(low, high, points + 1)
            values = np.asarray(model_all(model, 10.0 ** grid, parameters)[0])
            changed = np.flatnonzero((values[1:] < 0) != negative_low)   # first point past the sign change
            j = int(changed[0]) if changed.size else points - 1
            low, high = grid[j], grid[j + 1]
        crossovers[kind] = float(10.0 ** ((low + high) / 2))
    return crossovers["rising"], crossovers["falling"]


# Re[CM], Im[CM] and DEP force of one model from the parameters of a curve (OpenDEP View parameter names)
# Layers: core = cytoplasm (homogenous: the particle), 1st shell = membrane, 2nd shell = cell wall, plus the nucleus
def model_all(model, freq, parameters):
    if model == 0:
        return homogenous_particle_all(
            freq=freq,
            fitting_gen_fieldgrad=parameters["electric_field"],
            fitting_hopa_particle_radius=parameters["core_radius"],
            fitting_hopa_particle_perm=parameters["core_perm"],
            fitting_hopa_particle_cond=parameters["core_cond"],
            fitting_gen_buffer_perm=parameters["buffer_perm"],
            fitting_gen_buffer_cond=parameters["buffer_cond"],
            fitting_hopa_particle_surface_cond=parameters["core_surface_cond"])

    elif model == 1:
        return single_shell_all(
            freq=freq,
            fitting_gen_fieldgrad=parameters["electric_field"],
            fitting_sish_particle_radius=parameters["core_radius"],
            fitting_sish_membrane_thickness=parameters["1st_shell_thick"],
            fitting_sish_membrane_perm=parameters["1st_shell_perm"],
            fitting_sish_membrane_cond=parameters["1st_shell_cond"],
            fitting_sish_cytoplasm_perm=parameters["core_perm"],
            fitting_sish_cytoplasm_cond=parameters["core_cond"],
            fitting_gen_buffer_perm=parameters["buffer_perm"],
            fitting_gen_buffer_cond=parameters["buffer_cond"])

    elif model == 2:
        return two_shell_all(
            freq=freq,
            field_grad=parameters["electric_field"],
            particle_radius=parameters["core_radius"],
            inner_shell_thickness=parameters["1st_shell_thick"],
            outer_shell_thickness=parameters["2nd_shell_thick"],
            core_perm=parameters["core_perm"],
            core_cond=parameters["core_cond"],
            inner_shell_perm=parameters["1st_shell_perm"],
            inner_shell_cond=parameters["1st_shell_cond"],
            outer_shell_perm=parameters["2nd_shell_perm"],
            outer_shell_cond=parameters["2nd_shell_cond"],
            buffer_perm=parameters["buffer_perm"],
            buffer_cond=parameters["buffer_cond"])

    elif model == 3:
        return three_shell_all(
            freq=freq,
            field_grad=parameters["electric_field"],
            particle_radius=parameters["core_radius"],
            membrane_thickness=parameters["1st_shell_thick"],
            membrane_perm=parameters["1st_shell_perm"],
            membrane_cond=parameters["1st_shell_cond"],
            cytoplasm_perm=parameters["core_perm"],
            cytoplasm_cond=parameters["core_cond"],
            nucleus_radius=parameters["nucleus_radius"],
            envelope_thickness=parameters["envelope_thick"],
            envelope_perm=parameters["envelope_perm"],
            envelope_cond=parameters["envelope_cond"],
            nucleoplasm_perm=parameters["nucleoplasm_perm"],
            nucleoplasm_cond=parameters["nucleoplasm_cond"],
            buffer_perm=parameters["buffer_perm"],
            buffer_cond=parameters["buffer_cond"])

    elif model == 4:
        return four_shell_all(
            freq=freq,
            field_grad=parameters["electric_field"],
            particle_radius=parameters["core_radius"],
            wall_thickness=parameters["2nd_shell_thick"],
            wall_perm=parameters["2nd_shell_perm"],
            wall_cond=parameters["2nd_shell_cond"],
            membrane_thickness=parameters["1st_shell_thick"],
            membrane_perm=parameters["1st_shell_perm"],
            membrane_cond=parameters["1st_shell_cond"],
            cytoplasm_perm=parameters["core_perm"],
            cytoplasm_cond=parameters["core_cond"],
            nucleus_radius=parameters["nucleus_radius"],
            envelope_thickness=parameters["envelope_thick"],
            envelope_perm=parameters["envelope_perm"],
            envelope_cond=parameters["envelope_cond"],
            nucleoplasm_perm=parameters["nucleoplasm_perm"],
            nucleoplasm_cond=parameters["nucleoplasm_cond"],
            buffer_perm=parameters["buffer_perm"],
            buffer_cond=parameters["buffer_cond"])
