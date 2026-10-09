# Replicates and averages

## Biological and technical replicates

- **Biological replicates** are independent samples: different suspensions, cultures or days. Their spread is the real variation of the sample, and their number is the **n** of the statistics.
- **Technical replicates** are repeated measurements of the same suspension. Their spread is the measurement's; they make each biological value more precise but do not add to n.

In a [group](../user-guide/group-plots.md) the **Sample No.** of a replicate is its biological replicate: replicates with the same number are technical replicates of it.

## How a group is averaged

The same two steps for the data points, the parameters and the crossovers:

1. **Technical replicates** of each sample are averaged first.
2. **The sample means** are averaged; the **SD** is the spread across samples (n = number of samples).

So a sample measured three times counts once, like a sample measured once.

| The group has | The SD shown is |
|---|---|
| several samples (with or without technical replicates) | the SD across samples, n = samples |
| one sample measured several times | the SD of the technical replicates, labelled *technical SD* |
| a single measurement | the measurement's own error |

## Matching frequencies

Spectra of different runs are rarely measured at exactly the same frequencies. Points closer than **1 %** in frequency are treated as the same frequency (their geometric mean is used). A frequency that only one run measured, e.g. an extra point near a crossover, is kept as a single point and drawn as an **open marker**: it has no SD.

## Parameters and crossovers

Each replicate's curve gives its parameters; the group shows mean ± SD of each with the same two steps. A parameter with the same value in every curve (fixed in the fits) is shown as *the same in all* instead of a meaningless SD of zero.

The group's curve is the model with the **mean parameters**, not the mean of the curves: averaging curves point by point would blur the crossover, while the mean-parameter curve stays a physical spectrum.

Curves of different models are not averaged (a membrane permittivity of a single-shell fit and of a two-shell fit do not mean the same thing).
