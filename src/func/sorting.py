'''
Order of the plot lists (Curve, Scatter and Group plots), chosen in the Sort drop-down of each list

    newest              newest first (as the cards are added)
    oldest              oldest first
    name                by name, A to Z; numbers in names count as numbers (Sample 2 before Sample 10)
    first_crossover     1st crossover frequency, low to high
    second_crossover    2nd crossover frequency, low to high
    model               curves: by dielectric model
    group               scatters: by the replicate group they are in

The crossover of a curve is that of its model. A scatter takes the crossover of the curve linked to it, or else the
frequency where its measured values change sign; a group the (geometric) mean crossover of its replicates' curves, or
else where its mean changes sign. Items without a value go to the end; equal values are ordered by name.
'''

import math
import re

SORT_OPTIONS = {
    "curves": [("newest", "Newest first"), ("oldest", "Oldest first"), ("name", "Name (A–Z)"),
               ("first_crossover", "1st crossover"), ("second_crossover", "2nd crossover"), ("model", "Model")],
    "scatters": [("newest", "Newest first"), ("oldest", "Oldest first"), ("name", "Name (A–Z)"),
                 ("first_crossover", "1st crossover"), ("group", "Group")],
    "groups": [("newest", "Newest first"), ("oldest", "Oldest first"), ("name", "Name (A–Z)"),
               ("first_crossover", "1st crossover"), ("second_crossover", "2nd crossover")],
}
DEFAULT_SORT = "newest"


# Key of a name for sorting: case ignored, numbers by value ("Sample 2" before "Sample 10")
def natural_key(text):
    return [(0, int(part), "") if part.isdigit() else (1, 0, part.casefold())
            for part in re.split(r"(\d+)", str(text or "")) if part]


# A crossover frequency, or None when there is none (missing, zero, not a number)
def frequency_or_none(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value > 0 else None


# Frequencies where measured values change sign, low to high (interpolated on the log frequency axis between the
# points either side; values of exactly 0 are skipped)
def data_crossovers(frequencies, values):
    points = sorted((float(f), float(v)) for f, v in zip(frequencies, values)
                    if frequency_or_none(f) is not None and v is not None and math.isfinite(float(v)))
    points = [(f, v) for f, v in points if v != 0] or points
    crossovers = []
    for (f1, v1), (f2, v2) in zip(points, points[1:]):
        if v1 * v2 < 0:
            t = v1 / (v1 - v2)
            crossovers.append(10 ** (math.log10(f1) + t * (math.log10(f2) - math.log10(f1))))
    return crossovers


# Ids in the chosen order. ids: in the order they were added; name(id): the item's name; value(id): what the order
# other than newest / oldest / name sorts on (a number or a natural_key, None when the item has none)
def sort_ids(ids, mode, name, value=None):
    ids = list(ids)
    if mode == "oldest":
        return ids
    if mode == "name":
        return sorted(ids, key=lambda i: natural_key(name(i)))
    if value is None:                                   # newest, or an order this list does not have
        return ids[::-1]

    def key(i):
        v = value(i)
        return (v is None, 0 if v is None else v, natural_key(name(i)))
    return sorted(ids, key=key)
