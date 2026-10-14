# Curve plots

A curve is the Re[CM] spectrum (or the DEP force) of one dielectric model with one set of parameters. Curves are calculated, not measured: use them to see what a cell with given properties would do, or to show the fit of a measured spectrum.

## The toolbar

| Button | Action |
|---|---|
| **+** | new curve (single-shell, typical cell values) |
| open file | load a curve: OpenDEP Curve (`.odcurve`, also the older `.odc`) or OpenDEP Fit (`.odfit`, with its scatters) |
| open Excel | load a fitted curve exported by the older OpenDEP Compute (Excel) |
| **Sort** | order of the list: newest first (default), oldest first, name (A–Z), 1st crossover, 2nd crossover (low to high), model |
| **Curves Visibility** | show or hide all curves |

The sort order is saved with the project. Names sort with their numbers as numbers (*Sample 2* before *Sample 10*); curves without the crossover go to the end, and equal values are ordered by name. New curves take their place in the order. A curve you are editing stays where it is until you click outside the list.

## A curve's row

Eye (show / hide), name, colour, line type, line width, and the arrow that expands the curve.

Expanded, from top to bottom:

1. **Linked to**: the scatter this curve belongs to (see [Links](#links)).
2. **Model** and the curve's buttons: *simulate data* (noisy scatter from this curve, see [Scatter plots](scatter-plots.md#simulated-data)), *duplicate*, *save*, *delete*.
3. **Parameters**, in cards: Buffer, Cytoplasm (*Particle* in the homogeneous model), Other, Shell dimensions, Membrane, Cell wall, Nuclear envelope, Nucleoplasm. Only the cards of the chosen model are shown.
4. **CO(f) first / second**: the crossover frequencies, calculated (light fields: results, not entries).

## Models and parameters

| Model | Layers |
|---|---|
| Homogeneous | one particle (with a surface conductance) |
| Single-shell | cytoplasm + membrane |
| Two-shell | cytoplasm + membrane + cell wall |
| Three-shell | cytoplasm + membrane + nucleus (nuclear envelope, nucleoplasm) |
| Four-shell | cytoplasm + membrane + cell wall + nucleus |

| Parameter | Unit |
|---|---|
| Permittivity | relative (ε<sub>0</sub> = 1), e.g. 78 for the buffer |
| Conductivity | S/m (200 µS/cm = 0.02 S/m) |
| Particle radius, nucleus radius | µm |
| Membrane, wall and envelope thickness | nm |
| Surface conductance (homogeneous) | nS |
| ∇E² | V²/m³ (only scales the DEP force) |

Numbers are typed with a **point** as decimal separator; `1e-6` style is accepted. A field shows a rounded value; hover over it for the exact one.

What the models mean: [CM factor and models](../concepts/cm-factor-and-models.md).

## Crossover frequencies

**First** is where Re[CM] goes from negative to positive (nDEP → pDEP), **second** where it falls back to negative. They are found on the curve and then refined on the model, so they do not depend on how many points the curve has. *none*: the curve does not cross zero in the frequency range.

## Links

A curve can be linked to **one scatter**: the spectrum it was fitted to, or the measurement it describes. Choose it under **Linked to**.

- Hiding the curve also hides its scatter.
- Saving the curve can write both together as an **OpenDEP Fit** (`.odfit`), which OpenDEP Compute and View both open.
- Only linked curves can be added to a [replicate group](group-plots.md): the curve gives the group its parameters, the scatter its data points.

Under the link the program says which group the scatter is in, and whether the curve comes from a fit in OpenDEP Compute (*Fitted in OpenDEP Compute*) or was changed since (*Edited after the fit*: the fit's results are then no longer saved with it).

## Frequency range and graph content

f<sub>start</sub> and f<sub>stop</sub> above the tabs set the frequency range of all curves. **Re[CM(f)]** / **DEP Force** above the graph chooses what is drawn: the force uses the particle radius and ∇E².
