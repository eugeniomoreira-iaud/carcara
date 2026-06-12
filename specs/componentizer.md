# Componentizer Build Pipeline

Authoritative reference for how Carcara turns Python source into binary `.ghuser` files. Read this before editing `build_userobjects.py`, before adding a component bundle, and before changing CI for releases.

---

## 1. What problem this solves

A Grasshopper user object (`.ghuser`) is **not** a zip + XML. It is a binary `GH_Archive` written by Grasshopper's `GH_IO.dll`. The `GH_Archive` is a nested-dictionary tree (the same format as `.gh` files) serialized via `GH_Archive.Serialize_Binary()`. Hand-crafting one by zipping XML produces a file Grasshopper refuses to load.

That means our build needs **one specific .NET assembly** at build time: `GH_IO.dll`. It does **not** need Rhino or Grasshopper to be running.

The Ladybug Tools / COMPAS ecosystem solved this years ago with a small Python tool called the **componentizer**. We adopt it as-is rather than rewrite the binary serializer.

---

## 2. Toolchain

| Component | Role | Where it lives |
|---|---|---|
| `compas-actions.ghpython_components` | Upstream componentizer scripts | GitHub (vendored at `vendor/componentizer/`) |
| `componentize_cpy.py` | The CPython-3 variant we use (Rhino 8) | `vendor/componentizer/componentize_cpy.py` |
| `GH_IO.dll` | Grasshopper's serialization assembly | Bundled with Rhino 8, or auto-fetched from NuGet |
| `pythonnet` (`clr`) | CPython ↔ .NET bridge so we can call `GH_IO.dll` from Python 3.11+ | `pip install pythonnet>=3.0` |
| `build_userobjects.py` | Carcara-specific thin wrapper | repo root |

Important: there is also an IronPython variant (`componentize_ipy.py`) for Rhino 7. **We do not use it.** Carcara targets Rhino 8 / CPython only.

---

## 3. Input layout

The componentizer expects this directory structure:

```
grasshopper/components/
├── CRC_ConnectionString/
│   ├── metadata.json
│   ├── code.py
│   └── icon.png
├── CRC_QueryValues/
│   ├── metadata.json
│   ├── code.py
│   └── icon.png
└── …
```

Rules:

- The folder name becomes the `.ghuser` filename (with optional `--prefix` and `--version` appended).
- All three files are mandatory. Missing one → that bundle is skipped.
- **Flat layout.** No subcategory subdirectories. Subcategory is a field inside `metadata.json`.
- Folder names should match the convention `CRC_<PascalCase>` to keep Carcara's `CRC_` prefix consistent with the spec.

---

## 4. `metadata.json` schema

This is the full schema accepted by `componentize_cpy.py`. Fields marked `*` are required.

```jsonc
{
  "name":         "QueryValues",          // *required. Component display name.
  "nickname":     "QV",                   // *required. 1–5 char abbrev shown on the canvas.
  "category":     "Carcara",              // *required. Toolbar tab.
  "subcategory":  "Database",             // *required. Panel inside the tab.
  "description":  "Runs a SQL query…",    //  optional, default "".
  "exposure":     2,                      //  optional, default 2.
                                          //  Valid: -1 hidden, 2 primary, 4, 8, 16, 32, 64, 128.
  "instanceGuid": "…GUID…",               //  optional. Auto-generated if missing.
                                          //  Once shipped, KEEP IT STABLE between releases
                                          //  so upgrades don't break user definitions.
  "ghpython": {
    "isAdvancedMode": false,              //  optional, default false.
    "marshalGuids":   true,               //  optional, default true.
    "iconDisplay":    0,                  //  optional, default 0 (icon).
    "inputParameters": [
      {
        "name":              "host",      // *required.
        "nickname":          "host",      //  optional, defaults to name.
        "description":       "DB host",   //  optional.
        "optional":          true,        //  optional, default true.
        "allowTreeAccess":   true,        //  optional, default true.
        "showTypeHints":     true,        //  optional, default true.
        "scriptParamAccess": "item",      //  optional, default "item". Also: "list", "tree".
        "sourceCount":       0,           //  optional, default 0.
        "typeHintID":        "str",       //  optional, default "ghdoc". See §5 for valid values.
        "wireDisplay":       "default",   //  optional. Also: "faint", "hidden".
        "reverse":           false,       //  optional.
        "simplify":          false,       //  optional.
        "flatten":           false,       //  optional.
        "graft":             false        //  optional.
      }
    ],
    "outputParameters": [
      {
        "name":        "rows",            // *required.
        "nickname":    "rows",            //  optional.
        "description": "Returned rows",   //  optional.
        "optional":    false,             //  optional, default false on outputs.
        "sourceCount": 0,
        "reverse":     false,
        "simplify":    false,
        "flatten":     false,
        "graft":       false
      }
    ]
  }
}
```

