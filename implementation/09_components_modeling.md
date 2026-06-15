# C# Migration — Phase 09: C# Script Components — 01.Modeling (6 components)

## Goal

Convert the 6 components in subcategory **01.Modeling** from Python `code.py` script
bundles to C# `code.cs` script bundles, built as `.ghuser` via `componentize_cs.py`.
These components are Rhino-heavy — they consume and produce `Curve`, `Mesh`, `Point3d`,
and `Color` objects natively. Core logic comes from `grasshopper/csharp_shared/Geometry.cs`
(pure), `RhinoGeometry.cs` (RhinoCommon-dependent), and `Utils.cs`.

`instanceGuid` values ported verbatim from existing Python `metadata.json`.

## Depends on

- Phase 01 (toolchain).
- Phase 03 (`Geometry.cs` — polylabel, containment, duplicates).
- Phase 04 (`RhinoGeometry.cs` — offset, building mesh, WKT↔Rhino).
- Phase 07 (`Utils.cs` — color).

## Component inventory — 01.Modeling

| # | Bundle folder | Shared C# preludes | Python spec |
|---|---|---|---|
| 1 | `CRC_BuildingMeshes` | `RhinoGeometry.cs` | `crc_modules/rhino/building_mesh.py` |
| 2 | `CRC_IdentifyDuplicatePolylines` | `Geometry.cs`, `RhinoGeometry.cs` | `crc_modules/geometry/duplicates.py` |
| 3 | `CRC_OffsetPython` | `RhinoGeometry.cs` | `crc_modules/rhino/offset.py` |
| 4 | `CRC_PointInsidePolygon` | `Geometry.cs`, `RhinoGeometry.cs` | `crc_modules/geometry/polylabel.py` |
| 5 | `CRC_SortByContainer` | `Geometry.cs`, `RhinoGeometry.cs` | `crc_modules/geometry/containment.py` |
| 6 | `CRC_ColorCalculator` | `Utils.cs` | `crc_modules/utils/color.py` |

Before writing C#, open each `metadata.json` and `code.py` to confirm inputs, outputs,
and nicknames. Copy `instanceGuid` verbatim.

---

## Scope

Modeling components do not take `CString` / `CToggle` — they operate on local geometry
already on the canvas (no DB calls). No `CToggle` guard needed.

### `CRC_BuildingMeshes`

Inputs: `Curve` (list), `Height` (number).
Output: `Mesh` (list) — one closed mesh per footprint.
```csharp
// code.cs body
meshes = new List<Rhino.Geometry.Mesh>();
for (int i = 0; i < footprints.Count; i++)
{
    var m = BuildingMesh.BuildFromFootprint(footprints[i], height);
    if (m != null) meshes.Add(m);
}
```

### `CRC_IdentifyDuplicatePolylines`

Inputs: `Polylines` (list of Curve).
Outputs: `DuplicateIndices` (list of int), `Unique` (list of Curve), `report`.
Convert each input curve to WKT via `WktToRhino.RhinoCurveToWkt`, call
`Duplicates.FindDuplicatePolylines(wktList)`, map indices back to curves.

### `CRC_OffsetPython`

Inputs: `Curve` (item), `Distance` (number), `Plane` (optional).
Output: `OffsetCurve` (Curve list), `report`.
Call `RhinoOffset.OffsetCurve(curve, distance, plane)`.

### `CRC_PointInsidePolygon`

Inputs: `Polygon` (Curve list — closed polygons).
Output: `Point` (Point3d list), `report`.
For each curve: `RhinoCurveToWkt` → `Polylabel.FindPoleOfInaccessibility` → `Point3d(x, y, 0)`.

### `CRC_SortByContainer`

Inputs: `Geometries` (Curve list), `Containers` (Curve list, polygons).
Output: `Sorted` (DataTree — one branch per container), `report`.
Convert both lists to WKT → `Containment.SortByContainer` → build DataTree by
container index (curves with index `-1` go to an "unmatched" branch or are omitted
per Python behavior — read `code.py` to confirm).

### `CRC_ColorCalculator`

Inputs: `Values` (list of number), `Colormap` (string, optional, default `"viridis"`).
Output: `Colors` (list of `System.Drawing.Color`).
Call `ColorUtils.MapValuesToColors(values, colormap)` → convert `(r, g, b)` to
`System.Drawing.Color.FromArgb(255, r, g, b)`.

---

## Steps

1. Read each `grasshopper/components/CRC_<Name>/code.py` and `metadata.json`
   (behavioral spec). Confirm inputs/outputs against the Scope above.
2. Copy `instanceGuid` verbatim; add `"csharp_shared"` to each `metadata.json`.
3. Write `code.cs` for all 6. Reuse icons (no change needed).
4. Build: `conda run -n carcara python build_userobjects.py`.
5. Canvas validation (see checkpoints).

---

## Validation

No .NET unit tests at this phase. Canvas-only.

**Canvas checkpoints**:
1. Drop `CRC_PointInsidePolygon` on a rectangle → point near center.
2. Drop `CRC_ColorCalculator` with `{0, 0.5, 1}` → 3 distinct colors on viridis ramp.
3. Drop `CRC_BuildingMeshes` on a closed curve + height=5 → mesh with non-zero face
   count, visually closed.
4. Drop `CRC_IdentifyDuplicatePolylines` on two identical lines (one reversed) →
   index 1 flagged as duplicate.
5. Drop `CRC_SortByContainer` with a set of points and two non-overlapping polygons →
   DataTree branch 0 = points inside polygon 0, branch 1 = points inside polygon 1.
6. All 6 components appear in **Carcara → 01.Modeling**.

---

## Done when

- [ ] All 6 `code.cs` files written.
- [ ] All `metadata.json` updated with `instanceGuid` (verbatim) and `"csharp_shared"`.
- [ ] All 6 `.ghuser` files build.
- [ ] All 6 appear in GH toolbar under **Carcara → 01.Modeling**.
- [ ] Canvas checkpoints 1–5 confirmed by owner.
- [ ] Python pytest suite still passes.
