# Phase 08 — Geometry: Modeling (Offset, Meshes, Predicates)

## Goal

Implement the **01.Modeling** geometry components — the Rhino-heavy modeling tools:
curve offsetting, building-footprint extrusion, and the three spatial predicates
(re-keyed here from the old Phase 07 because they are 01.Modeling, not WKT conversion).

Components delivered (5, all subcategory **01.Modeling**):

| Component                        | Module                              | Notes                                                      |
|----------------------------------|-------------------------------------|------------------------------------------------------------|
| `CRC_OffsetPython`               | `rhino/offset.py`                   | Rhino `Curve.Offset` — fully Rhino-dependent               |
| `CRC_BuildingMeshes`             | `rhino/building_mesh.py`            | Footprint + height → extruded GrdF / LatF / RftF meshes   |
| `CRC_PointInsidePolygon`         | `geometry/polylabel.py`             | Interior point: centroid → polylabel fallback              |
| `CRC_SortByContainer`            | `geometry/containment.py`           | Group points by container curve → DataTree of indexes      |
| `CRC_IdentifyDuplicatePolylines` | `geometry/duplicates.py`            | Dedup by normalized signature (start-point/direction invariant) |

> `CRC_OffsetPython` and `CRC_BuildingMeshes` are **fully Rhino-dependent** — their core
> logic lives in `carcara/crc_modules/rhino/` (per CLAUDE.md: "CRC_OffsetPython and
> CRC_BuildingMeshes are fully Rhino-dependent — their core logic lives in crc_modules/rhino/").
> Rhino submodules are **excluded from pytest**; validation is the GH checkpoint only.
>
> The three predicate components (`CRC_PointInsidePolygon`, `CRC_SortByContainer`,
> `CRC_IdentifyDuplicatePolylines`) stay pure-Python in `geometry/` and keep pytest coverage.
> Port behavior from the legacy code in `ghuser-metadata/01.modeling.md` (`Pt_Plg.py`,
> `Srt_Ctn.py`, `IdDupPol.py`).

## Inputs you must give me

For `CRC_BuildingMeshes`:

- A polygon dataset (with optional `height` attribute) from PostGIS that you can feed
  into the component on the canvas.

Everything else is already resolved from the legacy decoded scripts — see Steps below.

## Steps

### 1. Implement `carcara/crc_modules/rhino/offset.py`

Uses **Rhino's `Curve.Offset`** — no shapely, no WKT round-trip.

Legacy source: `carcara-old/ghuser-metadata/scripts/OffsetPython.py`

Legacy inputs (exact names from the decoded script):

| Input | Type | Access | Notes |
|-------|------|--------|-------|
| `Crv` | `DataTree[Rhino.Geometry.Curve]` | tree | Planar polylines. Non-planar → warning + None in output. |
| `Dist` | `DataTree[float]` | tree | Offset distances. Single value applies to all; list matches curves cyclically if counts differ. |
| `CStyle` | `int` | item | Corner style: 0=None, 1=Sharp (default), 2=Round, 3=Smooth, 4=Chamfer — maps to `rg.CurveOffsetCornerStyle`. |

Legacy outputs (exact names):

| Output | Type | Notes |
|--------|------|-------|
| `out` | str | Processing log (uses the default `out` slot, index 0). |
| `OffCrv` | `DataTree[Rhino.Geometry.Curve]` | Offset curves. Failed offsets → `None` at same branch/index. Tree structure preserved. |

Core logic to implement in `crc_modules/rhino/offset.py`:

```python
import Rhino.Geometry as rg

CORNER_STYLE_MAP = {
    0: rg.CurveOffsetCornerStyle(0),   # None
    1: rg.CurveOffsetCornerStyle.Sharp,
    2: rg.CurveOffsetCornerStyle.Round,
    3: rg.CurveOffsetCornerStyle.Smooth,
    4: rg.CurveOffsetCornerStyle.Chamfer,
}
DEFAULT_TOLERANCE = 1e-6

def get_corner_style(style_int: int):
    """Map int to CurveOffsetCornerStyle enum (default Sharp)."""

def offset_curve(curve, distance: float, corner_style, tolerance: float = DEFAULT_TOLERANCE):
    """
    Offset a single planar Rhino curve.
    Returns (offset_curve_or_None, error_message_or_None).
    Checks planarity first (curve.TryGetPlane); calls curve.Offset(plane, distance, tolerance, corner_style).
    Returns first result if list is non-empty, else (None, 'Offset operation returned no results').
    """
```

The DataTree fan-out (branch iteration, distance mapping, None-filling for failures) stays in
`code.py` — it is GH plumbing, not domain logic.

### 2. Implement `carcara/crc_modules/rhino/building_mesh.py`

Uses Rhino mesh primitives — no pure-Python mesh dict, no shapely.

Legacy source: `carcara-old/ghuser-metadata/scripts/BuildingMeshes.py`

Legacy inputs (exact names):

| Input | Type | Access | Notes |
|-------|------|--------|-------|
| `BdgFp` | `tree[Rhino.Geometry.Polyline]` | tree | Building footprint polygons. Holes auto-detected by containment analysis. Empty branches preserved. |
| `BdgH` | `tree[float]` | tree | Heights. Must match `BdgFp` tree structure. Single value applies to all footprints in branch; list must be parallel to footprints. |

Legacy outputs (exact names):

| Output | Type | Notes |
|--------|------|-------|
| `out` | str | Performance analysis report (uses default `out` slot, index 0). |
| `GrdF` | `tree[Rhino.Geometry.Mesh]` | Ground faces with holes (ngon). One mesh per building. Empty branches preserved. |
| `LatF` | `tree[Rhino.Geometry.Mesh]` | Lateral wall faces. One mesh per building. |
| `RftF` | `tree[Rhino.Geometry.Mesh]` | Rooftop faces with holes (ngon). One mesh per building. |

Key implementation details (from decoded legacy):

- **Hole detection**: `is_polygon_inside(inner, outer)` tests multiple vertices + midpoints against `outer_curve.Contains(pt, rg.Plane.WorldXY, 1e-6)`. A polygon is a hole if all test points are `PointContainment.Inside` the exterior.
- **Grouping**: `group_polygons_with_holes_and_heights` — exterior polygons (not contained in any other) are grouped with their holes; height comes from the exterior polygon's original index.
- **Ground / Roof mesh**: `create_ngon_mesh_with_holes(exterior_poly, hole_polys)`. No holes → `rg.Mesh.CreateFromClosedPolyline`. With holes → `rg.Brep.CreatePlanarBreps([exterior_curve] + hole_curves, 1e-6)` then `rg.Mesh.CreateFromBrep`. Wrap all faces in a single ngon (`rg.MeshNgon.Create`).
- **Roof mesh**: duplicate of ground mesh, translated `(0, 0, height)`.
- **Lateral walls**: one quad face per edge segment, for both exterior and each hole polygon.
- **Height handling**: single value → broadcast to all footprints; list must match footprint count exactly (no cyclic mapping); positive values only.

Functions to expose in `crc_modules/rhino/building_mesh.py`:

```python
def is_polygon_inside(inner_poly, outer_poly) -> bool: ...
def group_polygons_with_holes_and_heights(polygons, heights) -> list: ...
def create_ngon_mesh_with_holes(exterior_poly, hole_polys): ...
def create_building_mesh_with_holes(exterior_poly, hole_polys, height) -> tuple: ...
    # Returns (ground_mesh, lateral_mesh, roof_mesh) or (None, None, None)
```

### 3. Implement `carcara/crc_modules/geometry/polylabel.py`, `duplicates.py`, `containment.py`

Pure-Python. Port behavior from the legacy decoded scripts (`Pt_Plg.py`, `Srt_Ctn.py`,
`IdDupPol.py` in `carcara-old/ghuser-metadata/scripts/`). These do NOT import Rhino.

### 4. GH bundles

**`CRC_OffsetPython/`** — `metadata.json` inputs / outputs:

```
Inputs:  Crv (Curve, tree), Dist (float, tree), CStyle (int, item, optional)
Outputs: out (str), OffCrv (Curve, tree)
subcategory: 01.Modeling, exposure: 1
```

`code.py` handles: DataTree branch iteration, distance fan-out (cyclic mapping when counts
differ), calls `crc_modules.rhino.offset.offset_curve`, fills `None` for failures, logs
to `out`. No `CToggle` on this component — it runs on data arrival (matches legacy).

**`CRC_BuildingMeshes/`** — `metadata.json` inputs / outputs:

```
Inputs:  BdgFp (Polyline, tree), BdgH (float, tree)
Outputs: out (str), GrdF (Mesh, tree), LatF (Mesh, tree), RftF (Mesh, tree)
subcategory: 01.Modeling, exposure: 1
scriptParamAccess: "tree" for all three mesh outputs
```

`code.py` handles: DataTree iteration matching `BdgFp` / `BdgH` branch count, calls
`crc_modules.rhino.building_mesh` functions, fills empty branches, writes performance
summary to `out`.

**`CRC_PointInsidePolygon/`**, **`CRC_SortByContainer/`**, **`CRC_IdentifyDuplicatePolylines/`** —
follow the standard GH component pattern (CToggle guard, report output). Port inputs/outputs
from the legacy decoded scripts.

### 5. Build & install

```powershell
python build_userobjects.py
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

## Tests

Only the three pure-Python predicate modules have pytest coverage (rhino/ is excluded):

```powershell
pytest tests/test_point_inside_polygon.py tests/test_sort_by_container.py tests/test_identify_duplicates.py -v
```

`CRC_OffsetPython` and `CRC_BuildingMeshes` are validated via the GH checkpoint below.

## Grasshopper checkpoint

Restart Grasshopper.

**CRC_OffsetPython** — wire Rhino curves directly into `Crv` (no WKT converter needed).
Set `Dist = 5.0`, `CStyle = 1` (Sharp). Confirm in the Rhino viewport that offset curves
appear at the correct distance. Then test each corner style (0–4) and verify the join
behavior changes. Try negative distance to shrink. Feed a non-planar curve; confirm `out`
logs the planarity warning and `OffCrv` contains `None` at that index without crashing GH.
Try a narrow concave shape where the offset self-intersects; confirm `out` reports whatever
Rhino returns (empty result or error message).

**CRC_BuildingMeshes** — pull building footprints from PostGIS using
`CRC_GeometriesWithSpatialFilter` + height attribute via `CRC_ValuesWithSpatialFilter`
(Phase 05). Feed both into `CRC_BuildingMeshes`. Confirm:

- Three separate DataTree outputs (`GrdF`, `LatF`, `RftF`) each contain one mesh per building.
- Meshes appear in the Rhino viewport at the correct planimetric position.
- Each building has the height from the attribute column.
- Buildings with courtyard holes extrude correctly: `GrdF` and `RftF` have the hole cut out;
  `LatF` includes wall faces for the inner hole boundary.
- Single height value (`BdgH` = constant): broadcasts to all footprints.
- List of heights parallel to footprints: each building gets its own height.
- `out` shows the performance summary including counts of successful/failed buildings.

Save canvases as `tests/_manual/smoke_offset.gh`, `tests/_manual/smoke_building_meshes.gh`.

## Commit

```
feat(modeling): add rhino/offset and rhino/building_mesh modules + GH components; keep predicate modules pure-Python
```

## Done when

- [ ] `carcara/crc_modules/rhino/offset.py` exists with `offset_curve` function (Rhino `Curve.Offset`, no shapely).
- [ ] `carcara/crc_modules/rhino/building_mesh.py` exists and produces `GrdF` / `LatF` / `RftF` DataTrees with hole support.
- [ ] `carcara/crc_modules/geometry/polylabel.py`, `duplicates.py`, `containment.py` exist and are pytest-covered.
- [ ] `CRC_OffsetPython` GH bundle passes the Rhino viewport check across all 5 corner styles.
- [ ] `CRC_BuildingMeshes` GH bundle produces correct three-tree output with courtyard holes and single-vs-list height behavior verified.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
