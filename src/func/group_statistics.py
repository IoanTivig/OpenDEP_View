import math
from datetime import datetime

import numpy as np
from scipy import stats

from src.func import parameters as model_parameters
from src.func import separation

'''
Statistics report of the replicate groups: every pair of groups ranked by separation (best first), the descriptive
statistics of each group, and pairwise tests of the crossovers and of the fitted model parameters

Unit of observation: the biological replicate (suspension); its technical replicates are averaged first, so n is
the number of suspensions. A group with a single suspension uses its technical replicates instead (marked
"technical": they show the measurement spread, not the biological one).

Per group and quantity: n, mean, SD, SEM, CV, median, range and the Shapiro-Wilk test of normality (n >= 3).
Per pair and quantity, both tests are reported:
    Welch's t-test        normal data (does not assume equal variances)
    Mann-Whitney U test   any distribution (ranks; exact p for small samples)
The test used for the conclusion is Welch's t-test unless the Shapiro-Wilk test rejects normality (p <= ALPHA) in
either group; then Mann-Whitney U. With n < 3, normality cannot be tested (noted). The p values of the test used are
corrected for the number of pairs with the Holm method, per quantity. Effect size: Hedges' g (bias-corrected
standardised mean difference).

The data points of the scatters are not tested: their errors are already the spread of the replicates, and the
model parameters and crossovers carry the comparison.
'''

ALPHA = 0.05


# The values of one quantity in a group, one per biological replicate (technical replicates averaged), or one per
# technical replicate when the group has a single suspension. curves: [{"biological", ...}], value(curve) -> number
# or None. Returns (values, level) with level "biological", "technical" or "none".
def sample_values(curves, value):
    by_biological = {}
    for curve in curves:
        v = value(curve)
        if v is not None and np.isfinite(v):
            by_biological.setdefault(str(curve["biological"]), []).append(float(v))
    if not by_biological:
        return np.array([]), "none"
    if len(by_biological) == 1:
        return np.array(next(iter(by_biological.values()))), "technical"
    return np.array([np.mean(v) for v in by_biological.values()]), "biological"


# n, mean, SD, SEM, CV (%), median, min, max, Shapiro-Wilk W and p, normal (True / False / None: not testable)
def describe(values, level):
    n = len(values)
    result = {"n": n, "level": level, "mean": None, "sd": None, "sem": None, "cv": None, "median": None,
              "min": None, "max": None, "shapiro_w": None, "shapiro_p": None, "normal": None}
    if n == 0:
        return result
    result.update(mean=float(np.mean(values)), median=float(np.median(values)), min=float(np.min(values)),
                  max=float(np.max(values)))
    if n >= 2:
        sd = 0.0 if np.ptp(values) == 0 else float(np.std(values, ddof=1))       # no rounding noise of the mean
        result.update(sd=sd, sem=sd / math.sqrt(n), cv=100 * sd / abs(result["mean"]) if result["mean"] else None)
    if n >= 3 and np.ptp(values) > 0:
        w, p = stats.shapiro(values)
        result.update(shapiro_w=float(w), shapiro_p=float(p), normal=bool(p > ALPHA))
    return result


def _hedges_g(a, b):
    n1, n2 = len(a), len(b)
    pooled = math.sqrt(((n1 - 1) * np.var(a, ddof=1) + (n2 - 1) * np.var(b, ddof=1)) / (n1 + n2 - 2))
    if pooled == 0:
        return None
    return float((np.mean(a) - np.mean(b)) / pooled * (1 - 3 / (4 * (n1 + n2) - 9)))


def _p(value):
    return None if value is None or not np.isfinite(value) else float(value)


# Both tests for two samples, the one used and why. Returns {"welch_t", "welch_p", "mwu_u", "mwu_p", "used",
# "reason", "p", "g"}; "used" None when there are too few values or no spread at all.
def compare(a, b, describe_a, describe_b):
    result = {"welch_t": None, "welch_p": None, "mwu_u": None, "mwu_p": None, "used": None, "reason": "",
              "p": None, "p_holm": None, "g": None}
    if len(a) < 2 or len(b) < 2:
        result["reason"] = "fewer than 2 values in a group"
        return result
    if np.ptp(np.concatenate([a, b])) == 0:
        result["reason"] = "the same value everywhere"
        return result
    if np.ptp(a) == 0 and np.ptp(b) == 0:
        result["reason"] = "no spread within the groups (fixed values)"
        return result
    welch = stats.ttest_ind(a, b, equal_var=False)
    mwu = stats.mannwhitneyu(a, b, alternative="two-sided")
    result.update(welch_t=_p(welch.statistic), welch_p=_p(welch.pvalue), mwu_u=float(mwu.statistic),
                  mwu_p=_p(mwu.pvalue), g=_hedges_g(a, b))
    not_normal = [d for d in (describe_a, describe_b) if d["normal"] is False]
    untestable = [d for d in (describe_a, describe_b) if d["normal"] is None]
    if not_normal:
        result.update(used="Mann-Whitney U", reason="normality rejected (Shapiro-Wilk)", p=result["mwu_p"])
    else:
        result.update(used="Welch t", reason="normality not testable (n < 3)" if untestable else
                      "normality not rejected (Shapiro-Wilk)", p=result["welch_p"])
    return result


