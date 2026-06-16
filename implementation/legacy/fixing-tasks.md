# Fix: chart components emit raw SVG body, not a full document

## Problem

When chaining any chart component's `svgCode` output into `CRC_SaveSVG`, the resulting file is **invalid SVG** — Illustrator refuses to open it with "multiple root elements" errors.

The chain produces a double-wrapped document:
```xml
<svg ...>          ← outer wrapper (CRC_SaveSVG's constructor)
  <svg ...>        ← inner wrapper (e.g. Heatmap's svgCode)
    <polygon .../>
    <text .../>
  </svg>
</svg>
```

Two `<svg>` root elements at any depth break all SVG parsers.

## Decision and scope

**Strip the `<svg>` and `<?xml?>` wrappers from every chart component.** They must output only raw body content (polygons, text, lines, etc.) as their `svgCode`. `CRC_SaveSVG` is the sole place that constructs the final document.

**Scope: two things change per component — `svgCode` assignment and the return tuple.** Everything else stays.

Specifically:

- The Rhino viewport preview is **kept**. `PreviewPayload`, `DrawViewportWires`, `DrawViewportMeshes`, `get_ClippingBox`, `isAdvancedMode: true`, and the `executingcomponent` subclass **all remain**. These components stay SDK-mode.
- Geometry construction blocks (bars, dots, lines, axes, etc.) are **kept**. They feed the viewport preview.
- The only removals are from the **return tuple** (geometry outputs dropped) and the **metadata `outputParameters`** list (reduced to 2).

## Changes required

### 1. `out` → `report` rename (Histogram and LinePlot only)

Histogram and LinePlot name their status output `out`, not `report`. Heatmap and ScatterPlot already use `report`.

Rename `out` → `report`: the code variable, every assignment to it, and the metadata output `name` field. The status output is preserved — only the name changes.

> Note: the original draft incorrectly mapped Histogram `out → svgCode` and LinePlot `out → removed`. Both are wrong. The correct mapping is `out → report` for both components.

### 2. `svgCode` = raw body (all 4 charts)

Replace the full-SVG wrapper construction with a body join only.

**Heatmap** `code.py` ~lines 264–271:
```python
# BEFORE (wraps in full SVG document)
svg_code = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg"'
    ' width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">\n'
    '{body}\n'
    '</svg>\n'
).format(w=_cw, h=_ch, body="\n".join(e for e in _svg_elems if e))

# AFTER (raw body only)
svg_code = "\n".join(e for e in _svg_elems if e)
```

**Histogram** `code.py` ~lines 188–196:
```python
# BEFORE
svg_code = (
    '<?xml ...?>\n'
    '<svg ... viewBox="...">\n'
    '{body}\n'
    '</svg>\n'
).format(w=..., h=..., body="\n".join(svg_body_parts))

# AFTER
svg_code = "\n".join(svg_body_parts)
```

**ScatterPlot** `code.py` ~lines 296–303:
```python
# AFTER
svg_code = "\n".join(e for e in _svg_elems if e)
```

**LinePlot** `code.py` ~lines 227–234:
```python
# BEFORE
svg_code = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg"'
    ' width="{w}mm" height="{h}mm"'
    ' viewBox="0 0 {w} {h}">\n'
    '{body}\n'
    '</svg>\n'
).format(w=round(cw, 4), h=round(ch, 4), body=svg_body)

# AFTER
svg_code = svg_body   # svg_body is already built just above this line
```

### 3. Return tuple → `(svgCode, report)` (all 4 charts)

Reduce the return tuple to two values. **Keep** the geometry construction blocks and `PreviewPayload` build intact — they feed the viewport preview.

- **Heatmap**: `return svg_code, report`
- **ScatterPlot**: `return svg_code, report`
- **Histogram**: `return svg_code, report` (was `(out, bars, axes, …)`; order flips; status renamed `out → report`)
- **LinePlot**: `return svg_code, report` (same)

### 4. `metadata.json` outputs → 2 only (all 4 charts)

`outputParameters` becomes exactly two entries for every chart component. **Output order must match the return tuple** (svgCode first, report second). Remove all geometry/color/label/grid/legend output params.

```json
"outputParameters": [
    {
        "name": "svgCode",
        "description": "Raw SVG body content (no <svg> wrapper). Chain into CRC_SaveSVG for file export."
    },
    {
        "name": "report",
        "description": "Verbose status — success details or error trace."
    }
]
```

### 5. `metadata.json` input renames (descriptive names)

The input-rename tables below are valid and must be applied. Update both `metadata.json` (`name` and `description` fields) and the matching `RunScript(self, ...)` parameter names in `code.py` — every internal reference to the old short variable name must be updated to the new descriptive name.

#### CRC_Histogram — inputs to rename

