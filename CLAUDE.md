# Carcara Plugin — Development Specification

## Overview

Carcara is a Python-based Grasshopper plugin for Rhino 8 that bridges PostGIS spatial databases with parametric design workflows. It enables architects and researchers to query, visualize, and export geospatial data directly from the Grasshopper canvas without leaving the design environment.

This document is the authoritative specification for agentic and collaborative development of the plugin. All code generation, refactoring, and feature additions must conform to the rules and patterns described here.

***

## Design Principles

1. **Separation of concerns**: All domain logic lives in the pure Python library (`carcara/crc_modules/`, import name `crc_modules`). Grasshopper component files contain only GH plumbing — input coercion, output assignment, and error display.
2. **No Rhino imports in the core library**: `crc_modules` must be importable and testable outside of Rhino using a standard CPython 3.11+ environment.
3. **Fail visibly, not silently**: Every component wraps its logic in a try/except and surfaces errors through a `report` output string. No component should crash Grasshopper.
4. **One responsibility per module**: Each file in `crc_modules/` handles one domain concern. Do not mix database logic with geometry conversion.
5. **Editable install**: The package is installed in editable mode (`pip install -e .`) so changes to source files are immediately reflected without reinstallation.

***

## Target Environment

| Property | Value |
|---|---|
| Rhino version | Rhino 8 |
| Python runtime | CPython 3.11+ (Rhino 8 ScriptEditor) |
| GH Python component | Python 3 Script |
| Database | PostgreSQL 14+ with PostGIS 3+ |
| DB driver | `psycopg2` (no ODBC) |
| Package manager | conda (environment: `carcara`) |
| OS | Windows 10/11 (primary), macOS (secondary) |

***

## Repository Structure

Repository root is the project root. There is no `carcara-rebuild/` wrapper folder anymore — what used to live inside it now sits at the repo root.

```
carcara/                              ← Repository root
│
├── carcara/                        ← THE deployable folder. Copied as-is to UserObjects.
│   ├── crc_modules/                ← Pure Python library (import name). No Rhino imports allowed.
│   │   ├── __init__.py
│   │   ├── db/                     ← DB layer (mostly 02.Queries; also ConnectionString + RunQuery/RunCommand which sit in 03.Utilities)
│   │   │   ├── __init__.py
│   │   │   ├── connection.py       ← build/parse CString + test_connection
│   │   │   ├── query.py            ← run_query / run_command (take CString)
│   │   │   ├── writer.py           ← INSERT, CREATE TABLE, CREATE Shapefile
│   │   │   └── spatial_query.py    ← Geometry queries with spatial filters (PK detect, ORDER BY)
│   │   ├── geometry/               ← wkt, polylabel, duplicates, containment (pure Python)
│   │   ├── rhino/                  ← Rhino-only: offset, building_mesh, curve_display (C#). Excluded from pytest.
│   │   ├── svg/                    ← export, save
│   │   ├── viz/                    ← histogram, scatter, lineplot, heatmap
│   │   └── utils/                  ← color, sql_composer, correction (false-origin SQL)
│   ├── userobjects/                ← Built .ghuser files (committed; shipped to users)
│   │   ├── CRC_ConnectionString.ghuser
│   │   └── …
│   └── version.txt                 ← Written by make_release.py; installer reads this
│
├── grasshopper/
│   ├── components/                 ← One FOLDER per GH component (componentizer bundle layout).
│   │   │                             Flat: no subcategory folders — subcategory lives in metadata.json.
│   │   ├── CRC_ConnectionString/
│   │   │   ├── metadata.json       ← Component metadata (name, nickname, category, params)
│   │   │   ├── code.py             ← Thin GH wrapper that calls into crc_modules/
│   │   │   └── icon.png            ← 24×24 PNG
│   │   └── …(one folder per component)
│   └── installer/                  ← Self-contained bootstrap installers (delivered in a .gh)
│       ├── install_python_libs.py  ← pip-installs deps into Rhino 8 CPython
│       └── install_carcara.py      ← downloads repo zip, copies carcara/ → UserObjects
│
├── specs/                          ← Internal specs and how-tos.
│   ├── componentizer.md            ← Componentizer build pipeline reference
│   ├── sdk-components.md           ← SDK/advanced-mode viewport-preview components how-to
│   └── ghuser-decoding.md          ← How to decode legacy .ghuser binaries (CPython only)
│
├── docs/                           ← Reports, design notes, branding assets.
│   ├── current-vs-legacy-component-report.md
│   └── assets/logo_carcara.png
│
├── tools/                          ← Dev utilities (not shipped).
│   └── decode_ghuser.py            ← Canonical legacy .ghuser decoder (stdlib only)
│
├── implementation/                 ← Phase-by-phase rebuild plans (00–12) + _archive/
│
├── tests/                          ← pytest (imports crc_modules.*); never touches the rhino submodule
│   ├── test_connection.py
│   ├── test_query.py
│   └── …
│
├── vendor/                         ← componentizer + GH_IO.dll (build toolchain)
│
├── carcara-old/                    ← LEGACY. Read-only reference of the original plugin.
│   ├── carcara/
│   │   ├── modules/                ← Old monolithic Python modules (charts, dataviz, geometry, odbc)
│   │   └── *.ghuser                ← Original .ghuser components — the rebuild target list
│   ├── ghuser-metadata/            ← Decoded reference layer: capture .md docs + decoded scripts/
│   ├── carcara_winsetup_rev06.gh
│   ├── LICENSE
│   └── README.md
│
├── build_userobjects.py            ← Build script: bundles → carcara/userobjects/*.ghuser
├── make_release.py                 ← Build + stamp version.txt (run before a release)
├── deploy.ps1                      ← Dev: copy carcara/ → UserObjects/carcara/
├── pyproject.toml
├── requirements.txt
└── README.md
```

