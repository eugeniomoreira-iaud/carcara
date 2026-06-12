# Phase 07 — WKT⇄GH Conversion (`geometry/wkt.py` + 2 converter components)

## Goal

Close the loop between PostGIS WKT strings (Phase 05) and Rhino geometry on the
Grasshopper canvas. This phase ships **only the two WKT⇄GH converters** — both in
subcategory **03.Utilities**. This is the first phase that **needs Rhino geometry
types**, so we are careful: pure WKT logic stays in `crc_modules/geometry/wkt.py`
(importable outside Rhino); the RhinoCommon conversion lives in `crc_modules/rhino/`,
the only place allowed to `import Rhino`.

> **Re-keyed (subcategories corrected against the `CLAUDE.md` master map).** An earlier
> draft of this phase bundled 7 components under one module. They actually span three
> subcategories and four modules, so the other five move to the phases that match their
> real subcategory / core module:
>
> | Component | Subcat | Core module | Now built in |
> |---|---|---|---|
> | `CRC_WKTtoGrasshopperGeometry` | 03.Utilities | `geometry/wkt.py` | **this phase** |
> | `CRC_GrasshopperGeometryToWKT` | 03.Utilities | `geometry/wkt.py` | **this phase** |
> | `CRC_GeometryEntities` | 02.Queries | `db/spatial_query.py` | Phase 05 (it's a DB geometry **download** — auto-detected geometry column + PK — not a WKT classifier) |
> | `CRC_PointInsidePolygon` | 01.Modeling | `geometry/polylabel.py` | Phase 08 |
> | `CRC_SortByContainer` | 01.Modeling | `geometry/containment.py` | Phase 08 |
> | `CRC_IdentifyDuplicatePolylines` | 01.Modeling | `geometry/duplicates.py` | Phase 08 |
> | `CRC_CurveDisplay` | 04.Dataviz | `rhino/curve_display.cs` (C#) | Phase 10 |

> **Coordinate correction does NOT live here (see CLAUDE.md → Coordinate Correction).**
> The two converters are **correction-free**. By the time WKT reaches the converter it is
> already **local** (Phase 05's SELECT subtracted `Cx`/`Cy` in SQL); GH geometry handed to
> the converter is still local and the write (Phase 06) adds `Cx`/`Cy` back in SQL. The
> false-origin shift happens in exactly one layer — the SQL. Do **not** add `Cx`/`Cy`
> inputs to these converters.

Components delivered (2):

| Component                      | Subcat       | Notes                          |
|--------------------------------|--------------|--------------------------------|
| `CRC_WKTtoGrasshopperGeometry` | 03.Utilities | WKT string → Rhino geometry    |
| `CRC_GrasshopperGeometryToWKT` | 03.Utilities | Rhino geometry → WKT string    |

## Inputs you must give me

For the two legacy `.ghuser` (`carcara_WKTtoGrasshopperGeometry_r02.ghuser`,
`carcara_GrasshopperGeometryToWKT_r02.ghuser`): input names, output names, types,
item/list/tree access. Specifically:

- **WKTtoGrasshopperGeometry** — does the legacy emit `Point3d`, `Curve`, `Brep`,
  mixed? What does it do with `MULTI*` and `GEOMETRYCOLLECTION`? (The legacy uses
  `construct_gh_geom`; mirror its multipart/branch behavior.)
- **GrasshopperGeometryToWKT** — what input types are accepted? Uniform-type
  enforcement? Single vs `MULTI*` output rules? (Legacy uses `construct_wkt` /
  `gh_polygon_to_wkt` / `gh_multipolygon_to_wkt`.)

## Steps

1. **Implement `carcara/crc_modules/geometry/wkt.py`** — pure shapely, no Rhino:
   ```python
   def wkt_to_shapely(wkt)
   def shapely_to_wkt(geom)
   def wkt_list_to_points(wkt_list)  # list of (x,y) tuples
   def classify_wkt(wkt) -> str       # 'POINT' | 'LINESTRING' | 'POLYGON' | 'MULTI*' | …
   ```
   `classify_wkt` is a shared helper (used to drive single vs MULTI* handling), not a
   standalone component. The modeling predicates (`point_in_polygon`,
   `sort_by_container`, `identify_duplicates`) are **not** here — they live in their own
   `geometry/` modules and ship in Phase 08.

2. **Tests** `tests/test_wkt.py`:
   - Round-trip: `shapely_to_wkt(wkt_to_shapely(s)) == s` for canonical shapes.
   - `classify_wkt` for each geometry type incl. `MULTI*`.
   - `wkt_list_to_points` for a list of `POINT(...)`.

3. **Create `carcara/crc_modules/rhino/convert.py`** — the **only** place in
   `crc_modules/` allowed to `import Rhino` (the `rhino/__init__.py` carries the
   Rhino-only warning). Functions:
   ```python
   def shapely_to_rhino(geom)            # → Rhino.Geometry.*
   def rhino_to_shapely(rhino_geom)      # → shapely
   ```
   Fail with a clear ImportError outside Rhino. **Not** pytest-tested directly; add
   `tests/test_rhino_convert.py` guarded by `pytest.importorskip("Rhino")` so CI skips it.

4. **GH bundles** (2 folders, subcategory **03.Utilities**). Each `code.py` imports from
   `crc_modules.geometry.wkt` and `crc_modules.rhino.convert`. **Never** `import Rhino`
   directly in `code.py` — go through `crc_modules/rhino/` so the dependency is explicit.

5. **Build & install** both bundles.

## Tests

```powershell
pytest tests/test_wkt.py -v
```

`test_rhino_convert.py` is skipped outside Rhino — expected.

## Grasshopper checkpoint

Restart Grasshopper. Build one canvas that exercises the round-trip:

1. `CRC_GeometriesWithSpatialFilter` (Phase 05) → WKT list →
   `CRC_WKTtoGrasshopperGeometry` → expect curves/points visible in the Rhino viewport,
   sitting near the origin (Phase 05 applied the `Cx`/`Cy` shift in SQL).
2. Take a Rhino `Curve` param → `CRC_GrasshopperGeometryToWKT` → panel. Confirm the
   round-trip is lossless for polylines, and that the emitted WKT is in **local**
   coordinates (no correction applied here).

Induce an error (malformed WKT) and confirm `report` shows the message without crashing GH.

Save canvases as `tests/_manual/smoke_wkt_*.gh`.

## Commit

```
feat(geometry): WKT shapely module + Rhino convert bridge + 2 converter components
```

## Done when

- [ ] `carcara/crc_modules/geometry/wkt.py` covers the converter helpers, pure Python.
- [ ] `carcara/crc_modules/rhino/convert.py` is the only Rhino-importing module.
- [ ] `tests/test_wkt.py` green; Rhino-side tests skipped cleanly outside Rhino.
- [ ] Both converter bundles built and validated on a chained canvas.
- [ ] The 5 moved components are tracked in their new phases (05 / 08 / 10).
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md` for the two converters.