| Current name | New descriptive name | Description |
|---|---|---|
| `cv` | `canvasRect` | Canvas boundary Rectangle3d (default 100×100 at origin) |
| `v` | `dataValues` | Data values to histogram (uses demo data if absent) |
| `b` | `numBins` | Number of histogram bins (default 10) |
| `nx` | `numXLabels` | Number of X-axis labels (default: all bin edges) |
| `ny` | `numYLabels` | Number of Y-axis labels (default 5) |
| `d` | `decimals` | Decimal places for labels (default 1) |
| `ext` | `axisExtension` | Axis extension beyond canvas (default 0) |
| `dist` | `labelDist` | Label distance from axis (default 10) |
| `gy` | `drawGridY` | Draw horizontal grid lines at Y labels (default False) |
| `bw` | `barOutlineWidth` | Bar outline width in pixels (default 1) |
| `aw` | `axisLineWidth` | Axis line width in pixels (default 2) |
| `gw` | `gridLineWidth` | Grid line width in pixels (default 1) |

#### CRC_ScatterPlot — inputs to rename

| Current name | New descriptive name | Description |
|---|---|---|
| `cv` | `canvasRect` | Canvas boundary Rectangle3d |
| `x` | `xValues` | X coordinates of data points (default demo data if absent) |
| `y` | `yValues` | Y coordinates of data points (default demo data if absent) |
| `r` | `dotRadius` | Dot radius — single value or list for variable sizes (default 2.0) |
| `nx` | `numXLabels` | Number of X-axis labels (default 5) |
| `ny` | `numYLabels` | Number of Y-axis labels (default 5) |
| `d` | `decimals` | Decimal places for labels (default 1) |
| `ext` | `axisExtension` | Axis extension beyond canvas (default 0) |
| `dist` | `labelDist` | Label distance from axis (default 10.0) |
| `mx` | `marginLeft` | Left margin as % of X range (default 0) |
| `my` | `marginBottom` | Bottom margin as % of Y range (default 0) |
| `gx` | `drawGridX` | Draw vertical grid lines (default False) |
| `gy` | `drawGridY` | Draw horizontal grid lines (default False) |
| `show_leg` | `showLegend` | Generate color legend (default False) |
| `col_vals` | `colorValues` | Values for color mapping; if None uses Y values |
| `colors` | `gradientColors` | Color gradient list for legend (min 2 System.Drawing.Color). Defaults cool-to-warm if absent. |
| `n_leg` | `numLegendSteps` | Number of legend steps (default 5) |
| `leg_w` | `legendBarWidth` | Legend bar width (default 5% of canvas) |
| `leg_dist` | `legendDist` | Distance from chart to legend (default 20) |
| `leg_l_dist` | `legendLabelDist` | Distance from legend bar to labels (default 5) |
| `leg_orient` | `legendOrientation` | Legend orientation: vertical or horizontal (default vertical) |
| `dw` | `dotOutlineWidth` | Dot outline width in pixels (default 0.5) |
| `aw` | `axisLineWidth` | Axis line width in pixels (default 2) |
| `gw` | `gridLineWidth` | Grid line width in pixels (default 1) |

#### CRC_LinePlot — inputs to rename

| Current name | New descriptive name | Description |
|---|---|---|
| `cv` | `canvasRect` | Canvas boundary Rectangle3d (default 100×100 at origin) |
| `x` | `xValues` | X coordinates (flat list = 1 series; DataTree = multi). Uses demo data if absent. |
| `y` | `yValues` | Y coordinates (same shape as xValues). Uses demo data if absent. |
| `nx` | `numXLabels` | Number of X-axis labels (default 5) |
| `ny` | `numYLabels` | Number of Y-axis labels (default 5) |
| `d` | `decimals` | Decimal places for labels (default 1) |
| `ext` | `axisExtension` | Axis extension beyond canvas (default 0) |
| `dist` | `labelDist` | Label distance from axis (default 10) |
| `mx` | `marginLeft` | Left margin as % of X range (default 0) |
| `my` | `marginBottom` | Bottom margin as % of Y range (default 0) |
| `gx` | `drawGridX` | Draw vertical grid lines at X labels (default False) |
| `gy` | `drawGridY` | Draw horizontal grid lines at Y labels (default False) |
| `lw` | `lineWidth` | Series line width in pixels (default 2) |
| `aw` | `axisLineWidth` | Axis line width in pixels (default 2) |
| `gw` | `gridLineWidth` | Grid line width in pixels (default 1) |

> Heatmap inputs are already descriptive and require no renaming.

### 6. `code.py` — RunScript signatures must match metadata names

Every parameter name in `RunScript(self, ...)` must match the `name` field of the corresponding `inputParameters` entry — that is how Grasshopper wires inputs to Python variables. Changing a metadata name requires a matching change in the code.py signature and every internal reference to the old short variable name throughout the file.

