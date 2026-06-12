# Phase 06 — DB Writer (`db/writer.py` + CreateTable / CreateShapefile)

## Goal

Write back to PostGIS from Grasshopper. This is the most destructive phase so
far — both DB-side writes are covered by tests and an opt-in `CToggle` guard
before any GH component lands.

> **CRC_CreateShapefile is NOT a file export.** The name is historical. Legacy
> behavior (confirmed): it **INSERTs geometries into an existing PostGIS table**
> with the false-origin correction applied in SQL. There is no shapefile, no
> GeoPandas, no Fiona, no out_path, no .shp/.dbf/.shx/.prj.

Components delivered:

| Component               | Purpose                                                       |
|-------------------------|---------------------------------------------------------------|
| `CRC_CreateTable`       | `CREATE TABLE` with columns (optionally a geometry column).   |
| `CRC_CreateShapefile`   | INSERT WKT geometries into an existing PostGIS table,         |
|                         | adding the false-origin correction back in SQL.               |

---

## Legacy interface (decoded — read-only reference)

**CRC_CreateTable** (`carcara-old/ghuser-metadata/scripts/CreateTable_interface.txt`):

- Inputs: `Connection String` (CString), `Connection Toggle` (CToggle),
  `list of columns`, `variable types` (parallel list of type strings),
  `schema`, `table name`, `replace table` (bool — DROP IF EXISTS before CREATE),
  `values` (initial row data to insert, optional).
- No output parameters are named in the decoded hook params (the two unnamed
  `CustomName: CustomNickName` entries are placeholder artifacts). Spec two
  outputs in the rebuild: `affected` (int) and `report` (str).
- Internal wiring: `SQL Composer` + `Run ODBC Command` (no geometry column in
  CreateTable — geometry is separate from CreateShapefile).

**CRC_CreateShapefile** (`carcara-old/ghuser-metadata/scripts/CreateShapefile_interface.txt`):

- Inputs: `Connection String` (CString), `Connection Toggle` (CToggle),
  `geometry` (list of WKT geometry strings), `SRID`,
  `variable types` (column type list), `schema`, `table name`,
  `replace table` (bool), `list of columns`, `values` (attribute values),
  `Correction X` (Cx), `Correction Y` (Cy).
- No named output params in the decoded hook params (same placeholder artifact).
  Spec one output in the rebuild: `report` (str, feedback string).
- Internal wiring: `Grasshopper Geometry to WKT` + `SQL Composer` +
  `Run ODBC Command`. Confirms geometry is INSERTed, not exported to file.

---

## Steps

> **Credential model:** both components take `CString` + `CToggle` and decode
> with `crc_modules.db.connection.parse_connection_string(CString)` before
> calling the functions below. See Phase 03/04 for the DB-component `code.py`
> pattern.

> **Coordinate correction — the WRITE side (see CLAUDE.md → Coordinate
> Correction).** `CRC_CreateShapefile` writes GH geometry (which is **local**,
> near the Rhino origin) back to PostGIS, so it must **add** the false origin
> to restore projected coordinates:
> `ST_Translate(ST_GeomFromText('<local_wkt>', SRID), Cx, Cy)`.
> It takes `Cx`/`Cy` as numeric **text** (default `"0"`), applied in SQL via
> `utils/correction.py` — **never `float()`**. Use the **same `Cx`/`Cy`**
> that were used to read the data so the round-trip is exact. (Legacy
> `CreateShapefile` exposes these as `Correction X`/`Correction Y`.)
> Plain `CRC_CreateTable` writes alphanumeric columns only and needs no
> correction.

