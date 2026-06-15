# Phase 02 — Smoke Test: First Real Component in Grasshopper

## Goal

Ship **one** small, real Carcara component end-to-end and click it on the
Grasshopper canvas. No database, no Rhino-specific geometry, no external
deps beyond the standard `crc_modules` library — pure Python in, pure Python
out. The point is to validate:

- Deploying the `carcara/` folder makes `crc_modules` importable from Rhino 8's
  Python (the `sys.path` bootstrap in `code.py` resolves it).
- The bundle layout works.
- `build_userobjects.py` produces a `.ghuser` that loads and runs in GH.
- The `report` / `if CToggle:` pattern from `CLAUDE.md` actually behaves on the
  canvas.

We pick **`CRC_SQLComposer`** as the smoke test because it is pure Python (no
DB, no Rhino, no external deps), its logic is a single string-replace loop, and
its legacy source is fully decoded and ready to read.

> **CRC_SRID is excluded from this and all phases.** It is a native Grasshopper
> ValueList component created manually by the user — it is not part of the
> componentizer build pipeline. No `srid.py`, no test, no bundle.

## Inputs you must give me

The decoded legacy script is already available at
`carcara-old/ghuser-metadata/scripts/SQLComposer.py` and the capture doc at
`carcara-old/ghuser-metadata/03.Utilities.md`. No action required — parameter
names and behavior are confirmed. Proceed directly to Steps.

## Steps

> Do **not** start until Phase 01's `CRC_Ping` has loaded successfully in
> Grasshopper. The smoke test is meaningful only on a known-good pipeline.

1. **Implement `carcara/crc_modules/utils/sql_composer.py`** with a single
   public function:

   ```python
   def compose(template: str, replacements: dict[str, str]) -> str:
       """
       Replace each key in `replacements` with its value inside `template`
       using plain str.replace(). No quoting, no escaping — the caller
       chooses placeholder tokens and is responsible for safe values.
       Raises ValueError if `template` is empty.
       Returns the final SQL statement string.
       """
   ```

   The legacy engine (`SQLComposer.py`, `replace_placeholders`) confirms this
   is a plain `str.replace` loop: for each `(placeholder, replacement)` pair,
   call `statement.replace(placeholder_str, replacement_str)`. Placeholder
   syntax is free-form — callers choose any unique substring (`#SCHEMA#`,
   `*TABLE*`, etc.).

   No Rhino imports. No psycopg2. Pure string logic.

2. **Write `tests/test_sql_composer.py`** with at least:
   - Happy path: template `"SELECT * FROM #TABLE#"`, replacements
     `{"#TABLE#": "buildings"}` → `"SELECT * FROM buildings"`.
   - Multiple replacements applied in sequence.
   - Unmatched placeholder: template returned with placeholder intact (no error).
   - Empty template: raises `ValueError`.

   Run `pytest tests/test_sql_composer.py -v` until green.