***

## Legacy Reference: `carcara-old/`

`carcara-old/` is the **frozen previous version** of the plugin. Treat it as read-only documentation, never as code to import or edit.

- **Purpose**: source of truth for behavior, inputs, outputs, and nicknames of every original component. When rebuilding a component, open the matching `.ghuser` in `carcara-old/carcara/` to confirm parameter names and semantics.
- **Do not**: edit, delete, move, or import from `carcara-old/`. Do not run its modules. Do not rebuild against its code.
- **Do**: extract metadata, inspect inputs/outputs, and port logic into the new layered architecture under `carcara/crc_modules/` + `grasshopper/components/`.
- **Decoded reference layer — `carcara-old/ghuser-metadata/`**: all 33 legacy `.ghuser` files have been decoded. The artifacts live here and are the preferred starting point for any component rebuild:
  - `01.Modeling.md`, `02.Queries.md`, `03.Utilities.md`, `04.Dataviz.md` — per-subcategory capture docs: component tables, input/output hook params, general logic descriptions, and links to decoded scripts.
  - `scripts/` — 51 canonical decoded source files. Naming conventions: `<Name>.py` (per-component script), `<Name>_interface.txt` (cluster hook params + internal component list for the 19 cluster-based components), `CRC_<Name>.py` (hand-captured wiring reconstruction for the 9 query components), and shared engine scripts (`RunODBCQuery.py`, `SQLComposer.py`, `GrasshopperGeometryToWKT.py`, etc.) deduped to one canonical copy each. `CurveDisplay` is C#.
  - **Before rebuilding a component**: read the matching capture `.md` entry and linked decoded script first. Do not attempt to re-decode the binary `.ghuser` unless verification is needed.
- **Inspecting a legacy `.ghuser` directly**: it is a **binary `GH_Archive`**, not a zip — do not try to unzip it. Three options: open it inside Grasshopper (drag onto the canvas after installing into `UserObjects/`), decode it via `GH_IO.dll`, or — preferred for agentic work — decode it with plain CPython (raw-deflate inflate + base64 script extraction; handles both script components and clusters). Full recipe: [`specs/ghuser-decoding.md`](specs/ghuser-decoding.md).

***

## Rebuild Mandate: Every Legacy `.ghuser` Must Be Reimplemented

Every `.ghuser` file present in `carcara-old/carcara/` must be rebuilt under the new architecture before the rebuild is considered complete. No legacy `.ghuser` is shipped as-is.

### Process per component