Example for Histogram: `RunScript(self, canvasRect, dataValues, numBins, numXLabels, numYLabels, decimals, axisExtension, labelDist, drawGridY, barOutlineWidth, axisLineWidth, gridLineWidth)` — not `cv, v, b, …`.

### 7. `metadata.json` description field (all 4 charts)

Update the component-level `description` field to reflect that these are chart renderers with **both** a Rhino viewport preview and `svgCode` export. Drop any framing that describes them as "pure Rhino geometry generators".

Example for Histogram: *"Renders a histogram chart in the Rhino viewport and exports raw SVG body content. Chain svgCode into CRC_SaveSVG to write the file."*

### 8. CRC_SaveSVG — NO change (verified correct)

`CRC_SaveSVG/code.py` lines 48–55 and `crc_modules/svg/save.py` `save_svg()` construct the `<?xml?>` + `<svg>` wrapper exactly once. After charts emit raw bodies there is no double-wrap. No fix required here.

### 9. SVG exporters — NO change (verified correct)

The four SVG-exporter components (`CRC_PolylineToSVG`, `CRC_CircleToSVG`, `CRC_NurbsToSVG`, `CRC_TextToSVG`) already emit raw element lists with no wrapper — verified: `CRC_PolylineToSVG` returns `(svg_code, report)` where `svg_code` is a list of elements. Do not modify these components.

> Shape note: charts emit `svgCode` as one joined multiline string (item access); exporters emit a list. `CRC_SaveSVG`'s input is `scriptParamAccess: list` — both work because Grasshopper wraps a single item into a 1-element list automatically. Leave as-is.

## Testing checklist

1. Place each of the 4 chart components on canvas with zero inputs. Verify viewport preview **still renders** — geometry must appear in the Rhino viewport (PreviewPayload is kept).
2. Verify `report` (not `out`) shows verbose success info for all 4 components.
3. Verify `svgCode` output contains **only raw SVG elements** (`<polygon>`, `<text>`, `<line>`, etc.) — no `<svg>` tag, no `<?xml?>` declaration.
4. Chain each `svgCode` → `CRC_SaveSVG` (with `file_path` + `save_flag`).
5. Open each produced `.svg` in Illustrator and in a browser — no "multiple root elements" error; file renders correctly (colors, geometry, text labels all present).
6. Confirm no duplicate XML declarations or nested root elements in any output file.
7. Run `build_userobjects.py` — all 4 chart components must build successfully via the SDK path (`isAdvancedMode: true`).
8. In the Grasshopper canvas, verify all wire labels show the new descriptive names (not abbreviations like `cv`, `v`, `b`).

---

# Part 2 — SVG-exporter components: viewport preview + color input bugs

## Components

CRC_PolylineToSVG, CRC_CircleToSVG, CRC_NurbsToSVG, CRC_TextToSVG (subcategory 04.Dataviz).

## Problem (reported from canvas use)

1. No viewport preview — geometry never draws in the Rhino viewport the way chart components do.
2. SVG generation fails when a color is input — geometry-only works, but feeding stroke/fill color (`sc`/`f`/`fC`) produces empty `svg_code`.

## Root causes (confirmed by code + metadata review)

### Bug A — color input produces empty SVG

- All color inputs declare `"typeHintID": "colour"`. The componentizer's valid id is `color` (see `specs/componentizer.md` type list around line 124; `colour` is NOT in it). An unknown id falls back to `ghdoc` (the componentizer default). So the color value arrives as a Grasshopper goo, NOT a `System.Drawing.Color`.
- `crc_modules/rhino/preview.py` `color_to_hex()` reads `color.R` — which raises AttributeError on the goo.
- Each exporter's per-item loop wraps the body in `try/except: failed += 1` (silent). Every colored item is therefore counted as failed, so `svg_code` comes out empty and the report reads "0 element(s) generated, N failed". This matches the symptom exactly.
- The same invalid `"colour"` appears in 8 metadata files: the 4 exporters plus CRC_Heatmap, CRC_ScatterPlot, CRC_ColorCalculator, CRC_CurveDisplay. Charts dodge the crash via default-color fallbacks; the exporters hit it because the user passes color directly.

### Bug B — no viewport preview

- Preview geometry is only added to the payload when a color is present. Polyline/Nurbs/Circle call `pv.add_curve(...)` inside `if stroke_color is not None`, and fills only when the curve is closed and a fill color is given. With geometry only (the normal case) the payload stays empty.
- `self.Hidden = True` suppresses Grasshopper's own default preview. Empty payload + Hidden = nothing visible. (Charts always populate the payload, so they draw.)

## Fixes

