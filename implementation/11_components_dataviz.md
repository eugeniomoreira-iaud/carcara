# C# Migration — Phase 11: C# Script Components — 04.Dataviz (10 components)

## Goal

Convert the 10 components in subcategory **04.Dataviz** from Python `code.py` script
bundles to C# `code.cs` script bundles, built as `.ghuser` via `componentize_cs.py`.
`CRC_CurveDisplay` is already done and is the proven template — note it as the
reference implementation and leave its bundle unchanged.

`instanceGuid` values ported verbatim from existing Python `metadata.json`.

## Depends on

- Phase 01 (toolchain; `CRC_CurveDisplay` is the template).
- Phase 05 (`Svg.cs` — SVG export).
- Phase 06 (`Viz.cs` — chart rendering as Rhino geometry + SVG).
- Phase 04 (`RhinoGeometry.cs` — curve→coordinate conversion for SVG export).

## Component inventory — 04.Dataviz

| # | Bundle folder | Shared C# preludes | Python spec | Notes |
|---|---|---|---|---|
| 24 | `CRC_CurveDisplay` | *(none — self-contained)* | `code.cs` (already C#) | **Already done. Template.** |
| 25 | `CRC_PolylineToSVG` | `Svg.cs`, `RhinoGeometry.cs` | `crc_modules/svg/export.py` | |
| 26 | `CRC_CircleToSVG` | `Svg.cs`, `RhinoGeometry.cs` | `crc_modules/svg/export.py` | |
| 27 | `CRC_NurbsToSVG` | `Svg.cs`, `RhinoGeometry.cs` | `crc_modules/svg/export.py` | |
| 28 | `CRC_TextToSVG` | `Svg.cs` | `crc_modules/svg/export.py` | |
| 29 | `CRC_Histogram` | `Viz.cs`, `Svg.cs` | `crc_modules/viz/histogram.py` | |
| 30 | `CRC_ScatterPlot` | `Viz.cs`, `Svg.cs` | `crc_modules/viz/scatter.py` | |
| 31 | `CRC_LinePlot` | `Viz.cs`, `Svg.cs` | `crc_modules/viz/lineplot.py` | |
| 32 | `CRC_Heatmap` | `Viz.cs`, `Svg.cs`, `Utils.cs` | `crc_modules/viz/heatmap.py` | needs ColorUtils |
| 33 | `CRC_SaveSVG` | `Svg.cs` | `crc_modules/svg/save.py` | |

Before writing C#, open each `metadata.json` and `code.py`. Copy `instanceGuid`
verbatim. Confirm `CRC_CurveDisplay` `instanceGuid` remains
`"d4e1f6a2-7b83-4c50-9e1d-3a8c2f0b6d44"` — do not modify that bundle.

---

## Scope

### `CRC_CurveDisplay` — already done; use as the template

The existing `grasshopper/components/CRC_CurveDisplay/code.cs` is a working C# script
component. It implements `IGH_PreviewObject` (the reason Python cannot replace it) and
is already being built via `componentize_cs.py`. **Leave this bundle untouched.**
Reference it when writing the other `code.cs` files to understand the
`GH_ScriptInstance` / `BeforeRunScript` / `DrawViewportWires` pattern.

### SVG export components (25–28)

Each takes a list of GH geometry objects and style parameters; outputs an SVG element
fragment string (not a full SVG document). Users chain fragments into `CRC_SaveSVG`.

Pattern for `CRC_PolylineToSVG`:
```csharp
// Shared preludes: Svg.cs, RhinoGeometry.cs
// Inputs: Polylines (List<Rhino.Geometry.Curve>), Stroke (string), StrokeWidth (double), Fill (string)
// Outputs: SVG (string), report (string)

SVG = "";
report = "No geometry";
try
{
    var coords = Polylines.Select(c => WktToRhino.CurveToCoordList(c)).ToList();
    var style = new SvgStyle { Stroke = Stroke, StrokeWidth = StrokeWidth, Fill = Fill, Opacity = 1.0 };
    SVG = SvgExport.PolylinesToSvg(coords, style);
    report = $"OK – {Polylines.Count} polylines";
}
catch (Exception ex) { report = "ERROR: " + ex.Message; }
```

Add a `CurveToCoordList` helper to `RhinoGeometry.cs` if not already present (reads
curve vertices as `(double x, double y)` list). Mirror `code.py` input structure exactly.

### Chart components (29–32)

Each takes numeric data plus labeling parameters; outputs:
- `RhinoGeom` (`List<GeometryBase>`) — Rhino geometry for canvas preview.
- `SVGContent` (string) — SVG string for export.

```csharp
// CRC_Histogram example
// Shared preludes: Viz.cs, Svg.cs
// Inputs: Values (List<double>), Bins (int), Title (string), XLabel (string), YLabel (string)
// Outputs: RhinoGeom (List<GeometryBase>), SVGContent (string), report (string)

try
{
    var result = Histogram.Render(Values, Bins, Title, XLabel, YLabel);
    RhinoGeom = result.RhinoGeometry;
    SVGContent = result.SvgContent;
    report = "OK";
}
catch (Exception ex) { report = "ERROR: " + ex.Message; }
```

Read each `code.py` to confirm whether the Python component writes the SVG file
automatically or outputs the SVG string — replicate the Python output contract.

### `CRC_SaveSVG` (33)

Inputs: `SVGElements` (str list), `FilePath` (str), `Width` (number), `Height` (number),
`Units` (str, default `"mm"`), `CToggle` (bool).
Output: `report` (str).

```csharp
report = "Set CToggle to True";
if (CToggle)
{
    try
    {
        var doc = SvgExport.WrapSvgDocument(SVGElements, Width, Height, Units);
        var (ok, msg) = SvgSave.SaveSvg(doc, FilePath);
        report = ok ? $"OK – saved to {FilePath}" : "ERROR: " + msg;
    }
    catch (Exception ex) { report = "ERROR: " + ex.Message; }
}
```

---

## Steps

1. Read all 10 `metadata.json` + `code.py` (or `code.cs` for CurveDisplay).
   Confirm inputs/outputs. Note that CurveDisplay needs no changes.
2. Copy `instanceGuid` verbatim for components 25–33; add `"csharp_shared"` lists.
3. Implement components 25–28 (SVG export) first — thin wrappers; easiest to validate.
4. Implement `CRC_SaveSVG` (33).
5. Implement chart components 29–32.
6. Build: `conda run -n carcara python build_userobjects.py`.
7. Canvas validation.

---

## Validation

**Canvas checkpoints**:
1. `CRC_CurveDisplay` (already works): connect a Curve, Width=2, Colour=red → curve
   appears in viewport with correct weight and color. Dash input `"2 1"` → dashed.
2. `CRC_PolylineToSVG` + `CRC_SaveSVG`: draw a simple polyline on the canvas, route
   through both, confirm SVG file is written and opens correctly in a browser.
3. `CRC_Histogram`: connect `{1, 2, 2, 3, 3, 3, 4}`, bins=4 → `RhinoGeom` output
   contains bar rectangle curves; bake to confirm geometry is visible.
4. All 10 components appear in **Carcara → 04.Dataviz**.

---

## Done when

- [ ] `CRC_CurveDisplay` bundle unchanged; still builds and loads.
- [ ] All 9 remaining `code.cs` files written (25–33).
- [ ] All `metadata.json` updated with `instanceGuid` (verbatim) and `"csharp_shared"`.
- [ ] All 10 `.ghuser` files build.
- [ ] All 10 appear in GH toolbar under **Carcara → 04.Dataviz**.
- [ ] Canvas checkpoints 1–3 confirmed by owner.
- [ ] Python pytest suite still passes.
