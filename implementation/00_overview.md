# C# Migration — Phase 00: Overview & Target Architecture

## Goal

Port the Carcara Grasshopper plugin from Python script components (`.ghuser` +
`crc_modules`) to **C# script components** packaged as `.ghuser` via the existing
`vendor/componentizer/componentize_cs.py` pipeline — exactly the same delivery model
as the already-working `CRC_CurveDisplay`. Shared C# logic lives in a single source
tree (`grasshopper/csharp_shared/`) and is concatenated into each component's script
at build time; no compiled DLL and no `.gha` at this stage.

Compiling a `.gha` Grasshopper assembly is an explicit **future phase** (Phase 12).
It is not the goal of Phases 01–11.

---

## Why C# (now, as script components)

| Factor | Python (.ghuser + crc_modules) | C# script (.ghuser, this phase) | C# compiled (.gha, future) |
|---|---|---|---|
| Deployment | Folder copy + pip install | Same folder-copy model; no pip | Single .gha + bundled DLLs |
| DB driver | psycopg2 (pip) | Npgsql via `#r "nuget:"` | Npgsql bundled in .gha |
| Viewport preview | Broken for IGH_PreviewObject | Works (proven in CurveDisplay) | Full compiled preview |
| Type safety | Runtime | Roslyn compile-on-load | Compile-time (dotnet build) |
| Unit tests | pytest (crc_modules) | Python suite is the oracle | .NET xUnit (future) |
| Edit loop | Edit code.py, reload | Edit code.cs, rebuild ghuser | dotnet build + Rhino restart |

