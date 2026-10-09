# Group plots

A **replicate group** is one sample (a cell line, a treatment) measured several times. The group averages its replicates into **one spectrum** (mean ± SD of the points) and **one curve** (the model with the mean of the replicates' parameters), with mean ± SD of every parameter and of the crossovers. Open the **Group plots** tab: the graph then shows only the groups.

## The toolbar

| Button | Action |
|---|---|
| **+** | new group |
| **Statistics report** | report of all visible groups: separation of every pair, descriptive statistics, tests ([Statistics report](statistics-report.md)) |
| **Single points** | show or hide the [single points](#on-the-graph) of all groups |

To hide a group, use the eye in its row.

## A group's row

Eye, name, **one colour** (spectrum and curve), point shape and size, line type and width, and the arrow that expands the group. Only the style can be changed: everything else is calculated from the replicates.

Expanded:

### Adding replicates and the buttons

**Add a replicate…** lists the curves that are [linked to a scatter](curve-plots.md#links) (as "curve / scatter"). A replicate is always such a pair: the scatter gives the data points, the curve the parameters. Link curves and scatters first, in Curve plots.

The buttons on the right: *save as OpenDEP file* (`.odfit` with replicates, curves and results, or the mean as `.odspec`), *save as table* (Excel with mean, parameters and replicates, or CSV with the mean), *delete the group* (its scatters and curves stay).

### Results

- **Samples**: the number of biological and technical replicates; on the right the model of the replicates' curves (*joint fit* when the group comes from one fit of all its spectra in OpenDEP Compute).
- **CO(f) first / second**: mean ± SD of the crossovers of the replicates' curves.
- **Parameter cards**, as in Curve plots: mean ± SD of each parameter, or the value alone when it is the same in all replicates (e.g. fixed in the fits). Hover over a value to see what it is based on.

Parameters are averaged only when all replicates use the same model; otherwise the group says so and shows none.

### Replicates

The table **Curve / Scatter / Sample No.** lists the replicates. **Sample No.** is the biological replicate (the suspension, the culture, the day): replicates with the **same** number are technical replicates of that sample. Edit it in the table. The button at the end of a row removes the replicate from the group.

How technical and biological replicates are averaged: [Replicates and averages](../concepts/replicates.md).

## On the graph

Each visible group draws its mean spectrum (points with the SD as error bars) and the curve of its mean parameters, in the group's colour. Frequencies measured only once in the whole group (e.g. an extra point near a crossover) are drawn as open markers: they have no SD. **Single points** in the toolbar hides them (saved with the project); the mean, the curve and the statistics do not change.

## Best separation

The card at the bottom of the panel shows the two visible groups that one frequency separates best: which group goes to pDEP and which to nDEP, at which **frequency**, the **separation score** (0 to 1), the **crossover ratio** and **ΔRe[CM]**. Hover over the card for the other pairs. Hide a group (eye) to leave it out.

What the numbers mean: [Separation of two populations](../concepts/separation.md).
