import json
from datetime import datetime
from pathlib import Path

'''
OpenDEP spectrum, curve and fit files, shared by OpenDEP Control, View and Compute (JSON)

    .odspec     OpenDEP Spectrum: a measured spectrum (View's "scatter"); "OpenDEP Scatter" .ods before 2026-10
    .odcurve    OpenDEP Curve: a model curve; .odc before 2026-10
    .odfit      OpenDEP Fit: spectra, a curve, and their links (scale factor per spectrum, sample, biological
                replicate); with the fit results ("fit") when OpenDEP Compute fitted the curve, and the average
                ("group") when View saved a replicate group. View converts the spectra to CM factor (÷ scale)
                when it opens the file, and writes them as CM factor (scale 1)

The older .ods / .odc names belong to other programs on Windows (LibreOffice / Excel spreadsheet, Excel data
connection), so they were renamed in every OpenDEP program; their content is the same and they still open.
Files are recognised by their content, so a renamed file opens too.
'''

SPECTRUM_SUFFIX = ".odspec"
CURVE_SUFFIX = ".odcurve"
FIT_SUFFIX = ".odfit"
LEGACY_SPECTRUM_SUFFIX = ".ods"
LEGACY_CURVE_SUFFIX = ".odc"
# Files View opens when they come from outside (command line, OpenDEP Compute's Send to View, drag and drop)
OPEN_SUFFIXES = (SPECTRUM_SUFFIX, CURVE_SUFFIX, FIT_SUFFIX, LEGACY_SPECTRUM_SUFFIX, LEGACY_CURVE_SUFFIX)

SPECTRUM_FORMAT = "OpenDEP Spectrum"
SPECTRUM_FORMATS = (SPECTRUM_FORMAT, "OpenDEP Scatter")       # current name, name in .ods files
CURVE_FORMAT = "OpenDEP Curve"
CURVE_VERSION = 2                                              # 2: outer radius for every model (View 2)
FIT_FORMAT = "OpenDEP Fit"
FIT_VERSION = 1

# File dialog filters (fit files open from both the scatter and the curve buttons)
FIT_FILTER = f"OpenDEP Fit (*{FIT_SUFFIX})"
SPECTRUM_OPEN_FILTER = (f"OpenDEP Spectrum (*{SPECTRUM_SUFFIX} *{LEGACY_SPECTRUM_SUFFIX});;{FIT_FILTER};;"
                        f"All OpenDEP files (*{SPECTRUM_SUFFIX} *{FIT_SUFFIX} *{LEGACY_SPECTRUM_SUFFIX})")
CURVE_OPEN_FILTER = (f"OpenDEP Curve (*{CURVE_SUFFIX} *{LEGACY_CURVE_SUFFIX});;{FIT_FILTER};;"
                     f"All OpenDEP files (*{CURVE_SUFFIX} *{FIT_SUFFIX} *{LEGACY_CURVE_SUFFIX})")
SPECTRUM_SAVE_FILTER = f"OpenDEP Spectrum (*{SPECTRUM_SUFFIX})"
CURVE_SAVE_FILTER = f"OpenDEP Curve (*{CURVE_SUFFIX});;OpenDEP Fit, the curve with its linked scatters (*{FIT_SUFFIX})"


class OpenDEPFileError(Exception):
    pass


# Content of an OpenDEP spectrum, curve or fit file, and which it is ("spectrum", "curve" or "fit")
def read_opendep_file(path):
    path = Path(path)
    # A real OpenDocument spreadsheet (.ods) is a zip archive
    with open(path, "rb") as file:
        if file.read(2) == b"PK":
            raise OpenDEPFileError(f"{path.name} is a LibreOffice / OpenDocument spreadsheet, not an OpenDEP "
                                   f"file. Save it as .xlsx and load it as an Excel scatter.")
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (UnicodeDecodeError, ValueError):
        raise OpenDEPFileError(f"{path.name} is not an OpenDEP spectrum or curve file.") from None

    if isinstance(data, dict) and (data.get("format") == FIT_FORMAT or {"spectra", "curve", "links"} <= set(data)):
        check_fit_document(path.name, data)
        return "fit", data
    if isinstance(data, dict) and "scatter" in data:
        return "spectrum", data
    if isinstance(data, dict) and "parameters" in data and "model" in data:
        return "curve", data
    raise OpenDEPFileError(f"{path.name} holds neither a spectrum nor a curve.")


# Keys View uses itself; everything else in a spectrum file is kept as read
VIEW_SCATTER_KEYS = ("name", "color", "point_size", "point_style", "visibility", "scatter", "widget",
                     "scale_factor", "scale_error")


# Keys of a spectrum file View does not use (format, quantity, raw values, normalisation, per-point data, known
# parameters, source, ... from OpenDEP Control and Compute)
def extra_spectrum_keys(data):
    return {key: value for key, value in data.items() if key not in VIEW_SCATTER_KEYS}


# After the points were edited in View, the per-point data of the file follows: a removed row is removed from
# every per-point list, an added row gets an empty entry (None); lists that still do not match the points are
# dropped (never left wrong). The file then says the values were edited.
# removed_row: index of a removed point; added: a point was added at the end
def after_points_edited(scatter, removed_row=None, added=False):
    n = len(scatter["scatter"]["frequencies"])

    def follow(values):
        values = list(values)
        if removed_row is not None and len(values) == n + 1:
            del values[removed_row]
        elif added and len(values) == n - 1:
            values.append(None)
        return values if len(values) == n else None

    points = scatter.get("points")
    if isinstance(points, dict):
        followed = {key: follow(values) if isinstance(values, list) else values for key, values in points.items()}
        scatter["points"] = {key: values for key, values in followed.items() if values is not None}
    raw = scatter.get("raw")
    if isinstance(raw, dict):
        for key in ("values", "errors"):
            if isinstance(raw.get(key), list):
                raw[key] = follow(raw[key])
                if raw[key] is None:
                    del raw[key]
    if "format" in scatter or "source" in scatter:
        scatter["edited_in_view"] = True