### F1 — `colour` -> `color` typeHintID (metadata.json)

Replace every `"typeHintID": "colour"` with `"color"`.

- 4 exporters: CRC_PolylineToSVG (`sc`, `f`), CRC_CircleToSVG (`sc`, `f`), CRC_NurbsToSVG (`sc`, `f`), CRC_TextToSVG (`fC`).
- Also the 4 latent files (same root bug, fix while here): CRC_Heatmap, CRC_ScatterPlot, CRC_ColorCalculator, CRC_CurveDisplay.

### F2 — harden `color_to_hex` (carcara/crc_modules/rhino/preview.py)

Accept a GH_Colour goo defensively: if the object has no `.R` attribute, fall back to its `.Value` (a `System.Drawing.Color`) before reading R/G/B. Keep the existing `None` guard. This ensures a stray goo never throws.

### F3 — always draw the viewport preview (4 exporters, code.py)

In each per-item loop, add the curve to the payload UNCONDITIONALLY, using the stroke color if given, else default black:

```python
_preview_clr = stroke_color if stroke_color is not None else Color.Black
_preview_w = max(1, int(sw_val)) if sw_val else 1
pv.add_curve(crv, _preview_clr, _preview_w)
if fill_color is not None and crv.IsClosed:   # circle: always closed
    pv.add_filled_curve(crv, fill_color)
```

PolylineToSVG: `crv` is already coerced. CircleToSVG: build `rg.ArcCurve(circ)` (already done in the loop). NurbsToSVG: `crv` is coerced. TextToSVG preview already defaults its fill color to black — leave it; it works once F1 lands.

### F4 — no-color SVG gets a default black stroke (4 exporters, code.py)

Decision: geometry exported with no color must still be visible in the file. In each loop:

```python
if stroke_color is not None:
    stroke_hex = color_to_hex(stroke_color)
else:
    stroke_hex = "#000000"          # default visible stroke
sw_val = float(_get(sw, i, 0) or 0)
if sw_val <= 0:
    sw_val = 1.0                     # a 0-width stroke is invisible in SVG
```

Fill stays `"none"` when no fill is given (do NOT auto-fill). TextToSVG fill already defaults to black — fine.

### F5 — surface per-item errors in the report (4 exporters)

The silent `except: failed += 1` is what hid Bug A. Capture the first failure's message so future breakage is visible, e.g. keep a `first_err` variable and append it:
`report = "OK – {ok} generated, {failed} failed (first: {first_err})"`.
Keep the loop resilient — one bad item must never abort the rest.

### F6 — rename output `svg_code` -> `svgCode` (4 exporters)

Match the chart components. Change the metadata `outputParameters` name and the returned variable name in code.py. Return stays `(svgCode, report)`. Description can mirror the chart wording: "SVG element string(s); chain into CRC_SaveSVG for file export."

## Files

- `grasshopper/components/CRC_{PolylineToSVG,CircleToSVG,NurbsToSVG,TextToSVG}/code.py`
- `grasshopper/components/CRC_{PolylineToSVG,CircleToSVG,NurbsToSVG,TextToSVG}/metadata.json`
- `grasshopper/components/CRC_{Heatmap,ScatterPlot,ColorCalculator,CurveDisplay}/metadata.json` (F1 only)
- `carcara/crc_modules/rhino/preview.py` (F2)

## Testing checklist

1. Place each exporter with geometry only (no color): viewport shows the geometry in black (F3); `svgCode` is non-empty with `stroke="#000000"` (F4); report says "OK".
2. Add stroke/fill color: `svgCode` is still generated (F1/F2), preview is colored, no "N failed".
3. Chain each `svgCode` -> CRC_SaveSVG -> open the .svg: geometry is visible.
4. Charts / ColorCalculator / CurveDisplay still build and accept color after the `colour`->`color` change.
5. `conda run -n carcara pytest tests/ -v` — add a test for the `color_to_hex` goo fallback (F2).
6. `conda run -n carcara python build_userobjects.py` — all touched components build via the SDK path (`isAdvancedMode: true`).

---

# Part 3 — Spatial-filter components: single-mask DataTree + correlation

## Components / files

- `grasshopper/components/CRC_GeometriesWithSpatialFilter/{code.py, metadata.json}`
- `grasshopper/components/CRC_ValuesWithSpatialFilter/{code.py, metadata.json}`
- `carcara/crc_modules/db/spatial_query.py` (shared filter logic)
- `tests/test_spatial_query.py`

## Problems (reported from canvas use)

