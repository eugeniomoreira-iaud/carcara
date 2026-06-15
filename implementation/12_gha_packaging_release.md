# C# Migration — Phase 12 (FUTURE): Compile to Carcara.gha

## Status: DEFERRED — not part of Phases 01–11

This phase is explicit future work. Do not begin it until all 32 C# script components
(Phases 08–11) are validated on the Grasshopper canvas and the Python pytest suite
continues to pass.

---

## Goal

Refactor the C# script-component delivery (Phases 01–11) into a compiled
**Carcara.gha** Grasshopper assembly. This eliminates the per-script Roslyn compile
and enables .NET unit tests, a `.yak` package, and CI via GitHub Actions.

---

## Depends on

- Phases 01–11 complete: all 32 C# script components (`.ghuser`) validated on canvas.
- All Python crc_modules pytest tests still passing.
- Owner sign-off that the C# script-component phase is complete.

---

## What changes vs the script-component phase

| Aspect | Script components (Phases 01–11) | Compiled .gha (this phase) |
|---|---|---|
| Build output | `.ghuser` files via componentize_cs.py | `Carcara.gha` via `dotnet build` |
| Shared logic | `csharp_shared/*.cs` concatenated at build | Compiled into `Carcara.Core.dll` |
| GH component | `GH_ScriptInstance` in `.ghuser` | `GH_Component` subclass in `Carcara.GH.dll` |
| NuGet deps | `#r "nuget:"` directives, resolved per-script | DLLs bundled alongside `Carcara.gha` |
| .NET tests | Python pytest is the oracle | `dotnet test` (xUnit, `Carcara.Tests`) |
| .NET target | Rhino 8 runtime (irrelevant) | `net7.0` (confirm Rhino 8 CoreCLR) |
| Deployment | Folder copy to UserObjects | Copy `Libraries\Carcara\` folder |

---

## Scope

### 1. Solution structure

```
src/
  Carcara.Core/           ← Refactor grasshopper/csharp_shared/*.cs here.
  │                         No Rhino/GH references (except in Carcara.Core/rhino/).
  │  db/                  ← from Db.cs
  │  geometry/            ← from Geometry.cs
  │  rhino/               ← from RhinoGeometry.cs (RhinoCommon-dependent sub-area)
  │  svg/                 ← from Svg.cs
  │  viz/                 ← from Viz.cs
  │  utils/               ← from Utils.cs
  │  Carcara.Core.csproj
  │
  Carcara.GH/             ← GH_Component subclasses (one per CRC_<Name>).
  │  Components/...
  │  CarcaraPlugin.cs     ← GH_AssemblyInfo
  │  Carcara.GH.csproj    ← References RhinoCommon + Grasshopper via McNeel NuGet SDK
  │
  Carcara.Tests/          ← xUnit tests targeting Carcara.Core only.
     Carcara.Tests.csproj

Carcara.sln
```

- **Target framework**: `net7.0` (confirm against Rhino 8 CoreCLR at the time this
  phase begins — the version may have advanced).
- **NuGet deps**: Npgsql and NetTopologySuite as `<PackageReference>` in
  `Carcara.Core.csproj`; bundled alongside `.gha` via `dotnet publish`.
- **RhinoCommon + Grasshopper**: McNeel NuGet SDK packages in `Carcara.GH.csproj`.

### 2. GH_Component subclasses

Each `GH_ScriptInstance` body from Phase 08–11 becomes a `GH_Component` subclass.
The `ComponentGuid` for each class must equal the `instanceGuid` in the corresponding
`grasshopper/components/CRC_*/metadata.json` — port verbatim, same as during the
script-component phase.

### 3. .NET unit tests

`Carcara.Tests` covers `Carcara.Core` (no Rhino/GH context needed). Port the Python
pytest assertions to xUnit:
- `DbTests/` — connection string, query runner, spatial query SQL templates.
- `GeometryTests/` — WKT round-trip, containment, duplicates.
- `SvgTests/` — element format, file write.
- `VizTests/` — chart geometry output, SVG element presence.
- `UtilsTests/` — correction regex, TranslateExpr, SqlComposer, colormap.
- `GuidAuditTests/` — every `GH_Component.ComponentGuid` matches `metadata.json`.

### 4. GUID audit

```csharp
// Carcara.Tests/GuidAuditTests.cs
[Fact]
public void All_Component_GUIDs_Match_MetadataJson()
{
    // Load all metadata.json from grasshopper/components/
    // Reflect over Carcara.GH assembly for all GH_Component subclasses
    // Assert ComponentGuid == instanceGuid for each matched pair
}
```

### 5. Dependency bundling

Post-build step copies all transitive NuGet DLLs alongside `Carcara.gha` into
`%APPDATA%\Grasshopper\Libraries\Carcara\`.

### 6. Remove Python artifacts

In a single commit after all C# components pass the GUID audit and canvas validation:
- Delete `carcara/crc_modules/` and all contents.
- Delete `grasshopper/components/*/code.py` Python script bundles.
- Delete `build_userobjects.py`, `deploy.ps1`, `vendor/componentizer/`,
  `vendor/ghio/`.
- Delete `tests/` Python pytest suite.
- Update/remove `requirements.txt` and `pyproject.toml` Python metadata.
- Keep `carcara-old/` (frozen legacy reference — never delete).
- Keep `grasshopper/csharp_shared/` as the historical source of the ported logic
  (or delete it once the refactor into `Carcara.Core/` is complete).

Commit message: `chore: remove Python crc_modules and script-component artifacts; C# gha migration complete`.

### 7. Installer

Replace the Python pip-based installer with a PowerShell script or `.gh` definition
that downloads the `Carcara.zip` release archive (containing the `Carcara/` bundle
folder) and copies it to `%APPDATA%\Grasshopper\Libraries\Carcara\`. No pip step.

### 8. Yak packaging

```powershell
yak build --platform win
```
A `.yak` package wraps the `Carcara/` folder with a `manifest.yml`. Publishing to
the Rhino package server is out of scope for Phase 12 — flag as follow-on work.

### 9. Versioning

- `<Version>` in `Carcara.GH.csproj`.
- `CarcaraPlugin.cs` `Version` property.
- `version.txt` at repo root (read by any remaining installer scripts).

---

## Tests / Validation

```powershell
cd src
dotnet test Carcara.Tests/ -v normal
dotnet build Carcara.sln -c Release
```

Full test suite green. GUID audit passes. Full canvas smoke test:
`CRC_ConnectionString` → `CRC_GeometriesWithSpatialFilter` → `CRC_WKTtoGrasshopperGeometry`
→ `CRC_OffsetPython` → `CRC_PolylineToSVG` → `CRC_SaveSVG`.

---

## Done when

- [ ] `Carcara.sln` with `Carcara.Core`, `Carcara.GH`, `Carcara.Tests` committed.
- [ ] `dotnet build src/Carcara.sln -c Release` succeeds with 0 errors.
- [ ] `Carcara.gha` produced with all 32 components (+ `CRC_SRID` as `GH_ValueList`).
- [ ] All `ComponentGuid` values pass the GUID audit test.
- [ ] All .NET tests pass (`dotnet test`).
- [ ] Dependency DLLs bundled under `Libraries\Carcara\`.
- [ ] New installer written; Python pip step removed.
- [ ] Python artifacts removed in one clean commit.
- [ ] Version set in `Carcara.GH.csproj` and `CarcaraPlugin.cs`.
- [ ] Full canvas smoke test passes.
- [ ] (Optional) `.yak` package built.
- [ ] Release tagged on `master`.

---

## After this phase

Post-release work (out of scope for Phase 12):
- CI via GitHub Actions: `dotnet test` + `dotnet build` on push.
- Yak publishing to the McNeel package server.
- Icon refresh.
- Documentation site / demo videos.
- Performance benchmarking (connection pooling, parallel geometry queries).
