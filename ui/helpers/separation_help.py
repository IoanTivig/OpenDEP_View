from src.func.general import format_frequency

'''
Tooltips of the Best separation card (Group plots): what each entry means and how it is calculated (see
src/func/separation.py), and for the values the numbers of the pair shown
'''

_COMMON_RANK = "<br><br>Only the order changes: every pair's values are those at its own best frequency f*."

HELP = {
    "title": "<b>Best separation</b><br>Of the visible groups, the pair ranked first by the criterion chosen in "
             "<i>Rank by</i>: at the best frequency f* one population is in pDEP (pulled to the electrodes), the "
             "other in nDEP (pushed away). Hide a group (eye) to leave it out.<br><br>Hover over the card for the "
             "other pairs; hover over an entry for how it is calculated.",
    "rank_score": "<b>Rank by separation score</b><br>How cleanly one frequency puts one group in pDEP and the "
                  "other in nDEP, with a strong enough force. Equal scores: larger ΔRe[CM] first." + _COMMON_RANK,
    "rank_ratio": "<b>Rank by crossover ratio</b><br>How far apart the two groups' first crossovers are (the curves "
                  "farthest apart first), whatever the spread of their samples. Equal ratios: higher separation "
                  "score first." + _COMMON_RANK,
    "rank_contrast": "<b>Rank by ΔRe[CM]</b><br>The largest difference in DEP force between a group in pDEP and "
                     "a group in nDEP, at the pair's best frequency. Pairs that are not on opposite sides there "
                     "come last." + _COMMON_RANK,
    "pair": "<b>The pair</b><br>Which group is in pDEP and which in nDEP at the best frequency f*, and how many of "
            "each group's samples (biological replicates) are on that side, from their own first crossovers "
            "fc1:<br>&nbsp;&nbsp;pDEP group: samples with fc1 &lt; f*<br>&nbsp;&nbsp;nDEP group: samples with "
            "fc1 &gt; f*<br>A few samples on the other side lower the separation score even when the crossover "
            "ratio is large.",
    "frequency": "<b>Best frequency f*</b><br>Where the separation score is highest:<br>&nbsp;&nbsp;f* = argmax "
                 "S(f)<br>searched on 600 log-spaced frequencies inside the range both groups were measured over, "
                 "below the lower geometric-mean second crossover of the two. The other entries of the card are "
                 "taken at f*.",
    "score": "<b>Separation score</b><br>How cleanly one frequency splits the two populations: 0 = no usable "
             "frequency, 1 = one group entirely in pDEP, the other entirely in nDEP, with a strong force.<br>"
             "&nbsp;&nbsp;S(f) = |P<sub>A</sub>(f) − P<sub>B</sub>(f)| · w(f)<br>"
             "&nbsp;&nbsp;P(f) = (1/n) Σ<sub>i</sub> Φ( ln(f / fc1<sub>i</sub>) / 0.2 )<br>"
             "&nbsp;&nbsp;w(f) = min(1, ΔRe[CM](f) / 0.5) if Re[CM]<sub>pDEP</sub> &gt; 0 &gt; "
             "Re[CM]<sub>nDEP</sub>, else 0<br>"
             "P: the group's share in pDEP, from the first crossover fc1<sub>i</sub> of each of its n samples, "
             "smoothed log-normally by ±22 % (Φ: standard normal cumulative distribution). w: the force weight, "
             "cells only move apart when the force difference is large enough.",
    "ratio": "<b>Crossover ratio</b><br>How far apart the two groups' first crossovers are:<br>"
             "&nbsp;&nbsp;R = fc1<sub>higher</sub> / fc1<sub>lower</sub><br>"
             "with fc1 the geometric-mean first crossover shown in each group, exp(mean of ln fc1 of its samples). "
             "About 1: the crossovers overlap; above about 1.5: clearly apart. It does not depend on the frequency "
             "or on the spread of the samples.",
    "contrast": "<b>ΔRe[CM]</b><br>The difference in DEP force between the two groups at f* (the force is "
                "proportional to Re[CM]):<br>"
                "&nbsp;&nbsp;ΔRe[CM] = Re[CM]<sub>pDEP group</sub>(f*) − Re[CM]<sub>nDEP group</sub>(f*)<br>"
                "&nbsp;&nbsp;CM = (ε*<sub>p</sub> − ε*<sub>m</sub>) / (ε*<sub>p</sub> + 2 ε*<sub>m</sub>), "
                "ε* = ε − jσ/ω<br>"
                "from each group's curve (the model with its geometric-mean parameters). Re[CM] lies between −0.5 "
                "and +1, so ΔRe[CM] is at most 1.5. In brackets: each group's Re[CM].",
    "second": "<b>2nd crossover</b><br>The separation at the high-frequency crossovers (pDEP back to nDEP), "
              "worked out like the separation score with the share still in pDEP:<br>"
              "&nbsp;&nbsp;P(f) = (1/n) Σ<sub>i</sub> [1 − Φ( ln(f / fc2<sub>i</sub>) / 0.2 )]<br>"
              "Shown only when every sample of both groups has a second crossover inside the measured range. It "
              "never decides the ranking.",
}


def _group(group):
    return f"<span style='color:{group['color']}'>●</span> {group['name']}"


# The tooltip of each value of the card for the pair shown: its numbers (3 decimals, so the sums add up), then the
# explanation. pair: an entry of separation.rank_pairs, or None (no pair: the explanations alone)
def value_tooltips(pair):
    tips = {key: HELP[key] for key in ("frequency", "score", "ratio", "contrast", "second")}
    if pair is None:
        return tips
    pdep, ndep = pair["pdep"], pair["ndep"]
    numbers = {
        "frequency": f"f* = {format_frequency(pair['frequency'])} for {_group(pdep)} / {_group(ndep)}",
        "score": f"S(f*) = |{pair['share_pdep']:.3f} − {pair['share_ndep']:.3f}| · "
                 + (f"{pair['weight']:.3f}" if pair["weight"] is not None else "1 (force not known)")
                 + f" = {pair['score']:.3f}<br>(share in pDEP of {_group(pdep)} and of {_group(ndep)}; force weight)",
    }
    firsts = sorted((g["first_crossover"], g) for g in (pdep, ndep) if g["first_crossover"])
    if pair["ratio"] and len(firsts) == 2:
        (low, low_group), (high, high_group) = firsts
        numbers["ratio"] = (f"R = {format_frequency(high)} ({_group(high_group)}) / {format_frequency(low)} "
                            f"({_group(low_group)}) = {pair['ratio']:.3f}")
    if pair["contrast"] is not None:
        numbers["contrast"] = (f"ΔRe[CM] = {pair['recm_pdep']:+.3f} ({_group(pdep)}) − ({pair['recm_ndep']:+.3f}) "
                               f"({_group(ndep)}) = {pair['contrast']:.3f}")
    second = pair["second"]
    if second:
        numbers["second"] = (f"S = |{second['share_pdep']:.3f} − {second['share_ndep']:.3f}| · "
                             + (f"{second['weight']:.3f}" if second["weight"] is not None else "1")
                             + f" = {second['score']:.3f} at {format_frequency(second['frequency'])}")
    for key, text in numbers.items():
        tips[key] = f"{text}<hr>{HELP[key]}"
    return tips