### `instanceGuid` — read this before shipping

If you omit `instanceGuid`, the componentizer generates a new one every build. That means **every release reshuffles GUIDs**, which breaks any Grasshopper definition that already wires the previous version of the component.

**Policy for Carcara**: as soon as a component is shipped, freeze its `instanceGuid` in `metadata.json`. Treat it as a public identity, not a build artifact.

---

## 5. Valid `typeHintID` values

The componentizer maps these string aliases to GHPython's internal GUIDs:

`none`, `ghdoc`, `float`, `bool`, `int`, `complex`, `str`, `datetime`, `guid`, `color`, `point`, `vector`, `plane`, `interval`, `uvinterval`, `box`, `transform`, `line`, `circle`, `arc`, `polyline`, `rectangle`, `curve`, `mesh`, `surface`, `subd`, `brep`, `pointcloud`, `geometrybase`

Defaults:

- DB connection params (host, user, etc.) → `"str"`
- Port numbers → `"int"`
- Run triggers → `"bool"`
- WKT strings flowing into Grasshopper geometry components → `"str"` (convert via shapely in `code.py`)
- Anything passed straight through from canvas → `"ghdoc"` (Grasshopper figures it out)

---

## 6. `code.py` rules

- Pure Python source. Runs as the GHPython component's body when the canvas user triggers it.
- Inputs and outputs map by **name** to whatever `metadata.json` declared. No glue code needed.
- No imports of `Rhino`, `Grasshopper`, or `rhinoscriptsyntax`. If RhinoCommon is required, isolate it in a `crc_modules/rhino/` submodule and import only from there.
- Always include a `report` string output. Always guard execution behind a `run: bool` input.
- The componentizer substitutes three tokens at build time:
  - `{{version}}` → `--version` CLI value
  - `{{name}}` → `metadata.json` "name"
  - `{{ghuser_name}}` → output filename without extension
- Coerce input types defensively at the top of the function body (e.g. `port = int(port) if port else 5432`). Type hints in `metadata.json` are a UI hint, not a guarantee.

Minimal template:

```python
import sys
import os

# GHPython has no __file__; the installer copies the deployable folder to
# .../UserObjects/carcara (package at .../carcara/crc_modules). Put the parent
# on sys.path so `import crc_modules` resolves.
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

rows, columns, report = [], [], "Set 'run' to True to execute"

if run:
    try:
        port = int(port) if port else 5432
        _rows, columns = run_query(host, port, database, user, password, sql)
        rows = [str(r) for r in _rows]
        report = f"OK – {len(rows)} rows returned"
    except Exception as e:
        report = f"ERROR: {e}"
```

---

## 7. `icon.png`

- 24×24 pixels. PNG with transparent background preferred.
- Path inside the bundle is fixed: `<CRC_Name>/icon.png`.
- A missing icon causes the build to skip the bundle.

A bare-minimum placeholder icon during development is fine. Replace before release.

---

## 8. Build host requirements

Per the upstream README:

| Target Rhino | Python | Componentizer script | DLL |
|---|---|---|---|
| Rhino 7 (IronPython) | IronPython 2.7.8.1 + NuGet | `componentize_ipy.py` | `GH_IO.dll` from Rhino 7 |
| Rhino 8 (CPython) | Python 3.9+ with `pythonnet` | `componentize_cpy.py` | `GH_IO.dll` from Rhino 8 |
| Rhino 8 (IronPython v2) | IronPython 2.7.8.1 | `componentize_ipy_v2.py` | `GH_IO.dll` |

**Carcara uses row 2 only.** Rhino does not have to be installed on the build machine — the componentizer will fetch `GH_IO.dll` from NuGet if it cannot find one locally. But fetching adds a network call to every build, so on dev machines we point at the local Rhino install for speed.

### `GH_IO.dll` search order

`build_userobjects.py` looks in this order:

1. `--ghio <path>` CLI flag, if supplied.
2. `C:\Program Files\Rhino 8\Plug-ins\Grasshopper\`
3. `C:\Program Files\Rhino 8 WIP\Plug-ins\Grasshopper\`
4. `%APPDATA%\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\` (user-installed Rhino)
5. Fall back: let the componentizer download from NuGet into a temp directory.

---

## 9. Running the build

### Local dev (Windows, Rhino 8 installed)

```powershell
# one-time
pip install pythonnet>=3.0 requests

