import itertools
import math

import numpy as np

'''
Separation of two replicate groups by DEP: at which frequency, and how well, one population is pulled (pDEP) while
the other is pushed (nDEP)

A population is in pDEP between its first and second crossover. Each sample (biological replicate; with a single
suspension, each technical replicate) gives its own crossovers, from the curve fitted to its scatter. To estimate
the share of a population in pDEP at a frequency f from a few samples, each sample's crossovers are smoothed by a
log-normal of width LOG_SPREAD:
    P_pDEP(f) = mean over samples of Φ(ln(f / fc1) / s) · (1 − Φ(ln(f / fc2) / s))        (no fc2: second factor 1)

Separation score of groups A and B at f: the difference of their shares in pDEP,
    S(f) = |P_A(f) − P_B(f)|
The best frequency maximises S; S goes from 0 (both populations behave the same at every frequency) to 1 (every
sample of one group is in pDEP while every sample of the other is in nDEP). (The product P_A · (1 − P_B) is not
used: it gives 0.25 for two identical groups.)

Reported with it, as usual in the DEP literature:
    crossover ratio   higher / lower mean first crossover (how far apart the populations' crossovers are)
    ΔRe[CM]           Re[CM] of the pDEP group minus that of the nDEP group at the best frequency, from the groups'
                      mean-parameter curves (the force contrast; the populations move opposite ways when the two
                      Re[CM] values have opposite signs)
'''

LOG_SPREAD = 0.20                     # ln units (about ± 22 %) smoothing of each sample's crossovers
GRID_POINTS = 600


def _phi(x):
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(x, dtype=float) / math.sqrt(2.0)))


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
    result = []
    for values in by_biological.values():
        seconds = [second for _, second in values if second]
        result.append((float(np.exp(np.mean(np.log([first for first, _ in values])))),
                       float(np.exp(np.mean(np.log(seconds)))) if seconds else None))
    return result


# Share of the group in pDEP at each frequency
def p_pdep(group_samples, frequencies):
    log_f = np.log(np.asarray(frequencies, dtype=float))
    shares = []
    for first, second in group_samples:
        share = _phi((log_f - math.log(first)) / LOG_SPREAD)
        if second:
            share = share * (1.0 - _phi((log_f - math.log(second)) / LOG_SPREAD))
        shares.append(share)
    return np.mean(shares, axis=0)


# Separation of two groups. group: {"name", "samples", "first_crossover" (mean, Hz), "recm" (f -> Re[CM] of its
# mean curve, or None)}. Returns {"pdep", "ndep" (the groups), "score", "frequency", "ratio", "recm_pdep",
# "recm_ndep", "contrast"}, or None when a group has no sample.
def separate(a, b):
    if not a["samples"] or not b["samples"]:
        return None
    crossovers = [f for group in (a, b) for sample in group["samples"] for f in sample if f]
    frequencies = np.logspace(math.log10(min(crossovers)) - 1, math.log10(max(crossovers)) + 1, GRID_POINTS)
    p_a, p_b = p_pdep(a["samples"], frequencies), p_pdep(b["samples"], frequencies)
    score = np.abs(p_a - p_b)
    i = int(np.argmax(score))
    pdep, ndep = (a, b) if p_a[i] >= p_b[i] else (b, a)
    frequency = float(frequencies[i])

    first = sorted(g["first_crossover"] for g in (a, b) if g["first_crossover"])
    recm_pdep = pdep["recm"](frequency) if pdep["recm"] else None
    recm_ndep = ndep["recm"](frequency) if ndep["recm"] else None
    return {"pdep": pdep, "ndep": ndep, "score": float(score[i]), "frequency": frequency,
            "ratio": first[1] / first[0] if len(first) == 2 else None,
            "recm_pdep": recm_pdep, "recm_ndep": recm_ndep,
            "contrast": recm_pdep - recm_ndep if recm_pdep is not None and recm_ndep is not None else None}


# Every pair of groups, best first (score, then contrast)
def rank_pairs(groups):
    pairs = [pair for a, b in itertools.combinations(groups, 2) if (pair := separate(a, b)) is not None]
    pairs.sort(key=lambda p: (-round(p["score"], 6), -(p["contrast"] or 0)))
    return pairs
