# C# Migration — Phase 06: csharp_shared/Viz.cs — Chart Rendering Port

## Goal

Port `carcara/crc_modules/viz/` (histogram, scatter, lineplot, heatmap) into
`grasshopper/csharp_shared/Viz.cs`. Charts output **Rhino geometry** (lines,
rectangles, text objects drawn on the GH canvas) and **hand-rolled SVG strings**
via `Svg.cs` — mirroring the Python `crc_modules/viz/` matplotlib behavior exactly
in terms of what the user sees. No raster image library (no SkiaSharp, no ScottPlot).

## Depends on

- Phase 01 (toolchain).
- Phase 05 (`Svg.cs` — used for SVG output path of chart components).
- Phase 04 (`RhinoGeometry.cs` — used only if chart components need to output Rhino
  geometry objects; see Scope).

## Python behavioral specs

| C# location in Viz.cs | Python spec |
|---|---|
| `Histogram` static class | `carcara/crc_modules/viz/histogram.py` |
| `ScatterPlot` static class | `carcara/crc_modules/viz/scatter.py` |
| `LinePlot` static class | `carcara/crc_modules/viz/lineplot.py` |
| `Heatmap` static class | `carcara/crc_modules/viz/heatmap.py` |

Read each Python file before writing C#. The Python files use matplotlib — understand
what geometry they draw (bars, axes, dots, grid lines, labels) and replicate that
structure in C#.

---

## Rendering approach (settled)

**No raster/bitmap library.** Charts output two things:

1. **Rhino geometry** (for the GH canvas preview): `List<Rhino.Geometry.GeometryBase>`
   containing lines, rectangles (as `Rectangle3d` or `PolylineCurve`), and
   `Rhino.Geometry.TextEntity` objects for labels and axis tick marks. The GH component
   sets these as output and optionally passes them to a Custom Preview or bakes them.

2. **SVG string** (for file export): the same chart rendered as SVG elements via
   `SvgExport` from `Svg.cs`. The GH component passes this to `CRC_SaveSVG` or outputs
   the string directly.

This is the same behavioral split the Python components have: matplotlib renders to
screen (canvas preview) and to an SVG/PNG file (export).

---

## Scope

`Viz.cs` is concatenated together with `Svg.cs` (listed in `"csharp_shared"` in
`metadata.json`) for chart components. No `#r "nuget:"` directives needed: Rhino
provides RhinoCommon, and SVG uses `System.Xml.Linq`.

### Common chart result type

```csharp
class ChartResult
{
    public List<Rhino.Geometry.GeometryBase> RhinoGeometry; // canvas preview
    public string SvgContent;                               // SVG for export
}
```

### `Histogram` class

```csharp
static class Histogram
{
    // Read viz/histogram.py for: bin count calculation, bar width, axis labels,
    // default color, grid lines.
    public static ChartResult Render(
        IEnumerable<double> values,
        int bins, string title, string xLabel, string yLabel,
        string color = "#1f77b4");
}
```

Rhino geometry output: one `PolylineCurve` rectangle per bin (bar), plus line
segments for axes and grid, plus `TextEntity` objects for tick labels and title.
SVG output: `<rect>` elements for bars, `<line>` for axes, `<text>` for labels
(via `SvgExport.PolylinesToSvg` and `SvgExport.TextsToSvg`).

### `ScatterPlot` class

```csharp
static class ScatterPlot
{
    public static ChartResult Render(
        IEnumerable<double> xValues, IEnumerable<double> yValues,
        string title, string xLabel, string yLabel,
        string color = "#1f77b4", double markerSize = 5.0);
}
```
Rhino geometry: `Circle` objects (or small `PolylineCurve` diamonds) per data point,
plus axis lines and labels. SVG: `<circle>` elements via `SvgExport.CirclesToSvg`.

### `LinePlot` class

```csharp
static class LinePlot
{
    public static ChartResult Render(
        IEnumerable<double> xValues, IEnumerable<double> yValues,
        string title, string xLabel, string yLabel,
        string color = "#1f77b4", double lineWidth = 1.5);
}
```
Rhino geometry: `PolylineCurve` connecting data points, plus axes. SVG:
`<polyline>` via `SvgExport.PolylinesToSvg`.

### `Heatmap` class

```csharp
static class Heatmap
{
    public static ChartResult Render(
        double[,] matrix,
        string title, string colormap = "viridis");
}
```
Rhino geometry: a grid of colored `PolylineCurve` rectangles (one per cell); color
mapped via `Utils.MapToColor` (Phase 07). SVG: `<rect>` elements with `fill` color.

---

## Steps

1. Read all four Python files (`histogram.py`, `scatter.py`, `lineplot.py`,
   `heatmap.py`). Note the axis scaling math, default dimensions (canvas size in
   pixels for matplotlib → choose equivalent units for Rhino geometry, e.g. 200×150
   Rhino units centered near origin).
2. Implement `ChartResult` type.
3. Implement `Histogram.Render` — bar geometry first, then axes, then labels.
4. Implement `ScatterPlot.Render`.
5. Implement `LinePlot.Render`.
6. Implement `Heatmap.Render` — requires `Utils.MapToColor` (stub until Phase 07).
7. Build a temporary component using `Viz.cs` + `Svg.cs` as shared preludes; test
   with hard-coded data.

---

## Validation

**Python oracle**: run the Python charts (`histogram.py` etc.) with test data; observe
the matplotlib output to understand bar widths, axis positions, label placement.
Replicate those proportions in Rhino geometry units.

**Canvas smoke test**:
- Connect `{1, 2, 2, 3, 3, 3, 4}` to a chart component; confirm Rhino geometry
  output has the expected number of bar rectangles.
- Confirm SVG string contains `<rect>` (histogram) or `<circle>` (scatter) elements.
- Optionally route SVG string to `CRC_SaveSVG` and open in a browser.

---

## Done when

- [ ] `grasshopper/csharp_shared/Viz.cs` written with `Histogram`, `ScatterPlot`,
      `LinePlot`, `Heatmap`.
- [ ] No raster/bitmap library referenced.
- [ ] `ChartResult.RhinoGeometry` contains correct geometry primitives for each chart
      type (bars, dots, lines, cells).
- [ ] `ChartResult.SvgContent` contains correct SVG elements matching Python svgwrite
      output structure.
- [ ] Axis scaling, default colors, and label placement match Python matplotlib behavior.
- [ ] Canvas smoke test confirms geometry output is non-empty for all four chart types.
- [ ] Python pytest suite still passes.
