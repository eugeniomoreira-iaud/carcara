# C# Migration — Phase 05: csharp_shared/Svg.cs — SVG Export Port

## Goal

Port `carcara/crc_modules/svg/` into `grasshopper/csharp_shared/Svg.cs`. The SVG
export layer converts coordinate sequences (already in local coordinates) to SVG
elements and writes files to disk. No DB, no Rhino canvas interaction — pure string
and file I/O. No extra NuGet dependency: use `System.Xml.Linq` (available in .NET
without any `#r "nuget:"`).

## Depends on

- Phase 01 (toolchain, prelude concat).
- Phase 03 (`Geometry.cs` — coordinate types used if SVG input comes from WKT).

## Python behavioral specs

| C# location in Svg.cs | Python spec |
|---|---|
| `SvgExport` static class | `carcara/crc_modules/svg/export.py` |
| `SvgSave` static class | `carcara/crc_modules/svg/save.py` |

Read both Python files in full before writing C#. The SVG output format must match
the Python `svgwrite` output (same element types, same attribute names, same
coordinate precision) so downstream SVG workflows are not broken.

---

## Scope

`Svg.cs` declares no `#r "nuget:"` directives — `System.Xml.Linq` is part of .NET
base and available in Rhino's C# script runtime.

### `SvgExport` class

Build SVG using `System.Xml.Linq` (`XDocument` / `XElement`). The SVG elements Carcara
uses are simple: `<polyline>`, `<circle>`, `<path>`, `<text>`. Hand-rolling them with
XLinq gives full control and no extra dependency.

```csharp
static class SvgExport
{
    // Convert a list of 2D polyline coordinate sequences to SVG <polyline> elements.
    public static string PolylinesToSvg(
        IEnumerable<IEnumerable<(double x, double y)>> polylines,
        SvgStyle style);

    // Convert circles (center + radius) to SVG <circle> elements.
    public static string CirclesToSvg(
        IEnumerable<(double cx, double cy, double r)> circles,
        SvgStyle style);

    // Convert NURBS curves (sampled to polylines) to SVG <path> elements.
    public static string NurbsCurvesToSvg(
        IEnumerable<IEnumerable<(double x, double y)>> sampledPoints,
        SvgStyle style);

    // Convert text annotations to SVG <text> elements.
    public static string TextsToSvg(
        IEnumerable<(double x, double y, string text, double size)> texts,
        SvgStyle style);

    // Wrap SVG element fragments in a full SVG document with a viewBox.
    public static string WrapSvgDocument(
        IEnumerable<string> elements,
        double width, double height, string units = "mm");
}

// Style record (or simple class with public fields).
class SvgStyle
{
    public string Stroke;
    public double StrokeWidth;
    public string Fill;
    public double Opacity;
}
```

The geometry input is already in local coordinates (DB correction applied at query
time). No additional coordinate transformation here.

### `SvgSave` class

```csharp
static class SvgSave
{
    // Write an SVG string to disk (UTF-8, no BOM).
    public static (bool ok, string message) SaveSvg(string svgContent, string filePath);
}
```

---

## Steps

1. Read `carcara/crc_modules/svg/export.py` — note the attribute names, coordinate
   format (decimal places), and viewBox calculation.
2. Read `carcara/crc_modules/svg/save.py` — note encoding and error handling.
3. Implement `SvgStyle` class.
4. Implement `SvgExport` methods. Match `svgwrite` attribute names (`points=`,
   `stroke=`, `stroke-width=`, `fill=`, etc.).
5. Implement `SvgSave` with `File.WriteAllText(path, content, Encoding.UTF8)`.
6. Build a temporary component with `Svg.cs` as prelude; test with hard-coded
   coordinate inputs.

---

## Validation

**Python oracle**:
```powershell
conda run -n carcara pytest tests/test_svg.py -v
```
Use these tests to understand expected SVG attribute format.

**Canvas smoke test**: a temporary component calls `SvgExport.PolylinesToSvg` with
a known coordinate list, outputs the SVG string, and optionally calls `SvgSave.SaveSvg`
to write to disk. Open the output SVG in a browser — confirm it matches the Python
`svgwrite` output visually.

---

## Done when

- [ ] `grasshopper/csharp_shared/Svg.cs` written with `SvgExport` and `SvgSave`.
- [ ] No `#r "nuget:"` directives (System.Xml.Linq is available without NuGet).
- [ ] `<polyline>`, `<circle>`, `<path>`, `<text>` element attribute format matches
      Python `svgwrite` output.
- [ ] `WrapSvgDocument` produces a valid SVG root with correct `viewBox`.
- [ ] `SvgSave.SaveSvg` writes UTF-8 file and returns `(true, ...)` on success.
- [ ] Python pytest suite still passes.
