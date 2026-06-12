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
- The `report` / `if run:` pattern from `CLAUDE.md` actually behaves on the
  canvas.

We pick **`CRC_SRID`** as the smoke test because it is the smallest real
component in the inventory (a lookup-style utility, no DB, no geometry, no
external assets).

## Inputs you must give me

Open `carcara-old/carcara/carcara_SRID_r00.ghuser` in Grasshopper (drag onto
the canvas) and tell me:

1. **Component name and nickname** as it appears in GH.
2. **Input parameters**: name, type hint (`str` / `int` / `bool` / etc.),
   item or list access, any default value.
3. **Output parameters**: name and one-line description each.
4. **Runtime behavior**: what does it return when you flip `run` / type a
   value? Is it a lookup of EPSG codes? A converter? A list of supported
   SRIDs? Paste a short transcript of you using it.
5. **Any hidden behavior**: dropdowns, right-click menus, default
   fall-through values.

Without this I will guess wrong about parameter names — and parameter names
are the user-visible API.

## Steps

> Do **not** start until Phase 01's `CRC_Ping` has loaded successfully in
> Grasshopper. The smoke test is meaningful only on a known-good pipeline.

1. **Implement `carcara/crc_modules/utils/srid.py`** based on the behavior you described.
   Typical shape (adjust to real legacy behavior):
   ```python
   def lookup_srid(name: str) -> tuple[int, str]:
       """Return (epsg_code, human_label) for a known SRID alias."""
   ```
   No Rhino imports. No file I/O. Pure data.

2. **Write `tests/test_srid.py`** with at least:
   - one happy path (`lookup_srid("WGS84")` → `(4326, ...)`)
   - one unknown-input path that raises a clear exception.
   Run `pytest tests/test_srid.py -v` until green.

3. **Build the GH bundle** at `grasshopper/components/CRC_SRID/`:
   - `metadata.json` — exact inputs/outputs from the legacy, subcategory
     `Utilities`, category `Carcara`.
   - `code.py` — follow the `CLAUDE.md` pattern (sys.path bootstrap that puts
     `…/UserObjects/carcara` on the path + `from crc_modules.utils.srid import …`
     + `if run:` + try/except + `report`).
   - `icon.png` — start with a placeholder; we'll refresh icons in Phase 11.

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
2. In the component tabs, find **Carcara → Utilities → SRID** (or whatever
   nickname your metadata declared).
3. Drag it onto an empty canvas. Wire it up:
   - Input → a `Panel` containing the test name (e.g. `WGS84`).
   - The `run` boolean → a `Boolean Toggle` set to `True`.
   - Each output → a `Panel`.
4. Verify:
   - The expected SRID number / label appears in the output panels.
   - The `report` panel shows `OK – ...` (or whatever success string you
     chose), not `ERROR: …` and not the "not yet run" string.
   - Flipping `run` to `False` switches `report` back to the "not yet run"
     string and clears outputs.
   - Typing an unknown alias makes `report` show `ERROR: …` **without**
     Grasshopper turning the component red-bubble-crashed. (Errors must
     route to `report`, never bubble up.)
5. Save the canvas as `tests/_manual/smoke_srid.gh` (gitignored) for future
   manual re-runs.

If any of those four checks fails, stop and fix before Phase 03 —
they will all recur in the real components.

## Commit

```
feat(utils): add SRID lookup + first GH smoke-test component CRC_SRID
```

## Done when

- [ ] `carcara/crc_modules/utils/srid.py` exists with the lookup function.
- [ ] `tests/test_srid.py` passes.
- [ ] `grasshopper/components/CRC_SRID/{metadata.json,code.py,icon.png}` all
      exist.
- [ ] `carcara/userobjects/CRC_SRID.ghuser` is built.
- [ ] Component loads in Grasshopper and behaves per the four canvas checks.
- [ ] Status of `CRC_SRID` flipped from ⬜ Todo to ✅ Done in `CLAUDE.md`.
- [ ] `CRC_Ping` deleted.
