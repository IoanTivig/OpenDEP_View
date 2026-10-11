# The window and projects

## The window

| Part | What it holds |
|---|---|
| **Top bar** | the project's name and file, **New project**, **Open project**, **Save**, **Help**, **Report bug** |
| **Graph** (left) | the curves and spectra; above it the choice between **Re[CM(f)]** and **DEP Force** and the graph size; under it zoom, [settings and image](graph.md), and how error bars are drawn |
| **Panel** (right) | the frequency range of the curves (f<sub>start</sub>, f<sub>stop</sub>) and three tabs |

The three tabs decide what the graph shows:

| Tab | Shows | Page |
|---|---|---|
| **Curve plots** | model curves (and their linked scatters) | [Curve plots](curve-plots.md) |
| **Scatter plots** | measured or simulated spectra | [Scatter plots](scatter-plots.md) |
| **Group plots** | one mean spectrum and one mean curve per replicate group | [Group plots](group-plots.md) |

Curve plots and Scatter plots are drawn together; Group plots shows only the groups, so the averages are not hidden among the replicates they come from.

Every item (curve, scatter, group) is a row with its eye (show / hide), name, colour and style. The arrow at the end of the row expands it: its settings, buttons and results.

## Projects

A project is **one file**, `<name>.odvproject`, made to be copied, backed up and sent to colleagues like any document. It holds the curves' parameters, the groups, the links, the graph settings and the tab in use, plus a copy of every spectrum (`.odspec`) and curve (`.odcurve`). It is a zip archive: any unzip tool shows the files inside.

- **Create new project** asks for the name and place of the project file. Files you load are **copied** into the project: your original files are never changed.
- **Save** (Ctrl+S) writes the project. The top bar shows when it was saved last. Closing the program or opening another project asks first if something was not saved.
- **Open project** (Ctrl+O) takes a project file. Opening a `.odvproject` file from outside (double-click, or dropping it on the command line) opens it as the project. The start screen lists the recent projects.
- Each save keeps the previous version as `<name>.odvproject.bak`, and an interrupted save never damages the project.
- If part of a project cannot be read (for example a damaged copy), the rest opens and a message lists what was left out.
- **Project folders** made by earlier versions (with a `project.json` inside) still open: choose their `project.json` in **Open project**. **Save** then writes them as one `.odvproject` file next to the folder, which is left untouched (delete it yourself once the file is saved).

## Files from outside

Besides the open buttons of each tab, OpenDEP files (`.odspec`, `.odcurve`, `.odfit`, and the older `.ods`, `.odc`) reach View in three ways. Each adds them to the open project, as **Open file** would:

| Way | How |
|---|---|
| **Send to View** in OpenDEP Compute | the button on Compute's Data, Fit and Export pages. The selected spectra, the current fit or the saved fits open here at once; Compute starts View if it is not running. |
| **Drag and drop** | drop files from the file explorer onto View's window |
| **Command line** | `"OpenDEP View.exe" file.odfit` (or `python main.py file.odfit`); also what a double-click on a file does when the installer has associated the file types with View |

Only one View runs per user: a second start with files hands them to the View that is already open and closes again. When no project is open, View asks for one and adds the files as soon as it is created or opened.

The two programs talk over a local channel of the computer (a named pipe on Windows, a socket file on Linux); nothing goes over the network.

## Keyboard

| Key | Action |
|---|---|
| Ctrl+N | new project |
| Ctrl+O | open project |
| Ctrl+S | save project |
| F1 | this guide, at the page of the tab in use |
| Ctrl+F (in the guide) | search the guide |

## Report bug

**Report bug** opens a short form for a problem; the last error message, the recent program output and, if you want, a screenshot go with it. When the program meets an unexpected error, the same window opens by itself with the error filled in.

- **Send to OpenDEP** sends the report to the OpenDEP team through the OpenDEP website. It needs a tester account (ask the team for one): the first time, sign in with your user name and password; the program then keeps a sign-in token for this computer, never your password (**Sign out** at the top of the form forgets it).
- **Save report** saves it in the `bug_reports/` folder of the program instead, on this computer only.
- The **Reports** tab lists the saved reports; **Sent** shows their number on the OpenDEP website. **Send selected** (Ctrl or Shift for several) or **Send all unsent** sends saved reports later, with their screenshots and output. The website never stores a report twice: one it already has (the same file, or the same text) is only confirmed with its number.
