# Phase 05 — Spatial Query (`db/spatial_query.py` + 3 components)

## Goal

Query PostGIS geometries (and their attribute rows) with optional WHERE clauses
and spatial filters, returning **WKT strings** to Grasshopper as DataTrees.
WKT-to-Rhino-geometry conversion is deliberately deferred to Phase 07; this
phase outputs strings only, which keeps it Rhino-independent and easy to test.

Components delivered (3, all subcategory **02.Queries**):

| Component                          | Purpose                                                      |
|------------------------------------|--------------------------------------------------------------|
| `CRC_GeometryEntities`             | Download all geometries + PKs from a table (no spatial filter). |
| `CRC_GeometriesWithSpatialFilter`  | SELECT geometries within a spatial filter + optional WHERE.  |
| `CRC_ValuesWithSpatialFilter`      | SELECT attribute values matching a spatial filter.           |

> Geometry columns are **auto-detected** from the PostGIS `geometry_columns`
> view — components do NOT take `x_col`/`y_col` inputs and do NOT use
> `ST_MakePoint`. The geometry expression in SQL is the detected geometry column
> itself. Primary keys are also auto-detected.

---

## Legacy interface (decoded — read-only reference)

**CRC_GeometryEntities** (`carcara-old/ghuser-metadata/scripts/GeometryEntities_interface.txt`):

- Inputs: `Connection String` (CString), `Connection Toggle` (CToggle),
  `Schema`, `Table`, `Correction X` (Cx), `Correction Y` (Cy).
- Outputs: `Geometry` (wkt), `Primary keys` (pk), `Exceptions` (report).
- Internal wiring uses multiple `SQL Composer` + `Run ODBC Query` calls
  (PK detection, geometry query) and `WKT to Grasshopper Geometry`.

**CRC_GeometriesWithSpatialFilter** (`carcara-old/ghuser-metadata/scripts/GeometriesWithSpatialFilter_interface.txt`):

- Inputs: `Connection String` (CString), `Connection Toggle` (CToggle),
  `Schema`, `Table`, `Correction X` (Cx), `Correction Y` (Cy),
  `Spatial Filter` (sp_ftl — GH geometry input, converted to WKT internally),
  `SRID`, `function` (the spatial predicate, e.g. ST_Intersects).
- Outputs: `Geometry` (wkt), `Primary keys` (pk), `Exceptions` (report).
- Spatial filter is a GH geometry (Curve in the wiring) passed through
  `Grasshopper Geometry to WKT` inside the cluster before being used in SQL.
  In the rebuild the component takes `filter_wkt` (a pre-converted WKT string)
  directly, because WKT conversion is a separate Phase 07 component.

**CRC_ValuesWithSpatialFilter** (`carcara-old/ghuser-metadata/scripts/ValuesWithSpatialFilter_interface.txt`):

- Inputs: `Connection String` (CString), `Connection Toggle` (CToggle),
  `Schema`, `Table`, `Column` (list), `Null Itens` (N — NULL sentinel string),
  `Correction X` (Cx), `Correction Y` (Cy), `Spatial Filter` (sp_ftl),
  `SRID`, `function`.
- Outputs: `Values` (attribute values), `Exceptions` (report).
- NULL handling: same post-fetch replacement as QueryValues (Replace Text
  wiring).

---

## Steps

> **Credential model:** like all DB components, the three bundles take
> `CString` + `CToggle` inputs (the connection string from
> `CRC_ConnectionString`) and decode with
> `crc_modules.db.connection.parse_connection_string(CString)` before calling
> the functions below. See Phase 03/04 for the DB-component `code.py` pattern.

> **Coordinate correction (see CLAUDE.md → Coordinate Correction).** These are
> geometry components, so they carry the false-origin shift. `Cx` / `Cy` are
> numeric **text** inputs (default `"0"`), applied **in SQL only** via
> `crc_modules/utils/correction.py` — the read path **subtracts** them so
> geometry lands near the Rhino origin, and a GH-drawn spatial filter is pushed
> back to the projected CRS by **adding** them. **Never `float()` Cx/Cy** —
> that defeats the precision fix. Cx/Cy are the **false-origin correction
> values**, distinct from `x_col`/`y_col` (coordinate-column names); the latter
> do NOT exist in this rebuild because geometry columns are auto-detected.