# Holm-corrected p values (None stays None), in the order given
def holm(p_values):
    indexed = sorted((p, i) for i, p in enumerate(p_values) if p is not None)
    m = len(indexed)
    corrected, running = [None] * len(p_values), 0.0
    for rank, (p, i) in enumerate(indexed):
        running = max(running, min(1.0, (m - rank) * p))
        corrected[i] = running
    return corrected


def stars(p):
    if p is None:
        return ""
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < ALPHA else "ns"


# The quantities of a group: [(key, label, unit, scale, value(curve))]; crossovers in kHz, then the parameters of
# the model (all curves of the group use it; see replicates.average_curves)
def quantities(model):
    items = [("first_crossover", "First crossover", "kHz", 1e-3, lambda c: c["first"]),
             ("second_crossover", "Second crossover", "MHz", 1e-6, lambda c: c["second"])]
    if model is None:
        return items
    for title, keys in model_parameters.grouped_parameters(model):
        for key in keys:
            _, label, unit = model_parameters.PARAMETER_INFO[key]
            name = label if title in ("Other", "Shell dimensions") else f"{title} {label.lower()}"
            items.append((key, name, unit, 1.0, lambda c, k=key: c["parameters"].get(k)))
    return items


# The whole report. groups: [{"name", "color", "model", "curves": [{"biological", "model", "parameters", "first",
# "second"}], "n_biological", "n_technical", "separation": dict for separation.rank_pairs}]
def build_report(groups):
    report = {"created": datetime.now().strftime("%Y-%m-%d %H:%M"), "alpha": ALPHA, "groups": [], "pairs": [],
              "fixed": []}

    # 1. Descriptive statistics of every group
    for group in groups:
        entry = {"name": group["name"], "color": group["color"], "model": group["model"],
                 "model_name": model_parameters.MODEL_NAMES[group["model"]] if group["model"] is not None else
                 "different models / none", "n_biological": group["n_biological"],
                 "n_technical": group["n_technical"], "quantities": {}, "values": {}}
        for key, label, unit, scale, value in quantities(group["model"]):
            values, level = sample_values(group["curves"], value)
            values = values * scale
            entry["quantities"][key] = {"label": label, "unit": unit, **describe(values, level)}
            entry["values"][key] = values
        report["groups"].append(entry)

    # 2. Quantities with the same value in every sample of every group (e.g. fixed in the fits): listed, not tested
    keys = {}
    for entry in report["groups"]:
        for key, q in entry["quantities"].items():
            keys.setdefault(key, (q["label"], q["unit"], []))[2].append(entry["values"][key])
    for key, (label, unit, all_values) in keys.items():
        joined = np.concatenate(all_values) if all_values else np.array([])
        if len(joined) and np.ptp(joined) == 0:
            report["fixed"].append({"key": key, "label": label, "unit": unit, "value": float(joined[0])})
    fixed = {item["key"] for item in report["fixed"]}

    # 3. Pairs, best separated first, with the tests of every quantity they share
    ranked = separation.rank_pairs([{**g["separation"], "name": g["name"], "index": i} for i, g in enumerate(groups)])
    done = {frozenset((p["pdep"]["index"], p["ndep"]["index"])) for p in ranked}
    unranked = [{"pdep": {"index": i}, "ndep": {"index": j}, "score": None, "frequency": None, "ratio": None,
                 "recm_pdep": None, "recm_ndep": None, "contrast": None}
                for i in range(len(groups)) for j in range(i + 1, len(groups)) if frozenset((i, j)) not in done]
    for rank, pair in enumerate(ranked + unranked, 1):
        a, b = report["groups"][pair["pdep"]["index"]], report["groups"][pair["ndep"]["index"]]
        tests = {}
        for key, q in a["quantities"].items():
            if key in fixed or key not in b["quantities"] or q["n"] == 0 or b["quantities"][key]["n"] == 0:
                continue
            if key not in ("first_crossover", "second_crossover") and a["model"] != b["model"]:
                continue
            tests[key] = {"label": q["label"], "unit": q["unit"],
                          **compare(a["values"][key], b["values"][key], q, b["quantities"][key])}
        report["pairs"].append({"rank": rank if pair["score"] is not None else None, "a": a["name"],
                                "b": b["name"], "a_index": pair["pdep"]["index"], "b_index": pair["ndep"]["index"], "score": pair["score"], "frequency": pair["frequency"],
                                "ratio": pair["ratio"], "recm_a": pair["recm_pdep"], "recm_b": pair["recm_ndep"],
                                "contrast": pair["contrast"], "tests": tests,
                                "same_model": a["model"] is not None and a["model"] == b["model"]})

    # 4. Holm correction over the pairs, per quantity
    for key in {k for pair in report["pairs"] for k in pair["tests"]}:
        rows = [pair["tests"][key] for pair in report["pairs"] if key in pair["tests"]]
        for row, corrected in zip(rows, holm([row["p"] for row in rows])):
            row["p_holm"] = corrected
    for entry in report["groups"]:
        entry["values"] = {key: [float(v) for v in values] for key, values in entry["values"].items()}
    return report
