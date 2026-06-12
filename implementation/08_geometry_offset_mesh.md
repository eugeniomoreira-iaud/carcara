# Phase 08 — Geometry: Modeling (Offset, Meshes, Predicates)

## Goal

Implement the **01.Modeling** geometry components — the Rhino-heavy modeling tools:
curve offsetting, building-footprint extrusion, and the three spatial predicates
(re-keyed here from the old Phase 07 because they are 01.Modeling, not WKT conversion).

Components delivered (5, all subcategory **01.Modeling**):

| Component                        | Module                       | Notes                                  |
|----------------------------------|------------------------------|----------------------------------------|
| `CRC_OffsetPython`               | `geometry/offset.py`         | Polygon/polyline offset (shapely)      |
| `CRC_BuildingMeshes`             | `geometry/building_mesh.py`  | Footprint + height → extruded mesh     |
| `CRC_PointInsidePolygon`         | `geometry/polylabel.py`      | Interior point: centroid → polylabel fallback |
| `CRC_SortByContainer`            | `geometry/containment.py`    | Group points by container curve → DataTree of indexes |
| `CRC_IdentifyDuplicatePolylines` | `geometry/duplicates.py`     | Dedup by normalized signature (start-point/direction invariant) |

> The last three moved from the old Phase 07. Pure algorithm (on coordinate tuples)
> stays in the listed `geometry/` modules; unavoidable RhinoCommon (curve `.Contains`,
> polyline extraction) is isolated in `crc_modules/rhino/`. Port behavior from the legacy
> code in `ghuser-metadata/01.modeling.md` (`Pt_Plg.py`, `Srt_Ctn.py`, `IdDupPol.py`).

## Inputs you must give me

For each legacy file:

1. `carcara_OffsetPython_r03.ghuser`
2. `carcara_BuildingMeshes_r03.ghuser`

Tell me:

- **OffsetPython** — input types (curve, polyline, polygon, WKT?), distance
  semantics (positive=outward for closed shapes?), join style (miter/round/bevel),
  mitre limit, handling of self-intersecting offsets.
- **BuildingMeshes** — how is height supplied (single number per footprint,
  attribute column from the DB, list parallel to footprints)? Is the output
  a Rhino `Mesh`, a `Brep`, or both? Are roofs flat or do they accept a
  pitch? Are interior holes preserved?

Also: a polygon dataset (with optional `height` attribute) you can throw at
both components on the canvas.

## Steps

1. **Implement `carcara/crc_modules/geometry/offset.py`** — pure shapely:
   ```python
   def offset_polygon(wkt: str, distance: float,
                      join_style: str = "mitre",
                      mitre_limit: float = 5.0) -> str
   def offset_polyline(wkt: str, distance: float,
                       cap_style: str = "flat",
                       join_style: str = "mitre") -> str
   ```
   Map string args to shapely's int enums. Return WKT, never shapely
   objects (keeps the boundary with Rhino in `crc_modules/rhino/`).

2. **Implement `carcara/crc_modules/geometry/building_mesh.py`** — pure Python.
   Produces a simple **mesh description** (lists of vertices + faces),
   independent of Rhino:
   ```python
   def extrude_footprint(footprint_wkt: str, height: float) -> dict
       # → {"vertices": [(x,y,z), ...], "faces": [(i,j,k,l), ...]}
   ```
   The Rhino-side adapter that converts this dict into `Rhino.Geometry.Mesh`
   lives in `carcara/crc_modules/rhino/convert.py` (added in Phase 07) — add a
   new helper `mesh_dict_to_rhino(mesh_dict)`.

3. **Tests**:
   - `tests/test_offset.py` — round-trip offset square → larger square,
     concentric output is geometrically valid.
   - `tests/test_building_mesh.py` — footprint with 4 vertices + height
     produces 8 vertices and 6 faces (top, bottom, 4 walls). Polygon with
     a hole produces correct topology (no walls collapsing, hole preserved
     in top + bottom faces).

4. **GH bundles**:
   - `CRC_OffsetPython/` — inputs: `wkt` (str or list of str), `distance`,
     `join_style`, `mitre_limit`, `run`. Outputs: `wkt`, `report`. Optional
     convenience: accept Rhino curves directly via `crc_modules.rhino.convert`,
     but document that as a secondary input mode.
   - `CRC_BuildingMeshes/` — inputs: `footprints` (list of WKT), `heights`
     (list of float), `run`. Outputs: `meshes`, `report`. Convert mesh
     dicts to Rhino meshes in `code.py` using the Rhino bridge.

5. **Build & install**.

## Tests

```powershell
pytest tests/test_offset.py tests/test_building_mesh.py -v
```

## Grasshopper checkpoint

Restart Grasshopper.

**CRC_OffsetPython** — feed a closed polyline from Rhino through
`CRC_GrasshopperGeometryToWKT` → `CRC_OffsetPython` (distance = 5.0,
join_style = "mitre") → `CRC_WKTtoGrasshopperGeometry`. Confirm in the
Rhino viewport that the result is a parallel curve at the requested offset.
Try negative distance to shrink. Try a self-intersecting offset on a
narrow concave shape; confirm `report` shows whatever shapely says
(possibly an empty polygon, possibly an error).

**CRC_BuildingMeshes** — pull building footprints from PostGIS using
`CRC_GeometriesWithSpatialFilter` + an attribute column for height via
`CRC_ValuesWithSpatialFilter` (Phase 05). Feed both into
`CRC_BuildingMeshes`. Confirm:

- Meshes appear in the Rhino viewport at the correct planimetric position.
- Each building has the height from the attribute column.
- Buildings with holes (e.g. courtyards) extrude correctly without filled
  cores.
- `report = "OK – N meshes"`.

Save canvases as `tests/_manual/smoke_offset.gh`,
`tests/_manual/smoke_building_meshes.gh`.

## Commit

```
feat(geometry): add offset and building-mesh modules + components
```

## Done when

- [ ] `carcara/crc_modules/geometry/offset.py` and `carcara/crc_modules/geometry/building_mesh.py` exist.
- [ ] Pytest covers both.
- [ ] Both GH bundles produce visible, correct geometry in Rhino.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