What is gained now:
- Single-language components (DB, geometry, and viewport preview all in C#).
- Npgsql replaces psycopg2 — no per-machine pip install for end users.
- `IGH_PreviewObject` works correctly (Python GH_ScriptInstance cannot forward it).
- `#r "nuget:"` directives let Rhino 8 auto-resolve NuGet deps per component.

Tradeoff accepted at this phase:
- No compiled .NET unit tests — the Python `crc_modules` pytest suite is the
  behavioral oracle. Port C# to match; run pytest to verify correctness.
- `#r "nuget:"` must be validated in Rhino 8 before porting all components (see
  Phase 01 early-validation step).

---

## Resolved Decisions

These were open in the previous plan and are now settled. Do not reopen them.

### 1. Geometry library
**NetTopologySuite (NTS)**, pulled per-component via
`#r "nuget: NetTopologySuite, <ver>"` in each C# script that needs geometry
operations. No compiled DLL reference; Rhino resolves it at script-compile time.

### 2. Chart rendering
**No raster/chart library.** Charts output:
- **Rhino geometry** (lines, rectangles, text objects) drawn on the Grasshopper
  canvas — mirrors the Python `crc_modules/viz/` matplotlib output in terms of
  what the user sees.
- **Hand-rolled SVG strings** using `System.Xml.Linq` — same element structure
  as the Python `svgwrite` output.
Drop SkiaSharp and ScottPlot entirely; they are not referenced anywhere in the plan.

### 3. .NET target framework
Not relevant during the script-component phase. Rhino 8 compiles each C# script in
its own runtime; no `<TargetFramework>` setting is needed. **`net7.0` is noted as the
target for the future `.gha` only** (Phase 12).

### 4. SDK references
Rhino 8 automatically provides RhinoCommon and Grasshopper to C# script components —
no project file, no NuGet reference needed for those. Third-party dependencies
(Npgsql, NTS) come via `#r "nuget: <pkg>, <ver>"` directives **embedded at the top
of each component's C# source**. The future `.gha` would instead use the McNeel NuGet
SDK packages.

### 5. Keep Python crc_modules
The Python `crc_modules` library and `grasshopper/components/*/code.py` script
bundles **remain in the repo for the entire migration** as the behavioral spec and
test oracle. Remove Python artifacts only as a final future step (Phase 12 / future
.gha phase), not now.

### 6. Delivery model
**C# script components** packaged as `.ghuser` via `vendor/componentizer/componentize_cs.py`
(exactly like the working `CRC_CurveDisplay`). The compiled **`.gha` is future work,
not part of Phases 01–11.**

---

## Target Architecture

### Shared C# source

```
grasshopper/
  csharp_shared/              ← Shared C# domain logic (one file per domain area).
  │                             Built into every component that needs it via prelude concat.
  │                             No Rhino/GH imports except where clearly marked.
  │  Db.cs                    ← Port of carcara/crc_modules/db/ (connection, query, spatial, writer)
  │  Geometry.cs              ← Port of carcara/crc_modules/geometry/ (WKT, polylabel, containment, duplicates)
  │  RhinoGeometry.cs         ← Port of carcara/crc_modules/rhino/ (WKT↔Rhino; RhinoCommon-dependent)
  │  Svg.cs                   ← Port of carcara/crc_modules/svg/ (export, save)
  │  Viz.cs                   ← Port of carcara/crc_modules/viz/ (histogram, scatter, lineplot, heatmap)
  │  Utils.cs                 ← Port of carcara/crc_modules/utils/ (color, sql_composer, correction)
  │
  components/                 ← One folder per component (unchanged bundle layout).
    CRC_ConnectionString/
      metadata.json           ← instanceGuid must match existing value
      code.cs                 ← Thin script body; #r nuget directives at top + shared helpers injected at build
      icon.png
    CRC_CurveDisplay/         ← Already done; is the template for all others.
      ...
    ...
```

### Build pipeline

`vendor/componentizer/componentize_cs.py` is extended (Phase 01) so that, for each
C# component bundle, it:

1. Reads the `#r "nuget: ..."` directives declared in `code.cs` (or in a per-component
   `nuget.txt` sidecar — TBD in Phase 01).
2. Concatenates the **shared prelude .cs files** declared by the component (list in
   `metadata.json` under a new `"csharp_shared"` key, e.g.
   `["Db.cs", "Utils.cs"]`).
3. Appends the component's own `code.cs` body.
4. BASE64-encodes the concatenated source and embeds it in the `.ghuser` archive,
   exactly as `componentize_cs.py` does today for `CRC_CurveDisplay`.

Result: each `.ghuser` is self-contained (shared logic is inlined); shared logic lives
in one source location and is not duplicated by hand; no compiled DLL and no `.gha`.

`build_userobjects.py` is updated to route:
- Bundles with `code.cs` → `componentize_cs.py` (extended).
- Bundles with `code.py` → `componentize_cpy.py` (unchanged).

### Component bundles

Each component bundle stays `grasshopper/components/CRC_<Name>/` with:
- `metadata.json` — `instanceGuid` ported verbatim from the existing Python
  `metadata.json` so canvas definitions reconnect automatically.
- `code.cs` — thin `GH_ScriptInstance` body; `#r "nuget: ..."` directives at top;
  calls shared helper methods (which are concatenated in by the build).
- `icon.png` — reuse existing drawn icons.

### Coordinate correction

Unchanged: `Cx`/`Cy` remain text, embedded verbatim into SQL `ST_Translate` calls
via `Utils.cs` (`ValidateOffset` / `TranslateExpr`). Never `double.Parse(Cx)`.
See CLAUDE.md → Coordinate Correction.

---

## Behavioral spec: Python crc_modules

The Python `crc_modules` library is **not removed** during this migration. It serves as:
- The authoritative behavioral spec for every C# port.
- The test oracle: run `conda run -n carcara pytest tests/ -v` to confirm that the
  C# components produce the same results.

A compiled .NET unit-test project is deferred to the `.gha` phase (Phase 12).
During Phases 01–11, validation is:
1. Python pytest suite — confirm logic parity.
2. Manual Rhino canvas validation per component (checkpoints listed in each phase).

---

## Migration Order (phase sequence)

```
00  Overview (this file)
01  Toolchain — extend componentize_cs.py; early-validation "hello DB" component
02  csharp_shared/Db.cs — Npgsql port of all db/* modules
03  csharp_shared/Geometry.cs — NTS port of geometry/*
04  csharp_shared/RhinoGeometry.cs — RhinoCommon port of rhino/*
05  csharp_shared/Svg.cs — SVG export/save
06  csharp_shared/Viz.cs — chart rendering (Rhino geometry + hand-rolled SVG)
07  csharp_shared/Utils.cs — color, sql_composer, correction
08  C# script components — 02.Queries (9 components)
09  C# script components — 01.Modeling (6 components)
10  C# script components — 03.Utilities (7 components)
11  C# script components — 04.Dataviz (10 components; CurveDisplay is already done)
12  FUTURE: compile to Carcara.gha (deferred; see Phase 12)
```

---

## Component Inventory Mapping

The same 32 scripted components (+ 1 native ValueList SRID) from the Python rebuild.
For C#, each maps to a `GH_ScriptInstance` bundle under `grasshopper/components/CRC_<Name>/`.

#### 01.Modeling (6)

| # | Component | Exp | Shared C# source | Python spec |
|---|---|---|---|---|
| 1 | CRC_BuildingMeshes | 1 | `RhinoGeometry.cs` | `crc_modules/rhino/building_mesh.py` |
| 2 | CRC_IdentifyDuplicatePolylines | 1 | `Geometry.cs` | `crc_modules/geometry/duplicates.py` |
| 3 | CRC_OffsetPython | 1 | `RhinoGeometry.cs` | `crc_modules/rhino/offset.py` |
| 4 | CRC_PointInsidePolygon | 1 | `Geometry.cs` | `crc_modules/geometry/polylabel.py` |
| 5 | CRC_SortByContainer | 1 | `Geometry.cs` | `crc_modules/geometry/containment.py` |
| 6 | CRC_ColorCalculator | 2 | `Utils.cs` | `crc_modules/utils/color.py` |

#### 02.Queries (9)

| # | Component | Exp | Shared C# source | Python spec |
|---|---|---|---|---|
| 7 | CRC_QuerySchemaNames | 1 | `Db.cs` | `crc_modules/db/query.py` |
| 8 | CRC_QueryTableNames | 1 | `Db.cs` | `crc_modules/db/query.py` |
| 9 | CRC_QueryColumnNames | 1 | `Db.cs` | `crc_modules/db/query.py` |
| 10 | CRC_QueryValues | 1 | `Db.cs` | `crc_modules/db/query.py` |
| 11 | CRC_GeometryEntities | 2 | `Db.cs`, `Utils.cs` | `crc_modules/db/spatial_query.py` |
| 12 | CRC_GeometriesWithSpatialFilter | 2 | `Db.cs`, `Utils.cs` | `crc_modules/db/spatial_query.py` |
| 13 | CRC_ValuesWithSpatialFilter | 2 | `Db.cs`, `Utils.cs` | `crc_modules/db/spatial_query.py` |
| 14 | CRC_CreateTable | 3 | `Db.cs` | `crc_modules/db/writer.py` |
| 15 | CRC_CreateShapefile | 3 | `Db.cs`, `Utils.cs` | `crc_modules/db/writer.py` |

#### 03.Utilities (7)

| # | Component | Exp | Shared C# source | Python spec |
|---|---|---|---|---|
| 16 | CRC_ConnectionString | 1 | `Db.cs` | `crc_modules/db/connection.py` |
| 17 | CRC_FindCorrectionParameters | 1 | `Db.cs`, `Utils.cs` | `crc_modules/utils/correction.py` |
| 18 | CRC_SQLComposer | 2 | `Utils.cs` | `crc_modules/utils/sql_composer.py` |
| 19 | CRC_RunQuery | 2 | `Db.cs` | `crc_modules/db/query.py` |
| 20 | CRC_RunCommand | 2 | `Db.cs` | `crc_modules/db/query.py` |
| 21 | CRC_GrasshopperGeometryToWKT | 3 | `RhinoGeometry.cs` | `crc_modules/geometry/wkt.py` |
| 22 | CRC_WKTtoGrasshopperGeometry | 3 | `RhinoGeometry.cs` | `crc_modules/geometry/wkt.py` |

#### 04.Dataviz (10)

| # | Component | Exp | Shared C# source | Python spec |
|---|---|---|---|---|
| 24 | CRC_CurveDisplay | 2 | *(already done; template)* | `grasshopper/components/CRC_CurveDisplay/code.cs` |
| 25 | CRC_PolylineToSVG | 2 | `Svg.cs` | `crc_modules/svg/export.py` |
| 26 | CRC_CircleToSVG | 2 | `Svg.cs` | `crc_modules/svg/export.py` |
| 27 | CRC_NurbsToSVG | 2 | `Svg.cs` | `crc_modules/svg/export.py` |
| 28 | CRC_TextToSVG | 2 | `Svg.cs` | `crc_modules/svg/export.py` |
| 29 | CRC_Histogram | 3 | `Viz.cs` | `crc_modules/viz/histogram.py` |
| 30 | CRC_ScatterPlot | 3 | `Viz.cs` | `crc_modules/viz/scatter.py` |
| 31 | CRC_LinePlot | 3 | `Viz.cs` | `crc_modules/viz/lineplot.py` |
| 32 | CRC_Heatmap | 3 | `Viz.cs` | `crc_modules/viz/heatmap.py` |
| 33 | CRC_SaveSVG | 4 | `Svg.cs` | `crc_modules/svg/save.py` |

---

## Future Phase: Compiled .gha

Phase 12 is deferred work — do not start it during Phases 01–11. When the C# script
components are all validated, Phase 12 will:
- Create a `src/` .NET solution (Carcara.Core + Carcara.GH + Carcara.Tests).
- Refactor `grasshopper/csharp_shared/*.cs` into `Carcara.Core` class library.
- Wrap them in `GH_Component` subclasses in `Carcara.GH`.
- Add a .NET xUnit test project targeting `Carcara.Core`.
- Bundle Npgsql/NTS as DLLs; package as `.yak`.
- Remove Python artifacts in one clean commit.

---

## Done when

- [ ] This overview reviewed and all resolved decisions understood.
- [ ] Phase 01 started with `componentize_cs.py` generalization and early-validation
      "hello DB" component confirmed working in Rhino 8.
