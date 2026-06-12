# Phase 05 — Spatial Query (`db/spatial_query.py` + 2 components)

## Goal

Query PostGIS geometries (and their attribute rows) with optional WHERE
clauses and bounding-box filters, returning **WKT strings** to Grasshopper.
WKT-to-Rhino-geometry conversion is deliberately deferred to Phase 07; this
phase outputs strings only, which keeps it Rhino-independent and easy to test.

Components delivered (3, all subcategory **02.Queries**):

| Component                          | Purpose                                              |
|------------------------------------|------------------------------------------------------|
| `CRC_GeometryEntities`             | Download all geometries + PKs from a table (no spatial filter). |
| `CRC_GeometriesWithSpatialFilter`  | SELECT geometries within a spatial filter + WHERE.   |
| `CRC_ValuesWithSpatialFilter`      | SELECT attribute values matching a spatial filter.   |

> `CRC_GeometryEntities` was re-keyed here from the old Phase 07 (it was mislabeled there
> as a WKT classifier). It is the unfiltered sibling of `GeometriesWithSpatialFilter`:
> same `db/spatial_query.py` machinery (PK detect, `ST_MakePoint` from `x_col`/`y_col`,
> `ST_Translate` correction, ORDER BY pk) minus the spatial `WHERE`. Implement it as
> `get_geometries(cstring, schema, table, x_col, y_col, cx, cy, where=None, srid=...)`.

## Inputs you must give me

For each legacy file, give me the input/output schema:

1. `carcara_GeometriesWithSpatialFilter_r03.ghuser`
2. `carcara_ValuesWithSpatialFilter_rev03.ghuser`

Specifically:

- Does the legacy take a literal bbox as 4 numbers (`xmin,ymin,xmax,ymax`),
  a Grasshopper rectangle, or both? (We will accept 4 numbers + SRID and
  document it. A Rhino-side adapter to take a rectangle goes in Phase 07.)
- Does the legacy require a `geom_column` input or does it auto-detect?
- Does the legacy return geometries **in the bbox SRID** or **reprojected
  to the table SRID**? The default we will adopt: input bbox SRID must match
  the table SRID, and we explicitly do not reproject. Confirm.
- Output shape: list of WKT strings + parallel list of attribute rows? Or
  a DataTree?
- **Correction:** confirm the legacy `Cx`/`Cy` correction inputs and their exact
  nicknames, and confirm the sign convention (read subtracts, filter/write adds).
  Confirm they were applied in SQL (`ST_Translate`) and kept as text.

Also: a test database with **at least one PostGIS table** containing real
polygons or points and a few attribute columns.

## Steps

> **Credential model:** like all DB components, the two bundles take `CString` +
> `CToggle` inputs (the connection string from `CRC_ConnectionString`) and decode
> with `crc_modules.db.connection.parse_connection_string(CString)` before calling
> the functions below. See Phase 03/04 for the DB-component `code.py` pattern.

> **Coordinate correction (see CLAUDE.md → Coordinate Correction).** These are
> geometry components, so they carry the false-origin shift. `Cx` / `Cy` are
> numeric **text** inputs (default `"0"`), applied **in SQL only** via
> `crc_modules/utils/correction.py` — the read path **subtracts** them so geometry
> lands near the Rhino origin, and a GH-drawn spatial filter is pushed back to the
> projected CRS by **adding** them. **Never `float()` Cx/Cy** — that defeats the
> precision fix. Note: legacy `_cx`/`_cy` are the **coordinate-column names**
> (`x_col`/`y_col` here), a different thing from the `Cx`/`Cy` correction.

1. **Implement `carcara/crc_modules/db/spatial_query.py`** per `CLAUDE.md` contract:
   ```python
   def get_geometries(cstring, schema, table, x_col, y_col,
                      cx="0", cy="0", where=None, srid=4326) -> tuple[list, list]

   def get_geometries_with_spatial_filter(cstring, schema, table, x_col, y_col,
                                          filter_wkt, cx="0", cy="0",
                                          srid=4326, sql_filter=None) -> tuple[list, list]
   ```
   - Geometry SELECT translates to **local**:
     `ST_AsText(ST_Translate(ST_MakePoint("x_col","y_col"), -Cx, -Cy))`.
   - Spatial filter pushes the local boundary back to **projected**:
     `ST_Intersects(ST_MakePoint("x_col","y_col"), ST_Translate(ST_GeomFromText(filter_wkt, srid), Cx, Cy))`.
   - `Cx`/`Cy` come from `utils.correction.validate_offset()` (numeric-text check,
     no float) and are embedded via `utils.correction.translate_expr()`.
   - Detect the primary key and `ORDER BY` it so geometries and PKs stay parallel
     (port the legacy PK-detection + ORDER BY templates).
   - **Identifier-escape** `schema`/`table`/`x_col`/`y_col` (psycopg2 `sql.Identifier`)
     so a malicious name cannot inject SQL.

