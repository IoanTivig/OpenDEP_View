# Scatter plots

A scatter is a DEP spectrum as points: frequency, Re[CM] (the CM factor) and its error. It comes from a measurement (OpenDEP Control, OpenDEP Compute, Excel) or is simulated from a curve.

## The toolbar

| Button | Action |
|---|---|
| **+** | new scatter with five example points (overwrite them in its table) |
| open file | load a spectrum: OpenDEP Spectrum (`.odspec`, also the older `.ods`) or OpenDEP Fit (`.odfit`) |
| open Excel | load an Excel table (see below) |
| **Scatter Visibility** | show or hide all scatters |

**Excel tables**: first sheet, row 1 is a header, then one point per row: column A frequency (Hz), B Re[CM], C error (empty = 0). Files exported by View have this form.

## A scatter's row

Eye, name, colour, point shape, point size; expanded:

- **Add Frequency** / **Remove Frequency** (the selected row) and the scatter's buttons: *duplicate*, *save* (`.odspec`), *save as Excel*, *delete*.
- **The points table**: frequency (Hz), Re[CM(f)] and its error. Edit a cell to change a point; the graph follows.

Values are CM factors. Spectra that OpenDEP Compute scaled to a model (an `.odfit` with a scale factor) are divided by the scale when they are loaded, so all scatters in View are on the same Re[CM] axis; the original values stay in the file.

Measurements from OpenDEP Control or Compute carry more than the three columns (e.g. per-point quality, the experiment's settings). View keeps that information and writes it back when it saves the scatter; if you add or remove points, the per-point lists follow.

## Error bars

The two buttons at the bottom right of the graph draw the errors as **bars** or as a shaded **area**.

## Simulated data

The *simulate data* button of a **curve** opens a window that makes a noisy scatter from that curve, e.g. to test a fit or to show what a measurement could look like:

- **Frequencies**: a number of log-spaced points between two frequencies, or a list you type.
- **Error bars**: random SDs between a minimum and a maximum, or none.
- **Noise**: additive white Gaussian, speckle (proportional to the value), pink, Poisson, or frequency-dependent; with its SD or scale.

**Generate scatter** adds it as a new scatter.