1. **Add shared helper** `detect_geometry_column(cstring, schema, table) -> str`
   in `carcara/crc_modules/db/spatial_query.py`:
   - Queries the PostGIS `geometry_columns` view:
     `SELECT f_geometry_column FROM geometry_columns WHERE f_table_schema = %s AND f_table_name = %s LIMIT 1`
   - Returns the column name string.
   - Raises `ValueError` if no geometry column is found.
   - This helper is also reused by `CRC_FindCorrectionParameters` in Phase 11.

2. **Add shared helper** `detect_primary_key(cstring, schema, table) -> str | None`
   in `db/spatial_query.py`:
   - Queries `information_schema.table_constraints` + `key_column_usage` to
     find the first PRIMARY KEY column name.
   - Returns the column name string, or `None` if no PK exists.
   - If `None`, the query returns `NULL` for `pk` and no `ORDER BY` is applied
     (or falls back to `ORDER BY 1`).

3. **Implement `carcara/crc_modules/db/spatial_query.py`** per CLAUDE.md contract:

   ```python
   def get_geometries(cstring: str, schema: str, table: str,
                      cx: str = "0", cy: str = "0",
                      where: str = None, srid: int = 4326) -> tuple[list, list]:
       """
       Returns (wkt_geometries, primary_keys).
       Auto-detects geometry column and primary key.
       Read SQL: ST_AsText(ST_Translate(<geom_col>, -Cx, -Cy)) ORDER BY pk.
       If no PK exists, returns NULL for pk entries.
       Cx/Cy are numeric TEXT embedded verbatim in SQL — never float()-parsed.
       Output is structured for DataTree: each geometry (including multipart
       members split into their parts) on same branch as its PK row.
       """

   def get_geometries_with_spatial_filter(cstring: str, schema: str, table: str,
                                          filter_wkt: str,
                                          cx: str = "0", cy: str = "0",
                                          srid: int = 4326,
                                          sql_filter: str = None) -> tuple[list, list]:
       """
       SELECT geometries translated to local (-Cx, -Cy), filtered by a
       GH-drawn boundary that is itself translated to the projected CRS (+Cx,+Cy)
       inside the WHERE:
           ST_Intersects(<geom_col>,
               ST_Translate(ST_GeomFromText(filter_wkt, srid), Cx, Cy))
           AND (sql_filter)
       Auto-detects geometry column and PK.
       Returns (wkt_geometries, primary_keys) structured as described above.
       """

   def get_values_with_spatial_filter(cstring: str, schema: str, table: str,
                                      columns: list,
                                      filter_wkt: str,
                                      cx: str = "0", cy: str = "0",
                                      srid: int = 4326,
                                      sql_filter: str = None) -> tuple[list, list]:
       """
       SELECT attribute columns for rows matching spatial filter.
       Same spatial filter logic as get_geometries_with_spatial_filter.
       Returns (rows, column_names).
       NULL values in the returned rows are left as None for the component
       layer to substitute via the N sentinel.
       """
   ```

   Implementation rules for all three functions:
   - Call `validate_offset(cx)` and `validate_offset(cy)` from
     `utils.correction` (numeric-text check, no float). Raise `ValueError` if
     invalid.
   - Build the geometry read expression with `translate_expr(geom_col_sql,
     cx, cy, direction="to_local")` → `ST_AsText(ST_Translate(..., -cx, -cy))`.
   - Build the spatial filter expression with `translate_expr(filter_sql, cx,
     cy, direction="to_projected")` →
     `ST_Intersects(<geom_col>, ST_Translate(ST_GeomFromText(%s, %s), cx, cy))`.
   - Cx/Cy are embedded verbatim as numeric text into the SQL via
     `translate_expr` — never passed as `%s` bind parameters (they are
     structural parts of the SQL, already validated as safe numeric literals).
   - Use `psycopg2.sql.Identifier` for `schema`, `table`, and the detected
     geometry column / PK column names to prevent injection.
   - Detect PK via `detect_primary_key()`; if `None`, `ORDER BY` clause is
     omitted and `pk` values in the output are `None`.

