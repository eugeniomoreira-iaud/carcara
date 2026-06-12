# Phase 10 — Visualization (`viz/*` + 4 chart components + CRC_CurveDisplay)

## Goal

Generate publication-quality charts from PostGIS-derived data, all the way from inside
Grasshopper. Charts are rendered via `matplotlib` and saved as **SVG files**. Also delivers
`CRC_CurveDisplay`, the Rhino-viewport preview component (C# script, separate build route).

Components delivered (all subcategory **04.Dataviz**):

| Component         | Module                    | Notes                                                               |
|-------------------|---------------------------|---------------------------------------------------------------------|
| `CRC_Histogram`   | `viz/histogram.py`        | matplotlib chart → SVG file                                        |
| `CRC_ScatterPlot` | `viz/scatter.py`          | matplotlib chart → SVG file                                        |
| `CRC_LinePlot`    | `viz/lineplot.py`         | matplotlib chart → SVG file                                        |
| `CRC_Heatmap`     | `viz/heatmap.py`          | matplotlib chart → SVG file                                        |
| `CRC_CurveDisplay`| `rhino/curve_display.cs`  | Rhino-viewport preview (C# GH_ScriptInstance). No matplotlib.      |

> `CRC_CurveDisplay` overrides `DrawViewportWires` for custom color/lineweight/dash preview.
> It is Rhino-only and is **excluded from pytest**; validation is the GH checkpoint only.
> Canonical source: `grasshopper/components/CRC_CurveDisplay/code.cs` (already written).

## Inputs you must give me

For each of the 4 chart legacy `.ghuser`, the standard rundown. Specifically:

- Styling parameters exposed in the legacy: title, axis labels, bins (histogram),
  color map (heatmap), marker size (scatter), linestyle, legend.
- For **Heatmap**: is the input a 2D matrix, or X/Y/value triples that need to be
  binned/interpolated? Different code paths.

## Steps

### 1. Implement `carcara/crc_modules/viz/{histogram,scatter,lineplot,heatmap}.py`

Each module exposes a single top-level function. Charts are saved as **SVG** only — no PNG,
no PIL:

```python
def render_histogram(values, *, bins=10, title="", out_path, **style) -> str
def render_scatter(x, y, *, title="", out_path, **style) -> str
def render_lineplot(x, y_series, *, title="", out_path, **style) -> str
def render_heatmap(matrix_or_xyz, *, title="", cmap="viridis", out_path, **style) -> str
```

Each function:

- Saves to `out_path` using `fig.savefig(out_path, format="svg")`.
- Returns the absolute path of the written file (or raises on failure).
- Calls `plt.close(fig)` immediately after saving to avoid figure leaks.
- **Never** calls `plt.show()` — this would block inside Rhino.
- Raises a clear exception (not a silent empty file) when given empty data.

### 2. Headless rendering

At the top of each `viz` module, before any other matplotlib import:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

This ensures no display server is required (Rhino's Python environment has none).

### 3. Tests `tests/test_viz.py`

- Each render function called with a `tmp_path` `out_path` (`.svg` extension) writes a
  non-empty SVG (`os.path.getsize(p) > 0`, file starts with `<?xml` or `<svg`).
- Pass empty data (`[]`) → expect a clear exception, not a 0-byte file.

### 4. GH bundles — 4 chart components

Each `code.py`:

- Coerces inputs (lists, strings, ints).
- Calls the right `render_*` function with `out_path` from the component input.
- Returns `out_path` as a string output and `report`.
- Guards execution with `if CToggle:`.

Example for `CRC_Histogram`:

```
Inputs:  CString (not needed — no DB call here), Values (float, list), Bins (int, item),
         Title (str, item), OutPath (str, item), CToggle (bool, item)
Outputs: out_path (str), report (str)
subcategory: 04.Dataviz
```

Port exact input/output names from the legacy decoded scripts before finalizing
`metadata.json` for each chart component.

### 5. CRC_CurveDisplay — C# component

**Source is final.** Canonical file: `grasshopper/components/CRC_CurveDisplay/code.cs`

Inputs / outputs (from the code):

| Input  | Type   | Access | Notes |
|--------|--------|--------|-------|
| `Curve`| Curve  | item   | Curve to preview. Null → no-op. |
| `Width`| int    | item   | Line width in pixels. <= 0 → no-op. |
| `Colour`| Color | item   | Display color. |
| `Dash` | object (cast to string) | item | Space-separated "dash gap" numeric values. Empty / null → solid line. Invalid number → exception surfaced by GH. |

Outputs: none — viewport preview only (overrides `DrawViewportWires`).

`metadata.json` for the bundle (`grasshopper/components/CRC_CurveDisplay/`):

```json
{
  "name": "CurveDisplay",
  "nickname": "CrvDpl.cs",
  "category": "Carcara",
  "subcategory": "04.Dataviz",
  "description": "Custom preview: control lineweight, color, and dash pattern on Rhino viewport curves.",
  "exposure": 1,
  "ghpython": {
    "isAdvancedMode": true,
    "marshalGuids": true,
    "iconDisplay": 0,
    "inputParameters": [
      { "name": "Curve",  "description": "Curves to preview",                                                      "typeHintID": "curve", "scriptParamAccess": "item" },
      { "name": "Width",  "description": "Width of the curves",                                                    "typeHintID": "int",   "scriptParamAccess": "item" },
      { "name": "Colour", "description": "Color of the curves",                                                    "typeHintID": "colour","scriptParamAccess": "item" },
      { "name": "Dash",   "description": "Dash pattern: space-separated values for dash and gap (e.g. '2 1')",    "typeHintID": "ghdoc", "scriptParamAccess": "item", "optional": true }
    ],
    "outputParameters": []
  }
}
```

**Build route for CRC_CurveDisplay:**

The upstream componentizer (`compas-actions.ghpython_components`) has a C# variant script
(`componentize_cs.py`). Check `vendor/componentizer/` for its presence:

- If `componentize_cs.py` exists in `vendor/componentizer/`, add a C# branch to
  `build_userobjects.py` that invokes it for bundles containing `code.cs` instead of
  `code.py`. Document this branch in the build script with a comment.
- If the C# variant is absent, create the `.ghuser` manually in Grasshopper: open a new
  `.gh` file, add a C# Script component, paste the contents of `code.cs`, add the four
  inputs (`Curve`, `Width`, `Colour`, `Dash`) and zero outputs, then save the component as
  a User Object to `carcara/userobjects/`. This is an accepted manual exception (same as
  `CRC_SRID`).

Do not assume `build_userobjects.py` already handles `.cs` — investigate first.

### 6. Build & install

```powershell
python build_userobjects.py
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

## Tests

```powershell
pytest tests/test_viz.py -v
```

`CRC_CurveDisplay` is validated only via the GH checkpoint (Rhino-dependent, no pytest).

## Grasshopper checkpoint

Restart Grasshopper.

**Chart components (Histogram, ScatterPlot, LinePlot, Heatmap)** — for each:

1. Pull numeric values from PostGIS using Phase 04 components.
2. Feed into the chart component with an `out_path` like `C:\temp\carcara_chart.svg`.
3. Flip `CToggle`. Open the SVG file. Confirm:
   - The file is a valid SVG (opens in a browser or SVG viewer; starts with `<svg` tag).
   - The chart actually plots the data.
   - The title and axis labels you wired in appear.
   - Empty input lists are surfaced as `report = "ERROR: ..."`, not as a blank chart or
     0-byte file.
4. For `CRC_Heatmap`: confirm the color map switches when you change the `cmap` input
   (e.g. `"plasma"` vs `"viridis"`).

**CRC_CurveDisplay:**

1. Wire a set of Rhino curves into `Curve`, set `Width = 3`, pick a color for `Colour`.
2. Leave `Dash` disconnected (solid line). Confirm viewport preview draws curves with the
   correct lineweight and color.
3. Connect a Panel with `"2 1"` to `Dash`. Confirm the dashed pattern appears (dash length
   2, gap 1).
4. Try `"5 2 1 2"` (dash-gap-dot-gap pattern). Confirm the more complex pattern renders.
5. Leave `Dash` as an empty string. Confirm solid line (no crash).
6. Enter an invalid `Dash` value like `"abc 1"`. Confirm GH surfaces the parse error
   without crashing.

Save canvases as `tests/_manual/smoke_viz_histogram.gh`, `tests/_manual/smoke_viz_scatter.gh`,
`tests/_manual/smoke_viz_lineplot.gh`, `tests/_manual/smoke_viz_heatmap.gh`,
`tests/_manual/smoke_curve_display.gh`.

## Commit

```
feat(viz): add SVG chart modules (histogram/scatter/lineplot/heatmap) + CRC_CurveDisplay C# component
```

## Done when

- [ ] All 4 `viz` modules exist, render SVG files headlessly, and are tested (non-empty SVG, empty data raises).
- [ ] All 4 GH chart bundles built and validated against real data (SVG opens correctly).
- [ ] `grasshopper/components/CRC_CurveDisplay/code.cs` exists (done).
- [ ] `grasshopper/components/CRC_CurveDisplay/metadata.json` and `icon.png` added.
- [ ] `CRC_CurveDisplay` `.ghuser` built (via `componentize_cs.py` or manually) and deployed.
- [ ] GH checkpoint for `CRC_CurveDisplay` passes (solid, dashed, error cases).
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