# File content of a scatter: View's keys, the format name, and the keys View does not use (kept as read)
def spectrum_file_data(scatter):
    data = {key: value for key, value in scatter.items() if key not in ("widget", "scale_factor", "scale_error")}
    data["format"] = SPECTRUM_FORMAT
    data.setdefault("format_version", 1)
    data["widget"] = None
    return data


# A fit file whose links point to spectra it does not have cannot be opened (the curve is optional: a replicate
# group saved without a curve)
def check_fit_document(name, data):
    n = len(data.get("spectra", []))
    curve = data.get("curve")
    if (curve is not None and not isinstance(curve, dict)) or n == 0 or any(
            not 0 <= int(link.get("spectrum", -1)) < n for link in data.get("links", [])):
        raise OpenDEPFileError(f"{name}: the fit file is incomplete (no spectra, or a linked spectrum is missing).")


# File content of a curve: the outer radius for every model (format version 2). OpenDEP Compute's own block
# ("opendep_compute", in curves Compute wrote) is left out: Compute reads it before View's fields, so a curve
# changed in View would otherwise open in Compute with its old values. The link is not part of a curve file
# (the project and the fit files keep it).
def curve_file_data(curve):
    data = {key: value for key, value in curve.items() if key not in ("widget", "opendep_compute", "link")}
    data.update({"format": CURVE_FORMAT, "format_version": CURVE_VERSION, "radius_convention": "outer",
                 "widget": None})
    return data


# A spectrum (or scatter) of a fit put on the CM-factor scale: values and errors ÷ the fitted scale factor. The
# values as measured and the factor stay in the data ("raw", "normalisation"), as in OpenDEP Compute's exports.
# Returns the changed keys: {"scatter", "raw", "normalisation"}
def scaled_to_cm_factor(spectrum, scale, scale_error=None):
    scale = float(scale) if scale else 1.0
    data = spectrum["scatter"]
    raw = dict(spectrum.get("raw") or {})
    raw.setdefault("values", [float(v) for v in data["recm_values"]])
    raw.setdefault("errors", [float(e) for e in data["recm_errors"]])
    return {"scatter": {"frequencies": list(data["frequencies"]),
                        "recm_values": [float(v) / scale for v in data["recm_values"]],
                        "recm_errors": [float(e) / scale for e in data["recm_errors"]]},
            "raw": raw,
            "normalisation": {"method": "fit_scale_factor", "factor": scale, "factor_error": scale_error,
                              "description": "value / factor: the scale factor of the fit in OpenDEP Compute"}}


# OpenDEP Fit document: the spectra (CM factor, so scale 1 in the links; biological replicate when in a group),
# the curve (optional), and for a replicate group its average. The fit results go along only while the curve is
# still the fitted one (not edited in View).
# scatters: the scatters' data; biological: their biological replicate labels (a group), or None
# group: {"name", "color", "point_style", "line_style", "average": replicates.average_group(...)} or None
def fit_file_data(name, scatters, curve=None, biological=None, group=None):
    links = []
    for i, scatter in enumerate(scatters):
        link = {"spectrum": i, "scale": 1.0, "scale_error": None, "sample": group["name"] if group else ""}
        if biological is not None:
            link["biological"] = str(biological[i])
        links.append(link)
    spectra = [spectrum_file_data(scatter) for scatter in scatters]

    data = {"format": FIT_FORMAT, "format_version": FIT_VERSION, "name": name,
            "created": datetime.now().isoformat(timespec="seconds"), "program": "OpenDEP View",
            "spectra": spectra, "links": links}
    if curve is not None:
        curve_data = curve_file_data(curve)
        fit = curve_data.pop("fit", None)
        status = curve_data.pop("fit_status", None)
        data["curve"] = curve_data
        if fit and status == "fitted":
            data["fit"] = fit
    if group is not None:
        data["group"] = group
    return data


# OpenDEP Spectrum document of a group's average: mean ± error, with n and the kind of error per point
def average_file_data(group_name, color, average):
    return {"format": SPECTRUM_FORMAT, "format_version": 2, "name": f"{group_name} (mean)", "color": color,
            "point_size": 50.0, "point_style": "o", "visibility": True,
            "scatter": {"frequencies": average["frequencies"], "recm_values": average["values"],
                        "recm_errors": average["errors"]},
            "quantity": "group_mean", "label": f"Mean ({average['summary']['error']})",
            "points": {"n_biological": average["n_biological"], "n_technical": average["n_technical"],
                       "error_kind": average["kind"]},
            "source": {"software": "OpenDEP View", "group": group_name, "error": average["summary"]["error"],
                       "biological_replicates": average["summary"]["n_biological"]},
            "created": datetime.now().isoformat(timespec="seconds"), "widget": None}


# Path with the first extension added when the user typed none of the allowed ones (an older extension typed on
# purpose, e.g. .odc for a colleague with View 1.x, is kept)
def with_suffix(file_path, suffixes):
    path = Path(file_path)
    return str(path if path.suffix.lower() in suffixes else path.with_name(path.name + suffixes[0]))
