import numpy as np

'''
Replicate groups: the average spectrum of a sample from its replicates

A group holds scatters, each with the biological replicate (suspension) it belongs to; scatters of the same
biological replicate are its technical replicates. So the same structure covers:
    biological and technical replicates    several suspensions, one or more scatters each
    biological replicates only             one scatter per suspension
    technical replicates only              one suspension, several scatters

Averaging of the spectra (CM-factor values, arithmetic: Re[CM] changes sign; scaling relative spectra to a model is
done by the fit in OpenDEP Compute), at each frequency:
    1. technical replicates are averaged within each suspension
    2. the suspension means are averaged; error = SD across suspensions (n = number of suspensions)
With a single suspension at a frequency, the error is the SD of its technical replicates (marked "technical").
A frequency measured only once in the whole group (e.g. a crossover refinement point) is kept as a single point
with its own error (marked "single").

Frequencies of different scatters are matched when they differ by less than FREQUENCY_TOLERANCE (relative).
'''

FREQUENCY_TOLERANCE = 0.01                     # 1 % (relative frequency difference)
KINDS = ("biological", "technical", "single")


# Group members' frequencies matched within the tolerance: list of clusters, each a list of (member index, point index)
def match_frequencies(members, tolerance=FREQUENCY_TOLERANCE):
    points = sorted((float(f), m, i) for m, member in enumerate(members)
                    for i, f in enumerate(member["frequencies"]) if f > 0)
    clusters, start = [], None
    for f, m, i in points:
        if clusters and f <= start * (1 + tolerance):
            clusters[-1].append((m, i))
        else:
            clusters.append([(m, i)])
            start = f
    return clusters


# Average spectrum of a group
# members: [{"biological": label, "frequencies": [...], "values": [...], "errors": [...]}]
# returns: {"frequencies", "values", "errors", "n_biological", "n_technical", "kind"} (one entry per point)
#          plus "summary": {"n_biological", "technical_per_biological", "error"}
def average_group(members, tolerance=FREQUENCY_TOLERANCE):
    scaled = [{"biological": str(member["biological"]),
               "frequencies": np.asarray(member["frequencies"], dtype=float),
               "values": np.asarray(member["values"], dtype=float),
               "errors": np.asarray(member["errors"], dtype=float)} for member in members]

    result = {"frequencies": [], "values": [], "errors": [], "n_biological": [], "n_technical": [], "kind": []}
    for cluster in match_frequencies(scaled, tolerance):
        # Geometric mean of the matched frequencies (the exact value when they are all the same)
        matched = [float(scaled[m]["frequencies"][i]) for m, i in cluster]
        frequency = matched[0] if max(matched) == min(matched) else float(np.exp(np.mean(np.log(matched))))

        # 1. Technical replicates: the mean of each scatter at this frequency, then of each suspension
        by_scatter = {}
        for m, i in cluster:
            by_scatter.setdefault(m, []).append(scaled[m]["values"][i])
        by_biological = {}
        for m, values in by_scatter.items():
            by_biological.setdefault(scaled[m]["biological"], []).append(float(np.mean(values)))

        # 2. Suspension means, and the error
        n_biological = len(by_biological)
        n_technical = len(by_scatter)
        if len(cluster) == 1:
            m, i = cluster[0]
            value, error, kind = float(scaled[m]["values"][i]), float(scaled[m]["errors"][i]), "single"
        elif n_biological >= 2:
            means = [float(np.mean(values)) for values in by_biological.values()]
            value, error, kind = float(np.mean(means)), float(np.std(means, ddof=1)), "biological"
        else:
            technical = next(iter(by_biological.values()))
            if len(technical) >= 2:
                value, error, kind = float(np.mean(technical)), float(np.std(technical, ddof=1)), "technical"
            else:                                     # one scatter with two close points: their mean and spread
                values = by_scatter[next(iter(by_scatter))]
                value, error, kind = float(np.mean(values)), float(np.std(values, ddof=1)), "technical"

        for key, item in (("frequencies", frequency), ("values", value), ("errors", error),
                          ("n_biological", n_biological), ("n_technical", n_technical), ("kind", kind)):
            result[key].append(item)

    result["summary"] = group_summary(members)
    return result


