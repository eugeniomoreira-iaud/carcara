# Carcara — C# Migration Plan

This folder contains the implementation plan for migrating the Carcara Grasshopper
plugin from Python script components (`.ghuser` + `crc_modules`) to **C# script
components**, packaged as `.ghuser` via `vendor/componentizer/componentize_cs.py` —
exactly the same delivery model as the already-working `CRC_CurveDisplay`.

The completed Python rebuild plans are archived in `_archive/python-rebuild/`.

---

## One principle

**Prove the C# script-component pipeline (including `#r "nuget: Npgsql"`) with one
trivial DB component in Rhino 8 first, then port subsystem by subsystem. Compiling
a `.gha` is an explicit future phase (Phase 12) — not the goal of Phases 01–11.**

---

## Reading order

| # | File | Topic | Rhino/canvas test? |
|---|---|---|---|
| 00 | `00_overview.md` | Strategy, architecture, resolved decisions, component inventory | no |
| 01 | `01_dotnet_toolchain.md` | Extend componentize_cs.py; `CRC_HelloDB` early-validation gate | **YES (gate)** |
| 02 | `02_core_db_npgsql.md` | `csharp_shared/Db.cs` — Npgsql port of connection/query/spatial/writer | canvas smoke |
| 03 | `03_core_geometry.md` | `csharp_shared/Geometry.cs` — NTS port of WKT, polylabel, containment, duplicates | canvas smoke |
| 04 | `04_core_rhino_geometry.md` | `csharp_shared/RhinoGeometry.cs` — RhinoCommon offset, building mesh, WKT↔Rhino | **YES** |
| 05 | `05_core_svg.md` | `csharp_shared/Svg.cs` — SVG export and save | canvas smoke |
| 06 | `06_core_viz.md` | `csharp_shared/Viz.cs` — chart rendering (Rhino geometry + hand-rolled SVG) | canvas smoke |
| 07 | `07_core_utils.md` | `csharp_shared/Utils.cs` — Correction, SqlComposer, ColorUtils | canvas smoke |
| 08 | `08_components_queries.md` | C# script components — 9 components in 02.Queries | **YES** |
| 09 | `09_components_modeling.md` | C# script components — 6 components in 01.Modeling | **YES** |
| 10 | `10_components_utilities.md` | C# script components — 7 components in 03.Utilities | **YES** |
| 11 | `11_components_dataviz.md` | C# script components — 10 components in 04.Dataviz | **YES** |
| 12 | `12_gha_packaging_release.md` | **FUTURE**: compile to Carcara.gha — deferred | deferred |

Each file follows the shape:
**Goal → Depends-on → Scope → Steps → Validation → Done when.**

---

## Conventions

- **Python `crc_modules` is the behavioral oracle, not the runtime.** Every C# port
  reads the matching Python file and replicates its logic and SQL templates verbatim.
  Run `conda run -n carcara pytest tests/ -v` throughout to confirm parity.
- **Port `instanceGuid` verbatim.** Every `code.cs` component must carry the same
  `instanceGuid` as the existing Python `metadata.json` so canvas definitions saved
  with the Python script components reconnect automatically.
- **Coordinate correction stays SQL-side.** `Cx`/`Cy` are text, embedded verbatim in
  `ST_Translate` SQL via `Correction.ValidateOffset` / `Correction.TranslateExpr`.
  Never `double.Parse(Cx)`. See `CLAUDE.md → Coordinate Correction`.
- **Shared logic lives once.** `grasshopper/csharp_shared/*.cs` is the C# analog of
  `crc_modules/`. The `componentize_cs.py` build concatenates the listed shared files
  into each component's script before embedding. No duplication by hand.
- **`#r "nuget:"` directives.** Third-party deps (Npgsql, NTS) are declared in the
  component's `code.cs` or shared prelude. The build step deduplicates and hoists them
  to the top of the concatenated script. Rhino 8 resolves them at script-compile time.
- **Python artifacts stay until Phase 12.** `crc_modules`, `code.py` files, and the
  Python pytest suite remain in the repo through Phases 01–11 as the behavioral spec
  and test oracle. Remove them only in the future `.gha` phase.
- **`carcara-old/` remains read-only.** Never edit or import from it; use it only to
  confirm legacy behavior.
- **`.gha` is future work.** Do not create a `.NET solution`, `.csproj` files, or a
  `GH_Component` subclass during Phases 01–11. That is Phase 12.

---

## Archive

`_archive/python-rebuild/` contains the completed Python rebuild plans (phases 00–12)
that produced the `crc_modules` library and `.ghuser` script components. They are kept
as historical reference and as the behavioral record for what is being ported to C#.
