# Phase 12 — Generic Query/Command Wrappers, Final Inventory Cross-check, Ship

## Goal

Close the inventory: deliver the two generic query/command runner components
and run the full audit confirming every legacy `.ghuser` listed in `CLAUDE.md`
has been reimplemented. End state: `carcara/userobjects/` ships a complete
plugin.

> **Name decision (resolved):** Components are **`CRC_RunQuery`** and
> **`CRC_RunCommand`**. ODBC is gone — the rebuild uses `psycopg2` throughout.
> Renaming is deliberate and documented in `metadata.json` descriptions.
> There are no `CRC_RunODBC*` components in the rebuild.

Components delivered:

| Component         | Legacy file                        | Module               | Notes                       |
|-------------------|------------------------------------|----------------------|-----------------------------|
| `CRC_RunQuery`    | `carcara_RunODBCQuery_rev03.ghuser`   | `db/query.py` (wrap) | Thin wrapper over `run_query`   |
| `CRC_RunCommand`  | `carcara_RunODBCCommand_rev01.ghuser` | `db/query.py` (wrap) | Thin wrapper over `run_command` |

---

## Legacy interface (decoded — read-only reference)

**CRC_RunQuery** (legacy: `RunODBCQuery.py` at
`carcara-old/ghuser-metadata/scripts/RunODBCQuery.py`):

- Inputs: `CString`, `CToggle`, `Query` (SQL query string).
- Outputs: `QResult` (DataTree — each branch is a column of data),
  `QHeaders` (DataTree — column names mirroring `QResult` structure).
- Subcategory: `03.Utilities` (confirmed from legacy script metadata).
- In the rebuild: rename inputs/outputs to use the new standard names
  (`sql` for the query input; `rows` / `columns` for outputs).

**CRC_RunCommand** (legacy: `RunODBCCommand.py` at
`carcara-old/ghuser-metadata/scripts/RunODBCCommand.py`):

- Inputs: `CString`, `CToggle`, `Command` (SQL command string).
- Outputs: `Fb` (str — detailed execution feedback, format:
  `"success: true\nRows Affected: N"` or error details).
- Subcategory: `03.Utilities` (confirmed from legacy script metadata).
- In the rebuild: rename input to `sql`; rename output to `report`
  (feedback string, same format as legacy `Fb`).

---

## Steps

1. **Wrap, don't reimplement**: both new components call `run_query` /
   `run_command` from `carcara/crc_modules/db/query.py` (already shipped in
   Phase 04). No new code in `crc_modules/`.

2. **GH bundles** (subcategory **03.Utilities**; same `CString` + `CToggle`
   pattern as Phase 04):

   `CRC_RunQuery/` — inputs:
   - `CString` (`str`, `item`), `CToggle` (`bool`, `item`)
   - `sql` (`str`, `item`, description: `"SQL SELECT statement to execute"`)

   Outputs:
   - `rows` (`tree` — DataTree by column: each branch contains one column's
     values for all returned rows)
   - `columns` (`tree` — DataTree of column name strings, mirroring `rows`
     structure)
   - `report` (`item`, str — `"OK – N rows, M columns"` or error message)

   `metadata.json`: `scriptParamAccess: "tree"` for `rows` and `columns`.

   `CRC_RunCommand/` — inputs:
   - `CString` (`str`, `item`), `CToggle` (`bool`, `item`)
   - `sql` (`str`, `item`, description: `"SQL DDL/DML command to execute (non-SELECT)"`)

   Outputs:
   - `report` (`item`, str — feedback string formatted as
     `"success: true\nRows Affected: N"` on success, or error details on
     failure)

   Default "not yet run" report for both: `"Set 'CToggle' to True to execute"`.

3. **No new tests** — the underlying functions are already covered by
   `tests/test_query.py`. Add one smoke test that imports both components'
   `code.py` strings and asserts they reference only the public API (`run_query`
   / `run_command`) and contain no direct `psycopg2` imports or raw connection
   logic.

4. **Build & install** both:
   ```powershell
   python build_userobjects.py
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```

5. **Inventory cross-check** — this is the gate that closes the rebuild:

   a. List every `.ghuser` in `carcara-old/carcara/`:
      ```powershell
      Get-ChildItem carcara-old\carcara\*.ghuser | Select-Object -Expand Name
      ```

   b. Cross-reference against the inventory tables in `CLAUDE.md`. For each
      legacy file, confirm there is a matching row with status ✅ Done.

   c. Cross-reference against `carcara/userobjects/`:
      ```powershell
      Get-ChildItem carcara\userobjects\*.ghuser | Select-Object -Expand Name
      ```
      Every legacy entry must have a corresponding built `.ghuser`.

   d. If you discover any legacy file that does **not** appear in the
      inventory, stop and add it as a new row before declaring complete.

   e. Confirm `CRC_SRID` is present as a manually created native GH ValueList
      component — it does not go through the componentizer build pipeline.

6. **README pass**: update the top-level `README.md` to point users at the
   GitHub installer (`grasshopper/installer/`, delivered as a `.gh`) and the
   committed `carcara/userobjects/*.ghuser`, and link to `CLAUDE.md` /
   `implementation/` for development.

---

## Tests

```powershell
pytest tests/ -v
python build_userobjects.py
```

The full suite must be green and the full build must produce one `.ghuser`
per inventory row.

---

## Grasshopper checkpoint — full plugin

Restart Grasshopper. Verify, by tab inspection alone, that the **Carcara**
ribbon shows (subcategories per the `CLAUDE.md` master map):

- **01.Modeling** — 6 components.
- **02.Queries** — 9 components.
- **03.Utilities** — 7 components.
- **04.Dataviz** — 10 components.

Total: **32 built components** (from the componentizer pipeline), plus
`CRC_SRID` added manually as a native GH ValueList = **33 total** covering
the full legacy inventory. The Phase 02 `CRC_Ping` smoke component is deleted
before shipping.

Open one canvas that exercises a full pipeline end-to-end:
`CRC_ConnectionString` → `CRC_GeometriesWithSpatialFilter` →
`CRC_WKTtoGrasshopperGeometry` → `CRC_OffsetPython` →
`CRC_PolylineToSVG` → `CRC_SaveSVG`. Save it as
`tests/_manual/smoke_full_pipeline.gh`. This canvas is the manual
acceptance test for the whole plugin.

---

## Commit

```
feat(db): add CRC_RunQuery + CRC_RunCommand wrappers; complete legacy inventory rebuild
```

---

## Done when

- [ ] Both `CRC_RunQuery` and `CRC_RunCommand` built, installed, and validated
      on the canvas with a real PostGIS connection.
- [ ] `CRC_RunQuery` outputs `rows`/`columns` as DataTree by column.
- [ ] `CRC_RunCommand` outputs `report` as feedback string
      (`"success: true\nRows Affected: N"`).
- [ ] Both components sit in subcategory **03.Utilities**.
- [ ] Every row in every `CLAUDE.md` inventory table is ✅ Done.
- [ ] Every legacy `.ghuser` in `carcara-old/carcara/` has a matching
      file in `carcara/userobjects/`.
- [ ] Full-pipeline smoke canvas runs cleanly in Grasshopper.
- [ ] `README.md` updated with install + dev pointers.
- [ ] `pytest tests/ -v` and `python build_userobjects.py` both green.

---

## After this phase

Everything past this point is post-rebuild work, out of scope for this plan:
icon refresh, plugin packaging (`.yak`), release tagging, CI on GitHub Actions,
documentation site, demo videos, etc. Open a separate plan for any of those
when you're ready.