# Average of one value over the group (a parameter or a crossover of the replicates' curves), with the same
# hierarchy as the spectra: technical replicates averaged per suspension first, then the suspensions.
#
# On the log scale (scale "log", all values > 0): geometric mean ×/÷ geometric SD (gsd = exp(SD of ln values)).
# Crossovers and fitted parameters of repeated runs are log-normal (their spread is multiplicative, see
# docs/concepts/replicates.md), and the first crossover is a product / ratio of parameters (fc ≈ σm / 2πrCmem), so
# the curve of the geometric-mean parameters crosses at the geometric-mean crossover; with arithmetic means it does
# not. Values that are 0 or negative cannot be on the log scale, and quantities that can be zero (log=False, e.g. a
# membrane conductance at the fit's lower bound) should not be: arithmetic mean ± SD (scale "linear").
# The ordinary mean ± SD (same hierarchy) is always given too, to compare with published values.
#
# items: [{"biological": label, "value": number or None}] (None, e.g. no crossover, is left out)
# log: False keeps the quantity on the linear scale
# returns: {"mean", "gsd", "sd", "scale", "arithmetic_mean", "arithmetic_sd", "fixed", "n_biological",
#           "n_technical", "kind"}; gsd only on the log scale, sd only on the linear scale (None without spread);
#           kind "none" when no item has a value
def average_scalar(items, log=True):
    by_biological = {}
    for item in items:
        if item["value"] is not None and np.isfinite(item["value"]):
            by_biological.setdefault(str(item["biological"]), []).append(float(item["value"]))
    n_technical = sum(len(values) for values in by_biological.values())
    if n_technical == 0:
        return {"mean": None, "gsd": None, "sd": None, "scale": None, "arithmetic_mean": None,
                "arithmetic_sd": None, "fixed": False, "n_biological": 0, "n_technical": 0, "kind": "none"}
    everything = [value for values in by_biological.values() for value in values]
    log = log and all(value > 0 for value in everything)
    result = {"scale": "log" if log else "linear", "fixed": False, "n_technical": n_technical}

    if n_technical >= 2 and np.allclose(everything, everything[0], rtol=1e-12, atol=0):
        # The same value everywhere (e.g. a parameter fixed in the fits): no spread, not rounding noise of the mean
        return {**result, "mean": everything[0], "gsd": 1.0 if log else None, "sd": None if log else 0.0,
                "arithmetic_mean": everything[0], "arithmetic_sd": 0.0, "fixed": True,
                "n_biological": len(by_biological), "kind": "biological" if len(by_biological) >= 2 else "technical"}

    if len(by_biological) >= 2:
        samples = list(by_biological.values())                       # each suspension's technical replicates
        kind = "biological"
    else:
        samples = [[value] for value in next(iter(by_biological.values()))]     # one suspension: its replicates
        kind = "technical" if n_technical >= 2 else "single"
    values = np.array([_center(sample, log) for sample in samples])
    arithmetic = np.array([np.mean(sample) for sample in samples])
    spread = len(values) >= 2
    return {**result, "mean": _center(values, log),
            "gsd": float(np.exp(np.std(np.log(values), ddof=1))) if log and spread else None,
            "sd": float(np.std(values, ddof=1)) if not log and spread else None,
            "arithmetic_mean": float(np.mean(arithmetic)),
            "arithmetic_sd": float(np.std(arithmetic, ddof=1)) if spread else None,
            "n_biological": len(by_biological), "kind": kind}


# Mean of values: geometric (log scale) or arithmetic
def _center(values, log):
    return float(np.exp(np.mean(np.log(values)))) if log else float(np.mean(values))


# The model of a group from the curves of its replicates: the average (average_scalar: geometric mean ×/÷ geometric
# SD) of every parameter of the model and of the first and second crossover. All curves must use the same model (the parameters of different models do not mean
# the same thing); otherwise nothing is averaged and "warning" says why.
# curves: [{"biological": label, "model": index, "parameters": {...}, "crossovers": (first, second)}]
# linear_scale: parameters kept on the linear scale (parameters.LINEAR_SCALE)
# returns: {"model", "n_curves", "parameters": {key: average_scalar}, "first_crossover", "second_crossover",
#           "warning"}
def average_curves(curves, model_parameters, model_names, linear_scale=()):
    result = {"model": None, "n_curves": len(curves), "parameters": {}, "first_crossover": None,
              "second_crossover": None, "warning": ""}
    if not curves:
        result["warning"] = "No curves linked to the scatters of this group"
        return result
    used = sorted({curve["model"] for curve in curves})
    if len(used) > 1:
        result["warning"] = ("The replicates' curves use different models (" +
                             ", ".join(model_names[m] for m in used) + "): parameters not averaged")
        return result

    model = used[0]
    result["model"] = model
    for key in model_parameters[model]:
        result["parameters"][key] = average_scalar(
            [{"biological": c["biological"], "value": c["parameters"].get(key)} for c in curves],
            log=key not in linear_scale)
    for index, name in enumerate(("first_crossover", "second_crossover")):
        result[name] = average_scalar([{"biological": c["biological"], "value": c["crossovers"][index] or None}
                                       for c in curves])
    return result


# What the group is made of: number of suspensions, technical replicates of each, and the error shown
def group_summary(members):
    technical = {}
    for member in members:
        technical[str(member["biological"])] = technical.get(str(member["biological"]), 0) + 1
    n_biological = len(technical)
    if n_biological >= 2:
        error = "SD across biological replicates"
    elif n_biological == 1 and sum(technical.values()) >= 2:
        error = "technical SD (1 biological replicate)"
    else:
        error = "error of the single spectrum"
    return {"n_biological": n_biological, "technical_per_biological": technical, "error": error}


# One line describing the group, e.g. "3 biological × 2 technical replicates · SD across biological replicates"
def summary_text(summary):
    n = summary["n_biological"]
    if n == 0:
        return "No scatters yet"
    counts = sorted(set(summary["technical_per_biological"].values()))
    technical = str(counts[0]) if len(counts) == 1 else f"{counts[0]}–{counts[-1]}"
    if n == 1:
        parts = f"1 biological replicate, {technical} technical"
    elif counts == [1]:
        parts = f"{n} biological replicates"
    else:
        parts = f"{n} biological × {technical} technical replicates"
    return f"{parts} · {summary['error']}"
