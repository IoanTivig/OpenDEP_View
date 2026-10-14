# Replicates and averages

## Biological and technical replicates

- **Biological replicates** are independent samples: different suspensions, cultures or days. Their spread is the real variation of the sample, and their number is the **n** of the statistics.
- **Technical replicates** are repeated measurements of the same suspension. Their spread is the measurement's; they make each biological value more precise but do not add to n.

In a [group](../user-guide/group-plots.md) the **Sample No.** of a replicate is its biological replicate: replicates with the same number are technical replicates of it.

## How a group is averaged

The same two steps for the data points, the parameters and the crossovers:

1. **Technical replicates** of each sample are averaged first.
2. **The sample means** are averaged; the spread is that across samples (n = number of samples).

So a sample measured three times counts once, like a sample measured once.

| The group has | The spread shown is |
|---|---|
| several samples (with or without technical replicates) | the spread across samples, n = samples |
| one sample measured several times | the spread of the technical replicates, labelled *technical* |
| a single measurement | the measurement's own error |

**Data points** (Re[CM] at each frequency) are averaged as usual, mean ± SD: Re[CM] changes sign, so it has no log scale. **Crossovers and parameters** are averaged on the log scale, as described below.

## Matching frequencies

Spectra of different runs are rarely measured at exactly the same frequencies. Points closer than **1 %** in frequency are treated as the same frequency (their geometric mean is used). A frequency that only one run measured, e.g. an extra point near a crossover, is kept as a single point and drawn as an **open marker**: it has no SD.

## Crossovers and parameters: geometric mean ×/÷ geometric SD

Each replicate's curve gives its crossovers and parameters. The group shows, with the same two steps:

**geometric mean ×/÷ geometric SD**, e.g. *31.2 kHz ×/÷ 2.0*

- The **geometric mean** is the mean of the logarithms, taken back: for two samples at 16 and 93 kHz it is √(16 × 93) = 38.6 kHz, the point halfway between them on the logarithmic frequency axis of the graph (the ordinary mean, 54.5 kHz, is pulled towards the higher one).
- The **geometric SD** (GSD) is a factor: about 68 % of the samples lie between mean / GSD and mean × GSD (16–62 kHz for 31.2 ×/÷ 2.0), as mean ± SD does on a linear scale. ×/÷ 1.1 is a spread of about 10 %.
- Hover over a value to see what it is based on, with the **ordinary mean ± SD** for comparison with published values.
- A parameter with the same value in every curve (fixed in the fits) is shown alone, without a spread.

### Why the log scale

**The spread of crossovers and parameters is multiplicative.** The first crossover depends on the cell as a product and ratio of its properties, f ≈ σ<sub>medium</sub> / (2π r C<sub>membrane</sub>): a 20 % larger capacitance lowers it by the same factor at any frequency. Suspension ageing, cell size and membrane state all act this way, and multiplicative causes give **log-normal** data, skewed towards high values. For crossovers of single cells within a suspension this was shown by Prieto et al. (2012), who fitted DEP trapping curves with a log-normal distribution.

**OpenDEP's run-to-run data are log-normal too.** In the cell database (first crossovers of 4 to 17 runs per cell line), the raw values were clearly skewed in every group with 8 or more runs and failed the Shapiro-Wilk normality test (p 0.001–0.005; HEK at the limit, p = 0.05), while their logarithms passed in all groups (p 0.07–1.0). For BPEI-1 (11 runs) mean ± SD is 40 ± 34 kHz, which suggests 6–74 kHz although no run lies below 14 kHz; the geometric 31 kHz ×/÷ 2.0 (16–62 kHz) describes the runs.

**The group's curve then crosses where its crossover says.** The group's curve is the model with the averaged parameters (not the mean of the curves: averaging curves point by point would blur the crossover, while the mean-parameter curve stays a physical spectrum). Since the crossover is a product / ratio of parameters, the curve of the **geometric-mean** parameters crosses at the **geometric-mean** crossover (in the cell database within ±3 %). With ordinary means it does not: the curve of the mean parameters crossed up to 2× lower than the mean crossover shown.

How much the ordinary mean exceeds the geometric one depends on the spread: about 1 % for ×/÷ 1.15, 5 % for ×/÷ 1.35, 28 % for ×/÷ 2. With the small spreads of a few well-controlled runs the two hardly differ, which is why mean ± SD is usual in DEP papers; with many runs over time the difference shows.

### Linear scale: conductances that can be zero

**Membrane conductivity**, **nuclear envelope conductivity** and **surface conductance** stay on the linear scale (mean ± SD). An insulating layer can have practically zero conductance, and a fit then puts the value at its lower bound (e.g. 10⁻¹⁰ S/m); on a log scale such an "undetermined, about zero" value would weigh as much as a measured one. Any other quantity with a value of 0 or below also stays linear. The scale is decided in advance for each quantity, never from the test results.

Curves of different models are not averaged (a membrane permittivity of a single-shell fit and of a two-shell fit do not mean the same thing).

## Further reading

- J. L. Prieto, J. Lu, J. L. Nourse, L. A. Flanagan, A. P. Lee, Frequency discretization in dielectrophoretic assisted cell sorting arrays to isolate neural cells, *Lab Chip* 12 (2012) 2182, doi:10.1039/c2lc21184j. Crossover / trapping frequencies of a cell population are log-normal because they are a non-linear function of radius and membrane capacitance.
- E. Limpert, W. A. Stahel, Problems with using the normal distribution – and ways to improve quality and efficiency of data analysis, *PLoS One* 6 (2011) e21403, doi:10.1371/journal.pone.0021403. Multiplicative variation, log-normal data and the notation x̄\* ×/ s\* (geometric mean ×/÷ geometric SD).
- J. M. Bland, D. G. Altman, Transforming data, *BMJ* 312 (1996) 770, doi:10.1136/bmj.312.7033.770.
