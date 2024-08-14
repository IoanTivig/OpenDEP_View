# OpenDEP View

OpenDEP View is a visualization and spectra generation software for Dielectrophoresis (DEP) experiments. It allows users to view and generate DEP spectra based on specific parameters. The program currently supports the homogeneous particle model and single-shell model, with ongoing development for the two-shell model.

This software is part of the OpenDEP project, which includes three key programs:
1. [OpenDEP Compute](https://github.com/IoanTivig/OpenDEP) - for spectra fitting and data conversion.
2. [OpenDEP Control](https://github.com/IoanTivig/OpenDEP_Control) - for automation and control of DEP experiments.
3. [OpenDEP View](https://github.com/IoanTivig/OpenDEP_View) - for visualization of spectra and spectra generation based on parameters.

Published under the GNU GPL v3.0 license.

## Features
- **Spectra Visualization**: Easily visualize DEP spectra using the homogeneous particle model and single-shell model.
- **Spectra Generation**: Generate DEP spectra based on user-defined parameters.
- **Generation/Simulation of Synthetic Experimental Data**: Simulate synthetic experimental data for testing and analysis.
- **Cosmetization of Graphs**: Customize and format graphs to be publication-ready without needing additional software.
- **Compatibility with OpenDEP Compute Data**: Works with data exported from OpenDEP Compute (currently supports Excel exports).
- **Standalone Execution on Windows**: The software can now be run directly from the `.exe` file in the root of the program.

## Installation
1. Download the latest release from this repository.
2. Add the repository to your IDE (tested with PyCharm).
3. Install the necessary requirements from the `requirements.txt` file.
4. Run the `main.py` file to launch the application.

   Alternatively, for Windows users:
   - Run the software directly from the provided `.exe` file in the root of the program, without any other installation.

5. Enjoy exploring, generating, and customizing DEP spectra!


## Publications
If you use this software in your research, please cite the following paper:
1. [OpenDEP: An Open-Source Platform for Dielectrophoresis Spectra Acquisition and Analysis](https://pubs.acs.org/doi/10.1021/acsomega.3c06052)

Other papers published by our team using OpenDEP:
1. [Early differentiation of mesenchymal stem cells is reflected in their dielectrophoretic behavior](https://www.nature.com/articles/s41598-024-54350-z)
2. [Dielectrophoretic characterization of peroxidized retinal pigment epithelial cells as a model of age-related macular degeneration](https://bmcophthalmol.biomedcentral.com/articles/10.1186/s12886-024-03617-0)

## Other DEP Tools (not developed by OpenDEP)
1. [MyDEP](https://mydepsoftware.github.io/)

## Additional Information
- **Development Status**: OpenDEP View is still under active development, and bugs may occur. If you encounter any issues, please report them or contact the developer for assistance.

Thank you for using OpenDEP View. Your feedback and contributions are highly appreciated!
