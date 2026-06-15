# C# Migration — Phase 08: C# Script Components — 02.Queries (9 components)

## Goal

Convert the 9 components in subcategory **02.Queries** from Python `code.py` script
bundles to C# `code.cs` script bundles, built as `.ghuser` via `componentize_cs.py`.
Each component's `code.cs` calls helpers from `grasshopper/csharp_shared/Db.cs` and
`Utils.cs` (concatenated in by the build). The GH script body handles only input
coercion, CToggle guarding, output assignment, and report/error surfacing.

`instanceGuid` values are ported verbatim from the existing Python `metadata.json`
files so canvas definitions reconnect automatically.

## Depends on

- Phase 01 (toolchain; `componentize_cs.py` extended; `#r nuget` confirmed).
- Phase 02 (`Db.cs` — all DB classes).
- Phase 07 (`Utils.cs` — `Correction`).

## Component inventory — 02.Queries

| # | Bundle folder | Python code ref | Shared C# preludes | instanceGuid source |
|---|---|---|---|---|
| 7 | `CRC_QuerySchemaNames` | `code.py` → `run_query` | `Db.cs` | existing `metadata.json` |
| 8 | `CRC_QueryTableNames` | `code.py` → `run_query` | `Db.cs` | existing `metadata.json` |
| 9 | `CRC_QueryColumnNames` | `code.py` → `run_query` | `Db.cs` | existing `metadata.json` |
| 10 | `CRC_QueryValues` | `code.py` → `run_query` | `Db.cs` | existing `metadata.json` |
| 11 | `CRC_GeometryEntities` | `code.py` → `get_geometries` | `Db.cs`, `Utils.cs` | existing `metadata.json` |
| 12 | `CRC_GeometriesWithSpatialFilter` | `code.py` → `get_geometries_with_spatial_filter` | `Db.cs`, `Utils.cs` | existing `metadata.json` |
| 13 | `CRC_ValuesWithSpatialFilter` | `code.py` → `get_values_with_spatial_filter` | `Db.cs`, `Utils.cs` | existing `metadata.json` |
| 14 | `CRC_CreateTable` | `code.py` → `create_table` | `Db.cs` | existing `metadata.json` |
| 15 | `CRC_CreateShapefile` | `code.py` → `create_shapefile` | `Db.cs`, `Utils.cs` | existing `metadata.json` |

Before writing any `code.cs`, open each existing `metadata.json` and copy the
`instanceGuid` value into the new `metadata.json`. If a bundle does not have an
`instanceGuid` yet, assign a new GUID and commit it to `metadata.json` before
writing C#.

---

## Scope

### `code.cs` pattern for every query component

Each `code.cs` is a `GH_ScriptInstance` body — the same form as `CRC_CurveDisplay/code.cs`.
Pattern (using `CRC_QuerySchemaNames` as example):

```csharp
// Shared preludes are concatenated before this file by componentize_cs.py.
// Db.cs provides: ConnectionString, QueryRunner, SpatialQuery, Writer.
// Utils.cs provides: Correction, SqlComposer, ColorUtils.

// Inputs: CString (string), CToggle (bool)
// Outputs: schemas (List<string>), report (string)

schemas = new List<string>();
report = "Set 'CToggle' to True to execute";

if (CToggle)
{
    try
    {
        var sql = "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name";
        var (rows, _) = QueryRunner.RunQuery(CString, sql);
        foreach (var row in rows)
            schemas.Add(row[0]?.ToString());
        report = $"OK – {schemas.Count} schemas";
    }
    catch (Exception ex)
    {
        report = "ERROR: " + ex.Message;
    }
}
```

The SQL templates for schema/table/column queries are ported verbatim from
`carcara/crc_modules/db/query.py`.

### `metadata.json` changes

Add `"csharp_shared": ["Db.cs"]` (or `["Db.cs", "Utils.cs"]` for spatial components)
to each bundle's `metadata.json`. Remove or keep `code.py` during transition — the
build router uses whichever file is present; if both exist, C# takes precedence
(confirm this in `build_userobjects.py`).

### Spatial geometry components (11, 12, 13)

These components expose `Cx` and `Cy` text inputs (default `"0"`). Call
`Correction.ValidateOffset(Cx)` at the top of `SolveInstance` before any SQL.
Surface any `ArgumentException` in the report output.

Output WKT strings (not Rhino geometry) — the user feeds these into
`CRC_WKTtoGrasshopperGeometry` (Phase 10). This matches the Python behavior.

### DataTree outputs (ValuesWithSpatialFilter, QueryValues)

Components returning columnar data output a `DataTree` where each branch is a column.
In `GH_ScriptInstance` context, use the DA helpers:
```csharp
// Branch per column
for (int col = 0; col < columns.Count; col++)
{
    var path = new GH_Path(col);
    DA.SetDataTree(0, /* ... build GH_Structure<GH_String> */);
}
```
Match the Python `DataTree` output structure exactly (same branch numbering).

---

## Steps

1. For each component, read `grasshopper/components/CRC_<Name>/code.py` and
   `metadata.json` (behavioral spec). Confirm inputs, outputs, and SQL queries.
2. Copy `instanceGuid` verbatim into new `metadata.json`; add `"csharp_shared"`.
3. Write `code.cs` for each component. Port SQL templates from `code.py` / `db/query.py`
   / `db/spatial_query.py` verbatim.
4. Build: `conda run -n carcara python build_userobjects.py`.
5. Load each `.ghuser` in Rhino 8 → canvas validation.

---

## Validation

**Python oracle**: run the Python pytest suite (tests that cover `crc_modules/db/`)
to understand expected SQL templates and output formats:
```powershell
conda run -n carcara pytest tests/test_connection.py tests/test_query.py -v
```

**Canvas checkpoints** (after each component is built):
1. Drop `CRC_QuerySchemaNames`: connect `CRC_ConnectionString` output + `CToggle=True`.
   Output panel should list database schemas.
2. Drop `CRC_QueryTableNames` + schema input → confirm table list.
3. Drop `CRC_GeometryEntities` on a known table; confirm WKT output count matches row count.
4. Drop `CRC_GeometriesWithSpatialFilter` with a drawn boundary curve → confirm spatial
   filter reduces the WKT list.
5. Drop `CRC_CreateTable` (CToggle=True) → confirm table is created in the DB.
6. Each of the 9 components must appear in **Carcara → 02.Queries** in the GH toolbar.

---

## Done when

- [ ] All 9 `code.cs` files written.
- [ ] All `metadata.json` files updated with `instanceGuid` (verbatim) and
      `"csharp_shared"` list.
- [ ] All 9 `.ghuser` files build successfully.
- [ ] All 9 appear in GH toolbar under **Carcara → 02.Queries**.
- [ ] `instanceGuid` values in C# components match the existing Python `metadata.json`.
- [ ] `Cx`/`Cy` inputs call `Correction.ValidateOffset`; never `double.Parse`.
- [ ] `CRC_QuerySchemaNames`, `CRC_GeometryEntities`, and `CRC_CreateTable` validated
      on canvas with a live PostGIS connection.
- [ ] Python pytest suite still passes.