1. Identify the legacy file in `carcara-old/carcara/carcara_<Name>_*.ghuser`.
2. Locate the matching row in the [Component Inventory](#component-inventory) below.
3. Implement the domain logic in the correct `carcara/crc_modules/` submodule.
4. Write tests in `tests/` (mock all DB calls).
5. Create the component bundle at `grasshopper/components/CRC_<Name>/` with `metadata.json`, `code.py`, and `icon.png` following the [Grasshopper Component Pattern](#grasshopper-component-pattern).
6. Run `python build_userobjects.py` to regenerate the `.ghuser` into `carcara/userobjects/`.
7. Flip the inventory status from ⬜ Todo to ✅ Done in the commit.

### Completion criteria

- Every legacy `.ghuser` listed in the inventory has a ✅ Done row.
- `carcara/userobjects/` contains the freshly built equivalent for every entry.
- No file under `carcara-old/` is referenced from runtime code.

***

## Core Library API Contracts

Every public function in `crc_modules/` must follow these rules:

- **No side effects on import**: no connections opened, no files written at import time.
- **Explicit parameters**: no global state, no config files read implicitly. All connection parameters passed explicitly to every function.
- **Return tuples for multi-value results**: `(result, message)` or `(rows, columns)` — never dictionaries for primary returns.
- **Raise exceptions on failure**: do not return `None` silently. The GH component layer handles exceptions and routes them to the `report` output.

### Connection model: `CString` + `CToggle` on the wire

Carcara uses the **legacy connection model**: `CRC_ConnectionString` builds a single
**connection string (`CString`)** that carries the (encoded) password, and every DB
component takes `CString` plus a `CToggle` boolean trigger as inputs. `CString` travels
on a canvas wire between components. Build, encode/decode, and test logic is pure
(no Rhino) and lives in `db/connection.py` so it is pytest-testable.

> Security note: `CString` embeds the password (encoded, **not** encrypted — obfuscation
> only). It must never be committed: `.gitignore` excludes `*.gh` and `*.py` test scripts.
> This is a deliberate revert to the legacy ergonomics over the sticky/DSN model.

### `crc_modules/db/connection.py`

```python
def build_connection_string(host: str, port: int, database: str,
                            user: str, password: str) -> str:
    """Returns a single CString (libpq conninfo) with the password encoded."""

def parse_connection_string(cstring: str) -> dict:
    """Returns a dict of psycopg2 connection kwargs (decodes the password)."""

def test_connection(cstring: str) -> tuple[bool, str]:
    """Returns (True, 'Connection successful') or (False, error_message)."""
```

### `crc_modules/db/query.py`

```python
def run_query(cstring: str, sql: str) -> tuple[list, list]:
    """
    Execute a SELECT statement.
    Returns (rows, columns) where:
      rows    : list of tuples
      columns : list of column name strings
    Raises psycopg2.Error on failure.
    """

def run_command(cstring: str, sql: str) -> int:
    """
    Execute a non-SELECT statement (INSERT, UPDATE, CREATE, etc.).
    Returns number of affected rows.
    Raises psycopg2.Error on failure.
    """
```

The `CToggle` boolean is handled at the GH component layer (`if CToggle:`), never inside
`crc_modules`. The high-level query components (QueryValues, QueryTableNames, …) build
their SQL by substituting placeholders via `utils/sql_composer.py` — port the legacy SQL
templates (schema/table/column listing, PK detection, ORDER BY, spatial filters) verbatim
into the matching `crc_modules` functions.

### `crc_modules/db/spatial_query.py`

> **Naming note.** Two distinct concepts share the `cx`/`cy` letters in the legacy code:
> - `x_col` / `y_col` — the **names of the coordinate columns** in the table, injected into
>   `ST_MakePoint("x_col", "y_col")`. (Legacy called these `_cx`/`_cy`.)
> - `Cx` / `Cy` — the **coordinate-correction false origin** (see
>   [Coordinate Correction](#coordinate-correction-projected-coordinates--false-origin)),
>   numeric **text**, applied via `ST_Translate` and **never parsed to float**.
>
> Keep them separate in the API.

```python
def get_geometries(cstring: str, schema: str, table: str,
                   cx: str = "0", cy: str = "0",
                   where: str = None, srid: int = 4326) -> tuple[list, list]:
    """
    Returns (wkt_geometries, primary_keys).
    Auto-detects geometry column (from geometry_columns view) and primary key.
    Builds ST_AsText(ST_Translate(<geom_expr>, -Cx, -Cy)) ordered by PK so geometries
    and keys stay parallel. If no PK exists, returns NULL for pk.
    Cx/Cy are numeric TEXT (the false origin) embedded verbatim into the SQL — never float()-parsed.
    Output is a DataTree: each geometry (including multipart members) on same branch as its PK.
    """

def get_geometries_with_spatial_filter(cstring: str, schema: str, table: str,
                                       filter_wkt: str,
                                       cx: str = "0", cy: str = "0",
                                       srid: int = 4326,
                                       sql_filter: str = None) -> tuple[list, list]:
    """
    SELECT geometries translated to local (-Cx, -Cy), filtered by a GH-drawn
    boundary that is itself translated to the projected CRS (+Cx, +Cy) inside
    the WHERE:
        ST_Intersects(<db_geom>, ST_Translate(ST_GeomFromText(filter_wkt, srid), Cx, Cy))
        AND (sql_filter)
    Auto-detects geometry column and PK. Returns DataTree with parallel wkt and pk branches.
    """

def get_values_with_spatial_filter(cstring: str, schema: str, table: str,
                                   columns: list[str],
                                   filter_wkt: str,
                                   cx: str = "0", cy: str = "0",
                                   srid: int = 4326,
                                   sql_filter: str = None) -> tuple[list, list]:
    """
    SELECT attribute columns for rows matching spatial filter.
    Same spatial filter logic as get_geometries_with_spatial_filter.
    Returns (rows, column_names) as DataTree by column.
    """
```

### `crc_modules/geometry/wkt.py`

```python
def wkt_to_shapely(wkt: str):
    """Returns a shapely geometry object."""

def shapely_to_wkt(geom) -> str:
    """Returns a WKT string."""

def wkt_list_to_points(wkt_list: list) -> list:
    """Returns list of (x, y) tuples from a list of WKT Point strings."""
```

***

## Coordinate Correction (projected coordinates / false origin)

Carcara works with **projected geographic coordinates** (UTM, SIRGAS 2000 / national grids).
Their absolute values are huge (eastings ~500 000, northings ~9 500 000). Rhino and
Grasshopper store coordinates as floats and **lose precision** at that magnitude — geometry
jitters, snapping fails, booleans break. This is unavoidable in RhinoCommon, so Carcara never
lets full-magnitude coordinates reach Rhino.

The fix is a **false origin**: a correction point `(Cx, Cy)` near the study area. Geometry
crossing the DB boundary is shifted so the study area sits near the Rhino origin:

- **Read (DB → Rhino):** subtract the correction — `local = projected − (Cx, Cy)`.
- **Write (Rhino → DB):** add it back — `projected = local + (Cx, Cy)`.

### The translation happens in SQL, never in Python/Rhino

`Cx` and `Cy` are passed as **text** and injected into the SQL as numeric literals. They are
**never** parsed to `float` in Python or RhinoCommon. That is the whole point: the big-number
arithmetic runs inside PostGIS at full numeric precision, and only the already-small *local*
result is ever materialized in Rhino.

> **Hard rule:** never `float(Cx)` / `float(Cy)`. Treat them as opaque numeric text. Validate
> they match a numeric literal (regex) so they stay injection-safe, then embed them verbatim
> into the SQL via the SQL composer.

Read path (geometry SELECT) — translate to local:
```sql
ST_AsText(ST_Translate(<geom_expr>, -Cx, -Cy))
```
Write path (geometry INSERT / shapefile export) — translate back to projected:
```sql
ST_Translate(ST_GeomFromText('<local_wkt>', SRID), Cx, Cy)
```
Spatial filter (a GH-drawn boundary, already local, used in a WHERE) — push it to projected:
```sql
ST_Intersects(<db_geom>, ST_Translate(ST_GeomFromText('<local_wkt>', SRID), Cx, Cy))
```

### WKT⇄GH conversions stay correction-free

`CRC_WKTtoGrasshopperGeometry` and `CRC_GrasshopperGeometryToWKT` do **not** apply correction.
By the time WKT reaches the converter it is already local (the SELECT subtracted Cx/Cy); by the
time GH geometry is converted to WKT it is still local (the INSERT adds Cx/Cy). Correction lives
in exactly one layer — the SQL — so the conversion layer never double-shifts.

### Shared helpers — `crc_modules/utils/correction.py`

```python
def validate_offset(value: str) -> str:
    """Return value unchanged if it is a numeric literal (kept as TEXT, never float()).
    Raise ValueError otherwise. Keeps Cx/Cy injection-safe. '0' = no shift."""

def translate_expr(geom_sql: str, cx: str, cy: str, direction: str) -> str:
    """Wrap a SQL geometry expression in ST_Translate.
       direction='to_local'     -> ST_Translate(<geom_sql>, -cx, -cy)   (read)
       direction='to_projected' -> ST_Translate(<geom_sql>,  cx,  cy)   (write / filter)
    cx, cy are numeric-validated text, embedded verbatim — never parsed to float."""
```

These are pure string/SQL helpers (no DB, no Rhino) → fully pytest-testable.

### Where it applies

Every component that reads or writes geometry across the DB boundary exposes `Cx` + `Cy`
**text** inputs (default `"0"` = no shift), all in **02.Queries**: the three spatial reads —
`GeometryEntities`, `GeometriesWithSpatialFilter`, `ValuesWithSpatialFilter` (subtract) — and the
geometry write `CRC_CreateShapefile` (add). The `CRC_FindCorrectionParameters` utility
(03.Utilities, `utils/correction.py`) finds a feature by `Column` = `Value` (both optional —
if neither is given it takes the table's first row), auto-detects the geometry column,
computes the geometry centroid, and returns the centroid coordinates as **text** `(Cx, Cy)` —
it does NOT take x_col/y_col.

Pure-GH modeling (**01.Modeling**) and **04.Dataviz** components do **not** correct — they
operate on whatever (already-local) geometry they are handed.

***

## Grasshopper Component Pattern

Every component is a **folder** under `grasshopper/components/<CRC_Name>/` containing exactly three files:

```
CRC_RunQuery/
├── metadata.json   ← Component name, category, params, type hints
├── code.py         ← The script body the GHPython component will run
└── icon.png        ← 24×24 PNG (toolbar icon)
```

This layout is dictated by the upstream componentizer (`compas-actions.ghpython_components`) used by Ladybug Tools, COMPAS, and now Carcara. The full schema, CLI, and rationale live in [`specs/componentizer.md`](specs/componentizer.md).

> **SDK / advanced-mode components.** Components that draw a custom Rhino-viewport preview
> (`DrawViewportWires` / `DrawViewportMeshes` / `get_ClippingBox`) are built differently: set
> `ghpython.isAdvancedMode: true`, write `code.py` as an `executingcomponent` subclass, and use
> the shared `crc_modules/rhino/preview.py` (`PreviewPayload`) helper. `build_userobjects.py`
> routes these through `componentize_py_sdk.py` (new Script-component schema), not the procedural
> builder. Full pattern, gotchas (e.g. `import System`, non-empty clipping box), and checklist:
> [`specs/sdk-components.md`](specs/sdk-components.md).

### `metadata.json` (required)

Minimum viable shape:

```json
{
  "name": "RunQuery",
  "nickname": "RQ",
  "category": "Carcara",
  "subcategory": "03.Utilities",
  "description": "Runs a raw SQL SELECT against a PostGIS database and returns rows and column names.",
  "exposure": 2,
  "ghpython": {
    "isAdvancedMode": false,
    "marshalGuids": true,
    "iconDisplay": 0,
    "inputParameters": [
      { "name": "CString",  "description": "Connection string with encoded password", "typeHintID": "str",  "scriptParamAccess": "item" },
      { "name": "CToggle",  "description": "Set True to execute",                     "typeHintID": "bool", "scriptParamAccess": "item" },
      { "name": "sql",      "description": "SQL SELECT",                              "typeHintID": "str",  "scriptParamAccess": "item" }
    ],
    "outputParameters": [
      { "name": "rows",    "description": "Returned rows" },
      { "name": "columns", "description": "Column names" },
      { "name": "report",  "description": "Status message" }
    ]
  }
}
```

Defaults applied by the componentizer: `optional=true` (inputs), `scriptParamAccess="item"`, `typeHintID="ghdoc"`. Override only when needed.

### `code.py` (required)

Plain Python source that runs as the component's `RunScript` body. Pattern:

```python
import sys
import os

# Make the crc_modules package importable from a Grasshopper Python 3 component.
# GHPython runs this code from an in-memory string, so __file__ is undefined.
# The installer copies the whole deployable folder to:
#   %APPDATA%\Grasshopper\UserObjects\carcara\   (Windows)
# with the package at .../carcara/crc_modules. Put the PARENT (.../carcara) on
# sys.path so `import crc_modules` resolves.
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

from crc_modules.db.query import run_query

rows, columns, report = [], [], "Set 'CToggle' to True to execute"

if CToggle:
    try:
        _rows, columns = run_query(CString, sql)
        rows = [str(r) for r in _rows]
        report = f"OK – {len(rows)} rows returned"
    except Exception as e:
        report = f"ERROR: {e}"
```

The componentizer supports three template tokens substituted at build time: `{{version}}`, `{{name}}`, `{{ghuser_name}}`. Use them in headers/comments if you want the printed build to reflect the release version.

### `icon.png` (required)

24×24 PNG, transparent background preferred. If missing, the build will fail.

### Rules for component bundles

- **Never** import `Rhino`, `rhinoscriptsyntax`, or `Grasshopper` in `code.py`. If RhinoCommon geometry conversion is needed, isolate it in a dedicated `carcara/crc_modules/rhino/` submodule that is clearly marked as Rhino-dependent.
- **Never** put business logic in `code.py`. If more than ~5 lines of non-plumbing code, it belongs in `crc_modules/`.
- **Always** include a `report` output that surfaces both success and error states.
- **Always** guard execution behind the `CToggle` boolean input to prevent accidental execution on canvas load.
- **Always** coerce input types explicitly: `N = int(N) if N else None`.
- **`subcategory` lives in `metadata.json` only.** Do not nest component folders by subcategory on disk — the source tree is flat.

### Credential handling (CString model)

Carcara uses the **legacy connection-string model**. `CRC_ConnectionString` collects host /
port / database / user / password and produces a single **`CString`** (a libpq conninfo
string with the password encoded) via `crc_modules.db.connection.build_connection_string()`.
`CString` is the component's output and travels on a canvas wire into every downstream DB
component, alongside a `CToggle` boolean trigger.

Each DB component decodes `CString` with `parse_connection_string()` (pure, pytest-tested)
and opens a psycopg2 connection per run. There is no `scriptcontext.sticky`, no DSN handle,
and no Rhino-side credential store — the credential travels on the wire as the legacy plugin
did.

> Security tradeoff (accepted): the encoded password lives inside `CString`, so it can appear
> on the canvas and would be serialized into a saved `.gh`. Encoding is obfuscation, **not**
> encryption. Mitigation: `.gitignore` excludes `*.gh` and test scripts; never commit a `.gh`
> that contains a live `CString`. If stronger isolation is needed later, reintroduce a
> sticky-backed handle — but the default, per project decision, is the CString wire.

***

## Build Pipeline

`.ghuser` files are **binary `GH_Archive` artifacts** produced by the componentizer. They are never written by hand, never zipped manually, and never committed to git.

### Toolchain

| Tool | Purpose |
|---|---|
| `componentize_cpy.py` | Upstream script from `compas-dev/compas-actions.ghpython_components` that writes binary `.ghuser` files via `GH_IO.dll` |
| `GH_IO.dll` | Grasshopper's serialization assembly. Bundled with Rhino 8 or fetched from NuGet. |
| `pythonnet` (`clr`) | Bridges CPython 3.11+ to `GH_IO.dll` |
| `build_userobjects.py` | Thin local wrapper that invokes the componentizer with our paths |

### Build script: `build_userobjects.py`

The wrapper must:

1. Ensure `pythonnet` is importable (else error with install instructions).
2. Locate `GH_IO.dll` — search Rhino 8 install paths first, then fall back to NuGet fetch.
3. Locate `componentize_cpy.py` (vendored in `vendor/componentizer/` or fetched at build time).
4. Invoke it with `source=grasshopper/components`, `target=carcara/userobjects`, `--ghio <path>`, `--version <from pyproject.toml>`.
5. Surface any per-component failures without aborting the whole build.

Full details, install matrix, troubleshooting, and CI snippets are in [`specs/componentizer.md`](specs/componentizer.md).

### Running the build

```powershell
conda run -n carcara python build_userobjects.py
```

Run from the repository root. Output: `carcara/userobjects/*.ghuser` (committed).

> **Environment note:** On Windows PowerShell, the `python` command resolves to the Windows Store stub unless the conda `carcara` environment is activated. Always prefix with `conda run -n carcara` (or use the full interpreter path). See [`specs/python-execution.md`](specs/python-execution.md) for details.

Installing is **one** copy: the whole deployable `carcara/` folder → the
UserObjects folder. It carries the `crc_modules` package, the built
`userobjects/*.ghuser`, and `version.txt` together. `deploy.ps1` does this for
dev; end users get it via the GitHub installer (`grasshopper/installer/`).

- **Windows**: `%APPDATA%\Grasshopper\UserObjects\carcara\`
- **macOS**: `~/Library/Application Support/McNeel/Rhinoceros/8.0/Plug-ins/Grasshopper/UserObjects/carcara/`

Components put `…/UserObjects/carcara` on `sys.path` and `import crc_modules`.
Copying only the `.ghuser` gives `No module named 'crc_modules'` — ship the
whole folder.

```powershell
conda run -n carcara python make_release.py    # build + stamp version.txt
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

DB components also need `psycopg2` available to Rhino's Python; their `code.py` carries a `# r: psycopg2` directive so Rhino installs it on first run.

***

## Dependencies

### Runtime (required by end users)

```
psycopg2>=2.9
shapely>=2.0
svgwrite>=1.4
matplotlib>=3.7
```

### Development only

```
python-dotenv
pytest
pythonnet>=3.0    # required by build_userobjects.py to call GH_IO.dll
requests          # optional: NuGet fallback fetch of GH_IO.dll
```

### `requirements.txt`

```
psycopg2>=2.9
shapely>=2.0
svgwrite>=1.4
matplotlib>=3.7
python-dotenv
pytest
pythonnet>=3.0
requests
```

All dependencies must be installable via pip into the Rhino 8 CPython environment. Verify with:

```powershell
conda run -n carcara python -c "import psycopg2, shapely, svgwrite, matplotlib; print('OK')"
```

***

## Testing

All tests live in `tests/` and run with standard pytest. Tests must not require a running database — use mocking for DB calls.

```bash
conda run -n carcara pytest tests/ -v
```

Run from the repository root.

> **Environment note:** On Windows PowerShell, the `python` command resolves to the Windows Store stub unless the conda `carcara` environment is activated. Always prefix with `conda run -n carcara` (or use the full interpreter path). See [`specs/python-execution.md`](specs/python-execution.md) for details.

### Test file naming

- `test_connection.py` — tests `carcara/crc_modules/db/connection.py`
- `test_query.py` — tests `carcara/crc_modules/db/query.py`
- `test_wkt.py` — tests `carcara/crc_modules/geometry/wkt.py`
- `test_svg.py` — tests `carcara/crc_modules/svg/export.py`

### Test pattern

```python
from unittest.mock import patch, MagicMock
from crc_modules.db.connection import test_connection

def test_connection_success():
    with patch("crc_modules.db.connection.psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        ok, msg = test_connection("host=localhost port=5432 dbname=db user=user password=pw")
        assert ok is True
        assert msg == "Connection successful"

def test_connection_failure():
    with patch("crc_modules.db.connection.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = Exception("Connection refused")
        ok, msg = test_connection("host=localhost port=5432 dbname=db user=user password=pw")
        assert ok is False
        assert "Connection refused" in msg
```

***

## Git and Version Control

### `.gitignore` must include

```
.env
dist/
__pycache__/
*.pyc
*.ghuser
test_*.py        # test scripts with real credentials
*.gh             # Grasshopper definition files with embedded credentials
```

### Branching strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, tested code only |
| `dev` | Active development |
| `feature/component-name` | Individual component development |

### Commit message convention

```
feat(db): add spatial_query module with bbox filter
fix(svg): handle empty polyline input in export.py
test(wkt): add round-trip WKT conversion tests
build: update build_userobjects.py XML escaping
```

***

## Component Inventory

All 33 components in one master map. Each maps to one bundle in `grasshopper/components/CRC_<Name>/`
and one or more functions in `crc_modules/`. The `Legacy file` column points to the original
`.ghuser` in `carcara-old/carcara/` that must be reimplemented.

The `subcategory` field in each `metadata.json` must be one of exactly: **`01.Modeling`**,
**`02.Queries`**, **`03.Utilities`**, **`04.Dataviz`**. **Exposure** controls toolbar placement
using the GH_IO enum: `2` = primary (dropdown front), `4` = secondary, `8` = tertiary,
`16` = quaternary/obscure. Values marked `?` are
not yet recovered — **read them from the legacy `.ghuser` before building** and fill in.

### Master component map (grouped by subcategory)

Within each subcategory, ordered by exposure (`1` first). Global `#` runs across all four.

#### 01.Modeling (6)

| # | Component | Exp | Core module | Legacy file | Status |
|---|---|---|---|---|---|
| 1 | CRC_BuildingMeshes | 2 | `rhino/building_mesh.py` | `carcara_BuildingMeshes_r03.ghuser` | ✅ Done |
| 2 | CRC_IdentifyDuplicatePolylines | 2 | `geometry/duplicates.py` | `carcara_IdentifyDuplicatePolylines_r03.ghuser` | ✅ Done |
| 3 | CRC_OffsetPython | 2 | `rhino/offset.py` | `carcara_OffsetPython_r03.ghuser` | ✅ Done |
| 4 | CRC_PointInsidePolygon | 2 | `geometry/polylabel.py` | `carcara_PointInsidePolygon_rev03.ghuser` | ✅ Done |
| 5 | CRC_SortByContainer | 2 | `geometry/containment.py` | `carcara_SortByContainer_rev03.ghuser` | ✅ Done |
| 6 | CRC_ColorCalculator* | 4 | `utils/color.py` (SDK) | `carcara_ColorCalculator_r00.ghuser` | ✅ Done |

#### 02.Queries (9)

| # | Component | Exp | Core module | Legacy file | Status |
|---|---|---|---|---|---|
| 7 | CRC_QuerySchemaNames | 2 | `db/query.py` | `carcara_QuerySchemaNames_r03.ghuser` | ✅ Done |
| 8 | CRC_QueryTableNames | 2 | `db/query.py` | `carcara_QueryTableNames_rev03.ghuser` | ✅ Done |
| 9 | CRC_QueryColumnNames | 2 | `db/query.py` | `carcara_QueryColumnNames_rev03.ghuser` | ✅ Done |
| 10 | CRC_QueryValues | 2 | `db/query.py` + `db/spatial_query.py` | `carcara_QueryValues_rev03.ghuser` | ✅ Done |
| 11 | CRC_GeometryEntities | 4 | `db/spatial_query.py` | `carcara_GeometryEntities_r03.ghuser` | ✅ Done |
| 12 | CRC_GeometriesWithSpatialFilter | 4 | `db/spatial_query.py` + `db/connection.py` | `carcara_GeometriesWithSpatialFilter_r03.ghuser` | ✅ Done |
| 13 | CRC_ValuesWithSpatialFilter | 4 | `db/spatial_query.py` + `db/connection.py` | `carcara_ValuesWithSpatialFilter_rev03.ghuser` | ✅ Done |
| 14 | CRC_CreateTable | 8 | `db/writer.py` | `carcara_CreateTable_r03.ghuser` | ✅ Done |
| 15 | CRC_CreateShapefile | 8 | `db/writer.py` | `carcara_CreateShapefile_r03.ghuser` | ✅ Done |

#### 03.Utilities (7)

| # | Component | Exp | Core module | Legacy file | Status |
|---|---|---|---|---|---|
| 16 | CRC_ConnectionString | 2 | `db/connection.py` | `carcara_ConnectionString_r03.ghuser` | ✅ Done |
| 17 | CRC_FindCorrectionParameters | 2 | `utils/correction.py` | `carcara_FindCorrectionParameters_r03.ghuser` | ✅ Done |
| 18 | CRC_SQLComposer | 4 | `utils/sql_composer.py` | `carcara_SQLComposer_rev02.ghuser` | ✅ Done |
| 19 | CRC_RunQuery | 4 | `db/query.py` | `carcara_RunODBCQuery_rev03.ghuser` | ✅ Done |
| 20 | CRC_RunCommand | 4 | `db/query.py` | `carcara_RunODBCCommand_rev01.ghuser` | ✅ Done |
| 21 | CRC_GrasshopperGeometryToWKT | 8 | `geometry/wkt.py` | `carcara_GrasshopperGeometryToWKT_r02.ghuser` | ✅ Done |
| 22 | CRC_WKTtoGrasshopperGeometry | 8 | `geometry/wkt.py` | `carcara_WKTtoGrasshopperGeometry_r02.ghuser` | ✅ Done |

#### 04.Dataviz (10)

| # | Component | Exp | Core module | Legacy file | Status |
|---|---|---|---|---|---|
| 24 | CRC_CurveDisplay | 2 | `rhino/curve_display.py` (SDK) | `carcara_CurveDisplay_r02.ghuser` | ✅ Done |
| 25 | CRC_PolylineToSVG* | 4 | `svg/export.py` (`rhino/preview.py`) | `carcara_PolylineToSVG_r03.ghuser` | ✅ Done |
| 26 | CRC_CircleToSVG* | 4 | `svg/export.py` (`rhino/preview.py`) | `carcara_CircletoSVG_r03.ghuser` | ✅ Done |
| 27 | CRC_NurbsToSVG* | 4 | `svg/export.py` (`rhino/preview.py`) | `carcara_NurbsToSVG_rev03.ghuser` | ✅ Done |
| 28 | CRC_TextToSVG* | 4 | `svg/export.py` (`rhino/preview.py`) | `carcara_TextToSVG_rev03.ghuser` | ✅ Done |
| 29 | CRC_Histogram* | 8 | `viz/histogram.py` (`rhino/preview.py`) | `carcara_Histogram_r01.ghuser` | ✅ Done |
| 30 | CRC_ScatterPlot* | 8 | `viz/scatter.py` (`rhino/preview.py`) | `carcara_ScatterPlot_r03.ghuser` | ✅ Done |
| 31 | CRC_LinePlot* | 8 | `viz/lineplot.py` (`rhino/preview.py`) | `carcara_LinePlot_r00.ghuser` | ✅ Done |
| 32 | CRC_Heatmap* | 8 | `viz/heatmap.py` (`rhino/preview.py`) | `carcara_Heatmap_rev00.ghuser` | ✅ Done |
| 33 | CRC_SaveSVG | 16 | `svg/save.py` | `carcara_SaveSVG_r03.ghuser` | ✅ Done |

Counts: **01.Modeling 6 · 02.Queries 9 · 03.Utilities 7 · 04.Dataviz 10 = 32.**

> **Note:** `CRC_SRID` (legacy `carcara_SRID_r00.ghuser`) is a native GH ValueList component — not a Python script component. It will be created manually and is not part of the componentizer build pipeline.

> Exposure values are sourced from the legacy `.ghuser` (captured per subcategory in
> `carcara-old/ghuser-metadata/`; decoded scripts and `_interface.txt` hook files are linked
> from those docs). Confirm any that are still uncertain when porting.

### Subcategory notes

- **01.Modeling** — modeling tasks for urban models. Rhino-heavy: keep pure algorithm (on
  coordinate tuples) in `crc_modules/geometry/`; isolate unavoidable RhinoCommon (mesh build,
  curve offset, containment) in `crc_modules/rhino/`. **`CRC_OffsetPython` and `CRC_BuildingMeshes`
  are fully Rhino-dependent — their core logic lives in `crc_modules/rhino/`.**
- **02.Queries** — DBMS comms, read + write, geometry + alphanumeric. Every component takes
  `CString` + `CToggle`. Geometry-returning queries live here (DB ops that return geometry),
  including the geometry write `CRC_CreateShapefile` (which INSERTs geometries with Cx/Cy correction).
- **03.Utilities** — helpers used alongside 02.Queries: the connection-string builder
  (`CRC_ConnectionString`, which *produces* the `CString`), the generic query/command
  runners (`CRC_RunQuery`, `CRC_RunCommand`), the SQL composer (free-form substring replace),
  geometry⇄WKT conversion, and the coordinate-correction false origin tools.
-   **04.Dataviz** — data visualizations rendered on screen (SDK-mode viewport preview) and exportable as SVG. All ten components use SDK mode (`CRC_CurveDisplay` for display-only curves; `CRC_ColorCalculator`; five SVG exporters: `CRC_PolylineToSVG`, `CRC_CircleToSVG`, `CRC_NurbsToSVG`, `CRC_TextToSVG`; and four chart renderers: `CRC_Histogram`, `CRC_ScatterPlot`, `CRC_LinePlot`, `CRC_Heatmap`). Charts combine Rhino geometry in the viewport via `PreviewPayload` with SVG file export via matplotlib. Only `CRC_SaveSVG` is procedural. Full SDK component inventory and gotchas: [`specs/sdk-components.md`](specs/sdk-components.md).

> **Engine / reuse pattern (from legacy).** `CRC_RunQuery` / `CRC_RunCommand` (03.Utilities)
> are the generic primitives — reimplement as thin GH wrappers over `run_query` / `run_command`.
> Every higher-level query component builds its SQL by placeholder substitution
> (`CRC_SQLComposer` → `utils/sql_composer.py`) and runs it through the same engine — port the
> legacy SQL templates verbatim into the matching `crc_modules` functions.
> **`CRC_QueryValues` is NOT a raw-SQL runner** (that is `CRC_RunQuery`): it takes
> `CString, CToggle, schema, table, column, N` where `N` is a **string** that replaces NULL
> values in the returned column (legacy input "Null Itens"), builds its SELECT internally,
> and outputs the column's values + report.

> **Coordinate correction.** The three geometry **reads** (`CRC_GeometryEntities`,
> `CRC_GeometriesWithSpatialFilter`, `CRC_ValuesWithSpatialFilter`) take `Cx` + `Cy` **text**
> inputs and **subtract** the false origin in SQL via `utils/correction.py`; the geometry **write**
> `CRC_CreateShapefile` **adds** it back. `CRC_FindCorrectionParameters` (03.Utilities) finds a
> feature by `Column` = `Value` (both optional — omitted: first row of the table), auto-detects
> the geometry column, computes its centroid, and returns the centroid coordinates as **text**
> `(Cx, Cy)` — it does NOT take x_col/y_col. Module `utils/correction.py`. Never `float()` Cx/Cy.
> See [Coordinate Correction](#coordinate-correction-projected-coordinates--false-origin).

> **Geometry column detection.** Spatial query components auto-detect the geometry column
> (PostGIS `geometry_columns` view) instead of requiring hardcoded names. Helper in
> `utils/correction.py` or `db/spatial_query.py`.

> **Module vs subcategory are independent.** `CRC_ConnectionString` and the `CRC_Run*` pair
> live in `db/` but sit in 03.Utilities; `CRC_SQLComposer` lives in `utils/` and sits in
> 03.Utilities; `CRC_ColorCalculator` lives in `utils/color.py` but sits in 01.Modeling and
> uses SDK mode. `CRC_CurveDisplay` is Python SDK-mode (was C# in the legacy) and sits in
> 04.Dataviz. Set `subcategory` from this table, not from the module path.

> **SDK-mode components.** Nine of the ten data-viz components (all except `CRC_SaveSVG`) plus CRC_ColorCalculator (10 total) use SDK mode: they draw a custom Rhino viewport preview via `PreviewPayload`. The five SVG exporters also emit files via matplotlib; the remaining four chart renderers and ColorCalculator are preview-only. Full inventory and gotchas: [`specs/sdk-components.md`](specs/sdk-components.md).

### Inventory cross-check

The rebuild is **complete only when every legacy `.ghuser` in `carcara-old/carcara/` appears in one of the tables above with status ✅ Done**. If you discover a legacy file not listed here, add a row before starting work — do not silently skip a component.

***

## Rules for Agentic Code Generation

When generating code for this repository, an AI agent must:

1. **Read this spec before writing any code.** Do not infer structure from the existing files alone.
2. **Write core logic in `crc_modules/` first**, then write the GH component wrapper. Never the reverse.
3. **Check the component inventory table** before creating a new file. Update the status column when a component is completed.
4. **Never add Rhino or Grasshopper imports** to any file under `crc_modules/`. If geometry conversion requires RhinoCommon, create `carcara/crc_modules/rhino/` and document it as a Rhino-dependent submodule.
5. **Always include `report` output** in every GH component. The `report` string must distinguish between "not yet run", "success", and "error" states.
6. **Always guard execution with `if CToggle:`** in every GH component.
7. **Write a corresponding test** in `tests/` for every new function added to `crc_modules/`. Mock all database calls.
8. **Do not modify `pyproject.toml`** unless adding a new dependency, and document why in the commit message.
9. **Do not create `.ghuser` files manually.** They are always generated by `build_userobjects.py` (which wraps the `compas-actions.ghpython_components` componentizer and `GH_IO.dll`). A `.ghuser` is a **binary `GH_Archive`**, not a zip — never hand-craft one.
10. **Match the commit message convention** defined in the Git section above.
11. **Treat `carcara-old/` as read-only legacy.** Never import from it, never edit it, never delete it. Use it only to recover original behavior, inputs, outputs, and nicknames when rebuilding a component.
12. **Rebuild every legacy `.ghuser`.** The end state of this project is that every file currently in `carcara-old/carcara/*.ghuser` has been reimplemented under `grasshopper/components/` and regenerated into `carcara/userobjects/` via `build_userobjects.py`. No legacy `.ghuser` ships as-is.
13. **Paths are repo-root relative.** There is no `carcara-rebuild/` directory anymore. All commands (`pytest`, `python build_userobjects.py`, `pip install -e .`) run from the repository root.
14. **Component layout is the componentizer bundle layout.** Each component is `grasshopper/components/CRC_<Name>/{metadata.json, code.py, icon.png}`. Flat, no subcategory subdirs. Subcategory is a metadata field. See [`specs/componentizer.md`](specs/componentizer.md) for the full schema and rationale.
15. **Never `float()` the `Cx`/`Cy` correction values.** They are numeric **text**, applied as a false-origin shift **inside SQL** (`ST_Translate`), to avoid the precision loss that motivates the whole correction system. Validate them as numeric literals via `utils/correction.py`, then embed verbatim. See [Coordinate Correction](#coordinate-correction-projected-coordinates--false-origin).