import itertools
import math

import numpy as np

'''
Separation of two replicate groups by DEP: at which frequency, and how well, one population is pulled (pDEP) while
the other is pushed (nDEP)

Each sample (biological replicate; with a single suspension, each technical replicate) gives its own crossovers, from
the curve fitted to its scatter. Separation is judged at the first crossover (nDEP -> pDEP), where populations are
normally separated. To estimate the share of a population in pDEP at a frequency f from a few samples, each sample's
first crossover is smoothed by a log-normal of width LOG_SPREAD:
    P_pDEP(f) = mean over samples of Φ(ln(f / fc1) / s)

Separation score of groups A and B at f: the difference of their shares in pDEP, weighted by the force that pulls
them apart,
    S(f) = |P_A(f) − P_B(f)| · w(f)
    w(f) = min(1, ΔRe[CM](f) / FULL_CONTRAST) when the pDEP group's Re[CM] is positive and the nDEP group's negative,
           else 0
ΔRe[CM] = Re[CM] of the pDEP group minus that of the nDEP group, from the groups' mean-parameter curves. S goes from
0 (no frequency splits them, or the force is too weak to move them apart) to 1 (every sample of one group in pDEP,
every sample of the other in nDEP, with Re[CM] at least ±FULL_CONTRAST / 2 apart). (The product P_A · (1 − P_B) is
not used: it gives 0.25 for two identical groups.)

Where it is searched: only inside the frequency range both groups were measured over (their scatters; the fitted
curves are not trusted outside it), and below the lower mean second crossover of the two groups. A crossover the
curve does not show (outside the plotted range) is unknown, never "pDEP up to any frequency".

The second crossover (pDEP -> nDEP, high frequency) is reported apart, the same way, only when both groups have one
inside the measured range ("second"); it never decides the best pair.

Reported with it, as usual in the DEP literature:
    crossover ratio   higher / lower geometric-mean first crossover (how far apart the populations' crossovers are)
    ΔRe[CM]           the force contrast at the best frequency (in brackets: each group's Re[CM])
and why the pair scores what it does: at the best frequency, how many samples of each group are on its side
(sides). The score measures how cleanly one frequency splits the samples, so a pair with a large crossover ratio
scores less when a few samples of one group overlap the other's.

The share in pDEP is the cumulative log-normal distribution of the crossovers, the model of DEP trapping curves of
Prieto et al., Lab Chip 12 (2012) 2182, who found the cells' crossovers in a suspension log-normal because the
crossover is a product / ratio of the cell's parameters (fc ≈ σm / 2πrCmem); the crossovers of repeated runs are
log-normal too (docs/concepts/replicates.md).
'''

LOG_SPREAD = 0.20                     # ln units (about ± 22 %) smoothing of each sample's crossovers
FULL_CONTRAST = 0.5                   # ΔRe[CM] that counts as a full-strength split (e.g. +0.25 / -0.25)
GRID_POINTS = 600


def _phi(x):
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(x, dtype=float) / math.sqrt(2.0)))


def _geometric_mean(values):
    values = [v for v in values if v]
    return float(np.exp(np.mean(np.log(values)))) if values else None


# The samples of a group: (first, second) crossover of each biological replicate (its technical replicates
# averaged), or of each technical replicate when there is a single suspension. Curves without a first crossover
# are left out. items: [{"biological": label, "first": Hz or None, "second": Hz or None}]
def samples(items):
    by_biological = {}
    for item in items:
        if item["first"]:
            by_biological.setdefault(str(item["biological"]), []).append((item["first"], item["second"]))
    if len(by_biological) == 1:
        return [(float(first), float(second) if second else None) for first, second in
                next(iter(by_biological.values()))]
    return [(_geometric_mean([first for first, _ in values]), _geometric_mean([second for _, second in values]))
            for values in by_biological.values()]


# Share of the group in pDEP at each frequency, from the first crossovers (kind "first"), or the share still in
# pDEP below the second crossovers (kind "second")
def p_pdep(group_samples, frequencies, kind="first"):
    log_f = np.log(np.asarray(frequencies, dtype=float))
    if kind == "first":
        shares = [_phi((log_f - math.log(first)) / LOG_SPREAD) for first, _ in group_samples]
    else:
        shares = [1.0 - _phi((log_f - math.log(second)) / LOG_SPREAD) for _, second in group_samples if second]
    return np.mean(shares, axis=0)


# Force weight at each frequency: ΔRe[CM] / FULL_CONTRAST (at most 1) where the pDEP group's Re[CM] is positive and
# the nDEP group's negative, else 0. recm_*: arrays (None without a mean curve: weight 1, the force is not known)
def force_weight(recm_pdep, recm_ndep):
    if recm_pdep is None or recm_ndep is None:
        return None
    opposite = (recm_pdep > 0) & (recm_ndep < 0)
    return np.where(opposite, np.minimum(1.0, (recm_pdep - recm_ndep) / FULL_CONTRAST), 0.0)


def _recm(group, frequencies):
    return np.asarray(group["recm"](frequencies), dtype=float) if group["recm"] else None


