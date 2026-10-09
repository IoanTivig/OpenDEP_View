# Files

The OpenDEP programs share three file types. They are JSON text: readable in any text editor and by other programs.

| File | Holds | Written by | Opened by |
|---|---|---|---|
| **OpenDEP Spectrum** `.odspec` | one spectrum: frequencies, values, errors, and the measurement's details | Control, Compute, View | Compute, View |
| **OpenDEP Curve** `.odcurve` | one model curve: model and parameters | Compute, View | Compute, View |
| **OpenDEP Fit** `.odfit` | spectra together with their curve: a fit, or a replicate group | Compute, View | Compute, View |

The older names `.ods` (spectrum) and `.odc` (curve) still open.

## OpenDEP Fit

An `.odfit` keeps what belongs together:

- **the spectra** (one or several) and **the curve**, with the link between them;
- for each spectrum its **scale** (OpenDEP Compute fits relative spectra by scaling them to the model) and its **biological replicate**;
- the **fit** from OpenDEP Compute: settings and results (R², errors). When the curve is changed in View, this block is dropped (the values no longer come from that fit);
- for a group saved from View: its style, the averaged spectrum, the results (mean ± SD of parameters and crossovers) and each replicate's own curve.

Opened in View: one spectrum becomes a scatter linked to its curve; several spectra become a [replicate group](group-plots.md). Spectra are converted to CM factor (divided by their scale).

Files also come straight from OpenDEP Compute (**Send to View**), by drag and drop, or on the command line: see [Files from outside](interface.md#files-from-outside).

## Other formats

| Format | Read | Written |
|---|---|---|
| Excel `.xlsx` | spectra (frequency, Re[CM], error in columns A to C); fitted curves of the older OpenDEP Compute | scatters; groups (mean, parameters, replicates); [statistics report](statistics-report.md) |
| CSV `.csv` | – | a group's mean spectrum |
| PDF | – | [statistics report](statistics-report.md) |
| PNG, TIFF, JPG | – | [images of the graph](graph.md) |

Excel files are written in the standard `.xlsx` format, which LibreOffice Calc and other office programs open as well.

## The project file

See [The window and projects](interface.md#projects): one `.odvproject` file (a zip archive) with `project.json`, plus a copy of every spectrum (`scatters/*.odspec`) and curve (`curves/*.odcurve`). Project folders of earlier versions open and are saved as a file.