1. **(Geometries)** The `sql_filter` input must be dropped.
2. **(Geometries)** When several separate polygons are supplied as the spatial filter, results merge per-polygon: the first matched entity of every polygon lands in the same branch, and entities hit by more than one polygon duplicate. Wanted: however many polygons are supplied, they act as a **single mask**, and the output is a DataTree mirroring the masked table — one branch per row. A multipart row may return more than one geometry in its branch (only in that case). No duplicates.
3. **(Values)** The `values` output must be a DataTree with ONE value per branch (branch per row), produced by the EXACT same filter operation and ordering as Geometries so the two outputs correlate row-for-row. No duplicates. Add a `pk` output. Only one column is allowed.

## Root causes (confirmed by code review)

- **Geometries**: `spatial_filter` is `scriptParamAccess: "item"`. Feeding N polygons makes Grasshopper execute the script N times; each run emits a DataTree starting at `GH_Path(0)`; GH merges the runs, so identical paths collide (the first entity of every polygon lands in branch `{0}`), and an entity intersecting two polygons is returned by two runs (duplicate). The per-row branch-building code (one `GH_Path(i)` per row, multipart split into the same branch) is already correct — only the multi-execution is wrong.
- **Values**: builds branches by COLUMN (`path = GH_Path(col_idx)`, each branch = a whole column) and suffers the same item-access multi-execution problem with multiple polygons.

## Fixes

### Module — `spatial_query.py`

1. `_build_spatial_filter_expr` — accept a **list** of filter WKTs and build one combined mask:

```python
def _build_spatial_filter_expr(geom_col, filter_wkts, cx, cy, srid, func):
    cx = validate_offset(cx); cy = validate_offset(cy)
    geoms = ", ".join(
        f"ST_GeomFromText({_quote_literal(w)}, {srid})" for w in filter_wkts)
    combined = f"ST_Translate(ST_Union(ARRAY[{geoms}]), {cx}, {cy})"
    if func == 0:
        return f"ST_Intersects({geom_col}, {combined})"
    return f"ST_Contains({combined}, {geom_col})"
```

`ST_Union` dissolves all polygons into a single geometry, so each table row matches at most once (no duplicates). The `+cx`/`+cy` correction and the `func` predicate semantics are unchanged.

2. `get_geometries_with_spatial_filter` — change `filter_wkt: str` to `filter_wkts: List[str]`. Remove the `sql_filter` parameter and its WHERE handling; WHERE becomes just the single spatial predicate. Keep `ORDER BY pk`. Still returns `(wkt_list, pk_list)`.

3. `get_values_with_spatial_filter`:
   - `filter_wkt` → `filter_wkts: List[str]`; remove `sql_filter`.
   - `columns: List[str]` → single `column: str`.
   - SELECT the column AND the primary key; `ORDER BY pk` (identical ordering to geometries). If the table has no PK, SELECT `NULL` as pk (parallel, mirroring geometries).
   - Return `(values_list, pk_list)` — the single column's values in row order and the parallel PKs. Drop the `col_names` return.

### CRC_GeometriesWithSpatialFilter

- **metadata.json**: remove the `sql_filter` input entirely; change `spatial_filter` to `"scriptParamAccess": "list"`.
- **code.py**:
  - Drop all `sql_filter` handling.
  - `spatial_filter` is now a list of geometries: `filter_wkts = [rh_geometry_to_wkt(g) for g in spatial_filter if g is not None]`; raise if the list is empty.
  - Call `get_geometries_with_spatial_filter(CString, schema, table, filter_wkts, cx=cx, cy=cy, srid=srid, func=func, sql_log=executed_sql)`.
  - Keep the existing branch builder (one `GH_Path(i)` per row; multipart → multiple geoms in the same branch). A single query = a single execution = no path collisions and no duplicates.

### CRC_ValuesWithSpatialFilter

- **metadata.json**: remove `sql_filter`; change `spatial_filter` to `"list"`; change `columns` (list) to a single `column` (item, str, description "Single column name to query"); add a `pk` output (DataTree). Output order: `values`, `pk`, `report`, `queries`.
- **code.py**:
  - Drop `sql_filter`; build `filter_wkts` from the `spatial_filter` list exactly as Geometries does.
  - Single `column`.
  - Call `get_values_with_spatial_filter(...)` → `(values_list, pk_list)`.
  - Apply the `N` null-replacement to the values.
  - Output branch per row, one value per branch:

```python
for i, (val, pk_val) in enumerate(zip(values_list, pk_list)):
    p = GH_Path(i)
    values.Add(str(val) if val is not None else "", p)
    pk.Add(pk_val, p)
```

  This mirrors the Geometries `GH_Path(i)` ordering (both `ORDER BY pk`), so branch `i` references the same entity in both components; the `pk` output makes the correlation explicit.

### Tests — `tests/test_spatial_query.py`

