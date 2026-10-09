'''
What a curve is linked to (as in OpenDEP Fit files, .odfit)

A curve is linked to one scatter at most (e.g. the data it was fitted to), and a scatter to one curve at most:
    curve["link"] = None | {"scatter": scatter id}
A replicate group (src/func/replicates.py) averages the curves linked to its scatters. (Projects of 2026-10-08
could link a curve to a group; such links are not read any more.)

Scatters in View hold CM-factor values: putting a relative spectrum on the model's scale is part of the fit in
OpenDEP Compute, and a fit file (.odfit) is converted when it is opened (opendep_files.scaled_to_cm_factor).
A fitted curve also keeps the fit from OpenDEP Compute: curve["fit"] (settings and results) and
curve["fit_status"] ("fitted", or "edited" once its values were changed in View).
'''

from src.func.opendep_files import scaled_to_cm_factor

LINK_KINDS = ("scatter",)


# Kind and id of what a curve is linked to, or (None, None)
def link_target(curve):
    link = curve.get("link") or {}
    for kind in LINK_KINDS:
        if kind in link:
            return kind, link[kind]
    return None, None


# The curve linked to a scatter or a group, or None
def linked_curve(curves, kind, target_id):
    for curve_id, curve in curves.items():
        if link_target(curve) == (kind, target_id):
            return curve_id
    return None


# Link a curve to a scatter or a group (None: unlink); the target leaves the curve it was linked to before
def set_link(curves, curve_id, kind=None, target_id=None):
    if kind is not None:
        remove_target(curves, kind, target_id)
    curves[curve_id]["link"] = {kind: target_id} if kind is not None else None


# A scatter or a group was deleted (or linked elsewhere): no curve is linked to it any more
def remove_target(curves, kind, target_id):
    for curve in curves.values():
        if link_target(curve) == (kind, target_id):
            curve["link"] = None


# Links by position, for project.json: [{"curve": index, "scatter": index}]
def links_to_indices(curves, curve_order, scatter_order, group_order=()):
    index = {"scatter": {sid: i for i, sid in enumerate(scatter_order)}}
    links = []
    for curve_index, curve_id in enumerate(curve_order):
        kind, target_id = link_target(curves[curve_id])
        if kind is not None and target_id in index[kind]:
            links.append({"curve": curve_index, kind: index[kind][target_id]})
    return links


# Links read from a project, back onto the curves (ids in the order they were created). A project saved with a
# scale factor in the link (2026-10-08, before scaling was left to Compute): the scatter is converted to CM factor.
def links_from_indices(curves, scatters, links, curve_order, scatter_order, group_order=()):
    order = {"scatter": scatter_order}
    for link in links:
        if not 0 <= link.get("curve", -1) < len(curve_order):
            continue
        for kind in LINK_KINDS:
            if kind in link and 0 <= link[kind] < len(order[kind]):
                set_link(curves, curve_order[link["curve"]], kind, order[kind][link[kind]])
                if kind == "scatter" and float(link.get("scale", 1.0)) != 1.0:
                    scatter = scatters[order[kind][link[kind]]]
                    scatter.update(scaled_to_cm_factor(scatter, link["scale"], link.get("scale_error")))
                    scatter["widget"].set_entries_with_data()


# Parameters that define the curve (the model and every value, cross-overs left out)
def defining_values(curve):
    parameters = {key: value for key, value in curve["parameters"].items() if "cross_over" not in key}
    return curve["model"], parameters
