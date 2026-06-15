# C# Migration — Phase 01: C# Script-Component Toolchain

## Goal

Generalize `vendor/componentizer/componentize_cs.py` to build **all** C# component
bundles (not just `CRC_CurveDisplay`), adding:
- Shared-prelude concatenation (inline `grasshopper/csharp_shared/*.cs` into each component).
- `#r "nuget: ..."` directive passthrough (prepended verbatim before the concatenated source).

Update `build_userobjects.py` to route C# bundles through the extended `componentize_cs.py`
and Python bundles through `componentize_cpy.py` as before.

**Critical early-validation gate**: before porting any real component, build and load a
trivial "hello DB" C# script component that opens a Npgsql connection via
`#r "nuget: Npgsql"` — and prove it works inside a componentized `.ghuser` in Rhino 8.
This de-risks the entire migration. Do not proceed to Phase 02 until this passes.

## Depends on

- Phase 00 resolved decisions understood.
- `vendor/componentizer/componentize_cs.py` existing (already present — it builds CurveDisplay).
- Rhino 8 installed on the validation machine.

---

## Scope

### 1. Extend `componentize_cs.py` — prelude concat + nuget directives

Current state: `componentize_cs.py` builds only `CRC_CurveDisplay`, with
`_CONVERTER_DATA` hard-coded for that component's four inputs.

Changes required:

**a. Generalize input-parameter handling.**
`_CONVERTER_DATA` is specific to CurveDisplay. Replace with a generic lookup or per-bundle
declaration. Options:
- Drive `ConverterData` from `metadata.json` (add an optional `"converterData"` dict per input parameter).
- Fall back to a type-hint-based default map for common types (str → `System.String`,
  int → `System.Int32`, bool → `System.Boolean`, curve → `Rhino.Geometry.Curve`, etc.).

**b. Shared prelude concatenation.**
Add a `"csharp_shared"` array to `metadata.json` listing which files from
`grasshopper/csharp_shared/` are needed, e.g.:
```json
"csharp_shared": ["Db.cs", "Utils.cs"]
```
Before BASE64-encoding the script, `componentize_cs.py` reads each listed file from
`grasshopper/csharp_shared/`, concatenates them in order, then appends `code.cs`.
The result is a single self-contained C# script embedded in the `.ghuser`.

**c. `#r "nuget:"` directive passthrough.**
Nuget directives must appear at the **very top** of the script (before any `using`
statements). Strategy:
1. Strip all `#r "nuget: ..."` lines from each shared prelude and from `code.cs`.
2. Collect them, deduplicate, sort (deterministic order).
3. Prepend them to the concatenated source before BASE64-encoding.

This ensures that even if two shared files both declare `#r "nuget: Npgsql, 8.*"`,
the output script has exactly one copy at the top.

**d. Public entry point.**
Add a new public function alongside the existing `create_curvedisplay_cs_ghuser`:
```python
def create_cs_ghuser(source: str, target: str,
                     shared_dir: str,
                     version: str | None = None,
                     prefix: str | None = None) -> None:
    """Build any C# script component .ghuser.
    source     = path to the CRC_<Name>/ bundle directory.
    target     = destination .ghuser file path.
    shared_dir = path to grasshopper/csharp_shared/.
    """
```
`create_curvedisplay_cs_ghuser` can remain as a wrapper calling `create_cs_ghuser`
(or be retired when CurveDisplay is rebuilt with the new path — for now keep it).

### 2. Update `build_userobjects.py`

Routing logic:
```python
for bundle_dir in component_bundles:
    has_cs = os.path.isfile(os.path.join(bundle_dir, "code.cs"))
    has_py = os.path.isfile(os.path.join(bundle_dir, "code.py"))
    if has_cs:
        create_cs_ghuser(bundle_dir, target, shared_dir=CSHARP_SHARED_DIR, ...)
    elif has_py:
        componentize_cpy(bundle_dir, target, ...)
    else:
        print(f"WARNING: no code.cs or code.py in {bundle_dir}, skipping")
```

During migration, most bundles still have `code.py`. Only bundles that have been
converted to `code.cs` use the new path. The two builders coexist.

### 3. Create `grasshopper/csharp_shared/` directory

Create the directory (empty at this phase; populated in Phases 02–07):
```
grasshopper/csharp_shared/
  Db.cs         ← Phase 02
  Geometry.cs   ← Phase 03
  RhinoGeometry.cs  ← Phase 04
  Svg.cs        ← Phase 05
  Viz.cs        ← Phase 06
  Utils.cs      ← Phase 07
```

