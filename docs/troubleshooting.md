# Troubleshooting

## Starting the program

| Problem | Cause and fix |
|---|---|
| The program closes at once, or says a `.ui` file is missing | It was not started from its own folder. Start the installed program from the Start menu, or from source run `python main.py` in the folder that holds `ui/` and `docs/`. |
| Help shows "The user guide was not found" | The `docs/` folder is missing next to the program: copy it from the release. |
| Linux: *could not load the Qt platform plugin "xcb"* | Install `libxcb-cursor0` (`sudo apt install libxcb-cursor0`). |
| `ModuleNotFoundError` (from source) | The requirements are not installed in the environment in use: activate the venv, then `pip install -r requirements.txt`. |

## Curves

| Problem | Cause and fix |
|---|---|
| A field does not accept a number | Use a point as the decimal separator (`0.02`, not `0,02`); `1e-6` style is fine. |
| CO(f) shows *none* | The curve does not cross zero between f<sub>start</sub> and f<sub>stop</sub>: widen the range, or check the parameters (e.g. buffer conductivity in S/m, not µS/cm). |
| The DEP force is tiny or huge | ∇E² and the particle radius set its size; it is meaningful only with the real field gradient of your chip. |

## Scatters and groups

| Problem | Cause and fix |
|---|---|
| A scatter from OpenDEP Compute lies far from its curve | It was a relative spectrum: open the `.odfit` (it holds the scale) instead of the loose spectrum. |
| **Add a replicate…** is empty | Only curves linked to a scatter can be added: link them under **Linked to** in Curve plots. |
| A group shows no parameters | Its replicates' curves use different models, or no replicate has a curve. |
| SD labelled *technical* | All replicates have the same Sample No.: if they are different suspensions, give each its own number. |
| Best separation says it needs two groups | At least two visible groups need curves with a first crossover. |

## Send to View (from OpenDEP Compute)

| Problem | Cause and fix |
|---|---|
| Compute asks for View's folder | View is not installed next to Compute. Show its folder once (the one with the program, or with `main.py` and `ui/`); Compute remembers it. |
| The files arrive, but View asks for a project | No project was open in View: create or open one; the files are added then. |
| View stays behind Compute's window | Some window managers do not let a program come to the front by itself: click View in the taskbar. |

## Reports and images

| Problem | Cause and fix |
|---|---|
| The report or image cannot be written | The file is open in another program (PDF viewer, Excel), or the folder is read-only. Close it or choose another folder. |
| The statistics report needs scipy | From source: `pip install -r requirements.txt` in the program's environment. |

## Reporting a problem

Click **Report bug** in the top bar: describe what you did, what you expected and what happened. The report is saved in `bug_reports/` with the last error and the recent program output; send it to the developers or attach it to an issue on GitHub.
