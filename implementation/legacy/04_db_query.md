# Phase 04 — DB Query (`db/query.py` + query components)

## Goal

Implement `run_query` / `run_command` in `crc_modules/db/query.py` and the
small internal SQL helpers that drive the catalogue-listing components.
Deliver the remaining query component (`CRC_QueryValues`) for this phase;
the three catalogue components are already ✅ Done (see status section below).

Components delivered in this phase:

| Component               | Purpose                                                    | Status    |
|-------------------------|------------------------------------------------------------|-----------|
| `CRC_QuerySchemaNames`  | List schemas in the DB.                                    | ✅ Done   |
| `CRC_QueryTableNames`   | List tables in a schema.                                   | ✅ Done   |
| `CRC_QueryColumnNames`  | List columns in a table.                                   | ✅ Done   |
| `CRC_QueryValues`       | Return all values in a column, NULLs replaced by sentinel. | ⬜ Todo   |

> **CRC_QueryValues is NOT a raw-SQL runner.** That role belongs to
> `CRC_RunQuery` in Phase 12. `CRC_QueryValues` is a targeted catalogue
> component: it takes schema + table + column + a NULL sentinel and returns
> every value in that column with NULLs substituted. It builds its SELECT
> internally via the legacy SQL template through `utils/sql_composer.py`.

---

## Already-Done: CRC_QuerySchemaNames / CRC_QueryTableNames / CRC_QueryColumnNames

These three components are built and installed. The following are **verification
items** to confirm during a Grasshopper checkpoint — do not rebuild them unless
a deficiency is found.

**Verification checklist for CRC_QuerySchemaNames:**

- Output parameter is named `Schemas` (legacy: `Schemas`) and `Exceptions`
  (legacy name for `report`).
- SQL must filter system schemas:
  `WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast','topology')`
  (or equivalent). Confirm the component does NOT return `pg_catalog`,
  `information_schema`, etc. If it does, add the filter — this is a bug.
- `report` distinguishes "not yet run" / "OK – N schemas" / error.

**Verification checklist for CRC_QueryTableNames:**

- Inputs: `CString`, `CToggle`, `schema`. Output: `tables`, `report`.
- SQL targets `information_schema.tables WHERE table_schema = %s`.

**Verification checklist for CRC_QueryColumnNames:**

- Inputs: `CString`, `CToggle`, `schema`, `table`. Outputs: `columns`, `types`, `report`.
- `columns` and `types` are positionally aligned.

---

## Inputs you must give me (remaining work)

For `CRC_QueryValues` (legacy: `carcara_QueryValues_rev03.ghuser`), the
interface is decoded at
`carcara-old/ghuser-metadata/scripts/QueryValues_interface.txt`. Key facts
already extracted:

- **Inputs (legacy):** `Connection String` (CString), `Connection Toggle`
  (CToggle), `Schema`, `table`, `Column`, `Null Itens` (a **string** — the
  value to substitute for NULL entries in the queried column).
- **Outputs (legacy):** `Values` (all values of the column, NULLs replaced),
  `Exceptions` (the error/status string, equivalent to `report`).
- Legacy internal wiring uses `SQL Composer` + `Run ODBC Query` + `Graft Tree`
  + `Replace Text`, confirming the NULL replacement may happen post-fetch via
  text replacement rather than SQL COALESCE. Check
  `carcara-old/ghuser-metadata/scripts/CRC_QueryValues.py` if present for the
  exact SQL template and the NULL-handling order; if not present, port from the
  interface wiring (`Replace Text` = post-fetch string replacement).

Confirm before implementing:

- Does `Null Itens` replace NULL with an arbitrary string, or with an empty
  string only? (Legacy description says "value to replace null items with" —
  treat it as an arbitrary replacement string.)
- Output access shape: legacy uses `Graft Tree` downstream, suggesting values
  are emitted as a grafted list (DataTree by item). Spec `scriptParamAccess`
  to `"list"` and test whether grafting is needed on the canvas.

---

## Steps

> **Credential model (CString):** DB components take a **`CString`** input (the
> connection string from `CRC_ConnectionString`) plus a **`CToggle`** boolean
> trigger. The function layer decodes `CString` with `parse_connection_string`;
> the GH layer never unpacks individual credentials. Every component below
> follows this DB-component pattern in `code.py`:
>
> ```python
> # sys.path bootstrap puts …/UserObjects/carcara on the path (see CLAUDE.md)
> from crc_modules.db.query import run_query
>
> values, report = [], "Set 'CToggle' to True to execute"
> if CToggle:
>     try:
>         _rows, _cols = run_query(CString, _sql)
>         values = [str(r[0]) if r[0] is not None else N for r in _rows]
>         report = "OK - {} values".format(len(values))
>     except Exception as e:
>         report = "ERROR: {}".format(e)
> ```

1. **Confirm `carcara/crc_modules/db/query.py`** matches spec (should already
   be done from Phase 03):
   ```python
   def run_query(cstring: str, sql: str) -> tuple[list, list]
   def run_command(cstring: str, sql: str) -> int
   ```
   - `run_query`: decode `cstring` via `parse_connection_string`, open
     connection, execute, fetch all, return `(rows_as_list_of_tuples,
     column_names_as_list_of_str)`. Close connection in `finally`.
   - `run_command`: same, then commit, return `cur.rowcount`.
   - Both raise `psycopg2.Error` on failure.