4. **Output shape (DataTree by row, multipart split):**
   - The function layer returns flat Python lists `(wkt_list, pk_list)` where
     multipart geometries (MULTIPOLYGON / MULTILINESTRING / MULTIPOINT) are
     **not split at the function level** — splitting happens in `code.py`.
   - In `code.py`, iterate over `(wkt, pk)` pairs. For each row, detect if
     `wkt` starts with `MULTI`; if so, parse with shapely and split into member
     geometries. All members from the same row go on the **same DataTree branch**
     (same `GH_Path` index as the row). The parallel `pk` DataTree has the
     same PK value on each of those branches.
   - Tables with no PK: `pk` branch values are `None` (null in GH).
   - `metadata.json` for wkt/pk outputs: `scriptParamAccess: "tree"`.

5. **GH bundles**:

   `CRC_GeometryEntities/` — inputs:
   - `CString` (`str`, `item`), `CToggle` (`bool`, `item`)
   - `schema` (`str`, `item`), `table` (`str`, `item`)
   - `Cx` (`str`, `item`, default `"0"`, description: `"Correction X — false origin (numeric text)"`)
   - `Cy` (`str`, `item`, default `"0"`, description: `"Correction Y — false origin (numeric text)"`)

   Outputs: `wkt` (`tree`), `pk` (`tree`), `report` (`item`).

   `CRC_GeometriesWithSpatialFilter/` — inputs:
   - `CString`, `CToggle`, `schema`, `table`
   - `filter_wkt` (`str`, `item`, optional — leave empty for no spatial filter)
   - `Cx` (`str`, `item`, default `"0"`), `Cy` (`str`, `item`, default `"0"`)
   - `srid` (`int`, `item`, default `4326`)
   - `sql_filter` (`str`, `item`, optional — extra WHERE clause fragment)

   Outputs: `wkt` (`tree`), `pk` (`tree`), `report` (`item`).

   `CRC_ValuesWithSpatialFilter/` — inputs:
   - `CString`, `CToggle`, `schema`, `table`
   - `columns` (`str`, `list` — list of column names to return)
   - `N` (`str`, `item`, description: `"Value to replace NULL entries with"`)
   - `filter_wkt` (`str`, `item`, optional)
   - `Cx` (`str`, `item`, default `"0"`), `Cy` (`str`, `item`, default `"0"`)
   - `srid` (`int`, `item`, default `4326`)
   - `sql_filter` (`str`, `item`, optional)

   Outputs: `values` (`tree`), `report` (`item`).
   Output is a DataTree by column: each branch contains one column's values
   for all matched rows, parallel across branches.

   For all three: `Cx`/`Cy` are `typeHintID: "str"` — never `float`/`int`.

6. **Build & install** all three bundles:
   ```powershell
   python build_userobjects.py
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```

---

## Tests

```powershell
pytest tests/test_spatial_query.py -v
```

Test file: `tests/test_spatial_query.py`. Mock `psycopg2.connect` throughout.
Specifically:

- **`detect_geometry_column`**: mock `cursor.fetchone` to return `("geom",)`;
  assert return value is `"geom"`. Test raise on empty result.
- **`detect_primary_key`**: mock to return `("id",)` and `None`; assert both
  paths.
- **SQL shape for `get_geometries`**: assert produced SQL contains `ST_AsText`,
  `ST_Translate`, and `ORDER BY` with the PK column.
- **Correction signs**: with `cx="500000"`, `cy="9500000"`:
  - Read path: assert SQL contains `-500000` and `-9500000` (local = projected
    minus false origin).
  - Filter path: assert WHERE clause contains `+500000` and `+9500000`
    (filter pushed back to projected).
  - Assert values appear **verbatim as text** (not `500000.0` — no float
    reformatting).