1. **Implement `carcara/crc_modules/db/writer.py`**:

   ```python
   def create_table(cstring: str,
                    schema: str,
                    table: str,
                    columns: list,       # list of (name: str, type: str) tuples
                    geom_column: str | None = None,
                    geom_type: str | None = None,
                    srid: int = 4326,
                    replace_table: bool = False) -> int:
       """
       Execute CREATE TABLE (optionally preceded by DROP TABLE IF EXISTS when
       replace_table=True). Returns cur.rowcount (DDL typically returns -1;
       coerce to 0 in the GH layer). Uses psycopg2.sql.Identifier and
       SQL.format for every name — never f-string interpolation of identifiers.
       If geom_column and geom_type are provided, adds a PostGIS geometry
       column: <geom_column> geometry(<geom_type>, <srid>).
       Raises psycopg2.Error on failure.
       """

   def insert_geometries(cstring: str,
                         schema: str,
                         table: str,
                         geom_column: str,
                         wkt_list: list,      # list of local WKT strings
                         srid: int,
                         cx: str = "0",
                         cy: str = "0",
                         column_names: list | None = None,
                         values: list | None = None) -> int:
       """
       INSERT WKT geometries into an existing PostGIS table, applying the
       false-origin add-back in SQL:
           ST_Translate(ST_GeomFromText(%s, %s), cx, cy)
       cx and cy are validated as numeric text by validate_offset() and
       embedded verbatim into the SQL — NEVER passed as %s bind parameters
       and NEVER parsed with float().
       Returns number of rows inserted.
       Raises psycopg2.Error on failure.
       """
   ```

   - `create_table`: uses `psycopg2.sql.Identifier` and `SQL.format` for
     every name. Commits on success. Returns `cur.rowcount`.
   - `insert_geometries`: calls `validate_offset(cx)` and `validate_offset(cy)`
     from `utils.correction`. Builds the INSERT with the geometry expression
     inline (not as a bind parameter). Uses `executemany` for batch insert.
     Commits on success. Returns row count.

2. **Tests** `tests/test_writer.py`:
   - `create_table`: mock `psycopg2.connect`; assert produced SQL contains
     `CREATE TABLE`, properly quoted identifiers (schema + table + column
     names), and — when `geom_column` is provided — a `geometry(<type>,<srid>)`
     declaration. Assert `DROP TABLE IF EXISTS` appears when
     `replace_table=True`.
   - `insert_geometries` with correction:
     - With `cx="500000"`, `cy="9500000"`, assert the INSERT SQL contains
       `ST_Translate(ST_GeomFromText(%s, %s), 500000, 9500000)` with the Cx/Cy
       as **text literals** in the SQL string, not as `%s` bind slots.
     - Assert `validate_offset` is called and `float()` is never called on
       cx/cy (check no `float(cx)` / `float(cy)` in the source).
     - Assert `psycopg2.Error` propagates on connection failure.
   - `insert_geometries` no-correction: with `cx="0"`, `cy="0"`, assert the
     `ST_Translate` still appears (translation by zero is fine; it keeps the
     SQL consistent) or that the zero case is handled cleanly.