# every build
python build_userobjects.py
```

Outputs go to `carcara/userobjects/` (committed; shipped to users).

### With a version tag

```powershell
python build_userobjects.py --version 1.0.0
```

### Clean rebuild

```powershell
python build_userobjects.py --clean
```

### Explicit DLL path

```powershell
python build_userobjects.py --ghio "C:\Program Files\Rhino 8\Plug-ins\Grasshopper"
```

### CI (GitHub Actions sketch)

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
- run: pip install pythonnet>=3.0 requests
- run: python build_userobjects.py --version ${{ github.ref_name }}
- uses: actions/upload-artifact@v4
  with:
    name: carcara-ghuser
    path: carcara/userobjects/*.ghuser
```

No Rhino install is required in CI — `GH_IO.dll` is pulled from NuGet by the componentizer the first time. Cache `vendor/componentizer/` and (optionally) the downloaded `GH_IO.dll` between runs.

---

## 10. Installing the built `.ghuser` files

Installing is **one** copy: the whole deployable `carcara/` folder → the
UserObjects folder. It carries the `crc_modules` package, the built
`userobjects/*.ghuser`, and `version.txt` together. `deploy.ps1` does it for dev;
end users get it via the GitHub installer (`grasshopper/installer/`). GHPython has
no `__file__`, so each `code.py` puts `…/UserObjects/carcara` on `sys.path` and
imports `crc_modules`.

Deployed layout:

```
%APPDATA%\Grasshopper\UserObjects\carcara\
├── crc_modules\            ← package; sys.path points at the PARENT (…\carcara)
├── userobjects\*.ghuser    ← Grasshopper scans UserObjects recursively, so these load
└── version.txt
```

UserObjects folders:

- **Windows**: `%APPDATA%\Grasshopper\UserObjects\carcara\`
- **macOS**: `~/Library/Application Support/McNeel/Rhinoceros/8.0/Plug-ins/Grasshopper/UserObjects/carcara/`

> Copying only the `.ghuser` yields `No module named 'crc_modules'`. Ship the
> whole `carcara/` folder so the package is on Rhino's Python path.

Third-party deps (e.g. `psycopg2` for DB components) must also be importable by
Rhino's Python. They are installed once by `grasshopper/installer/install_python_libs.py`
(run before the components are used).

Restart Grasshopper (or reload the user objects via the GH menu) and the components appear in the **Carcara** tab.

---

## 11. Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `ImportError: No module named 'clr'` when running build | `pythonnet` not installed | `pip install pythonnet>=3.0` |
| `Could not load file or assembly 'GH_IO'` | DLL not on disk and NuGet fetch blocked | Pass `--ghio` pointing at a folder that contains `GH_IO.dll` |
| Built `.ghuser` opens with all params blank | `metadata.json` typo in param names, or `inputParameters` missing/empty | Validate `metadata.json` against §4; check `name` fields |
| Same component appears twice in toolbar after upgrade | `instanceGuid` changed between releases | Freeze `instanceGuid` per §4 — never let it regenerate after first ship |
| Componentizer skips a bundle silently | Missing `metadata.json`, `code.py`, or `icon.png` | `build_userobjects.py` prints `SKIP <name>: missing [...]` — supply the missing file |
| `code.py` runs in Rhino but fails to import `crc_modules` | the `carcara/` folder isn't in UserObjects, or the `sys.path` bootstrap doesn't resolve | Run `install_carcara.py` (or `deploy.ps1`); confirm `…\UserObjects\carcara\crc_modules` exists |

---

## 12. Reference links

- Componentizer upstream: <https://github.com/compas-dev/compas-actions.ghpython_components>
- `componentize_cpy.py` raw source: <https://raw.githubusercontent.com/compas-dev/compas-actions.ghpython_components/main/componentize_cpy.py>
- Ladybug Tools `.ghuser` example repo: <https://github.com/ladybug-tools/ladybug-grasshopper>
- Grasshopper file-format wiki (binary `GH_Archive`): <https://wiki.mcneel.com/labs/grasshopper_fileformat>
- `GH_Archive.Serialize_Binary` API: <https://developer.rhino3d.com/api/grasshopper/html/M_GH_IO_Serialization_GH_Archive_Serialize_Binary.htm>
- Finding `GH_IO.dll` on a Rhino install: <https://james-ramsden.com/grasshopper-where-is-grasshopper-dll-and-gh_io-dll/>
- pythonnet docs: <https://pythonnet.github.io/>
