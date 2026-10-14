# Separation of two populations

Two cell populations can be separated by DEP at a frequency where one is in **pDEP** (pulled to the electrodes) and the other in **nDEP** (pushed away). Such a frequency lies between their crossovers: above the first crossover of one population and below that of the other. The further apart their crossovers, and the less they vary from sample to sample, the cleaner the separation.

## What View calculates

For each visible group, from the first crossovers of its samples (one per biological replicate):

- **Share in pDEP** at frequency f: the part of the population whose first crossover lies below f. Each sample's crossover is smoothed over ±22 % (a log-normal of width 0.2 in ln f), so a few samples still give a smooth estimate. This is the log-normal model Prieto et al. (*Lab Chip* 12 (2012) 2182) fitted to DEP trapping curves of cell populations.
- **Force weight** at f: ΔRe[CM] / 0.5, at most 1, from the groups' curves (the model with the geometric-mean parameters, see [Replicates and averages](replicates.md)). It is 0 unless the pDEP group's Re[CM] is positive and the nDEP group's negative. Cells only move apart when the force is strong enough, so a split where both Re[CM] are near zero does not count.
- **Separation score** of two groups at f: the difference of their shares in pDEP times the force weight. The **best frequency** is where the score is highest.

| Score | Meaning |
|---|---|
| 0 | no frequency splits the two groups, or the force there is too weak |
| 0.5 | e.g. the share in pDEP differs by the whole population but ΔRe[CM] is only 0.25, or a full-strength force with half the population split |
| 1 | at the best frequency, one group is entirely in pDEP, the other entirely in nDEP, and their Re[CM] are at least 0.5 apart (e.g. +0.25 / −0.25) |

**Where it looks.** Only inside the frequency range both groups were measured over: the fitted curves are not used to guess beyond the data. It also stays below the lower (geometric-mean) second crossover of the two groups. A crossover that a curve does not show is treated as unknown.

**Second crossover.** The high-frequency crossover (pDEP back to nDEP) is rarely used to separate cells: the forces near it are weak and it often lies above the measured range. When every sample of both groups has a second crossover inside the measured range, View shows the separation there on its own line (**2nd crossover**), worked out the same way. It never decides the best pair.

Reported with it, as usual in DEP work:

- **Crossover ratio**: higher / lower geometric-mean first crossover (the crossovers shown in the groups). Above about 1.5 the crossovers are clearly apart; close to 1 they overlap.
- **ΔRe[CM]**: Re[CM] of the pDEP group minus that of the nDEP group at the best frequency, from the groups' curves. In brackets: each group's Re[CM].

## Ranking the pairs

**Rank by** in the Best separation card chooses which pair comes first (kept with the project; the [Statistics report](../user-guide/statistics-report.md) lists the pairs in the same order):

| Rank by | First comes the pair with | Equal values |
|---|---|---|
| **Sep. score** (default) | the cleanest split at one frequency, with a strong enough force | larger ΔRe[CM] first |
| **CO ratio** | the first crossovers farthest apart (the most different populations on average) | higher score first |
| **ΔRe[CM]** | the largest force difference at the best frequency, among pairs on opposite sides there | higher score first |

Only the order changes: every pair's values are always those at its own best frequency (where its separation score is highest), so the numbers of a pair do not depend on the ranking.

Every entry of the card has a tooltip with its definition and formula; the values' tooltips also show the numbers of the pair shown, e.g. *S(f\*) = |0.966 − 0.117| · 1.000 = 0.849*.

## Why a pair ranks where it does

Next to each group's name, the panel shows how many of its samples are on its side at the best frequency, from their crossovers: e.g. *BPEI-1 pDEP 9/11 · SH-SY5Y nDEP 2/2*. (The [Statistics report](../user-guide/statistics-report.md) has the same in its *Samples on side* column, and the panel's tooltip lists the other pairs.)

The score measures how **cleanly one frequency splits the samples**, not how far apart the averages are. So a pair with a large crossover ratio can rank below a pair with a smaller one: in the example, two BPEI-1 runs have crossovers among those of SH-SY5Y, so no frequency puts all BPEI-1 samples in pDEP and all SH-SY5Y samples in nDEP; a group whose runs are all below SH-SY5Y's ranks first even with a smaller ratio. Read both: the **ratio** says how different the populations are on average, the **score** and the sample counts say whether one frequency would sort them.

## Reading it

- A high score with few samples is an estimate: two samples per group cannot show the real spread. Add biological replicates before relying on a pair.
- The best frequency sits between the first crossovers, where the force is still strong enough; check it with a short frequency sweep.
- Conditions matter: crossovers move with the medium conductivity and with how long cells have been in the DEP buffer. Compare groups measured under the same protocol.

The [Statistics report](../user-guide/statistics-report.md) lists every pair, best first, with the tests of their crossovers and parameters.
