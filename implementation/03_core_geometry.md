# C# Migration — Phase 03: csharp_shared/Geometry.cs — NTS Port

## Goal

Port `carcara/crc_modules/geometry/` into `grasshopper/csharp_shared/Geometry.cs`
using NetTopologySuite (NTS) as the WKT/geometry engine. This file is concatenated
into components that need geometry predicates and WKT operations. No Rhino/GH
references here — pure C# logic, fully testable via canvas smoke tests.

## Depends on

- Phase 01 complete (`#r "nuget:"` confirmed working; `create_cs_ghuser` extended).

## Python behavioral specs

| C# location in Geometry.cs | Python spec |
|---|---|
| `WktUtils` static class | `carcara/crc_modules/geometry/wkt.py` |
| `Polylabel` static class | `carcara/crc_modules/geometry/polylabel.py` |
| `Containment` static class | `carcara/crc_modules/geometry/containment.py` |
| `Duplicates` static class | `carcara/crc_modules/geometry/duplicates.py` |

Read each Python file before writing C#. The Python file is the behavioral spec.

---

## Scope

`Geometry.cs` declares `#r "nuget: NetTopologySuite, 2.*"` at the top (concat step
deduplicates).

### `WktUtils` class

```csharp
static class WktUtils
{
    // Parse a WKT string to an NTS geometry.
    public static NetTopologySuite.Geometries.Geometry WktToGeometry(string wkt);

    // Serialize an NTS geometry to WKT.
    public static string GeometryToWkt(NetTopologySuite.Geometries.Geometry geom);

    // Extract (x, y) coordinate pairs from a list of WKT Point strings.
    public static List<(double x, double y)> WktListToPoints(List<string> wktPoints);
}
```
NTS WKT reader/writer: `new WKTReader()` / `new WKTWriter()` from
`NetTopologySuite.IO`.

### `Polylabel` class

Port the polylabel algorithm from `geometry/polylabel.py`. Polylabel finds the pole
of inaccessibility (point farthest from the polygon boundary) used as label anchor.
If the Python module uses NTS `LargestEmptyCircle` (available in NTS 2.x), use the
same. Otherwise port the JS polylabel algorithm (MIT-licensed).

```csharp
static class Polylabel
{
    public static (double x, double y) FindPoleOfInaccessibility(
        string polygonWkt, double precision = 1.0);
}
```

### `Containment` class

Port `geometry/containment.py`. `CRC_SortByContainer` groups geometries by which
container polygon they fall inside.

```csharp
static class Containment
{
    // Returns, for each input geometry, the index of the container that contains it
    // (-1 if none). Uses NTS Geometry.Contains / Geometry.Intersects.
    public static List<int> SortByContainer(
        List<string> geometryWkts, List<string> containerWkts);
}
```

### `Duplicates` class

Port `geometry/duplicates.py`. `CRC_IdentifyDuplicatePolylines` identifies polylines
that are geometrically identical (same vertices in same or reverse order).

```csharp
static class Duplicates
{
    public static List<int> FindDuplicatePolylines(List<string> polylineWkts);
}
```
Use `NTS.Geometry.EqualsExact()` with tolerance. Match the Python behavior for
reversed-vertex detection (check both forward and reversed coordinate order).

---

## NuGet reference

`#r "nuget: NetTopologySuite, 2.*"` at the top of `Geometry.cs`. Confirm the version
does not conflict with any NTS version bundled inside Rhino 8/Grasshopper. If Rhino
bundles an NTS version, use the same version number to avoid type-identity conflicts.

---

## Steps

1. Read `carcara/crc_modules/geometry/wkt.py` — implement `WktUtils` with
   `WKTReader` / `WKTWriter` from NTS.
2. Read `carcara/crc_modules/geometry/polylabel.py` — implement `Polylabel`. Check
   which algorithm the Python file uses (shapely `representative_point` vs a true
   polylabel) and mirror it.
3. Read `carcara/crc_modules/geometry/containment.py` — implement `Containment`.
4. Read `carcara/crc_modules/geometry/duplicates.py` — implement `Duplicates`.
5. Build a throwaway `CRC_GeomSmoke` component (or extend `CRC_HelloDB`) to test:
   - WKT round-trip: input a polygon WKT, parse with `WktToGeometry`, re-serialize,
     compare.
   - `Polylabel`: input a closed rectangle curve WKT; output should be a point near
     center.
   - `Containment`: input two polygons + a point; confirm index assignment.

---

## Validation

**Python oracle**:
```powershell
conda run -n carcara pytest tests/test_wkt.py -v
```
Port the test assertions as manual canvas checks.

**Canvas smoke test**: build a temporary component using `Geometry.cs` as a shared
prelude, wire known inputs, confirm outputs match the Python pytest expectations.

---

## Done when

- [ ] `grasshopper/csharp_shared/Geometry.cs` written with `WktUtils`, `Polylabel`,
      `Containment`, `Duplicates`.
- [ ] `#r "nuget: NetTopologySuite, 2.*"` declared (version pinned to match Rhino 8).
- [ ] WKT round-trip produces correct output (matches `wkt.py` behavior).
- [ ] `Polylabel` output matches Python for the same polygon input.
- [ ] `Containment` returns correct container indices; -1 for no match.
- [ ] `Duplicates` flags reversed-vertex polylines as Python does.
- [ ] No Rhino/GH types referenced in `Geometry.cs`.
- [ ] Python pytest suite still passes.