- Update every `get_geometries_with_spatial_filter(... filter_wkt="...")` call to `filter_wkts=["..."]`.
- Remove `test_extra_sql_filter_anded` (the `sql_filter` parameter is gone).
- Update the Values tests: `columns=[...]` → `column="name"`; the new return is `(values, pk)` not `(rows, cols)` — adjust assertions accordingly.
- Add a multi-polygon test: two filter WKTs produce ONE WHERE predicate containing `ST_Union(ARRAY[` and both polygons, with a single spatial predicate (no OR, no duplication).
- Add a test: Values returns parallel `values` and `pk` lists ordered by pk.

## Note — identical filter logic guarantees correlation

Both components now call the same `_build_spatial_filter_expr` (single `ST_Union` mask) and `ORDER BY pk`. Same table + same mask + same order means branch `i` in Geometries and branch `i` in Values reference the same entity; the `pk` outputs allow explicit correlation. No duplicates in either.

## Verification

1. Geometries: feed 2+ separate polygons (as a list) → one branch per matched row, no entity duplicated across branches; multipart rows show more than one geom in their branch.
2. Values: same 2 polygons + one column → `values` DataTree with one value per branch; `pk` DataTree parallel; branch `i` matches Geometries branch `i`.
3. Confirm the `sql_filter` input is gone from both components.
4. `conda run -n carcara pytest tests/test_spatial_query.py -v` is green.
5. `conda run -n carcara python build_userobjects.py` builds both components.

---

# Part 4 — CRC_CreateTable: match legacy Create-Table2 (tabular CREATE + INSERT + mandatory PK)

## Context

The user imported the legacy cluster `carcara-old/carcara/Create-Table2.ghuser` (v1.3, 2025/11/13). Decoded, it CREATEs a table AND INSERTs row data (`values`), plus an `Id Values` join-key input. The current CRC_CreateTable does DDL only (CREATE TABLE + optional geometry column), with no data insertion. This task upgrades CRC_CreateTable to the legacy behavior, **tabular-only** — the geometry column is dropped (geometry writes stay in CRC_CreateShapefile). **Every created table must have a primary key.**

## Decoded legacy contract (Create-Table2)

A GH cluster with hook inputs: `CString`, `CToggle`, `schema`, `table name`, `values`, `list of columns`, `variable types`, `replace table`, `Id Values`. It builds CREATE + INSERT SQL via native GH wiring (Series, Tree Statistics, Graft/Flatten, Concatenate, Text Join) plus a Python 3 Script, then executes it through a generic Run ODBC Command. Tabular; no geometry. The Python-3-Script SQL body is not recoverable from the binary (Rhino 8 script chunk), so it is reimplemented cleanly in psycopg2.

## Decisions

- Tabular-only: drop `geom_column` / `geom_type` / `srid` from the component.
- `values` = DataTree, **branch per row**; each branch holds that row's values across the columns (parallel to `column_names`).
- `Id Values`: optional. If given → an `id` PRIMARY KEY column populated with those values (one per row). If absent → auto-increment integer identity PK. **Never create a table without a primary key.**

## Target component contract (upgraded CRC_CreateTable)

Inputs: `CString`, `CToggle`, `schema`, `table`, `column_names` (list), `column_types` (list, parallel to `column_names`), `values` (tree access — branch per row), `id_values` (list, optional), `replace_table` (bool). REMOVE `geom_column`, `geom_type`, `srid`.

Outputs: `affected` (rows inserted), `report`.

### Primary-key rules

- `id_values` present → add an `id` PRIMARY KEY column; type inferred (integer if every value is int-castable, else text); populated with `id_values[i]` for row `i`.
- `id_values` absent → add `id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY`; the INSERT omits `id`.
- If `id` is already among `column_names` → that column becomes the PK (do not add a second id column); if it then has neither supplied values nor identity, raise.
- Never create a table without a primary key.

## Module changes — `carcara/crc_modules/db/writer.py`

Keep the existing `create_table` (geometry) and `insert_geometries` untouched — `tests/test_writer.py` and CRC_CreateShapefile depend on them. ADD:

- `insert_rows(cstring, schema, table, column_names, rows) -> int`: identifier-safe INSERT via `executemany`; `rows` = list of tuples parallel to `column_names`; returns the row count; raises `psycopg2.Error`.
- `create_table_with_data(cstring, schema, table, columns, rows, id_values=None, replace_table=False) -> int`:
  - `columns` = list of `(name, sql_type)`.
  - Resolve the PK per the rules above.
  - Optional `DROP TABLE IF EXISTS` when `replace_table`.
  - `CREATE TABLE` with the PK + columns, using `psycopg2.sql` `Identifier` / `SQL` — never string-format identifiers.
  - INSERT the rows (include the `id` column when `id_values` is given; otherwise omit it so the identity fills it).
  - Commit; return rows inserted.
  - Pure psycopg2, no Rhino. Raises on failure.

