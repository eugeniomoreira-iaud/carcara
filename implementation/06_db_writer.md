# Phase 06 — DB Writer (`db/writer.py` + CreateTable / CreateShapefile)

## Goal

Write back to PostGIS and export to shapefile. This is the most destructive
phase so far — we make sure both DB-side writes and file-system writes are
covered by tests and an opt-in `run` guard before any GH component lands.

Components delivered:

| Component               | Purpose                                                  |
|-------------------------|----------------------------------------------------------|
| `CRC_CreateTable`       | `CREATE TABLE` (optionally with PostGIS geometry column) |
| `CRC_CreateShapefile`   | Export a SELECT result to a `.shp` on disk               |

## Inputs you must give me

For each legacy file, the usual rundown:

1. `carcara_CreateTable_r03.ghuser`
2. `carcara_CreateShapefile_r03.ghuser`

Specifically I need to know:

- **CreateTable** — does the legacy take column-name list + column-type list
  as two parallel lists? Or one combined string? Does it create a geometry
  column and how is the geom type chosen (POINT / POLYGON / MULTIPOLYGON)?
  Does it create a PRIMARY KEY?
- **CreateShapefile** — what does the legacy use to write the shapefile?
  PostGIS's `pgsql2shp` CLI? Python `pyshp` / `fiona`? The new
  implementation will use **GeoPandas + Fiona** if available, or fall back
  to `psycopg2 + shapely + shapefile` (pyshp). Tell me your preference
  before I lock that in. Default: GeoPandas if importable, pyshp fallback.
- Does CreateShapefile take a SQL query, or a table name + filter? Both?

Also: a test DB **where you are OK with new tables being created and
dropped**. Do not point this at production data.

## Steps

> **Credential model:** both components take `CString` + `CToggle` and decode with
> `crc_modules.db.connection.parse_connection_string(CString)` before calling the
> functions below. See Phase 03/04 for the DB-component `code.py` pattern.

> **Coordinate correction — the WRITE side (see CLAUDE.md → Coordinate Correction).**
> `CRC_CreateShapefile` writes GH geometry (which is **local**, near the Rhino origin)
> back to PostGIS, so it must **add** the false origin to restore projected coordinates:
> `ST_Translate(ST_GeomFromText('<local_wkt>', SRID), Cx, Cy)`. It takes `Cx`/`Cy` as
> numeric **text** (default `"0"`), applied in SQL via `utils/correction.py` —
> **never `float()`**. Use the **same `Cx`/`Cy`** that were used to read the data so the
> round-trip is exact. (Legacy `CreateShapefile` exposes these as `_cX`/`_cY`.) Plain
> `CRC_CreateTable` writes alphanumeric columns only and needs no correction.

1. **Implement `carcara/crc_modules/db/writer.py`**:
   ```python
   def create_table(cstring: str,
                    schema: str, table: str,
                    columns: list[tuple[str, str]],
                    geom_column: str | None = None,
                    geom_type: str | None = None,
                    srid: int = 4326,
                    if_not_exists: bool = True) -> int

   def export_shapefile(cstring: str,
                        sql: str, geom_column: str, srid: int,
                        out_path: str,
                        cx: str = "0", cy: str = "0") -> int
   ```
   - `create_table` returns affected rowcount (`-1` for DDL on most drivers,
     we coerce to `0`). Uses `psycopg2.sql.Identifier` and `SQL.format` for
     every name — never f-string interpolation of identifiers.
   - `export_shapefile` runs `sql` (must include `ST_AsBinary(geom)` or the
     function adds it), iterates rows, writes to `.shp`/`.dbf`/`.shx`/`.prj`.
     Returns count of features written.
   - Both raise on failure; the component layer catches.

2. **Tests** `tests/test_writer.py`:
   - `create_table`: mock `psycopg2.connect`; assert the produced SQL
     contains `CREATE TABLE`, properly quoted identifiers, the geometry
     column declared as `geometry(<type>, <srid>)`, and `IF NOT EXISTS`
     when requested.
   - `export_shapefile`: mock the connection and the shapefile writer;
     assert the right files are created at `out_path`.

3. **GH bundles**:
   - `CRC_CreateTable/` (02.Queries) — inputs: `CString`, `CToggle` + `schema`,
     `table`, `column_names` (list of str), `column_types` (list of str),
     `geom_column` (str, optional), `geom_type` (str, optional),
     `srid` (int, default 4326), `if_not_exists` (bool, default True).
     Outputs: `affected`, `report`.
   - `CRC_CreateShapefile/` — inputs: `CString`, `CToggle` + `sql`,
     `geom_column`, `srid`, `out_path`, plus `Cx` (str, `"0"`), `Cy` (str, `"0"`)
     for the false-origin add-back when writing GH-local geometry. Outputs:
     `feature_count`, `report`. `Cx`/`Cy` are `typeHintID: "str"`.

4. **Defensive wiring**: in `code.py` for both, the `CToggle` boolean is the
   only thing that triggers a write. Set the "not yet run" report string
   to something explicit like `"Set CToggle=True to CREATE the table. This is
   destructive."`

5. **Build & install**.

## Tests

```powershell
pytest tests/test_writer.py -v
```

## Grasshopper checkpoint

> **This phase mutates your test database.** Use a throwaway DB or schema.

**CRC_CreateTable** — point at a test schema. Wire `column_names =
["id","name","value"]`, `column_types = ["serial","text","double precision"]`,
`geom_column = "geom"`, `geom_type = "POINT"`, `srid = 4326`. Flip `CToggle`.
Then verify with `CRC_QueryTableNames` from Phase 04 that the table is
listed. Re-run with same name and `if_not_exists=True`: no error, no rows.

**CRC_CreateShapefile** — point at a table that already has data and
geometry. Provide a writeable `out_path` (`C:\temp\carcara_test.shp`).
Flip `CToggle`. Verify on disk that `.shp/.dbf/.shx/.prj` exist and the
feature count matches the source table. Open in QGIS to confirm geometry
renders.

Then induce failures (read-only path, wrong SRID, table missing) and
confirm `report` shows the error cleanly.

Save canvases as `tests/_manual/smoke_writer_*.gh`.

## Commit

```
feat(db): add writer module + CRC_CreateTable + CRC_CreateShapefile
```

## Done when

- [ ] `carcara/crc_modules/db/writer.py` exists with both functions, identifier-safe.
- [ ] `CRC_CreateShapefile` adds `Cx`/`Cy` in SQL (text, no `float()`); round-trip with Phase 05 read confirmed.
- [ ] `tests/test_writer.py` covers DDL shape and shapefile write call.
- [ ] Both GH bundles built and validated against a real test DB.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