3. **Build the GH bundle** at `grasshopper/components/CRC_SQLComposer/`:

   **`metadata.json`** — exact inputs/outputs from the legacy source (`sql`,
   `var`, `val` in; `out`, `stmt` out), subcategory `03.Utilities`, category
   `Carcara`, exposure `4`:

   ```json
   {
     "name": "SQLComposer",
     "nickname": "SQLComp.py",
     "category": "Carcara",
     "subcategory": "03.Utilities",
     "description": "Generates SQL statements by replacing variable placeholders with corresponding values.",
     "exposure": 4,
     "ghpython": {
       "isAdvancedMode": false,
       "marshalGuids": true,
       "iconDisplay": 0,
       "inputParameters": [
         { "name": "sql",  "description": "SQL template with placeholders (e.g., 'SELECT * FROM #table# WHERE col = #value#').", "typeHintID": "str",  "scriptParamAccess": "item" },
         { "name": "var",  "description": "List of placeholder strings to be replaced.", "typeHintID": "str",  "scriptParamAccess": "list" },
         { "name": "val",  "description": "List of replacement values corresponding to the placeholders.", "typeHintID": "str",  "scriptParamAccess": "list" }
       ],
       "outputParameters": [
         { "name": "out",  "description": "Processing log" },
         { "name": "stmt", "description": "Final SQL statement after all replacements." },
         { "name": "report", "description": "Status message" }
       ]
     }
   }
   ```

   **`code.py`** — follow the `CLAUDE.md` sys.path bootstrap pattern.
   `CToggle` guards execution. Zip `var` and `val` into a `dict` and call
   `compose(sql, replacements)`. Surface results via `stmt` and `report`.
   No Rhino imports, no DB calls:

   ```python
   import sys
   import os

   _bases = []
   _appdata = os.environ.get("APPDATA")
   if _appdata:
       _bases.append(os.path.join(_appdata, "Grasshopper", "UserObjects", "carcara"))
   _bases.append(os.path.join(
       os.path.expanduser("~"), "Library", "Application Support", "McNeel",
       "Rhinoceros", "8.0", "Plug-ins", "Grasshopper", "UserObjects", "carcara"))
   for _b in _bases:
       if os.path.isdir(_b) and _b not in sys.path:
           sys.path.insert(0, _b)

   from crc_modules.utils.sql_composer import compose

   stmt, report = "", "Set 'CToggle' to True to execute"

   if CToggle:
       try:
           if not sql:
               raise ValueError("No SQL template provided.")
           _var = var if isinstance(var, (list, tuple)) else ([var] if var else [])
           _val = val if isinstance(val, (list, tuple)) else ([val] if val else [])
           if len(_var) != len(_val):
               raise ValueError(
                   f"var and val must have the same length "
                   f"(got {len(_var)} and {len(_val)})."
               )
           replacements = dict(zip([str(v) for v in _var], [str(v) for v in _val]))
           stmt = compose(sql, replacements)
           n = len(replacements)
           report = f"OK – {n} replacement{'s' if n != 1 else ''} applied"
       except Exception as e:
           report = f"ERROR: {e}"
   ```

   **`icon.png`** — start with a placeholder 24×24 PNG; icons are refreshed
   in a later phase.

4. **Build & install** (deploy the whole folder so `crc_modules` is on the path):

   ```powershell
   python build_userobjects.py
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```

5. **Retire `CRC_Ping`** once the smoke test passes — delete the
   `grasshopper/components/CRC_Ping/` folder. The pipeline is proven; the
   placeholder isn't needed anymore.

## Tests

```powershell
pytest tests/ -v
python build_userobjects.py
```

Both must succeed.

## Grasshopper checkpoint — **this is the real one**

1. Restart Grasshopper.
2. In the component tabs, find **Carcara → 03.Utilities → SQLComposer** (nickname
   `SQLComp.py`).
3. Drag it onto an empty canvas. Wire it up:
   - `sql` input → a `Panel` containing e.g. `SELECT * FROM #SCHEMA#.#TABLE#`.
   - `var` input → a `Panel` (list) with `#SCHEMA#` and `#TABLE#`.
   - `val` input → a `Panel` (list) with `public` and `buildings`.
   - `CToggle` → a `Boolean Toggle` set to `True`.
   - Each output → a `Panel`.
4. Verify:
   - `stmt` shows `SELECT * FROM public.buildings`.
   - `report` shows `OK – 2 replacements applied`, not `ERROR: …` and not
     the "not yet run" string.
   - Flipping `CToggle` to `False` switches `report` back to the "not yet
     run" string and clears `stmt`.
   - Providing mismatched `var`/`val` lengths makes `report` show `ERROR: …`
     **without** Grasshopper turning the component red-bubble-crashed. (Errors
     must route to `report`, never bubble up.)
5. Save the canvas as `tests/_manual/smoke_sqlcomposer.gh` (gitignored) for
   future manual re-runs.

If any of those four checks fails, stop and fix before Phase 03 —
they will all recur in the real components.

## Commit

```
feat(utils): add sql_composer + first GH smoke-test component CRC_SQLComposer
```

## Done when

- [ ] `carcara/crc_modules/utils/sql_composer.py` exists with the `compose`
      function.
- [ ] `tests/test_sql_composer.py` passes.
- [ ] `grasshopper/components/CRC_SQLComposer/{metadata.json,code.py,icon.png}`
      all exist.
- [ ] `carcara/userobjects/CRC_SQLComposer.ghuser` is built.
- [ ] Component loads in Grasshopper and behaves per the four canvas checks.
- [ ] Status of `CRC_SQLComposer` flipped from ⬜ Todo to ✅ Done in `CLAUDE.md`.
- [ ] `CRC_Ping` deleted.