2. **Add tests** `tests/test_spatial_query.py`:
   - Mock `psycopg2.connect` and assert the produced SQL matches a regex
     containing `ST_AsText`, `ST_Translate`, and the right parameter bindings.
   - **Correction:** with `cx="500000"`, `cy="9500000"`, assert the SELECT contains
     `ST_Translate(..., -500000, -9500000)` and the filter contains
     `ST_Translate(..., 500000, 9500000)` — and assert the values appear **verbatim
     as text** (no float reformatting like `500000.0`).
   - Assert `validate_offset` rejects non-numeric text (`"500000; DROP TABLE"`).
   - Confirm `Identifier` quoting is applied (try a name with a quote).
   - Assert `(wkt_list, pk_list)` shape is returned.

3. **GH bundles**:
   - `CRC_GeometriesWithSpatialFilter/` — inputs: `CString`, `CToggle`,
     `schema`, `table`, `x_col`, `y_col`, `filter_wkt` (str, optional),
     `Cx` (str, default `"0"`), `Cy` (str, default `"0"`), `srid` (int, 4326),
     `sql_filter` (str, optional). Outputs: `wkt`, `pk`, `report`.
   - `CRC_ValuesWithSpatialFilter/` — same inputs but adds `columns`
     (list of column names). Outputs: `rows`, `report`.

   Type-hint accordingly in `metadata.json` — `Cx`/`Cy` are **`typeHintID: "str"`**
   (text, never `float`/`int`), `scriptParamAccess: "item"`.

4. **Build & install** both bundles.

## Tests

```powershell
pytest tests/test_spatial_query.py -v
```

## Grasshopper checkpoint

Restart Grasshopper. For each:

**CRC_GeometriesWithSpatialFilter** — wire `CString` + `CToggle` + a real table
(e.g. `public.cities`) + `x_col`/`y_col` (the coordinate columns) + leave
`filter_wkt` empty + `Cx="0"`/`Cy="0"` + flip `CToggle`. Expect:

- `wkt` populated with `POINT(...)` / `POLYGON(...)` strings.
- `pk` parallel to `wkt`, one primary key per geometry.
- `report = "OK – N geometries"`.

Then **add a `filter_wkt`** boundary (a GH-drawn polygon converted to WKT) covering
half the data and re-run; `wkt` should shrink. Then provide an out-of-area boundary
and confirm `wkt = []` and `report = "OK – 0 geometries"` (not an error).

**CRC_ValuesWithSpatialFilter** — same wiring (`CString` + `CToggle` + table) + a list
of column names. Confirm output rows contain only those columns.

**Correction check** — set `Cx`/`Cy` to a point near your study area (the projected
coordinate as text, e.g. `Cx="500000"`, `Cy="9500000"`). Re-run: the returned geometry
should now sit near the Rhino origin (small coordinates, no jitter) instead of far out in
projected space. Set them back to `"0"` and confirm geometry returns to full projected
magnitude. The Cx/Cy used to read must match the Cx/Cy later used to write the same data back.

Save canvases as `tests/_manual/smoke_spatial_*.gh`.

## Commit

```
feat(db): add spatial_query module with WHERE + bbox filters and 2 GH components
```

## Done when

- [ ] `carcara/crc_modules/db/spatial_query.py` matches spec, uses identifier escaping.
- [ ] `Cx`/`Cy` applied in SQL via `utils/correction.py`, kept as text (no `float()`), tested.
- [ ] `tests/test_spatial_query.py` covers SQL shape + correction signs + error paths.
- [ ] Both GH bundles built, installed, and validated against real PostGIS data.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
