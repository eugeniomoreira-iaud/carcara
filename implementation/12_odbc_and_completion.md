# Phase 12 — ODBC Wrappers, Final Inventory Cross-check, Ship

## Goal

Close the inventory: the two remaining `CRC_RunODBC*` components and the
full audit that confirms every legacy `.ghuser` listed in `CLAUDE.md` has
been reimplemented. End state: `carcara/userobjects/` ships a complete plugin.

Components delivered:

| Component             | Module               | Notes                                        |
|-----------------------|----------------------|----------------------------------------------|
| `CRC_RunODBCQuery`    | `db/query.py` (wrap) | Thin wrapper over `run_query`                |
| `CRC_RunODBCCommand`  | `db/query.py` (wrap) | Thin wrapper over `run_command`              |

## Inputs you must give me

1. For each of `carcara_RunODBCQuery_rev03.ghuser` and
   `carcara_RunODBCCommand_rev01.ghuser`, the input/output schema.

2. **One decision**: the legacy components used ODBC; `CLAUDE.md` mandates
   `psycopg2`. Two options:

   a. **Keep the legacy names** (`CRC_RunODBCQuery`, `CRC_RunODBCCommand`)
      for user-facing continuity. Behavior is `psycopg2` under the hood,
      and the component description in `metadata.json` notes the change.
      Recommended for backwards compatibility on existing GH definitions.

   b. **Rename** to `CRC_RunQuery` / `CRC_RunCommand`. Cleaner, but breaks
      existing canvases.

   Tell me which one you want. If unspecified, default to (a).

## Steps

1. **Wrap, don't reimplement**: both new components call `run_query` /
   `run_command` from `carcara/crc_modules/db/query.py` (already shipped Phase
   04). No new code in `crc_modules/`.

2. **GH bundles** (02.Queries; same `CString` + `CToggle` pattern as Phase 04):
   - `CRC_RunODBCQuery/`   — inputs: `CString`, `CToggle`, `sql`;
     outputs: `rows`, `columns`, `report`.
   - `CRC_RunODBCCommand/` — inputs: `CString`, `CToggle`, `sql`;
     outputs: `affected`, `report`.

3. **No new tests** — the underlying functions are already covered by
   `tests/test_query.py`. Add one smoke test that imports both components'
   `code.py` strings and asserts they reference the public API only.

4. **Build & install** both.

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

6. **README pass**: update the top-level `README.md` to point users at the
   GitHub installer (`grasshopper/installer/`, delivered as a `.gh`) and the
   committed `carcara/userobjects/*.ghuser`, and link to `CLAUDE.md` /
   `implementation/` for development.

## Tests

```powershell
pytest tests/ -v
python build_userobjects.py
```

The full suite must be green and the full build must produce one `.ghuser`
per inventory row.

## Grasshopper checkpoint — full plugin

Restart Grasshopper. Verify, by tab inspection alone, that the **Carcara**
ribbon shows (subcategories per the `CLAUDE.md` master map):

- **01.Modeling** — 6 components.
- **02.Queries** — 13 components.
- **03.Utilities** — 4 components.
- **04.Dataviz** — 10 components.

Total: 33 components (the full legacy inventory; the Phase 02 `CRC_Ping`
smoke component is deleted before shipping).

Open one canvas that exercises a full pipeline end-to-end:
`CRC_ConnectionString` → `CRC_GeometriesWithSpatialFilter` →
`CRC_WKTtoGrasshopperGeometry` → `CRC_OffsetPython` →
`CRC_PolylineToSVG` → `CRC_SaveSVG`. Save it as
`tests/_manual/smoke_full_pipeline.gh`. This canvas is the manual
acceptance test for the whole plugin.

## Commit

```
feat(db): add ODBC* wrappers; complete legacy inventory rebuild
```

## Done when

- [ ] Both ODBC wrappers built, installed, and validated.
- [ ] Every row in every `CLAUDE.md` inventory table is ✅ Done.
- [ ] Every legacy `.ghuser` in `carcara-old/carcara/` has a matching
      file in `carcara/userobjects/`.
- [ ] Full-pipeline smoke canvas runs cleanly in Grasshopper.
- [ ] `README.md` updated with install + dev pointers.
- [ ] `pytest tests/ -v` and `python build_userobjects.py` both green.

---

## After this phase

Everything past this point is post-rebuild work, out of scope for this
plan: icon refresh, plugin packaging (`.yak`), release tagging, CI on
GitHub Actions, documentation site, demo videos, etc. Open a separate
plan for any of those when you're ready.
