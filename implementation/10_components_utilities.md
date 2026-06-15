# C# Migration — Phase 10: C# Script Components — 03.Utilities (7 components)

## Goal

Convert the 7 components in subcategory **03.Utilities** from Python `code.py` script
bundles to C# `code.cs` script bundles, built as `.ghuser` via `componentize_cs.py`.
This subcategory contains the connection string builder, generic query/command runners,
SQL composer, WKT↔GH geometry converters, and the coordinate correction finder.

`instanceGuid` values ported verbatim from existing Python `metadata.json`.

## Depends on

- Phase 01 (toolchain).
- Phase 02 (`Db.cs` — ConnectionString, QueryRunner, SpatialQuery).
- Phase 03 (`Geometry.cs` — WKT utils).
- Phase 04 (`RhinoGeometry.cs` — WKT↔Rhino bridge).
- Phase 07 (`Utils.cs` — SqlComposer, Correction).

## Component inventory — 03.Utilities

| # | Bundle folder | Shared C# preludes | Python spec |
|---|---|---|---|
| 16 | `CRC_ConnectionString` | `Db.cs` | `crc_modules/db/connection.py` |
| 17 | `CRC_FindCorrectionParameters` | `Db.cs`, `Utils.cs` | `crc_modules/utils/correction.py` |
| 18 | `CRC_SQLComposer` | `Utils.cs` | `crc_modules/utils/sql_composer.py` |
| 19 | `CRC_RunQuery` | `Db.cs` | `crc_modules/db/query.py` |
| 20 | `CRC_RunCommand` | `Db.cs` | `crc_modules/db/query.py` |
| 21 | `CRC_GrasshopperGeometryToWKT` | `RhinoGeometry.cs` | `crc_modules/geometry/wkt.py` |
| 22 | `CRC_WKTtoGrasshopperGeometry` | `RhinoGeometry.cs` | `crc_modules/geometry/wkt.py` |

---

## Scope

### `CRC_ConnectionString` (produces CString)

Inputs: `Host` (str), `Port` (int, default 5432), `Database` (str), `User` (str),
`Password` (str).
Output: `CString` (str).
No `CToggle` — pure transform, no DB call.
```csharp
CString = ConnectionString.Build(Host, Port, Database, User, Password);
```

### `CRC_FindCorrectionParameters`

Inputs: `CString` (str), `CToggle` (bool), `Schema` (str), `Table` (str),
`Column` (str, optional), `Value` (str, optional).
Outputs: `Cx` (str), `Cy` (str), `report` (str).

Behavior: auto-detects geometry column from `geometry_columns` view; finds a row where
`Column = Value` (or first row if both omitted); computes `ST_Centroid`, returns
centroid coordinates as text strings. Does NOT take `x_col`/`y_col`. Call
`Correction.ValidateOffset` on the returned coordinates before outputting.

This is in **03.Utilities** but calls into `SpatialQuery` / DB (add `Db.cs` to shared
preludes).

### `CRC_SQLComposer`

Inputs: `SQL` (str, template), `Keys` (str list), `Values` (str list).
Output: `Result` (str), `report` (str).
```csharp
Result = SqlComposer.Compose(SQL, keys.Zip(values).ToDictionary(p => p.First, p => p.Second));
```
No DB call, no CToggle.

### `CRC_RunQuery` and `CRC_RunCommand`

Both follow the standard `CString + CToggle` pattern.

`CRC_RunQuery`: outputs `rows` (DataTree — branch per column), `columns` (list), `report`.
`CRC_RunCommand`: outputs `report` (str — `"OK – N rows affected"` on success).

Read `code.py` for each to confirm exact output format (especially `rows` DataTree
branch structure — must match Python exactly).

### `CRC_GrasshopperGeometryToWKT`

Inputs: `Geometry` (GeometryBase list).
Output: `WKT` (str list), `report`.
Converts each GH geometry to WKT via `WktToRhino.RhinoCurveToWkt`. Correction-free —
coordinates are not modified; the component just serializes what it receives.

### `CRC_WKTtoGrasshopperGeometry`

Inputs: `WKT` (str list).
Output: `Geometry` (GeometryBase list), `report`.
Converts each WKT string to a GH geometry via `WktToRhino.WktToRhinoGeometry`.
Correction-free. Handles POINT, LINESTRING, POLYGON, MULTIPOLYGON.

---

## Steps

1. Read each `metadata.json` and `code.py` (behavioral spec). Confirm inputs/outputs.
2. Copy `instanceGuid` verbatim; add `"csharp_shared"` to each `metadata.json`.
3. Write `code.cs` for all 7.
4. Build: `conda run -n carcara python build_userobjects.py`.
5. Canvas validation.

---

## Validation

**Python oracle**:
```powershell
conda run -n carcara pytest tests/ -v
```

**Canvas checkpoints**:
1. Drop `CRC_ConnectionString`: fill Host/Port/Database/User/Password via Panels;
   `CString` output is a non-empty string.
2. Wire `CString` into `CRC_RunQuery` with `CToggle=True` and `SELECT 1 AS test`;
   `rows` DataTree branch 0 should contain `"1"`.
3. Drop `CRC_WKTtoGrasshopperGeometry` with input
   `"POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))"` → bake output as 1-unit square.
4. Wire `CRC_GrasshopperGeometryToWKT` on the same square → output should match the
   WKT input (modulo coordinate formatting precision).
5. Drop `CRC_SQLComposer` with template `"SELECT {col} FROM {schema}.{tbl}"`,
   keys `{col}`, `{schema}`, `{tbl}`, values `geom`, `public`, `parcelas` →
   output `"SELECT geom FROM public.parcelas"`.
6. All 7 appear in **Carcara → 03.Utilities**.

---

## Done when

- [ ] All 7 `code.cs` files written.
- [ ] All `metadata.json` updated with `instanceGuid` (verbatim) and `"csharp_shared"`.
- [ ] All 7 `.ghuser` files build.
- [ ] All 7 appear in GH toolbar under **Carcara → 03.Utilities**.
- [ ] Canvas checkpoints 1–5 confirmed.
- [ ] Conversion components are correction-free (no `Cx`/`Cy` inputs).
- [ ] Python pytest suite still passes.