## Component changes

- **`metadata.json`**: drop `geom_column` / `geom_type` / `srid`; add `values` (tree access) and `id_values` (list, optional). Update the component-level description: `"CREATE TABLE in PostGIS and INSERT row data; always adds a primary key (from Id Values or auto-increment). Destructive when replace_table=True."` Outputs stay `affected`, `report`; exposure stays `8`.
- **`code.py`**: read and validate the parallel `column_names` / `column_types` lists; read the `values` DataTree (tree access) into `rows` (branch per row) and validate each row length == column count; read `id_values` (optional) and validate `len == number of rows`; call `create_table_with_data(...)`; report rows inserted; keep the `CToggle` guard and the destructive-operation note.

## Tests — `tests/test_writer.py`

- `insert_rows`: `executemany` is called, identifiers are quoted.
- `create_table_with_data`:
  - (a) `id_values` given → `id` PK column appears in CREATE and values are bound.
  - (b) no `id_values` → identity PK in CREATE, INSERT omits `id`.
  - (c) `replace_table=True` → DROP issued before CREATE.
  - (d) row-length validation raises.
- Mock `psycopg2.connect`.
- Keep the existing `create_table` geometry tests (function retained).

## Verification

1. CreateTable with `column_names` + `column_types` + `values` (branch per row), no `id_values` → table created with identity PK, rows inserted, `affected` = N.
2. With `id_values` → `id` PK populated; the new table can JOIN to an existing table on `id`.
3. `replace_table=True` drops then recreates.
4. `conda run -n carcara pytest tests/test_writer.py -v` is green.
5. `conda run -n carcara python build_userobjects.py` builds CRC_CreateTable.

### Value coercion + quoting (string vs numeric)
GH delivers every `values` cell as a string, so an `integer` column would receive text. The INSERT is parameterized (`executemany` with `%s`), so psycopg2 already quotes text values with single quotes and binds numbers unquoted — there is **no manual quote-insertion** and it is injection-safe. The remaining fix is **type-aware coercion** of each cell to the right Python type per its declared `column_types` before binding.

Add a pure helper in `carcara/crc_modules/db/writer.py`:

`coerce_value(raw, sql_type)`:
- blank / None / empty-after-strip -> `None` (SQL NULL), for every column type.
- `integer` / `int` / `int4` / `int8` / `bigint` / `smallint` / `serial` -> `int(raw)`
- `double precision` / `real` / `numeric` / `decimal` / `float` / `float4` / `float8` -> `float(raw)`
- `boolean` / `bool` -> parse (`true`/`t`/`1`/`yes` -> True; `false`/`f`/`0`/`no` -> False)
- `text` / `varchar` / `char` / `uuid` / `date` / `timestamp` / `json` / ... and fallback -> `str(raw)`

