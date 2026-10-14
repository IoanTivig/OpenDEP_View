# OpenDEP View

**Views, simulates and compares dielectrophoresis (DEP) spectra.** OpenDEP View draws Clausius-Mossotti (CM) curves from the dielectric models of cells and particles, shows measured spectra next to them, averages replicate measurements into groups, ranks how well two cell populations can be separated, and makes publication-ready graphs and reports. It is part of the OpenDEP suite, with [OpenDEP Control](https://github.com/IoanTivig/OpenDEP_Control) (runs the experiments) and [OpenDEP Compute](https://github.com/IoanTivig/OpenDEP_Compute) (converts images into spectra and fits them).

## What it does

- **Model curves.** Re[CM] and the DEP force of a homogeneous particle and of single-, two-, three- and four-shell cells, from parameters you type in. The crossover frequencies are calculated exactly.
- **Measured spectra (scatters).** Opens the files of OpenDEP Control and OpenDEP Compute and Excel tables, or simulates noisy data from a curve.
- **Links.** A curve can be linked to the scatter it was fitted to; both then travel together (`.odfit` files).
- **Replicate groups.** Biological and technical replicates are averaged into one spectrum and one curve per group, with the geometric mean ×/÷ geometric SD of every parameter and crossover (they are log-normal), so each group's curve crosses where its crossover says.
- **Separation.** Ranks every pair of groups by how well one frequency splits them into a pDEP and an nDEP population.
- **Statistics report.** Normality and pairwise tests of the groups, as PDF and Excel.
- **Graphs.** Fonts, ticks, grid, legend and frame are adjustable; images are saved at the size and resolution a journal asks for.

## Where to start

| I want to… | Read |
|---|---|
| install and start the program | [Installation](installation.md) |
| make a first graph | [Quick start](quickstart.md) |
| find my way around, work with projects | [The window and projects](user-guide/interface.md) |
| draw model curves | [Curve plots](user-guide/curve-plots.md) |
| show measured spectra, simulate data | [Scatter plots](user-guide/scatter-plots.md) |
| average replicates, compare samples | [Group plots](user-guide/group-plots.md), [Statistics report](user-guide/statistics-report.md) |
| format the graph and save an image | [The graph and images](user-guide/graph.md) |
| know which files it reads and writes | [Files](user-guide/files.md) |
| understand the models and the numbers | [CM factor and models](concepts/cm-factor-and-models.md), [Replicates and averages](concepts/replicates.md), [Separation of two populations](concepts/separation.md), [Statistical tests](concepts/statistics.md) |
| fix a problem | [Troubleshooting](troubleshooting.md) |

## Help inside the program

Press **F1** or click **Help** in the top bar. The guide opens at the page of the tab you are working in. Hover over a field or button for a short explanation (tooltip). **Report bug** in the top bar sends a description of a problem to the OpenDEP team (or saves it), with the last error attached.

## Citation

If you use OpenDEP View in your research, please cite: [OpenDEP: An Open-Source Platform for Dielectrophoresis Spectra Acquisition and Analysis](https://pubs.acs.org/doi/10.1021/acsomega.3c06052), *ACS Omega* (2023). For single-cell measurements, also: [All-in-One Method for Iterative Single-Cell Dielectrophoretic and Optical Characterization: Advancing the OpenDEP Platform](https://pubs.acs.org/doi/10.1021/acsomega.5c06195), *ACS Omega* (2025).

## License

GNU General Public License v3.0, like the rest of the OpenDEP suite.
