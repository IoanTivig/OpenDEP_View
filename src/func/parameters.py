'''
The parameters of the curve models, as OpenDEP View names them: which ones each model uses (see models.model_all)
and how they are shown, grouped as in the curve widget

Layers: core = cytoplasm (homogeneous: the particle), 1st shell = membrane, 2nd shell = cell wall, plus the nucleus
(nuclear envelope and nucleoplasm) of the three- and four-shell models.
'''

MODEL_NAMES = ["Homogeneous", "Single-shell", "Two-shell", "Three-shell", "Four-shell"]

_COMMON = ["buffer_perm", "buffer_cond", "core_perm", "core_cond", "core_radius", "electric_field"]
_MEMBRANE = ["1st_shell_perm", "1st_shell_cond", "1st_shell_thick"]
_WALL = ["2nd_shell_perm", "2nd_shell_cond", "2nd_shell_thick"]
_NUCLEUS = ["nucleus_radius", "envelope_thick", "envelope_perm", "envelope_cond", "nucleoplasm_perm",
            "nucleoplasm_cond"]

# Parameters each model uses (model index as in the curves)
MODEL_PARAMETERS = {0: _COMMON + ["core_surface_cond"],
                    1: _COMMON + _MEMBRANE,
                    2: _COMMON + _MEMBRANE + _WALL,
                    3: _COMMON + _MEMBRANE + _NUCLEUS,
                    4: _COMMON + _MEMBRANE + _WALL + _NUCLEUS}

# key -> (group, label, unit), grouped and ordered as in the curve widget (Curve plots); the group of the core is
# "Particle" in the homogeneous model, "Cytoplasm" otherwise
PARAMETER_INFO = {
    "buffer_perm": ("Buffer", "Permittivity", "ε₀"),
    "buffer_cond": ("Buffer", "Conductivity", "S/m"),
    "core_perm": ("Cytoplasm", "Permittivity", "ε₀"),
    "core_cond": ("Cytoplasm", "Conductivity", "S/m"),
    "core_surface_cond": ("Cytoplasm", "Surface cond.", "nS"),
    "core_radius": ("Other", "Particle Radius", "µm"),
    "nucleus_radius": ("Other", "Nucleus radius", "µm"),
    "electric_field": ("Other", "∇E²", "V²/m³"),
    "1st_shell_thick": ("Shell dimensions", "Membrane thickness", "nm"),
    "2nd_shell_thick": ("Shell dimensions", "Wall thickness", "nm"),
    "envelope_thick": ("Shell dimensions", "Envelope thickness", "nm"),
    "1st_shell_perm": ("Membrane", "Permittivity", "ε₀"),
    "1st_shell_cond": ("Membrane", "Conductivity", "S/m"),
    "2nd_shell_perm": ("Cell wall", "Permittivity", "ε₀"),
    "2nd_shell_cond": ("Cell wall", "Conductivity", "S/m"),
    "envelope_perm": ("Nuclear envelope", "Permittivity", "ε₀"),
    "envelope_cond": ("Nuclear envelope", "Conductivity", "S/m"),
    "nucleoplasm_perm": ("Nucleoplasm", "Permittivity", "ε₀"),
    "nucleoplasm_cond": ("Nucleoplasm", "Conductivity", "S/m"),
}

GROUP_ORDER = ["Buffer", "Cytoplasm", "Other", "Shell dimensions", "Membrane", "Cell wall", "Nuclear envelope",
               "Nucleoplasm"]

# Icon of each model (as in the curve widget's model list)
MODEL_ICONS = [":/ui/qt/resources/buttons/homogenous_icon.png", ":/ui/qt/resources/buttons/singleshell_icon.png",
               ":/ui/qt/resources/buttons/twoshell_icon.png", ":/ui/qt/resources/buttons/threeshell_icon.png",
               ":/ui/qt/resources/buttons/fourshell_icon.png"]


# Group title of a parameter in a model (the core is the particle in the homogeneous model)
def group_title(key, model):
    group = PARAMETER_INFO[key][0]
    return "Particle" if group == "Cytoplasm" and model == 0 else group


# The model's parameters in display order: [(group title, [keys])]
def grouped_parameters(model):
    keys = MODEL_PARAMETERS[model]
    groups = []
    for group in GROUP_ORDER:
        members = [key for key in keys if PARAMETER_INFO[key][0] == group]
        if members:
            groups.append((group_title(members[0], model), members))
    return groups
