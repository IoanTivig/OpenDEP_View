# OpenDEP View

**Views, simulates and compares dielectrophoresis (DEP) spectra.** OpenDEP View draws Clausius-Mossotti (CM) curves from the dielectric models of cells and particles, shows measured spectra next to them, averages replicate measurements into groups, ranks how well two cell populations can be separated, and makes publication-ready graphs and statistics reports.

It is part of the **OpenDEP** suite, free and open-source software for DEP research:

| Program | What it does |
|---|---|
| [OpenDEP Control](https://github.com/IoanTivig/OpenDEP_Control) | runs the experiments on a Raspberry Pi (camera, function generator, pump) and measures DEP spectra |
| [OpenDEP Compute](https://github.com/IoanTivig/OpenDEP_Compute) | converts image sets into spectra, fits spectra, reports cell parameters |
| **OpenDEP View** | compares spectra and model curves, averages replicates, simulates data, publication graphs |
## Features

- **Model curves:** Re[CM], Im[CM] and the DEP force of a homogeneous particle and of single-, two-, three- and four-shell cells, from parameters you type in; the crossover frequencies are calculated exactly.
- **Measured spectra:** opens the files of OpenDEP Control and OpenDEP Compute (`.odspec`, `.odcurve`, `.odfit`) and Excel tables, or simulates noisy data from a curve (white or pink noise).
- **Links:** a curve linked to the scatter it was fitted to; both travel together.
- **Replicate groups:** biological and technical replicates averaged into one spectrum and one curve per group, with mean ± SD of every parameter and crossover.
- **Separation:** ranks every pair of groups by how well one frequency splits them into a pDEP and an nDEP population.
- **Statistics report:** normality and pairwise tests (Welch t, Mann-Whitney U) of the crossovers and parameters, as PDF and Excel.
- **Publication graphs:** fonts, ticks, grid, legend and frame adjustable; images at the size and resolution a journal asks for.
- **Projects** as single `.odvproject` files, easy to send to a colleague; spectra and fits arrive directly from OpenDEP Compute (**Send to View**).
- **User guide** inside the program (**F1**) and a **Report bug** form.

## Installation

**Windows:** download `OpenDEP_View_Setup_<version>.exe` from the [Releases](https://github.com/IoanTivig/OpenDEP_View/releases) page and run it (no administrator rights needed). It registers the suite's files, so a double-click opens a project or adds a spectrum, curve or fit.

**From the source code** (Windows, Linux, macOS; Python 3.12):

```
git clone https://github.com/IoanTivig/OpenDEP_View
cd OpenDEP_View
python -m venv venv
venv/bin/python -m pip install -r requirements.txt        (Windows: venv\Scripts\python)
venv/bin/python main.py
```

Start it from its own folder. Details, including notes for Linux: [Installation](docs/installation.md). Then the [Quick start](docs/quickstart.md): a first graph in a few minutes.

## Documentation

The user guide is in [docs/](docs/index.md) and inside the program (F1): [the window and projects](docs/user-guide/interface.md), [curve plots](docs/user-guide/curve-plots.md), [scatter plots](docs/user-guide/scatter-plots.md), [group plots](docs/user-guide/group-plots.md), the [statistics report](docs/user-guide/statistics-report.md), [the graph and images](docs/user-guide/graph.md), [files](docs/user-guide/files.md), and the concepts: [CM factor and models](docs/concepts/cm-factor-and-models.md), [replicates and averages](docs/concepts/replicates.md), [separation of two populations](docs/concepts/separation.md), [statistical tests](docs/concepts/statistics.md).

## Earlier version

OpenDEP View 1.x (PyQt5) stays available as the branch [`v1`](https://github.com/IoanTivig/OpenDEP_View/tree/v1) of this repository. Version 2 opens the same Excel spectra and the Excel exports of OpenDEP Compute 1.x.

## Citation

If you use OpenDEP in your research, please cite:

> Tivig I., et al. *OpenDEP: An Open-Source Platform for Dielectrophoresis Spectra Acquisition and Analysis.* ACS Omega 8 (2023) 38715–38722. [doi:10.1021/acsomega.3c06052](https://pubs.acs.org/doi/10.1021/acsomega.3c06052)

For single-cell measurements (dielectrophoresis and optical tweezers on the same cell), please also cite:

> Gherghinoiu F., Savopol T., Tivig I., Moisescu M.G. *All-in-One Method for Iterative Single-Cell Dielectrophoretic and Optical Characterization: Advancing the OpenDEP Platform.* ACS Omega 10 (2025) 44333–44343. [doi:10.1021/acsomega.5c06195](https://pubs.acs.org/doi/10.1021/acsomega.5c06195)

Work using OpenDEP:

- [Early differentiation of mesenchymal stem cells is reflected in their dielectrophoretic behavior](https://www.nature.com/articles/s41598-024-54350-z), *Scientific Reports* (2024)
- [Dielectrophoretic characterization of peroxidized retinal pigment epithelial cells as a model of age-related macular degeneration](https://bmcophthalmol.biomedcentral.com/articles/10.1186/s12886-024-03617-0), *BMC Ophthalmology* (2024)

## Other DEP tools

- [MyDEP](https://mydepsoftware.github.io/) (not developed by OpenDEP)

## License

GNU General Public License v3.0 (see [LICENSE](LICENSE)).
