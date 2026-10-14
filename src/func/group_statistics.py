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

Scale: crossovers and fitted parameters of repeated runs are log-normal (their spread is multiplicative; see
docs/concepts/replicates.md), so a quantity whose values are all > 0 is analysed on the log scale (Limpert & Stahel,
PLoS One 6 (2011) e21403; Bland & Altman, BMJ 312 (1996) 770 and 1153); a quantity with a value <= 0 in any group,
and the conductances that can be zero (parameters.LINEAR_SCALE: fits put zero at their lower bound), stay on the
linear scale. The scale is decided per quantity for all groups together, before looking at any test.

Per group and quantity: n, mean (geometric on the log scale) with its spread (geometric SD, a factor ×/÷; or SD)
and 95 % confidence interval, median, range, the Shapiro-Wilk test of normality on the analysed scale (n >= 3), and
the ordinary mean ± SD for comparison with published values.
Per pair and quantity, both tests are reported:
    Welch's t-test        normal data on the analysed scale (does not assume equal variances); on the log scale it
                          compares the geometric means
    Mann-Whitney U test   any distribution (ranks, the same on both scales; exact p for small samples)
The test used for the conclusion is Welch's t-test unless the Shapiro-Wilk test rejects normality (p <= ALPHA) in
either group; then Mann-Whitney U. With n < 3, normality cannot be tested (noted). The p values of the test used are
corrected for the number of pairs with the Holm method, per quantity. Effect size: the ratio of the geometric means
with its 95 % CI (log scale; the difference of the means on the linear scale), and Hedges' g on the analysed scale.