- **`validate_offset` rejection**: assert `validate_offset("500000; DROP TABLE")`
  raises `ValueError`.
- **No-PK path**: mock `detect_primary_key` returning `None`; assert returned
  `pk_list` contains `None` values and no `ORDER BY` PK clause in SQL.
- **Identifier quoting**: pass a table name containing a double-quote; assert
  the SQL contains the properly escaped identifier (psycopg2 `Identifier`).
- **Return shape**: assert `get_geometries` returns a tuple `(list, list)`.
- **Multipart split** (unit, no DB): given a `MULTIPOLYGON (...)` WKT string,
  assert the component-layer splitting logic yields two or more member WKT
  strings all on the same DataTree branch index.

---

## Grasshopper checkpoint

Restart Grasshopper. Wire `CRC_ConnectionString` → each component below.

**CRC_GeometryEntities** — wire `CString` + `CToggle` + a real PostGIS table
(any table with a geometry column). Leave `Cx`/`Cy` at `"0"`. Flip `CToggle`.
Expect:

- `wkt` populated with WKT strings (POINT / POLYGON / LINESTRING etc.).
- `pk` parallel to `wkt`, one primary key value per geometry row.
- `report = "OK – N geometries"`.

**No-PK table check**: point at a table that has no primary key. Confirm:
- `pk` output contains null values (not an error).
- `report` still shows `"OK – N geometries"` (not an error state).

**CRC_GeometriesWithSpatialFilter** — same wiring + a `filter_wkt` boundary
(a GH-drawn polygon converted to WKT via Phase 07's `CRC_GrasshopperGeometryToWKT`,
or a hand-typed WKT) covering half the data. Flip `CToggle`.
- `wkt` should be a subset of the unfiltered result.
- Provide an out-of-area boundary: `wkt = []`, `report = "OK – 0 geometries"`.

**Multipart geometry check**: if your DB has a MULTIPOLYGON or MULTILINESTRING
table, run `CRC_GeometryEntities` against it. Confirm that each multipart row
produces its member geometries on the same DataTree branch, and the `pk` tree
has the same structure.

**Correction check** — set `Cx`/`Cy` to a projected coordinate near your study
area (as text, e.g. `Cx="500000"`, `Cy="9500000"`). Re-run: the returned WKT
should now use small (near-origin) coordinates. Set back to `"0"` and confirm
geometry returns to full projected magnitude. The Cx/Cy used to read must match
the Cx/Cy used to write the same data back (Phase 06 round-trip).

**CRC_ValuesWithSpatialFilter** — same wiring (`CString` + `CToggle` + table)
+ a list of column names + `filter_wkt`. Confirm:
- Output `values` DataTree has one branch per column.
- `N` sentinel correctly replaces NULL entries.

Save canvases as `tests/_manual/smoke_spatial_*.gh`.

---

## Commit

```
feat(db): add spatial_query module with geometry-column autodetect and 3 GH components
```

---

## Done when

- [ ] `carcara/crc_modules/db/spatial_query.py` matches CLAUDE.md spec:
      `get_geometries`, `get_geometries_with_spatial_filter`,
      `get_values_with_spatial_filter`, `detect_geometry_column`,
      `detect_primary_key`. No `x_col`/`y_col` inputs anywhere. No `ST_MakePoint`.
- [ ] Geometry column auto-detected from `geometry_columns` view.
- [ ] `Cx`/`Cy` applied in SQL via `utils/correction.py`, kept as text (no
      `float()`), tested for both signs.
- [ ] No-PK path: `pk` returns null values, no error raised.
- [ ] Multipart geometries split into members on the same DataTree branch.
- [ ] `tests/test_spatial_query.py` covers SQL shape + correction signs +
      no-PK path + identifier quoting + multipart splitting.
- [ ] All three GH bundles built, installed, and validated against real
      PostGIS data.
- [ ] Statuses of all three components flipped to ✅ Done in `CLAUDE.md`.
