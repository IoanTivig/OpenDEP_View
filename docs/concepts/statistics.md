# Statistical tests

The [Statistics report](../user-guide/statistics-report.md) compares groups by the **crossovers** and **model parameters** of their replicates' curves. One value per **biological replicate** (technical replicates averaged first); a group with a single suspension uses its technical replicates, marked *technical*: they show the measurement's spread, not the biological one.

## Scale: log for crossovers and parameters

Crossovers and fitted parameters of repeated runs are **log-normal**: their spread is multiplicative (see [Replicates and averages](replicates.md#why-the-log-scale)). So every quantity whose values are all above zero is analysed on the **log scale**:

- each group is summarised as **geometric mean ×/÷ geometric SD**, with the **95 % confidence interval** of the geometric mean (asymmetric, e.g. 31.2 kHz, 19.5–49.8);
- the normality test and Welch's t-test use the logarithms of the values.

Quantities with a value of 0 or below, and the conductances that can be zero (membrane, nuclear envelope, surface conductance), stay on the **linear scale**: mean ± SD and tests on the values. The scale is fixed for each quantity, for all groups together, before any test is run; choosing it after seeing the p values would bias them. The report also lists the **ordinary mean ± SD** of every quantity, to compare with published values.

## Normality: Shapiro-Wilk

Tests whether a group's values could come from a normal distribution (needs n ≥ 3), on the analysed scale: on the log scale it tests the logarithms, i.e. whether the values are log-normal. **p > 0.05**: normality is not rejected. With few values the test rarely rejects anything, so "normal" then means "no evidence against it".

## Comparing two groups

Both tests are always reported:

| Test | Assumes | Compares |
|---|---|---|
| **Welch's t-test** | normal data on the analysed scale; the two groups may have different SDs | the means (on the log scale: the geometric means) |
| **Mann-Whitney U test** | nothing about the distribution | the ranks (whether one group's values tend to be larger); the same on both scales |

**The test used** for the conclusion is Welch's t-test, unless Shapiro-Wilk rejects normality in either group; then Mann-Whitney U. With n < 3 normality cannot be tested and Welch's t-test is used (the report says so).

## Many pairs: Holm correction

With several groups, many pairs are tested, and some will look significant by chance. The p values of each quantity (e.g. the first crossover) are corrected over all pairs with the **Holm** method: the smallest p is multiplied by the number of pairs, the next by one less, and so on. It controls the chance of any false positive and is less strict than Bonferroni.

Significance (Holm-corrected): \* p < 0.05, \*\* p < 0.01, \*\*\* p < 0.001, *ns* not significant.

## Effect size

Effect sizes say how large a difference is, which p values do not.

- **Ratio of the geometric means** (log scale), first group / second, with its 95 % confidence interval, e.g. *0.22× (0.07–0.71)*: the first group's crossover is about a fifth of the second's, and the interval does not include 1. For the first crossover it is the inverse of the **crossover ratio** of the [separation](separation.md). On the linear scale, the **difference** of the means with its interval.
- **Hedges' g**: the difference of the means in units of the pooled SD (on the analysed scale), corrected for small samples. About 0.2 small, 0.5 medium, 0.8 large; DEP parameters of different cell lines often differ by g > 2. Sign: first group of the pair minus the second.

## Small samples

| n per group | Note |
|---|---|
| 2 | normality cannot be tested; Mann-Whitney cannot reach p < 0.33 |
| 3 | Mann-Whitney cannot reach p < 0.1 (two-sided) |
| 5 or more | the tests start to have useful power |

A non-significant result with few samples does not mean the groups are the same: look at the effect size and the separation, and add biological replicates.

## In a paper

A methods sentence that matches the report: *"Crossover frequencies and fitted parameters were log-normally distributed (Shapiro-Wilk) and are given as geometric mean ×/÷ geometric SD; groups were compared on log-transformed values with Welch's t-test (Mann-Whitney U when normality was rejected), Holm-corrected over all pairs, with the ratio of geometric means and its 95 % confidence interval as effect size. Membrane conductivities were analysed on the linear scale."*

## Further reading

- E. Limpert, W. A. Stahel, *PLoS One* 6 (2011) e21403: log-normal data and the ×/÷ notation.
- J. M. Bland, D. G. Altman, Transforming data, *BMJ* 312 (1996) 770; The use of transformation when comparing two means, *BMJ* 312 (1996) 1153: tests on log values, ratio of geometric means.
- J. L. Prieto et al., *Lab Chip* 12 (2012) 2182: log-normal crossover frequencies in DEP.
- S. S. Shapiro, M. B. Wilk, *Biometrika* 52 (1965) 591.
- B. L. Welch, *Biometrika* 34 (1947) 28.
- H. B. Mann, D. R. Whitney, *Ann. Math. Stat.* 18 (1947) 50.
- S. Holm, *Scand. J. Stat.* 6 (1979) 65.
- L. V. Hedges, *J. Educ. Stat.* 6 (1981) 107.
