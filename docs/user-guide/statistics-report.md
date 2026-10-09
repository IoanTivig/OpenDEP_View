# Statistics report

**Statistics report** (Group plots toolbar) compares the visible replicate groups and writes the result as a **PDF** (to read and share) and / or an **Excel workbook** (`.xlsx`, also opened by LibreOffice Calc and other office programs), to check or reuse the numbers. Hide a group (eye) to leave it out; at least two groups are needed.

## The PDF

1. **Figure**: the mean spectrum and mean curve of every group, with the best separation frequency marked.
2. **Groups**: model, biological and technical replicates. Values that are the same in every sample (e.g. fixed in the fits) are listed here once and not tested.
3. **Separation of the pairs**, best first: best frequency, separation score, crossover ratio, ΔRe[CM], and how many quantities differ significantly.
4. **Descriptive statistics** of each group: n, mean, SD, SEM, CV, median, range, and the Shapiro-Wilk test of normality.
5. **Pairwise tests**, pair by pair in the order of the ranking: Welch's t-test and the Mann-Whitney U test for each crossover and parameter, the test used, the Holm-corrected p value (significant ones highlighted, with stars) and the effect size (Hedges' g).
6. **Methods**: what was calculated, in words, ready to adapt for a paper.

## The Excel workbook

| Sheet | Holds |
|---|---|
| Summary | groups, values that were not tested, methods |
| Separation | the ranking of the pairs |
| Descriptive | one row per group and quantity |
| Pairwise tests | one row per pair and quantity |
| Sample values | every value used, one per sample: to redo the analysis in another program |

## What is compared

The **crossovers** and the **model parameters** of the replicates' curves, one value per biological replicate (technical replicates averaged first). Parameters are compared only between groups that use the same model. The scatter points themselves are not tested: their errors already are the spread of the replicates.

Which test is used when, and how to read the results: [Statistical tests](../concepts/statistics.md).

## Few replicates

With three samples per group the tests have little power: the Mann-Whitney test cannot go below p = 0.1, and normality can hardly be judged. Read the p values together with the effect sizes and the separation, and add biological replicates where a decision depends on it.
