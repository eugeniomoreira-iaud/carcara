# Phase 00 — Scaffolding & Audit

> **Note (post-restructure):** this phase is DONE and predates the repo
> restructure. The package now lives at `carcara/crc_modules/` and its import
> name is `crc_modules` (not `carcara`); the deployable folder is `carcara/`.
> The steps below are kept for history with paths/commands corrected.

## Goal

Bring the repository up to the layout declared in `CLAUDE.md` so every later
phase can assume a clean baseline. No new behavior, no new components — just
folders, packaging, and a sanity check that `import crc_modules` works.

## Inputs you must give me

None. This phase is purely structural.

## Current state (auto-detected, 2026-06-09)

- ✅ `carcara/__init__.py` exists
- ✅ `carcara/db/` exists with partial `connection.py`, `query.py`
- ✅ `pyproject.toml` exists at repo root
- ✅ `build_userobjects.py` exists at repo root
- ✅ `specs/componentizer.md` exists
- ⚠️ `grasshopper/components/CRC_ConnectionString.py` is a **flat `.py` file**.
  Spec requires the **bundle layout** (folder containing `metadata.json`,
  `code.py`, `icon.png`). This must be migrated.
- ⚠️ `test_connection.py`, `test_query.py` live at **repo root**. Spec puts
  them under `tests/`.
- ❌ No `tests/` directory.
- ❌ No `dist/` directory.
- ❌ No `vendor/componentizer/` (componentizer not yet vendored).
- ❌ No `carcara/geometry/`, `carcara/svg/`, `carcara/viz/`, `carcara/utils/`
  packages.

## Steps

1. **Create the missing package skeleton** under `carcara/crc_modules/`:
   ```
   carcara/crc_modules/geometry/__init__.py
   carcara/crc_modules/svg/__init__.py
   carcara/crc_modules/viz/__init__.py
   carcara/crc_modules/utils/__init__.py
   carcara/crc_modules/rhino/__init__.py
   ```
   Each `__init__.py` stays empty for now (except `rhino/` which carries a
   Rhino-only warning docstring).

2. **Move tests** to the canonical location:
   - `test_connection.py` → `tests/test_connection.py`
   - `test_query.py`      → `tests/test_query.py`
   - Add `tests/__init__.py` if pytest discovery needs it (usually not).

3. **Build output dir is `carcara/userobjects/`** and is **committed** (it ships
   to users). No `dist/.gitkeep` is needed anymore.

4. **Create / update `.gitignore`** to include:
   ```
   .env
   dist/
   __pycache__/
   *.pyc
   *.ghuser
   *.gh
   # but DO commit the shipped components inside the deployable folder:
   !carcara/userobjects/
   !carcara/userobjects/*.ghuser
   ```
   Note: `*.gh` masks Grasshopper definitions (they can embed credentials).

5. **Migrate `CRC_ConnectionString.py`** out of the flat layout:
   - Read the current contents of `grasshopper/components/CRC_ConnectionString.py`.
   - Move them to `grasshopper/components/CRC_ConnectionString/code.py`.
   - Stub `grasshopper/components/CRC_ConnectionString/metadata.json` with the
     minimum schema from `CLAUDE.md` (real metadata gets finalized in Phase 03).
   - Add a **placeholder 24×24 `icon.png`** (any solid color is fine for now).
   - Delete the original flat `.py`.

6. **Verify `pyproject.toml`** has:
   - `name = "carcara"`
   - the runtime deps from `CLAUDE.md` (`psycopg2`, `shapely`,
     `svgwrite`, `matplotlib`)
   - the `[build-system]` block (setuptools or hatchling — either is fine).
   - `[tool.setuptools.packages.find]` with `where = ["carcara"]`,
     `include = ["crc_modules*"]`.
   - `[tool.pytest.ini_options]` with `pythonpath = ["carcara"]` so tests import
     `crc_modules` with no install.
   - If anything is missing, add it. Document the addition in the commit.

7. **Confirm imports** (no editable install needed — `pythonpath` handles it):
   ```powershell
   python -c "import sys; sys.path.insert(0, 'carcara'); import crc_modules, crc_modules.db.connection, crc_modules.db.query; print('OK')"
   ```

## Tests

```powershell
pytest tests/ -v
```

The two migrated tests must still pass. If they reference the old import
paths or relative imports, fix them.

## Grasshopper checkpoint

**None this phase.** No new component is built; the only Grasshopper-related
work is the layout migration of `CRC_ConnectionString`, which we do **not**
build into a `.ghuser` yet — Phase 01 wires up the build pipeline, and
Phase 02 ships the first `.ghuser` end-to-end.

If you want sanity though, run:
```powershell
python -c "import json; print(json.load(open('grasshopper/components/CRC_ConnectionString/metadata.json'))['name'])"
```
Should print `ConnectionString`.

## Commit

```
chore(scaffold): create package skeleton, migrate tests, bundle-layout components
```

## Done when

- [ ] `carcara/crc_modules/{db,geometry,svg,viz,utils,rhino}/__init__.py` all exist.
- [ ] `tests/test_connection.py` and `tests/test_query.py` exist and pass.
- [ ] `grasshopper/components/CRC_ConnectionString/` is a folder with the
      three required files; no flat `.py` left behind.
- [ ] `import crc_modules` succeeds (via `pythonpath` or with `carcara/` on sys.path).
- [ ] `pytest tests/ -v` is green.
