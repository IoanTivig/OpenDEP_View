# Quick start

A first graph: a model curve, a measured spectrum next to it, and an image of the graph.

## 1. Create a project

On the start screen click **Create new project** and give the project file a name and place (for example `Cell lines.odvproject`). The project keeps your curves, scatters, groups and graph settings; **Save** (Ctrl+S) writes them. Next time, open it from **Recent projects** or with **Open project**. See [The window and projects](user-guide/interface.md).

## 2. Draw a model curve

1. The **Curve plots** tab is open. Click **+** (new curve) in its toolbar.
2. Expand the curve (arrow on the right of its row) and choose the model, e.g. **Single-shell**.
3. Type the parameters: buffer conductivity, membrane permittivity, particle radius… The curve and the crossover frequencies (CO(f) first / second) update as you type.
4. Set the frequency range of the curves with **f<sub>start</sub>** and **f<sub>stop</sub>** above the tabs.

Details: [Curve plots](user-guide/curve-plots.md).

## 3. Add a measured spectrum

1. Open the **Scatter plots** tab.
2. Click the load button and choose a spectrum: an OpenDEP Spectrum (`.odspec`) from OpenDEP Control or Compute, or an Excel table (frequency, Re[CM], error).
3. The points appear on the graph with their error bars. Their colour, shape and size are set in the scatter's row.

To show which curve belongs to which measurement, link them: in the curve, choose the scatter under **Linked to**. Details: [Scatter plots](user-guide/scatter-plots.md).

## 4. Save an image

1. Format the graph with the **settings** button (gear) under the graph: fonts, ticks, grid, legend.
2. Click the **image** button under the graph, choose name, folder, format (PNG, TIFF, JPG) and resolution, and save.

Details: [The graph and images](user-guide/graph.md).

## Next steps

- Several measurements of the same sample? Average them in [Group plots](user-guide/group-plots.md).
- Two cell lines to separate? See [Separation of two populations](concepts/separation.md) and the [Statistics report](user-guide/statistics-report.md).
