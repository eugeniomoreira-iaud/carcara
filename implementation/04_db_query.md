# Phase 04 — DB Query (`db/query.py` + 4 query components)

## Goal

Run arbitrary SQL against PostGIS from Grasshopper and surface
`(rows, columns)` into the canvas. Cover the four read-side query
components in one phase, because they all share `db/query.py`.

Components delivered:

| Component               | Purpose                                |
|-------------------------|----------------------------------------|
| `CRC_QueryValues`       | Run an arbitrary SELECT, return rows.  |
| `CRC_QuerySchemaNames`  | List schemas in the DB.                |
| `CRC_QueryTableNames`   | List tables in a schema.               |
| `CRC_QueryColumnNames`  | List columns in a table.               |

## Inputs you must give me

For each of the four legacy `.ghuser` files, open in Grasshopper and report:

1. `carcara_QueryValues_rev03.ghuser`
2. `carcara_QuerySchemaNames_r03.ghuser`
3. `carcara_QueryTableNames_rev03.ghuser`
4. `carcara_QueryColumnNames_rev03.ghuser`

For each, give me:

- Input parameter names, types, defaults.
- Output parameter names. (e.g. is it `rows` + `columns`, or `data tree`?)
- Whether the legacy emits rows as a flat list of strings, a DataTree by row,
  or a DataTree by column. **This affects `scriptParamAccess`** in
  `metadata.json` (`item` vs `list` vs `tree`).
- Whether `QuerySchemaNames` filters out system schemas (`pg_*`, `information_schema`).

Also confirm: a real test database with at least one non-trivial schema +
table (e.g. PostGIS `tiger` data, or a `public.cities` table with rows) so
we can validate output shape.

## Steps

> **Credential model (CString):** DB components take a **`CString`** input (the
> connection string from `CRC_ConnectionString`) plus a **`CToggle`** boolean trigger.
> The function layer decodes `CString` with `parse_connection_string`; the GH layer
> never unpacks individual credentials. Every component below follows this
> DB-component pattern in `code.py`:
>
> ```python
> # sys.path bootstrap puts …/UserObjects/carcara on the path (see CLAUDE.md)
> from crc_modules.db.query import run_query
>
> rows, columns, report = [], [], "Set 'CToggle' to True to execute"
> if CToggle:
>     try:
>         _rows, columns = run_query(CString, sql)   # CString carries the creds
>         rows = [str(r) for r in _rows]
>         report = "OK - {} rows".format(len(rows))
>     except Exception as e:
>         report = "ERROR: {}".format(e)
> ```

1. **Implement `carcara/crc_modules/db/query.py`** to spec:
   ```python
   def run_query(cstring, sql) -> tuple[list, list]
   def run_command(cstring, sql) -> int
   ```
   - `run_query`: decode `cstring` via `parse_connection_string`, open connection,
     execute, fetch all, return `(rows_as_list_of_tuples, column_names_as_list_of_str)`.
     Close connection in `finally`.
   - `run_command`: same, then commit, return `cur.rowcount`.
   - Both raise `psycopg2.Error` on failure (do not catch and stringify here
     — the GH layer does that).

2. **Add small SQL helpers** in the same module (private):
   ```python
   def _list_schemas() -> str
   def _list_tables(schema: str) -> str
   def _list_columns(schema: str, table: str) -> str
   ```
   These return SQL strings that read from `information_schema`. Keeping
   them in `carcara/crc_modules/db/query.py` (not in components) preserves the
   "no business logic in code.py" rule.

3. **Update `tests/test_query.py`**:
   - `run_query` success path: mock `cursor.fetchall` and
     `cursor.description`, assert returned tuple shape.
   - `run_query` failure path: mock raises `psycopg2.OperationalError`,
     assert it propagates.
   - `run_command` rowcount path.
   - String tests for `_list_schemas` / `_list_tables` / `_list_columns`
     output SQL.

4. **Build four GH bundles** under `grasshopper/components/` (all subcategory
   **02.Queries**). Each takes `CString` + `CToggle`, not raw credentials:
   - `CRC_QueryValues/`        — inputs `CString,CToggle,sql`; outputs `rows,columns,report`.
   - `CRC_QuerySchemaNames/`   — inputs `CString,CToggle`; outputs `schemas,report`.
   - `CRC_QueryTableNames/`    — inputs `CString,CToggle,schema`; outputs `tables,report`.
   - `CRC_QueryColumnNames/`   — inputs `CString,CToggle,schema,table`; outputs `columns,types,report`.

   Each `code.py` follows the DB-component pattern above (bootstrap +
   `if CToggle:` try/except calling `run_query(CString, sql)`). **None of them
   assemble SQL by string concatenation of user input** — use the private
   helpers from `query.py` to avoid injection in the schema/table/column list
   components. `CRC_QueryValues` accepts raw SQL on purpose (explicit
   power-user component).

5. **Build & install all four** (deploy the whole folder so `crc_modules` is on path):
   ```powershell
   python build_userobjects.py
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```

## Tests

```powershell
pytest tests/test_query.py -v
```

## Grasshopper checkpoint

Restart Grasshopper after installing. For each component:

First run `CRC_ConnectionString` (enter the five params) and wire its `CString`
output (plus a `CToggle`) into each query component below.

**CRC_QuerySchemaNames** — wire `CString` → toggle `CToggle`. The `schemas`
output should list `public` and any others. The `report` should be `OK – N schemas`.

**CRC_QueryTableNames** — `CString` + `schema = "public"`. The
`tables` output should list every public table.

**CRC_QueryColumnNames** — `CString` + `schema = "public"` +
`table = "<some table>"`. The `columns` and `types` outputs should align
positionally.

**CRC_QueryValues** — `CString` + `sql = "SELECT 1 AS one, 'a' AS letter"`.
Expect `rows = ["(1, 'a')"]` and `columns = ["one", "letter"]`. Then try
something real like `SELECT name FROM <a table you have> LIMIT 5;`.

For each, induce a failure (wrong table, syntax error). Confirm `report`
shows the underlying psycopg2 error verbatim and the component does not
red-bubble.

Save canvases as `tests/_manual/smoke_query_*.gh`.

## Commit

```
feat(db): add run_query/run_command + 4 query components
```

## Done when

- [ ] `carcara/crc_modules/db/query.py` matches spec + helpers added.
- [ ] `tests/test_query.py` covers happy + error paths.
- [ ] Four GH bundles built and validated on the canvas against a real DB.
- [ ] Statuses of all four query components flipped to ✅ Done in `CLAUDE.md`.
