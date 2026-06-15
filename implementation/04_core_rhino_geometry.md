# C# Migration — Phase 04: csharp_shared/RhinoGeometry.cs — RhinoCommon Port

## Goal

Port `carcara/crc_modules/rhino/` into `grasshopper/csharp_shared/RhinoGeometry.cs`.
This is the one shared file that carries RhinoCommon references — it converts between
NTS/WKT and Rhino types, builds meshes, and offsets curves. Validation is by GH canvas
only (no unit tests — RhinoCommon requires a running Rhino context).

`CRC_CurveDisplay` is already a working C# script component and is the template for
this whole approach; its logic does **not** need to be re-ported here.

## Depends on

- Phase 01 (toolchain, prelude concat confirmed).
- Phase 03 (`Geometry.cs` / NTS WKT utils — used by the WKT↔Rhino bridge).

## Python behavioral specs

| C# location in RhinoGeometry.cs | Python spec |
|---|---|
| `WktToRhino` static class | `carcara/crc_modules/rhino/` WKT conversion functions |
| `RhinoOffset` static class | `carcara/crc_modules/rhino/offset.py` |
| `BuildingMesh` static class | `carcara/crc_modules/rhino/building_mesh.py` |

`CRC_CurveDisplay`: the source is `grasshopper/components/CRC_CurveDisplay/code.cs`
(already a working C# script). Its logic stays in `code.cs` — do not abstract it into
a shared file unless a second component needs the same preview logic.

---

## Scope

`RhinoGeometry.cs` does **not** declare any `#r "nuget:"` directives — Rhino 8
provides RhinoCommon and Grasshopper to C# script components automatically. NTS
types come from `Geometry.cs` (concatenated before this file when needed).

### `WktToRhino` class

Bridges WKT strings (from DB queries) to RhinoCommon types for GH component outputs:

```csharp
static class WktToRhino
{
    // Convert a WKT string to a RhinoCommon GeometryBase suitable for GH output.
    // POINT    → Point3d
    // LINESTRING / POLYGON rings → PolylineCurve
    // MULTIPOLYGON / GEOMETRYCOLLECTION → List<GeometryBase> (caller flattens)
    public static Rhino.Geometry.GeometryBase WktToRhinoGeometry(string wkt);

    // Convert a RhinoCommon Curve to a WKT LINESTRING or POLYGON string.
    public static string RhinoCurveToWkt(Rhino.Geometry.Curve curve);

    // Convert a list of RhinoCommon Point3d to WKT MULTIPOINT.
    public static string RhinoPointsToWkt(IEnumerable<Rhino.Geometry.Point3d> points);
}
```

Coordinate mapping for `WktToRhinoGeometry`:
- `POINT` → `new Point3d(x, y, 0)`
- `LINESTRING` → `new PolylineCurve(points)`
- `POLYGON` → exterior ring as `PolylineCurve`; interior holes noted on the
  geometry or returned as separate curves (match Python `wkt.py` behavior exactly).
- `MULTIPOLYGON` / `GEOMETRYCOLLECTION` → list of the above (caller iterates).

### `RhinoOffset` class

Port `rhino/offset.py`. `CRC_OffsetPython` takes a closed polyline and a distance;
returns the offset polyline via RhinoCommon `Curve.Offset`.

```csharp
static class RhinoOffset
{
    public static Rhino.Geometry.Curve[] OffsetCurve(
        Rhino.Geometry.Curve curve, double distance,
        Rhino.Geometry.Plane plane);
}
```
Read `offset.py` for the exact `Curve.Offset` parameters (tolerance, corner style).
Match Python defaults.

### `BuildingMesh` class

Port `rhino/building_mesh.py`. `CRC_BuildingMeshes` extrudes a flat footprint polygon
by a height value to produce a closed mesh.

```csharp
static class BuildingMesh
{
    public static Rhino.Geometry.Mesh BuildFromFootprint(
        Rhino.Geometry.Curve footprint, double height);
}
```
Read `building_mesh.py` for the extrusion strategy (cap method, side faces, weld
threshold). Match Python output — same face count, same weld behavior.

---

## Steps

1. Read `carcara/crc_modules/rhino/` Python files before writing C#.
2. Implement `WktToRhino`: start with POINT and LINESTRING; add POLYGON and
   multi-types. Test with `CRC_WKTtoGrasshopperGeometry` component (Phase 10).
3. Implement `RhinoOffset`. Read `offset.py` for parameters.
4. Implement `BuildingMesh`. Read `building_mesh.py` for extrusion logic.
5. `CRC_CurveDisplay` (`code.cs`) stays as-is — it is the proven template and
   does not need changes.

---

## Validation

Canvas-only (RhinoCommon requires Rhino context):

- `WktToRhino`: build a temporary component that takes a WKT string input, calls
  `WktToRhino.WktToRhinoGeometry`, outputs `GeometryBase`. Drop a panel with
  `"POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0))"` — should bake as a 10-unit square.
- `RhinoOffset`: drop `CRC_OffsetPython` (Phase 09 component) on a closed rectangle;
  confirm offset curve appears at the correct distance.
- `BuildingMesh`: drop `CRC_BuildingMeshes` (Phase 09) on a closed curve with
  height=5; confirm mesh has non-zero face count and is closed.

Python oracle for WKT conversion behavior:
```powershell
conda run -n carcara pytest tests/test_wkt.py -v
```

---

## Done when

- [ ] `grasshopper/csharp_shared/RhinoGeometry.cs` written with `WktToRhino`,
      `RhinoOffset`, `BuildingMesh`.
- [ ] No `#r "nuget:"` directives needed (Rhino provides RhinoCommon automatically).
- [ ] WKT→Rhino conversion produces correct geometry types for POINT, LINESTRING,
      POLYGON, MULTIPOLYGON.
- [ ] Rhino→WKT conversion matches Python `wkt.py` output format.
- [ ] `RhinoOffset` behavior matches `offset.py`.
- [ ] `BuildingMesh` behavior matches `building_mesh.py`.
- [ ] `CRC_CurveDisplay.ghuser` still builds and loads without regression.
- [ ] Canvas validation for WKT conversion, offset, and mesh confirmed by owner.