2. **Confirm private SQL helpers** in `query.py` (used by the Done components):
   ```python
   def _list_schemas() -> str
   def _list_tables(schema: str) -> str
   def _list_columns(schema: str, table: str) -> str
   ```
   Ensure `_list_schemas()` SQL includes a `WHERE schema_name NOT IN (...)`
   filter excluding `pg_catalog`, `information_schema`, `pg_toast`, and
   `topology`. If missing, add it.

3. **Add private SQL helper for QueryValues**:
   ```python
   def _list_values(schema: str, table: str, column: str) -> str
   ```
   Returns a SQL string:
   `SELECT "<column>" FROM "<schema>"."<table>" ORDER BY 1`
   (Use `psycopg2.sql.Identifier` for identifiers — never f-string
   interpolation. The helper returns the SQL object/string; actual execution
   goes through `run_query`.)

4. **Implement `CRC_QueryValues` bundle** at
   `grasshopper/components/CRC_QueryValues/`:

   `metadata.json` — subcategory `02.Queries`, inputs:
   - `CString` (`typeHintID: "str"`, `scriptParamAccess: "item"`)
   - `CToggle` (`typeHintID: "bool"`, `scriptParamAccess: "item"`)
   - `schema` (`typeHintID: "str"`, `scriptParamAccess: "item"`)
   - `table` (`typeHintID: "str"`, `scriptParamAccess: "item"`)
   - `column` (`typeHintID: "str"`, `scriptParamAccess: "item"`)
   - `N` (`typeHintID: "str"`, `scriptParamAccess: "item"`,
     description: `"Value to replace NULL entries with"`)

   Outputs:
   - `values` (description: `"All values of the queried column, NULLs replaced by N"`)
   - `report` (description: `"Status message / Exceptions"`)

   `code.py` pattern:
   ```python
   from crc_modules.db.query import run_query, _list_values

   values, report = [], "Set 'CToggle' to True to execute"
   if CToggle:
       try:
           sql = _list_values(schema, table, column)
           _rows, _ = run_query(CString, sql)
           null_sub = N if N is not None else ""
           values = [str(r[0]) if r[0] is not None else null_sub for r in _rows]
           report = "OK - {} values".format(len(values))
       except Exception as e:
           report = "ERROR: {}".format(e)
   ```

   > **NULL handling**: post-fetch string replacement (matching legacy
   > `Replace Text` wiring), not SQL COALESCE. If `N` is None/unset,
   > substitute empty string.

5. **Update `tests/test_query.py`**:
   - `run_query` success path: mock `cursor.fetchall` and
     `cursor.description`, assert returned tuple shape.
   - `run_query` failure path: mock raises `psycopg2.OperationalError`,
     assert it propagates.
   - `run_command` rowcount path.
   - String tests for `_list_schemas()` SQL — assert output contains
     `information_schema` (source table) and `NOT IN` exclusion clause.
   - String tests for `_list_tables`, `_list_columns`, `_list_values`.
   - `_list_values` NULL-replacement test: given rows `[(None,), ("hello",)]`
     and `N = "N/A"`, assert output list is `["N/A", "hello"]`.

6. **Build & install**:
   ```powershell
   python build_userobjects.py
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```

---

## Tests

```powershell
pytest tests/test_query.py -v
```

---

## Grasshopper checkpoint

Restart Grasshopper after installing. First run `CRC_ConnectionString` (enter
the five params) and wire its `CString` output (plus a `CToggle`) into each
component below.

**Verify existing Done components (spot-check only):**

- `CRC_QuerySchemaNames` — `schemas` output must NOT include `pg_catalog` or
  `information_schema`. If it does, fix `_list_schemas()` filter and rebuild.
- `CRC_QueryTableNames` — `tables` output lists tables in the specified schema.
- `CRC_QueryColumnNames` — `columns` and `types` are aligned.

**CRC_QueryValues** — wire `CString` + `CToggle` + `schema = "public"` +
`table = "<a table you have>"` + `column = "<a column with NULLs>"` +
`N = "N/A"`. Expect `values` to be a list of strings with no Python `None`
values (NULLs replaced by `"N/A"`). Then try a column with no NULLs:
all values appear unchanged. Then induce a failure (wrong column name) and
confirm `report` shows the psycopg2 error and the component does not red-bubble.

Save canvases as `tests/_manual/smoke_query_*.gh`.

---

## Commit

```
feat(db): add CRC_QueryValues + system-schema filter to _list_schemas
```

---

## Done when

- [ ] `carcara/crc_modules/db/query.py` includes `_list_values` and the
      system-schema exclusion filter in `_list_schemas`.
- [ ] `tests/test_query.py` covers happy + error paths for all helpers,
      including NULL substitution in `_list_values`.
- [ ] `CRC_QueryValues` GH bundle built and validated against a real DB.
- [ ] `CRC_QuerySchemaNames` confirmed to exclude system schemas on the canvas.
- [ ] Status of `CRC_QueryValues` flipped to ✅ Done in `CLAUDE.md`.