The data points of the scatters are not tested: their errors are already the spread of the replicates, and the
model parameters and crossovers carry the comparison.
'''

ALPHA = 0.05
CONFIDENCE = 0.95


# The values of one quantity in a group, one per biological replicate (technical replicates averaged: geometric
# mean on the log scale), or one per technical replicate when the group has a single suspension. curves:
# [{"biological", ...}], value(curve) -> number or None. Returns (values, level) with level "biological",
# "technical" or "none".
def sample_values(curves, value, log=False):
    by_biological = {}
    for curve in curves:
        v = value(curve)
        if v is not None and np.isfinite(v):
            by_biological.setdefault(str(curve["biological"]), []).append(float(v))
    if not by_biological:
        return np.array([]), "none"
    if len(by_biological) == 1:
        return np.array(next(iter(by_biological.values()))), "technical"
    mean = (lambda v: np.exp(np.mean(np.log(v)))) if log else np.mean
    return np.array([mean(v) for v in by_biological.values()]), "biological"


def _scaled(values, log):
    return np.log(values) if log else np.asarray(values, dtype=float)


def _t(df):
    return float(stats.t.ppf(0.5 + CONFIDENCE / 2, df))


# n, scale, mean (geometric on the log scale) and spread (gsd: geometric SD, a factor; or sd), 95 % CI of the mean,
# median, min, max, ordinary mean and SD, Shapiro-Wilk W and p on the analysed scale, normal (True / False / None:
# not testable)
def describe(values, level, log=False):
    n = len(values)
    result = {"n": n, "level": level, "scale": "log" if log else "linear", "mean": None, "gsd": None, "sd": None,
              "ci_low": None, "ci_high": None, "median": None, "min": None, "max": None, "arithmetic_mean": None,
              "arithmetic_sd": None, "shapiro_w": None, "shapiro_p": None, "normal": None}
    if n == 0:
        return result
    x = _scaled(values, log)
    back = np.exp if log else (lambda v: v)
    result.update(mean=float(back(np.mean(x))), median=float(np.median(values)), min=float(np.min(values)),
                  max=float(np.max(values)), arithmetic_mean=float(np.mean(values)))
    if n >= 2:
        constant = np.ptp(values) == 0                              # no rounding noise of the mean
        s = 0.0 if constant else float(np.std(x, ddof=1))
        half = _t(n - 1) * s / math.sqrt(n)
        result.update(gsd=math.exp(s) if log else None, sd=None if log else s,
                      ci_low=float(back(np.mean(x) - half)), ci_high=float(back(np.mean(x) + half)),
                      arithmetic_sd=0.0 if constant else float(np.std(values, ddof=1)))
    if n >= 3 and np.ptp(values) > 0:
        w, p = stats.shapiro(x)
        result.update(shapiro_w=float(w), shapiro_p=float(p), normal=bool(p > ALPHA))
    return result


def _hedges_g(a, b):
    n1, n2 = len(a), len(b)
    pooled = math.sqrt(((n1 - 1) * np.var(a, ddof=1) + (n2 - 1) * np.var(b, ddof=1)) / (n1 + n2 - 2))
    if pooled == 0:
        return None
    return float((np.mean(a) - np.mean(b)) / pooled * (1 - 3 / (4 * (n1 + n2) - 9)))


# Difference of the means of a and b (analysed scale) with its Welch 95 % CI: (difference, low, high)
def _welch_interval(a, b):
    va, vb = np.var(a, ddof=1) / len(a), np.var(b, ddof=1) / len(b)
    difference = float(np.mean(a) - np.mean(b))
    se = math.sqrt(va + vb)
    if se == 0:
        return difference, None, None
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    return difference, difference - _t(df) * se, difference + _t(df) * se


def _p(value):
    return None if value is None or not np.isfinite(value) else float(value)


# Both tests for two samples, the one used and why. log: analysed on the log scale. Returns {"welch_t", "welch_p",
# "mwu_u", "mwu_p", "used", "reason", "p", "g", "effect", "effect_low", "effect_high", "effect_kind"}: effect is
# the ratio of the geometric means a / b (log scale, effect_kind "ratio") or the difference of the means a − b
# ("difference"), with its 95 % CI; "used" None when there are too few values or no spread at all.
def compare(a, b, describe_a, describe_b, log=False):
    result = {"welch_t": None, "welch_p": None, "mwu_u": None, "mwu_p": None, "used": None, "reason": "",
              "p": None, "p_holm": None, "g": None, "effect": None, "effect_low": None, "effect_high": None,
              "effect_kind": "ratio" if log else "difference"}
    if len(a) < 2 or len(b) < 2:
        result["reason"] = "fewer than 2 values in a group"
        return result
    if np.ptp(np.concatenate([a, b])) == 0:
        result["reason"] = "the same value everywhere"
        return result
    if np.ptp(a) == 0 and np.ptp(b) == 0:
        result["reason"] = "no spread within the groups (fixed values)"
        return result
    xa, xb = _scaled(a, log), _scaled(b, log)
    welch = stats.ttest_ind(xa, xb, equal_var=False)
    mwu = stats.mannwhitneyu(a, b, alternative="two-sided")
    difference, low, high = _welch_interval(xa, xb)
    back = math.exp if log else (lambda v: v)
    result.update(welch_t=_p(welch.statistic), welch_p=_p(welch.pvalue), mwu_u=float(mwu.statistic),
                  mwu_p=_p(mwu.pvalue), g=_hedges_g(xa, xb), effect=back(difference),
                  effect_low=back(low) if low is not None else None,
                  effect_high=back(high) if high is not None else None)
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
# rank_by: what the pairs are ranked by (separation.RANKINGS), as in Best separation
def build_report(groups, rank_by="score"):
    report = {"created": datetime.now().strftime("%Y-%m-%d %H:%M"), "alpha": ALPHA, "groups": [], "pairs": [],
              "fixed": [], "rank_by": rank_by, "rank_label": separation.RANKINGS.get(rank_by, "separation score")}

    # 1. The scale of every quantity, the same for all groups: log when every value of every group is > 0
    raw = {}
    for group in groups:
        for key, _, _, _, value in quantities(group["model"]):
            raw.setdefault(key, []).extend(v for v in map(value, group["curves"]) if v is not None and np.isfinite(v))
    log_scale = {key: bool(values) and all(v > 0 for v in values) and key not in model_parameters.LINEAR_SCALE
                 for key, values in raw.items()}
    report["log_scale"] = log_scale

    # 2. Descriptive statistics of every group
    for group in groups:
        entry = {"name": group["name"], "color": group["color"], "model": group["model"],
                 "model_name": model_parameters.MODEL_NAMES[group["model"]] if group["model"] is not None else
                 "different models / none", "n_biological": group["n_biological"],
                 "n_technical": group["n_technical"], "quantities": {}, "values": {}}
        for key, label, unit, scale, value in quantities(group["model"]):
            values, level = sample_values(group["curves"], value, log_scale[key])
            values = values * scale
            entry["quantities"][key] = {"label": label, "unit": unit, **describe(values, level, log_scale[key])}
            entry["values"][key] = values
        report["groups"].append(entry)

    # 3. Quantities with the same value in every sample of every group (e.g. fixed in the fits): listed, not tested
    keys = {}
    for entry in report["groups"]:
        for key, q in entry["quantities"].items():
            keys.setdefault(key, (q["label"], q["unit"], []))[2].append(entry["values"][key])
    for key, (label, unit, all_values) in keys.items():
        joined = np.concatenate(all_values) if all_values else np.array([])
        if len(joined) and np.ptp(joined) == 0:
            report["fixed"].append({"key": key, "label": label, "unit": unit, "value": float(joined[0])})
    fixed = {item["key"] for item in report["fixed"]}

    # 4. Pairs, best separated first, with the tests of every quantity they share
    ranked = separation.rank_pairs([{**g["separation"], "name": g["name"], "index": i} for i, g in enumerate(groups)],
                                   rank_by)
    done = {frozenset((p["pdep"]["index"], p["ndep"]["index"])) for p in ranked}
    unranked = [{"pdep": {"index": i}, "ndep": {"index": j}, "score": None, "split": None, "weight": None,
                 "frequency": None, "ratio": None, "recm_pdep": None, "recm_ndep": None, "contrast": None,
                 "second": None}
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
                          **compare(a["values"][key], b["values"][key], q, b["quantities"][key], log_scale[key])}
        report["pairs"].append({"rank": rank if pair["score"] is not None else None, "a": a["name"],
                                "b": b["name"], "a_index": pair["pdep"]["index"], "b_index": pair["ndep"]["index"],
                                "score": pair["score"], "split": pair["split"], "weight": pair["weight"],
                                "frequency": pair["frequency"], "ratio": pair["ratio"], "recm_a": pair["recm_pdep"],
                                "recm_b": pair["recm_ndep"], "contrast": pair["contrast"],
                                # samples of A in pDEP and of B in nDEP at the best frequency: (on side, of n)
                                "a_side": (pair["pdep_samples"][0], sum(pair["pdep_samples"]))
                                if pair.get("pdep_samples") else None,
                                "b_side": (pair["ndep_samples"][1], sum(pair["ndep_samples"]))
                                if pair.get("ndep_samples") else None,
                                "second": {"score": pair["second"]["score"], "frequency": pair["second"]["frequency"],
                                           "pdep": pair["second"]["pdep"]["name"]} if pair["second"] else None,
                                "tests": tests,
                                "same_model": a["model"] is not None and a["model"] == b["model"]})

    # 5. Holm correction over the pairs, per quantity
    for key in {k for pair in report["pairs"] for k in pair["tests"]}:
        rows = [pair["tests"][key] for pair in report["pairs"] if key in pair["tests"]]
        for row, corrected in zip(rows, holm([row["p"] for row in rows])):
            row["p_holm"] = corrected
    for entry in report["groups"]:
        entry["values"] = {key: [float(v) for v in values] for key, values in entry["values"].items()}
    return report
