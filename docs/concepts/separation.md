# Separation of two populations

Two cell populations can be separated by DEP at a frequency where one is in **pDEP** (pulled to the electrodes) and the other in **nDEP** (pushed away). Such a frequency lies between their crossovers: above the first crossover of one population and below that of the other. The further apart their crossovers, and the less they vary from sample to sample, the cleaner the separation.

## What View calculates

For each visible group, from the crossovers of its samples (one per biological replicate):

- **Share in pDEP** at frequency f: the part of the population whose first crossover lies below f (and the second, if any, above f). Each sample's crossovers are smoothed over ±22 % (a log-normal of width 0.2 in ln f), so a few samples still give a smooth estimate.
- **Separation score** of two groups at f: the difference of their shares in pDEP. The **best frequency** is where the score is highest.

| Score | Meaning |
|---|---|
| 0 | the two groups behave the same at every frequency |
| 0.5 | at the best frequency, the share in pDEP differs by half the population |
| 1 | at the best frequency, one group is entirely in pDEP, the other entirely in nDEP |

Reported with it, as usual in DEP work:

- **Crossover ratio**: higher / lower mean first crossover. Above about 1.5 the crossovers are clearly apart; close to 1 they overlap.
- **ΔRe[CM]**: Re[CM] of the pDEP group minus that of the nDEP group at the best frequency, from the groups' mean-parameter curves. The two values in brackets should have opposite signs; the larger the difference, the stronger the cells are pulled apart.

## Reading it

- A high score with few samples is an estimate: two samples per group cannot show the real spread. Add biological replicates before relying on a pair.
- The best frequency sits between the crossovers; in practice choose one where ΔRe[CM] is still large, and check it with a short frequency sweep.
- Conditions matter: crossovers move with the medium conductivity and with how long cells have been in the DEP buffer. Compare groups measured under the same protocol.

The [Statistics report](../user-guide/statistics-report.md) lists every pair, best first, with the tests of their crossovers and parameters.