Each file is a standalone C# partial namespace (no `using` at file top — those go in
`code.cs` or are hoisted as `#r` / `using` in the concatenation step). Design TBD in
Phase 02 when the first file is written; establish the convention then.

### 4. Early-validation component: `CRC_HelloDB`

**This is the most important deliverable of Phase 01.** Build a throwaway C# script
component — name `HelloDB`, subcategory `Debug` — that:
- Declares `#r "nuget: Npgsql, 8.*"` (or latest stable).
- Has inputs `CString` (str) and `CToggle` (bool).
- On `CToggle = true`: parses `CString` as a Npgsql connection string, opens a
  connection, runs `SELECT 1`, closes it, outputs `report = "Npgsql OK"`.
- On failure: outputs `report = "ERROR: <message>"`.

This component does **not** use any shared prelude — its `code.cs` is entirely
self-contained so that the test is minimal:

```csharp
#r "nuget: Npgsql, 8.*"

using System;
using Npgsql;

// Inputs: CString (string), CToggle (bool)
// Outputs: report (string)

report = "Set CToggle to True";
if (CToggle)
{
    try
    {
        using var conn = new NpgsqlConnection(CString);
        conn.Open();
        using var cmd = new NpgsqlCommand("SELECT 1", conn);
        cmd.ExecuteScalar();
        report = "Npgsql OK – connection verified";
    }
    catch (Exception ex)
    {
        report = "ERROR: " + ex.Message;
    }
}
```

Place the bundle at `grasshopper/components/CRC_HelloDB/` with `metadata.json` (assign
a fresh GUID — this component is temporary), `code.cs`, and a placeholder `icon.png`
(copy any existing icon).

Build: `conda run -n carcara python build_userobjects.py`.
Load `CRC_HelloDB.ghuser` in Rhino 8 → Grasshopper → drop on canvas → wire
`CRC_ConnectionString` output + Boolean Toggle (true) → panel on `report` must read
`"Npgsql OK – connection verified"`.

**The owner must confirm this test passes before Phases 02–11 proceed.** If `#r "nuget:"`
does not resolve inside a `.ghuser`-loaded C# script, the whole architecture needs
revision.

---

## Steps

1. **Extend `componentize_cs.py`**: implement `create_cs_ghuser` with prelude concat
   and `#r` deduplication (see Scope section above). Keep `create_curvedisplay_cs_ghuser`
   working (regression check: rebuild CurveDisplay with the new path and confirm it
   still loads).

2. **Update `build_userobjects.py`**: add the routing logic; define `CSHARP_SHARED_DIR`
   pointing to `grasshopper/csharp_shared/`.

3. **Create `grasshopper/csharp_shared/`** (empty directory; add a `.gitkeep`).

4. **Write `CRC_HelloDB` bundle**: `metadata.json`, `code.cs`, `icon.png`.

5. **Build**: `conda run -n carcara python build_userobjects.py`. Confirm:
   - `CRC_CurveDisplay.ghuser` still builds correctly (regression).
   - `CRC_HelloDB.ghuser` is produced.

6. **Load-test in Rhino 8**: install `CRC_HelloDB.ghuser` → confirm `#r "nuget: Npgsql"`
   resolves and the connection test passes.

7. **Owner sign-off**: record the result in a comment or commit message before
   proceeding to Phase 02.

---

## Tests / Validation

There is no .NET test project at this phase. Validation is:

```powershell
# Build all .ghuser files
conda run -n carcara python build_userobjects.py

# Confirm CurveDisplay still works (regression)
Test-Path "carcara\userobjects\CRC_CurveDisplay.ghuser"

# Confirm HelloDB was built
Test-Path "carcara\userobjects\CRC_HelloDB.ghuser"
```

Functional validation: owner loads `CRC_HelloDB.ghuser` in Rhino 8 and reports
`"Npgsql OK"` with a live PostGIS connection. This is the gate for Phase 02.

Python pytest suite is not affected by this phase — run it as a sanity check:
```powershell
conda run -n carcara pytest tests/ -v
```

---

## Done when

- [ ] `componentize_cs.py` extended with `create_cs_ghuser` (prelude concat + `#r` dedup).
- [ ] `build_userobjects.py` routes C# bundles through `componentize_cs.py`.
- [ ] `grasshopper/csharp_shared/` directory created.
- [ ] `CRC_HelloDB` bundle written and builds to `.ghuser`.
- [ ] `CRC_CurveDisplay.ghuser` still builds without regression.
- [ ] **Owner confirms `CRC_HelloDB` loads in Rhino 8 and `#r "nuget: Npgsql"` resolves.**
- [ ] Python pytest suite still passes (no regressions in crc_modules).