3. **GH bundles**:

   `CRC_CreateTable/` (subcategory `02.Queries`) — inputs:
   - `CString` (`str`, `item`), `CToggle` (`bool`, `item`)
   - `schema` (`str`, `item`), `table` (`str`, `item`)
   - `column_names` (`str`, `list` — list of column name strings)
   - `column_types` (`str`, `list` — list of SQL type strings, parallel)
   - `geom_column` (`str`, `item`, optional — name of geometry column to add)
   - `geom_type` (`str`, `item`, optional — e.g. `"POLYGON"`, `"POINT"`)
   - `srid` (`int`, `item`, default `4326`)
   - `replace_table` (`bool`, `item`, default `False` — DROP IF EXISTS first)

   Outputs:
   - `affected` (int, the DDL rowcount coerced: `-1 → 0`)
   - `report` (str, feedback string, format: `"success: true\nRows Affected: N"`)

   Default "not yet run" report: `"Set CToggle=True to CREATE the table. This
   operation is destructive if replace_table=True."`.

   `CRC_CreateShapefile/` (subcategory `02.Queries`) — inputs:
   - `CString` (`str`, `item`), `CToggle` (`bool`, `item`)
   - `schema` (`str`, `item`), `table` (`str`, `item`)
   - `geom_column` (`str`, `item` — name of the target geometry column)
   - `geometry` (`str`, `list` — list of local WKT strings from GH)
   - `srid` (`int`, `item`, default `4326`)
   - `Cx` (`str`, `item`, default `"0"`, description: `"Correction X — false origin (numeric text)"`)
   - `Cy` (`str`, `item`, default `"0"`, description: `"Correction Y — false origin (numeric text)"`)
   - `column_names` (`str`, `list`, optional — attribute column names)
   - `values` (`str`, `tree`, optional — attribute values parallel to geometry)
   - `replace_table` (`bool`, `item`, default `False`)

   Outputs:
   - `report` (str, feedback string, format: `"success: true\nRows Affected: N"`)

   Default "not yet run" report: `"Set CToggle=True to INSERT geometries. This
   operation writes to the database."`.

   `Cx`/`Cy` are `typeHintID: "str"` — never `float`/`int`.

4. **Defensive wiring**: both components guard all execution behind
   `if CToggle:`. On failure, `report` contains the exception message verbatim.
   On DDL success where rowcount is `-1`, the GH layer coerces to `0` and
   formats `"success: true\nRows Affected: 0"`.

5. **Build & install**:
   ```powershell
   python build_userobjects.py
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```

---

## Tests

```powershell
pytest tests/test_writer.py -v
```

---

## Grasshopper checkpoint

> **This phase mutates your test database.** Use a throwaway DB or schema.

**CRC_CreateTable** — point at a test schema. Wire:
- `column_names = ["name", "value"]`
- `column_types = ["text", "double precision"]`
- `geom_column = "geom"`, `geom_type = "POLYGON"`, `srid = 4326`
- `replace_table = False`

Flip `CToggle`. Expect `report = "success: true\nRows Affected: 0"` (DDL).
Verify with `CRC_QueryTableNames` (Phase 04) that the table is listed. Re-run
with same name and `replace_table=False`: expect no error. Re-run with
`replace_table=True`: table is dropped and recreated.

**CRC_CreateShapefile** (geometry INSERT round-trip with Phase 05):

1. Read geometries from a test table using `CRC_GeometryEntities` (Phase 05)
   with `Cx="500000"`, `Cy="9500000"` (or whatever matches your test area).
   Note the returned WKT values (these are in local coordinates).
2. Wire those WKT values into `CRC_CreateShapefile`, pointing at a throwaway
   target table (create it first with `CRC_CreateTable`). Use the **same**
   `Cx="500000"`, `Cy="9500000"`.
3. Flip `CToggle`. Expect `report = "success: true\nRows Affected: N"`.
4. Read back using `CRC_GeometryEntities` with the same Cx/Cy. The returned
   WKT should match the original (round-trip check).

Then induce failures (wrong schema, table missing, invalid Cx format like
`"abc"`) and confirm `report` shows the error cleanly and the component does
not red-bubble.

Save canvases as `tests/_manual/smoke_writer_*.gh`.

---

## Commit

```
feat(db): add writer module + CRC_CreateTable + CRC_CreateShapefile (INSERT, not file export)
```

---

## Done when

- [ ] `carcara/crc_modules/db/writer.py` exists with `create_table` and
      `insert_geometries`, identifier-safe.
- [ ] `CRC_CreateShapefile` INSERTs geometries; adds `Cx`/`Cy` in SQL (text,
      no `float()`); round-trip with Phase 05 read confirmed on canvas.
- [ ] `report` format is `"success: true\nRows Affected: N"` for both components.
- [ ] `tests/test_writer.py` covers DDL shape, INSERT SQL correction signs,
      and identifier quoting.
- [ ] Both GH bundles built and validated against a real test DB.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
