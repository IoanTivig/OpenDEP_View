# Installation

OpenDEP View runs on **Windows** and **Linux** (and macOS from source). It needs no internet connection.

## Windows: the installer

1. Download `OpenDEP_View_Setup_<version>.exe` from the **Releases** page of the [OpenDEP View repository](https://github.com/IoanTivig/OpenDEP_View).
2. Run it. It installs the program for the current user (no administrator rights needed), adds it to the Start menu and, if you tick it, to the desktop.
3. Uninstall from Windows Settings → Apps. Your projects and files are not touched.

The installer also registers the suite's file types, so a double-click opens them in View:

| File | Double-click |
|---|---|
| `.odvproject` OpenDEP View project | opens the project |
| `.odspec` spectrum, `.odcurve` model curve, `.odfit` fit | added to the open project (a View that is already running gets them) |

The older `.ods` / `.odc` names are not registered, because Windows uses them for OpenDocument spreadsheets and Office files: open those with **Open file** in View.

From the command line (e.g. for several computers): `OpenDEP_View_Setup_<version>.exe /VERYSILENT` installs without questions; add `/ALLUSERS` to install for all users (needs administrator rights).

## From source (Windows, Linux, macOS)

You need **Python 3.12**.

```
git clone https://github.com/IoanTivig/OpenDEP_View.git
cd OpenDEP_View
python -m venv venv
```

Activate the environment and install the requirements:

| System | Activate | Then |
|---|---|---|
| Windows | `venv\Scripts\activate` | `pip install -r requirements.txt` |
| Linux, macOS | `source venv/bin/activate` | `pip install -r requirements.txt` |

Start the program **from its own folder** (it finds `ui/` and `docs/` there):

```
python main.py
```

### Linux notes

- PyQt6 comes with its own Qt. On some distributions Qt needs one system library more: if the program stops with *"could not load the Qt platform plugin xcb"*, install `libxcb-cursor0` (Debian, Ubuntu: `sudo apt install libxcb-cursor0`).
- Fonts: the program asks for *Segoe UI* and falls back to the system font (DejaVu Sans, Liberation Sans) when it is missing. Everything works; only the letters look slightly different.

## What is installed

| Package | Used for |
|---|---|
| PyQt6 | the window |
| numpy, matplotlib | the models and the graph |
| scipy | the statistical tests of the [Statistics report](user-guide/statistics-report.md) |
| openpyxl | Excel files (also read and written by LibreOffice) |
| pillow | saving images (resolution, grayscale) |
| colorednoise | pink noise in simulated data |

## Next

[Quick start](quickstart.md): a first graph in a few minutes.