`create_table_with_data` coerces every cell via `coerce_value` (using the column's declared type) before `executemany`; psycopg2 then quotes text (single quotes) automatically and binds numbers unquoted. `id_values` are coerced to the inferred id type the same way. **Blank cells become NULL for all column types.**

---

# Part 5 — CRC_CreateShapefile: CreateTable + auto `geom` column (not a file export)

## Context
CRC_CreateShapefile currently only INSERTs WKT geometries into an existing table (`insert_geometries`). It should instead mirror the upgraded CRC_CreateTable (Part 4): CREATE a table with attribute data AND a geometry column **always named `geom`**, with the geometry type **auto-detected**, geometry supplied as a **DataTree, branch per row** (more than one item in a branch = multipart), keeping the Cx/Cy false-origin add-back and SRID. This is a table-with-geometry ("like a shapefile"), NOT a file export.

## Decisions
- geom type: **strict single type**. All rows must share a base type (point / line / polygon) or it is an error. If any branch is multipart, the column becomes `MULTI<base>` and every row is promoted to `MULTI<base>`.
- A blank/empty `values` cell -> NULL (shared with Part 4's `coerce_value`).

## Target contract (upgraded CRC_CreateShapefile)
Inputs: `CString`, `CToggle`, `schema`, `table`, `column_names` (list, optional), `column_types` (list, parallel, optional), `values` (tree access — branch per row, optional), `id_values` (list, optional), `geometry` (tree access — branch per row; >1 item per branch = multipart; **required**), `srid` (int, default 4326), `Cx` (str, default "0"), `Cy` (str, default "0"), `replace_table` (bool).
REMOVE `geom_column` (always `geom`) and `geom_type` (auto-detected).
Outputs: `affected` (rows inserted), `report`.

## Behavior
1. Coerce data rows from `values` per `column_types` using the Part 4 `coerce_value` helper (blank -> NULL).
2. Per geometry branch `i`: convert the Rhino geom(s) to WKT via `rh_geometry_to_wkt` (`carcara/crc_modules/rhino/wkt_conversion.py`). 1 item -> a single WKT; >1 items -> combine into one `MULTI<base>` WKT (all parts must share a base type within the branch; mixed base in a branch -> error).
3. Detect the base type across all rows (strict): all rows must share a base type, else error. If any branch is multipart, the column type is `MULTI<base>` and every row is promoted to `MULTI<base>` (a single geom -> a MULTI with one member). Otherwise the singular type (`POINT` / `LINESTRING` / `POLYGON`).
4. CREATE TABLE: id PRIMARY KEY (Part 4 rules) + the data columns + `geom geometry(<detected>, <srid>)`. `replace_table` -> DROP first.
5. INSERT each row: the coerced data values + the geometry via `ST_Translate(ST_GeomFromText(%s, %s), <Cx>, <Cy>)` — Cx/Cy validated as numeric TEXT and embedded verbatim (never `float()`, never bound); wkt + srid bound via `%s`.
6. Alignment: `values` branch `i` <-> `geometry` branch `i` <-> `id_values[i]`. Validate counts are equal. `values` / `column_names` are optional, so a geometry-only table (id PK + geom) is allowed; `geometry` is required.
7. Mandatory PK always.

## Module changes — `carcara/crc_modules/db/writer.py`
Keep `create_table` and `insert_geometries` (tests + back-compat). Refactor the shared helpers out of `create_table_with_data`: `_resolve_pk(...)` and `coerce_value(...)`. ADD:
- `create_table_with_geometry(cstring, schema, table, columns, rows, geom_wkts, geom_type, srid, cx, cy, id_values=None, replace_table=False) -> int`: reuse PK resolution + coercion; CREATE the columns + id PK + `geom geometry(geom_type, srid)`; INSERT per row (coerced values + a geom `ST_Translate(ST_GeomFromText(%s, %s), <cx>, <cy>)` slot, cx/cy via `validate_offset` embedded verbatim); commit; return the row count. Pure psycopg2, no Rhino.

## Pure helpers — `carcara/crc_modules/geometry/wkt.py` (shapely, testable)
- `combine_wkts(wkts) -> str`: 1 -> as-is; >1 -> `MULTI<base>` built from same-base parts; mixed base -> `ValueError`.
- `detect_wkt_type(wkts) -> str`: returns the base/multi type token; strict (error if base types differ across the list); returns `MULTI<base>` if any item is multipart, else the singular token.
- `promote_to_multi(wkt, target_type) -> str`: wrap a single geom as a MULTI member when the column type is MULTI.

The component calls `rh_geometry_to_wkt` (Rhino) to get each per-geom WKT, then uses these pure helpers for combine/detect/promote.

## Component `code.py`
Read the inputs; per branch convert the Rhino geoms to WKT (`rh_geometry_to_wkt`) then `combine_wkts`; run `detect_wkt_type` across the rows to get `geom_type`; promote rows if the type is MULTI; call `create_table_with_geometry(...)`; report rows inserted; keep the `CToggle` guard and the destructive-operation note.

## `metadata.json`
Remove `geom_column` and `geom_type`. Change `geometry` to `tree` access (branch per row), typeHintID `ghdoc`. Add `id_values` (list, optional); `column_names` / `column_types` (lists); `values` (tree). Keep `srid`, `Cx`, `Cy`, `replace_table`. Update the description: "Creates a PostGIS table with attribute columns AND a geometry column named 'geom' (type auto-detected). Geometry is a DataTree: branch per row; more than one item per branch = multipart. Applies false-origin (Cx/Cy) add-back in SQL. Not a file export." Outputs: `affected`, `report`.

## Tests
- `tests/test_writer.py`: `create_table_with_geometry` (CREATE has `geom geometry(TYPE, srid)` + id PK; INSERT uses `ST_Translate(ST_GeomFromText(...))` with Cx/Cy verbatim; values coerced); `coerce_value` (int / float / bool / text / blank->NULL).
- `tests/test_wkt.py` (or the geometry tests): `combine_wkts` (2 polygons -> MULTIPOLYGON; mixed -> error); `detect_wkt_type` (strict error on mixed base; MULTI when multipart).

## Verification
1. Single-part polygons per branch + attributes -> table with `geom geometry(POLYGON, srid)` + id PK; rows inserted, affected = N; text columns quoted, numeric columns numeric, blanks NULL.
2. A branch with 2 polygons -> column promoted to MULTIPOLYGON, all rows MULTI; that row holds both parts.
3. Mixed base types across rows -> a clear error.
4. Cx/Cy add-back present in the SQL; geometry stored projected.
5. `conda run -n carcara pytest tests/ -v` is green.
6. `conda run -n carcara python build_userobjects.py` builds CreateShapefile.
