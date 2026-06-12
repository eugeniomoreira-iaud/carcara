# Phase 10 — Visualization (`viz/*` + 4 chart components)

## Goal

Generate publication-quality charts from PostGIS-derived data, all the way
from inside Grasshopper. Charts are rendered via `matplotlib` and emitted
as either an in-memory `PIL.Image` or a saved PNG / SVG file, depending on
what the legacy expects.

Components delivered (all subcategory **04.Dataviz**):

| Component         | Module               | Notes                                  |
|-------------------|----------------------|----------------------------------------|
| `CRC_Histogram`   | `viz/histogram.py`   | matplotlib chart                       |
| `CRC_ScatterPlot` | `viz/scatter.py`     | matplotlib chart                       |
| `CRC_LinePlot`    | `viz/lineplot.py`    | matplotlib chart                       |
| `CRC_Heatmap`     | `viz/heatmap.py`     | matplotlib chart                       |
| `CRC_CurveDisplay`| `geometry/wkt.py`    | **Rhino-viewport preview** (moved from old Phase 07) — different route from the matplotlib charts: a custom display/preview component, not a file export |

> `CRC_CurveDisplay` is 04.Dataviz but is a Rhino viewport preview, not a matplotlib
> render. It likely overrides `DrawViewportWires` (custom color/thickness). Confirm the
> legacy UI behavior (`carcara_CurveDisplay_r02.ghuser`) before building; its display code
> is Rhino-only and lives in `crc_modules/rhino/`, not in `viz/`.

## Inputs you must give me

For each of the 4 legacy `.ghuser`, the standard rundown. Specifically:

- What is the **output**? A file on disk, an in-canvas image preview, both?
  Grasshopper has limited image-preview options — most legacy plotters save
  to disk and return the path.
- Styling parameters exposed in the legacy: title, axis labels, bins
  (histogram), color map (heatmap), marker size (scatter), linestyle,
  legend.
- For **Heatmap**: is the input a 2D matrix, or X/Y/value triples that need
  to be binned/interpolated? Different code paths.

## Steps

1. **Implement `carcara/crc_modules/viz/{histogram,scatter,lineplot,heatmap}.py`**.
   Each module exposes a single top-level function:
   ```python
   def render_histogram(values, *, bins=10, title="", out_path=None, **style) -> str
   def render_scatter(x, y, *, title="", out_path=None, **style) -> str
   def render_lineplot(x, y_series, *, title="", out_path=None, **style) -> str
   def render_heatmap(matrix_or_xyz, *, title="", cmap="viridis", out_path=None, **style) -> str
   ```
   Each returns the absolute path of the written file (or raises). Use
   `matplotlib.pyplot.figure(...)` + `fig.savefig(out_path)` + `plt.close(fig)`
   to avoid figure leaks. **Never** call `plt.show()` — this would block
   inside Rhino.

2. **Headless rendering**: at the top of each `viz` module, set
   `matplotlib.use("Agg")` so the build does not require a display server.

3. **Tests** `tests/test_viz.py`:
   - Each function called with a `tmp_path` `out_path` writes a non-empty
     PNG (`os.path.getsize(p) > 0`).
   - Pass empty data → expect a clear exception, not a 0-byte PNG.

4. **GH bundles** (4 folders). Each `code.py`:
   - Coerces inputs.
   - Calls the right `render_*` function.
   - Returns `out_path` as a string and `report`.

5. **Build & install**.

## Tests

```powershell
pytest tests/test_viz.py -v
```

## Grasshopper checkpoint

Restart Grasshopper. For each chart component, build one canvas:

1. Pull values from PostGIS using Phase 04 components (e.g. a column of
   numeric attributes).
2. Feed into the chart component with an `out_path` like
   `C:\\temp\\carcara_chart.png`.
3. Flip `run`. Open the PNG. Confirm:
   - The chart actually plots the data.
   - The title and axis labels you wired in appear.
   - Empty input lists are surfaced as `report = "ERROR: ..."`, not as a
     blank chart.

For `CRC_Heatmap`, also confirm the color map switches when you change
the `cmap` input.

Save canvases as `tests/_manual/smoke_viz_*.gh`.

## Commit

```
feat(viz): add histogram / scatter / lineplot / heatmap with 4 GH components
```

## Done when

- [ ] All 4 `viz` modules exist, render PNGs headlessly, and are tested.
- [ ] All 4 GH bundles built and validated against real data.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