# The best frequency of a pair in a window: {"pdep", "ndep", "score", "split", "weight", "frequency", "recm_pdep",
# "recm_ndep", "contrast", "share_pdep", "share_ndep" (each group's share in pDEP there), "pdep_samples",
# "ndep_samples" (see sides)}, or None (empty window)
def _best(a, b, low, high, kind):
    if not low or not high or high <= low:
        return None
    frequencies = np.logspace(math.log10(low), math.log10(high), GRID_POINTS)
    p_a, p_b = p_pdep(a["samples"], frequencies, kind), p_pdep(b["samples"], frequencies, kind)
    r_a, r_b = _recm(a, frequencies), _recm(b, frequencies)
    a_pdep = p_a >= p_b
    split = np.abs(p_a - p_b)
    if r_a is not None and r_b is not None:
        weight = np.where(a_pdep, force_weight(r_a, r_b), force_weight(r_b, r_a))
    else:
        weight = np.ones_like(split)
    score = split * weight
    i = int(np.argmax(score))
    pdep, ndep = (a, b) if a_pdep[i] else (b, a)
    r_pdep, r_ndep = (r_a, r_b) if a_pdep[i] else (r_b, r_a)
    share_pdep, share_ndep = (p_a[i], p_b[i]) if a_pdep[i] else (p_b[i], p_a[i])
    recm_pdep = float(r_pdep[i]) if r_pdep is not None else None
    recm_ndep = float(r_ndep[i]) if r_ndep is not None else None
    return {"pdep": pdep, "ndep": ndep, "score": float(score[i]), "split": float(split[i]),
            "weight": float(weight[i]) if r_a is not None and r_b is not None else None,
            "frequency": float(frequencies[i]), "recm_pdep": recm_pdep, "recm_ndep": recm_ndep,
            "contrast": recm_pdep - recm_ndep if recm_pdep is not None and recm_ndep is not None else None,
            "share_pdep": float(share_pdep), "share_ndep": float(share_ndep),
            "pdep_samples": sides(pdep["samples"], frequencies[i], kind),
            "ndep_samples": sides(ndep["samples"], frequencies[i], kind)}


# Why a pair scores what it does: at frequency f, how many samples of a group are in pDEP and how many in nDEP
# (from their crossovers, without the smoothing): (in pDEP, in nDEP). kind "first": in pDEP above the first
# crossover; "second": in pDEP below the second crossover
def sides(group_samples, f, kind="first"):
    if kind == "first":
        crossovers = [first for first, _ in group_samples]
        pdep = sum(1 for c in crossovers if c < f)
    else:
        crossovers = [second for _, second in group_samples if second]
        pdep = sum(1 for c in crossovers if c > f)
    return pdep, len(crossovers) - pdep


# Separation of two groups. group: {"name", "samples", "first_crossover" (mean, Hz), "range" ((lowest, highest)
# measured frequency, Hz), "recm" (frequencies -> Re[CM] of its mean curve, or None)}.
# Returns the best first-crossover separation (see _best) with "ratio" and "second" (the separation at the second
# crossovers, or None), or None when a group has no sample or the groups share no measured range.
def separate(a, b):
    if not a["samples"] or not b["samples"] or None in (*a["range"], *b["range"]):
        return None
    low = max(a["range"][0], b["range"][0])
    high = min(a["range"][1], b["range"][1])
    if high <= low:
        return None

    # 1. First crossover: up to the lower mean second crossover of the two groups (where both are still rising)
    seconds = [s for s in (_geometric_mean([x for _, x in g["samples"]]) for g in (a, b)) if s and low < s < high]
    result = _best(a, b, low, min([high] + seconds), "first")
    if result is None:
        return None

    # 2. Second crossover, apart: only when every sample of both groups has one inside the measured range
    second = None
    if all(x and low < x < high for g in (a, b) for _, x in g["samples"]):
        second = _best(a, b, min(seconds), high, "second")

    first = sorted(g["first_crossover"] for g in (a, b) if g["first_crossover"])
    return {**result, "ratio": first[1] / first[0] if len(first) == 2 else None, "second": second}


# What the pairs can be ranked by (Best separation, Rank by): key -> label. Only the order changes; every pair's
# values stay those at its own best frequency (highest separation score).
#   score      separation score, then ΔRe[CM]
#   ratio      crossover ratio (pairs without one last), then score
#   contrast   ΔRe[CM] at the best frequency, for pairs on opposite sides there (force weight > 0; the others last),
#              then score
RANKINGS = {"score": "separation score", "ratio": "crossover ratio", "contrast": "ΔRe[CM]"}


# Every pair of groups, best first by the chosen ranking
def rank_pairs(groups, by="score"):
    pairs = [pair for a, b in itertools.combinations(groups, 2) if (pair := separate(a, b)) is not None]
    score = lambda p: -round(p["score"], 6)
    if by == "ratio":
        pairs.sort(key=lambda p: (p["ratio"] is None, -(p["ratio"] or 0), score(p)))
    elif by == "contrast":
        opposite = lambda p: p["contrast"] is not None and (p["weight"] is None or p["weight"] > 0)
        pairs.sort(key=lambda p: (not opposite(p), -(p["contrast"] or 0) if opposite(p) else 0, score(p)))
    else:
        pairs.sort(key=lambda p: (score(p), -(p["contrast"] or 0)))
    return pairs
