# Statistical tests

The [Statistics report](../user-guide/statistics-report.md) compares groups by the **crossovers** and **model parameters** of their replicates' curves. One value per **biological replicate** (technical replicates averaged first); a group with a single suspension uses its technical replicates, marked *technical*: they show the measurement's spread, not the biological one.

## Normality: Shapiro-Wilk

Tests whether a group's values could come from a normal distribution (needs n ≥ 3). **p > 0.05**: normality is not rejected. With few values the test rarely rejects anything, so "normal" then means "no evidence against it".

## Comparing two groups

Both tests are always reported:

| Test | Assumes | Compares |
|---|---|---|
| **Welch's t-test** | normal data; the two groups may have different SDs | the means |
| **Mann-Whitney U test** | nothing about the distribution | the ranks (whether one group's values tend to be larger) |

**The test used** for the conclusion is Welch's t-test, unless Shapiro-Wilk rejects normality in either group; then Mann-Whitney U. With n < 3 normality cannot be tested and Welch's t-test is used (the report says so).

## Many pairs: Holm correction

With several groups, many pairs are tested, and some will look significant by chance. The p values of each quantity (e.g. the first crossover) are corrected over all pairs with the **Holm** method: the smallest p is multiplied by the number of pairs, the next by one less, and so on. It controls the chance of any false positive and is less strict than Bonferroni.

Significance (Holm-corrected): \* p < 0.05, \*\* p < 0.01, \*\*\* p < 0.001, *ns* not significant.

## Effect size: Hedges' g

The difference of the means in units of the pooled SD, corrected for small samples. It says how large a difference is, which p values do not: about 0.2 small, 0.5 medium, 0.8 large, and DEP parameters of different cell lines often differ by g > 2. Sign: first group of the pair minus the second.

## Small samples

| n per group | Note |
|---|---|
| 2 | normality cannot be tested; Mann-Whitney cannot reach p < 0.33 |
| 3 | Mann-Whitney cannot reach p < 0.1 (two-sided) |
| 5 or more | the tests start to have useful power |

A non-significant result with few samples does not mean the groups are the same: look at the effect size and the separation, and add biological replicates.

## Further reading

- S. S. Shapiro, M. B. Wilk, *Biometrika* 52 (1965) 591.
- B. L. Welch, *Biometrika* 34 (1947) 28.
- H. B. Mann, D. R. Whitney, *Ann. Math. Stat.* 18 (1947) 50.
- S. Holm, *Scand. J. Stat.* 6 (1979) 65.
- L. V. Hedges, *J. Educ. Stat.* 6 (1981) 107.
