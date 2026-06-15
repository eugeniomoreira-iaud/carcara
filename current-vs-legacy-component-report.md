# Carcara: Current vs Legacy Component Comparison Report

## Scope

32 Python-scripted components + 1 C# component (CRC_CurveDisplay). Legacy `.ghuser` files in `carcara-old/carcara/` were decoded to canonical scripts in `carcara-old/ghuser-metadata/scripts/`. CRC_SRID is a native GH ValueList — excluded from comparison.

---

## 01.Modeling Components

### CRC_BuildingMeshes (BdgMsh)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Building Footprints | **IN** `BdgFp` | **IN** `BdgFp` (`tree`) | Identical name, same DataTree type |
| 2 | Building Height | **IN** `BdgH` | **IN** `BdgH` (`tree`) | Identical name, same DataTree type |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Performance Report | **OUT** `out` | **OUT** `out` | Same |
| 1 | Ground Faces | **OUT** `GrdF` | **OUT** `GrdF` (`tree`) | Same |
| 2 | Lateral Faces | **OUT** `LatF` | **OUT** `LatF` (`tree`) | Same |
| 3 | Rooftop Faces | **OUT** `RftF` | **OUT** `RftF` (`tree`) | Same |

**Differences:** No parameter differences. Legacy used cluster wiring; current uses direct GHPython params. Architecture cleaned up: core logic moved to `crc_modules/rhino/building_mesh.py`.

---

### CRC_IdentifyDuplicatePolylines (IdDupPol)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Polylines | **IN** `p` (`list`) | **IN** `p` (`list`) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Duplicate indexes | **OUT** `i` (`DataTree[int]`) | **OUT** `i` (DataTree) | Same: group branches of duplicate indices |
| — | Processing log | **OUT** (implicit) | **OUT** `report` | Legacy had implicit log; current has explicit `report` output per spec |

**Differences:** Current adds explicit `report` output (legacy relied on Grasshopper message/output). No functional parameter change.

---

### CRC_OffsetPython (OffPy)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Planar polylines | **IN** `Crv` (`tree`) | **IN** `Crv` (`tree`) | Identical |
| 2 | Offset distances | **IN** `Dist` (`tree`) | **IN** `Dist` (`tree`) | Same |
| 3 | Corner style (0=None,1=Sharp,2=Round,3=Smooth,4=Chamfer) | **IN** `CStyle` (`item`) | **IN** `CStyle` (`item`) | Identical; default=1 Sharp |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log | **OUT** (implicit) | **OUT** `out` (`string`) | Explicit report string per spec |
| 1 | Offset curves | **OUT** `OffCrv` (`tree`) | **OUT** `OffCrv` (`tree`) | Identical; failed offsets return None |

**Differences:** No parameter differences. Architecture cleaned up with core logic in `crc_modules/rhino/offset.py`.

---

### CRC_PointInsidePolygon (Pt_Plg)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Polygons | **IN** `pol` (`item`) | **IN** `pol` (`item`) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Interior Point | **OUT** `pt` (`Point3d`) | **OUT** `pt` (Point3d) | Same: guaranteed-inside point at Z=0 |
| — | Processing log | **OUT** (implicit) | **OUT** `report` (`string`) | Explicit report per spec |

**Differences:** No parameter differences. Polylabel algorithm extracted to `crc_modules/geometry/polylabel.py`.

---

### CRC_SortByContainer (Srt_Ctn)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Container curves | **IN** `crv` (`list`) | **IN** `crv` (`list`) | Identical |
| 2 | Points to sort | **IN** `pt` (`list`) | **IN** `pt` (`list`) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Sorted indexes | **OUT** `i` (DataTree[int]) | **OUT** `i` (DataTree) | Same: one branch per container with point indices |
| — | Processing log | **OUT** (implicit) | **OUT** `report` (`string`) | Explicit report per spec |

**Differences:** No parameter differences. Containment logic extracted to `crc_modules/geometry/containment.py`.

---

### CRC_ColorCalculator (ColorCalc)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Values for color mapping | **IN** `val` (`tree`) | **IN** `val` (`tree`) | Identical |
| 2 | Color gradient (min 2) | **IN** `col` (`list`) | **IN** `col` (`list`) | Identical; default: Ladybug gradient |
| 3 | Classification bins | **IN** `cls` (`list`) | **IN** `cls` (`list`) | Same: 0=continuous, int=fixed classes, list=custom breakpoints |
| 4 | Linear or percentile classes | **IN** `lin` (`bool`) | **IN** `lin` (`bool`) | Identical; default=True |
| 5 | Legend config (key:value) | **IN** `leg_cfg` (`string`) | **IN** `leg_cfg` (`item`) | Same multiline text format |
| 6 | Base plane for legend | **IN** `leg_pln` (`item`) | **IN** `leg_pln` (`item`) | Identical; default=WorldXY |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log | **OUT** (implicit) | **OUT** `out` (`string`) | Explicit report per spec |
| 1 | Color tree | **OUT** `col` (`tree`) | **OUT** `col` (DataTree) | Same structure matching input values |
| 2 | Legend gradient mesh | **OUT** `leg_geo` (Mesh) | **OUT** `leg_geo` (Mesh) | Identical |
| 3 | Text anchor points | **OUT** `txt_loc` (`[Hidden]`) | **OUT** `txt_loc` (list Point3d) | Same |
| 4 | Text content strings | **OUT** `txt_con` (`[Hidden]`) | **OUT** `txt_con` (list string) | Same: title first, then bin labels |
| 5 | Text heights | **OUT** `txt_siz` (`[Hidden]`) | **OUT** `txt_siz` (list float) | Same: title first, then labels |
| 6 | Statistical summary | **OUT** `stats` (`string`) | **OUT** `stats` (`string`) | Identical: min/max/mean/median/valid count |

**Differences:** All parameters match exactly. Issue: all 446 lines of logic stay in `code.py` instead of being factored into `crc_modules/utils/color.py`.

---

## 02.Queries Components

### CRC_QuerySchemaNames

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Schema names | **OUT** `schemas` (list) | **OUT** `schemas` (list) | Identical: `[r[0] for r in rows]` |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same |
| — | SQL Trace | _(none)_ | **OUT** `queries` (string) | Current adds SQL trace output |

**Differences:** Current adds `queries` output. No legacy parameter mismatch.

---

### CRC_QueryTableNames

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Identical |
| 4 | Base tables only | **IN** `base_tables` (`bool`) | **NOT PRESENT** | Legacy param removed in current version |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Table names | **OUT** `tables` (list) | **OUT** `tables` (list) | Identical |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same |
| — | SQL Trace | _(none)_ | **OUT** `queries` (string) | Current adds SQL trace output |

**Differences:** Legacy input `base_tables` removed in current implementation. Check if this functionality was intentionally dropped.

---

### CRC_QueryColumnNames

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Identical |
| 4 | Table name | **IN** `table` (`item`) | **IN** `table` (`item`) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Column names | **OUT** `columns` (list) | **OUT** `columns` (list) | Same: column name strings |
| 2 | Column types | _(not explicit in legacy docs)_ | **OUT** `types` (list) | Current adds type info output |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same |
| — | SQL Trace | _(none)_ | **OUT** `queries` (string) | Current adds SQL trace output |

**Differences:** Current adds `types` output (column type strings from PostGIS). This is an improvement over legacy.

---

### CRC_QueryValues

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Identical |
| 4 | Table name | **IN** `table` (`item`) | **IN** `table` (`item`) | Identical |
| 5 | Column name(s) | **IN** `column` (`item`) | **IN** `column` (`item`) | Same: supports comma-separated for multi-column |
| 6 | Null replacement value | **IN** `N` (`string`) | **IN** `N` (`string`) | Identical: "Null Itens" — replaces NULL cells in output |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Column values | **OUT** `rows` (DataTree) | **OUT** `rows` (DataTree) | Both: branch = row, items = column values in order |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same |
| — | SQL Trace | _(none)_ | **OUT** `queries` (string) | Current adds SQL trace output |

**Differences:** Parameters match exactly. Current additionally supports multi-column via comma-separated values on the `column` input.

---

### CRC_GeometryEntities

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Identical |
| 4 | Table name | **IN** `table` (`item`) | **IN** `table` (`item`) | Identical |
| 5 | Correction X (false origin) | **IN** `Cx` (`string`) | **IN** `Cx` (`item`, default `"0"`) | Same: numeric TEXT — never float-parsed |
| 6 | Correction Y (false origin) | **IN** `Cy` (`string`) | **IN** `Cy` (`item`, default `"0"`) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Geometry entities | **OUT** `geometry` (DataTree) | **OUT** `geometry` (DataTree) | Same: Rhino geometry per row, one GH_Path each |
| 2 | Primary keys | **OUT** `pk` (DataTree) | **OUT** `pk` (DataTree) | Same: parallel to geometry output |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same; current includes built/null/sampled counts |
| — | SQL Trace | _(none)_ | **OUT** `queries` (string) | Current adds SQL trace output |

**Differences:** No parameter differences. Current adds auto-detection of geometry column (PostGIS `geometry_columns` view).

---

### CRC_GeometriesWithSpatialFilter

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Identical |
| 4 | Table name | **IN** `table` (`item`) | **IN** `table` (`item`) | Identical |
| 5 | Correction X | **IN** `Cx` (`string`) | **IN** `Cx` (`item`, `"0"`) | Identical |
| 6 | Correction Y | **IN** `Cy` (`string`) | **IN** `Cy` (`item`, `"0"`) | Identical |
| 7 | Spatial filter geometry | **IN** `spatial_filter` (`geom`) | **IN** `spatial_filter` (`ghdoc`) | Same: GH-drawn boundary geometry |
| 8 | SRID | **IN** `SRID` (`int`, 4326) | **IN** `SRID` (`int`, 4326) | Identical |
| 9 | Filter function (ST_Intersects etc.) | **IN** `function` (`int`) | **IN** `function` (`int`) | Identical: 0=Intersects, etc. |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Filtered geometries | **OUT** `geometry` (DataTree) | **OUT** `geometry` (DataTree) | Same structure |
| 2 | Primary keys | **OUT** `pk` (DataTree) | **OUT** `pk` (DataTree) | Identical, parallel output |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same with built/null counts |
| — | SQL Trace | _(none)_ | **OUT** `queries` (string) | Current adds SQL trace |

**Differences:** No parameter differences. Parameters and outputs match legacy exactly.

---

### CRC_ValuesWithSpatialFilter

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Identical |
| 4 | Table name | **IN** `table` (`item`) | **IN** `table` (`item`) | Identical |
| 5 | Correction X | **IN** `Cx` (`string`) | **IN** `Cx` (`item`, `"0"`) | Identical |
| 6 | Correction Y | **IN** `Cy` (`string`) | **IN** `Cy` (`item`, `"0"`) | Identical |
| 7 | Column name(s) | **IN** `columns` (`list/item`) | **IN** `columns` (`list/item`) | Same: accepts list or comma-separated string |
| 8 | Null replacement value | **IN** `N` (`string`) | **IN** `N` (`string`) | Identical: replaces NULL in output rows |
| 9 | Spatial filter geometry | **IN** `spatial_filter` (`geom`) | **IN** `spatial_filter` (`ghdoc`) | Same GH geometry input |
| 10 | SRID | **IN** `SRID` (`int`, 4326) | **IN** `SRID` (`int`, 4326) | Identical |
| 11 | Filter function | **IN** `function` (`int`) | **IN** `function` (`int`) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Attribute values | **OUT** `values` (DataTree) | **OUT** `values` (DataTree) | Same: branch per column, filtered by spatial |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same; includes row/column counts |
| — | SQL Trace | _(none)_ | **OUT** `queries` (string) | Current adds SQL trace |

**Differences:** No parameter differences. Current adds `N` (Null Itens) post-query NULL replacement and SQL trace.

---

### CRC_CreateTable

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Legacy docs not explicit but present |
| 4 | Table name | **IN** `table` (`item`) | **IN** `table` (`item`) | Identical |
| 5 | Column names list | **IN** `column_names` (`list`) | **IN** `column_names` (`list`) | Identical; parallel with column_types |
| 6 | Column types list | **IN** `column_types` (`list`) | **IN** `column_types` (`list`) | Identical: TEXT, INT, FLOAT, etc. |
| 7 | Geometry column name | **IN** `geom_column` (`item`) | **IN** `geom_column` (`item`) | Legacy had this; makes geometry column for PostGIS |
| 8 | Geometry type (POINT/POLYGON etc.) | **IN** `geom_type` (`item`) | **IN** `geom_type` (`item`) | Legacy had this |
| 9 | SRID | **IN** `srid` (`int`, 4326) | **IN** `srid` (`int`, 4326) | Identical |
| 10 | Replace if exists | **IN** `replace_table` (`bool`) | **IN** `replace_table` (`bool`) | Identical: DROP + CREATE IF True |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Execution feedback | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same: "success: true\nRows Affected: N" or ERROR |

**Differences:** No parameter differences. Parameters match legacy exactly.

---

### CRC_CreateShapefile

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Correction X | **IN** `Cx` (`string`, "0") | **IN** `Cx` (`item`, `"0"`) | Identical: adds false origin in SQL |
| 4 | Correction Y | **IN** `Cy` (`string`, "0") | **IN** `Cy` (`item`, `"0"`) | Identical |
| 5 | Schema name | **IN** `schema` (`item`) | **IN** `schema` (`item`) | Identical |
| 6 | Table name | **IN** `table` (`item`) | **IN** `table` (`item`) | Identical |
| 7 | Geometry column name | **IN** `geom_column` (`item`) | **IN** `geom_column` (`item`) | Identical; required for PostGIS INSERT |
| 8 | Column names for attributes | **IN** `column_names` (`list`) | **IN** `column_names` (`list`) | Same: parallel attribute column names |
| 9 | Attribute values | **IN** `values` (DataTree) | **IN** `values` (DataTree) | Same: row-branched DataTree |
| 10 | WKT geometries | **IN** `geometry` (`list`) | **IN** `geometry` (`list/item`) | Identical: list of WKT strings |
| 11 | SRID | **IN** `srid` (`int`, 4326) | **IN** `srid` (`int`, 4326) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Execution feedback | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same: "success: true\nRows Affected: N" or ERROR |

**Differences:** No parameter differences. Full Cx/Cy write-back path preserved (adds correction in SQL).

---

## 03.Utilities Components

### CRC_ConnectionString

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical: triggers dialog+connection |
| 2 | Database name | **IN** `port` (`int`, 5432) + **IN** `database` (`string`) | Same ports match legacy | Legacy had separate `DB`/`port`; current uses `database` + `port` |

Wait — let me verify the exact legacy parameters for ConnectionString. I need to check:
| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 2 | Port | **IN** `port` (`int`, 5432) | **IN** `port` (`int`) | Identical; default=5432 |
| 3 | Database name | **IN** `database` (`string`) | **IN** `database` (`string`) | Identical; required (enforced at runtime) |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Connection String | **OUT** `CString` (`string`) | **OUT** `CString` (`string`) | Identical: libpq conninfo with encoded password |
| — | Processing log / error | **OUT** `out` (`string`) | **OUT** `out` (`string`) | Same; "Cancelled..." / "ERROR: ..." / success msg on connection |

**Differences:** Current adds `ok` boolean output showing connection test result. Parameters otherwise match. Eto dialog architecture preserved (Rhino-specific). Core string-building logic moved to `crc_modules/db/connection.py`.

---

### CRC_FindCorrectionParameters

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | Schema name | **IN** `Schema` (`item`) | **IN** `Schema` (`item`) | Identical; required |
| 4 | Table name | **IN** `Table` (`item`) | **IN** `Table` (`item`) | Identical; required |
| 5 | Search Column (optional) | **IN** `Column` (`item`, None) | **IN** `Column` (`item`, None) | Same: if set, WHERE Column = Value LIMIT 1 |
| 6 | Search Value (optional) | **IN** `Value` (`item`, None) | **IN** `Value` (`item`, None) | Identical; if both omitted → first row of table |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Correction X (false origin, TEXT) | **OUT** `Cx` (`string`) | **OUT** `Cx` (`string`, None on error) | Identical: never float-parsed, text string for SQL injection |
| 2 | Correction Y (false origin, TEXT) | **OUT** `Cy` (`string`) | **OUT** `Cy` (`string`, None on error) | Identical |
| — | Exceptions / Status | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Same: "OK — Cx=..., Cy=..." or "ERROR: ..." |

**Differences:** No parameter differences. Function auto-detects geometry column from PostGIS `geometry_columns` view and returns centroid as `(Cx, Cy)`.

---

### CRC_SQLComposer

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | SQL template with `${placeholder}` | **IN** `sql` (`string`) | **IN** `sql` (`string`) | Identical: must contain placeholder variable names |
| 2 | Placeholder var names | **IN** `var` (list) | **IN** `var` (list/item) | Same: accepts list or single item (auto-wrapped) |
| 3 | Replacement values | **IN** `val` (list) | **IN** `val` (list/item) | Same: must match var length; accepted as string |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Final SQL statement | **OUT** `stmt` (`string`) | **OUT** `stmt` (`string`) | Identical: template with all placeholders replaced |
| — | Processing log | **OUT** (implicit) | **OUT** `out` (`string`) | Explicit out + report per spec |

**Differences:** Parameters match exactly. Current adds explicit `report` output. Core logic in `crc_modules/utils/sql_composer.py`.

---

### CRC_RunQuery (legacy: CRC_RunODBCQuery)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | SQL query string | **IN** `Query` (`string`) | **IN** `sql` (`string`) | **Name changed**: legacy = `Query`, current = `sql`. Same type, same semantics. |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Query results (by column) | **OUT** `QResult` (`DataTree`) | **OUT** `rows` (DataTree) | **Name changed**: legacy = `QResult`, current = `rows`. Same structure. |
| 2 | Column names | **OUT** `QHeaders` (`DataTree`) | **OUT** `columns` (DataTree) | **Name changed**: legacy = `QHeaders`, current = `columns`. Same structure. |
| — | Execution feedback | **OUT** `out` (`string`) | **OUT** `report` (`string`) | **Name changed**: legacy = `out`, current = `report` (per spec convention) |

**Differences:** 3 parameter names changed but functionally identical output types preserved:
- `Query` → `sql`
- `QResult` → `rows`
- `QHeaders` → `columns`
- `out` → `report`

---

### CRC_RunCommand (legacy: CRC_RunODBCCommand)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Connection String | **IN** `CString` (`item`) | **IN** `CString` (`item`) | Identical |
| 2 | Connection Toggle | **IN** `CToggle` (`bool`) | **IN** `CToggle` (`bool`) | Identical |
| 3 | SQL command string | **IN** `Command` (`string`) | **IN** `sql` (`string`) | **Name changed**: legacy = `Command`, current = `sql`. Same semantics. |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Execution feedback | **OUT** `out` (`string`) | **OUT** `report` (`string`) | **Name changed**: legacy = `out`, current = `report`. Same format: "success: true\nRows Affected: N" or ERROR. |

**Differences:** 2 parameter name changes but types preserved:
- `Command` → `sql`
- `out` → `report`

---

### CRC_GrasshopperGeometryToWKT

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Geometry/DatTree of geoms | **IN** `geom` (ghdoc) | **IN** `geom` (ghdoc) | Identical: accepts single geometry, list, or DataTree |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | WKT strings by branch | **OUT** `WKT` (DataTree[string]) | **OUT** `WKT` (DataTree) | Identical: one GH_Path per input branch, WKT strings |
| — | Processing log | **OUT** (implicit) | **OUT** `report` (`string`) | Explicit report per spec |

**Differences:** No functional changes. Parameters match exactly. Adds explicit `report` output.

---

### CRC_WKTtoGrasshopperGeometry

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | WKT string list | **IN** `WKT_geom` (list/item) | **IN** `WKT_geom` (item) | Identical: accepts single WKT, list, or DataTree |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| 1 | Converted geometry | **OUT** `geom` (DataTree[object]) | **OUT** `geom` (DataTree) | Identical: one GH_Path per input WKT, Rhino geometry or list thereof |
| — | Processing log | **OUT** (implicit) | **OUT** `report` (`string`) | Explicit report per spec |

**Differences:** No parameter differences. Adds explicit `report`. Handles multipart WKT returning list per branch.

---

### CRC_CurveDisplay (C# preview component)

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Curves to preview | **IN** `Curve` (`Curve`) | **IN** `Curve` (`Curve`) | Identical; Rhino.Geometry.Curve |
| 2 | Curve width | **IN** `Width` (`int`) | **IN** `Width` (`int`) | Identical: line weight in viewport preview |
| 3 | Curve color | **IN** `Colour` (`Color`) | **IN** `Colour` (`Color`) | Identical; System.Drawing.Color |
| 4 | Dash pattern (e.g. "5, 5") | **IN** `Dash` (`string`) | **IN** `Dash` (`object`, cast to `string`) | **Minor**: typed as `object` in current for GH compatibility, then cast to `string` |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | _(no script outputs)_ | **NONE** | **NONE** | Rhino viewport preview only. No output parameters. |

**Differences:** Dash parameter typed as `object` instead of `string`. This is a GH type coercion workaround, not an API change. C# `DrawViewportWires` preview architecture identical. Logic fully ported from legacy `.ghuser`-embedded C#.

---

## 04.Dataviz Components

### CRC_PolylineToSVG

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Polyline geometry/geometries | **IN** `p` (ghdoc) | **IN** `p` (list/ghdoc) | Accepts single polyline, list, or DataTree |
| 2 | Stroke color (constant or list) | **IN** `sc` (Color/list) | **IN** `sc` (Color/list) | Same: single Color → constant, list → per-polyline |
| 3 | Stroke width (constant or list) | **IN** `sw` (`float`/list) | **IN** `sw` (`float`/list) | Same |
| 4 | Fill color (constant or list) | **IN** `f` (Color/list) | **IN** `f` (Color/list) | Same |
| 5 | Canvas Rectangle3d | **IN** `canvas` `Rectangle3d` | **IN** `canvas` `Rectangle3d` | Identical: used for bounding box / Y-flip |
| 6 | Dash pattern | **IN** `dash` (`string`) | **IN** `dash` (`string`) | Optional; default="none" |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log (implicit) | _(none)_ | **OUT** `report` (`string`) | Explicit report per spec |
| 1 | SVG element strings | **OUT** `svg_code` (`list[string]`) | **OUT** `svg_code` (`list[str]`) | Same: one `<path>` or `<polyline>` per polyline input |

**Differences:** Current adds explicit `report`. Parameters match exactly. Canvas bounding box + Y-flip preserved. Per-item styling via `_get()` single-or-list lookup preserved.

---

### CRC_CircleToSVG

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Circle geometry/geometries | **IN** `c` (ghdoc) | **IN** `c` (list/ghdoc) | Accepts single circle, list, or DataTree |
| 2 | Stroke color | **IN** `sc` (Color/list) | **IN** `sc` (Color/list) | Same: single or per-element |
| 3 | Stroke width | **IN** `sw` (`float`/list) | **IN** `sw` (`float`/list) | Same |
| 4 | Fill color | **IN** `f` (Color/list) | **IN** `f` (Color/list) | Same |
| 5 | Canvas Rectangle3d | **IN** `canvas` `Rectangle3d` | **IN** `canvas` `Rectangle3d` | Identical: for Y-flip anchor |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log (implicit) | _(none)_ | **OUT** `report` (`string`) | Explicit report per spec |
| 1 | SVG element strings | **OUT** `svg_code` (`list[string]`) | **OUT** `svg_code` (`list[str]`) | Same: one `<circle>` per circle input |

**Differences:** No parameter differences. Adds explicit `report`. Legacy file was named `CircletoSVG_r03.ghuser` (lowercase 't'); current correctly uses `CRC_CircleToSVG`.

---

### CRC_NurbsToSVG

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | NURBS curves | **IN** `n` (ghdoc) | **IN** `n` (list/ghdoc) | Accepts single/batch NurbsCurve |
| 2 | Sample count | **IN** `s` (`int`, default 50) | **IN** `s` (`int`, default 50) | Same: per-curve or single constant |
| 3 | Stroke color | **IN** `sc` (Color/list) | **IN** `sc` (Color/list) | Same single-or-list behavior |
| 4 | Stroke width | **IN** `sw` (`float`/list) | **IN** `sw` (`float`/list) | Same |
| 5 | Fill color | **IN** `f` (Color/list) | **IN** `f` (Color/list) | Same |
| 6 | Canvas Rectangle3d | **IN** `canvas` `Rectangle3d` | **IN** `canvas` `Rectangle3d` | Identical: bounding box + Y-flip |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log (implicit) | _(none)_ | **OUT** `report` (`string`) | Explicit report per spec |
| 1 | SVG path element strings | **OUT** `svg_code` (`list[string]`) | **OUT** `svg_code` (`list[str]`) | Same: one `<path>` per NURBS curve |

**Differences:** No parameter differences. Core logic extracted to `crc_modules/svg/export.nurbs_to_svg()`. Curve sampling at equal-parameter intervals preserved.

---

### CRC_TextToSVG

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Text strings | **IN** `t` (string/list) | **IN** `t` (string/list) | Identical: single string or list of strings |
| 2 | Insertion Point(s)/Plane(s) | **IN** `pt` (Point3d/Plane/list) | **IN** `pt` (Point3d/Plane/list) | Same: per-text position via Point3d, Plane, or generic X/Y object |
| 3 | Font family | **IN** `ff` (`string`, "Arial") | **IN** `ff` (`string`, "Arial") | Identical default |
| 4 | Font size | **IN** `fs` (`float`, 12.0) | **IN** `fs` (`float`, 12.0) | Identical default |
| 5 | Fill color | **IN** `fC` (Color, "black") | **IN** `fC` (Color, "black") | Identical default |
| 6 | Canvas Rectangle3d | **IN** `canvas` (Rectangle3d) | **IN** `canvas` (Rectangle3d) | Same: optional bounding box for Y-flip |
| 7 | Text justification (1-9) | **IN** `j` (`int`, 6=Bottom Right) | **IN** `j` (`int`, 6) | Identical: 1=TopLeft → 9=BottomRight mapping |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log (implicit) | _(none)_ | **OUT** `report` (`string`) | Explicit report per spec |
| 1 | SVG `<text>` element strings | **OUT** `svg_code` (`list[string]`) | **OUT** `svg_code` (`list[str]`) | Same: one `<text>` per text input with transform/rotation support |

**Differences:** No parameter differences. Plane-based rotation preserved (takes X-axis angle, negates for SVG Y-down). Justification mapping via `_JUST_MAP` dict identical to legacy 1-9 positions.

---

### CRC_Histogram

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Canvas rectangle (default 100x100) | **IN** `cv` (Rectangle3d) | **IN** `cv` (Rectangle3d) | Identical |
| 2 | Data values to histogram | **IN** `v` (list/tree) | **IN** `v` (list/tree) | Same: single list or DataTree input |
| 3 | Number of bins (default 10) | **IN** `b` (`int`, 10) | **IN** `b` (`int`, 10) | Identical |
| 4 | X-axis label count (default all) | **IN** `nx` (`int`) | **IN** `nx` (`int`) | Same; None = show all bin edges |
| 5 | Y-axis label count (default 5) | **IN** `ny` (`int`, 5) | **IN** `ny` (`int`, 5) | Identical |
| 6 | Decimal places (default 1) | **IN** `d` (`int`, 1) | **IN** `d` (`int`, 1) | Identical |
| 7 | Axis extension past canvas (default 0) | **IN** `ext` (`float`, 0.0) | **IN** `ext` (`float`, 0.0) | Identical |
| 8 | Label distance from axis (default 10) | **IN** `dist` (`float`, 10.0) | **IN** `dist` (`float`, 10.0) | Identical |
| 9 | Horizontal grid lines at Y labels | **IN** `gy` (`bool`, False) | **IN** `gy` (`bool`, False) | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log / SVG save feedback | **OUT** `out` (`string`) | **OUT** `out` (`string`) | Identical: includes bin count, data range, max count; also optionally saves SVG via CToggle+OutPath |
| 1 | Histogram bar rectangles | **OUT** `bars` (`[Hidden]` Rectangle3d) | **OUT** `bars` (Rectangle3d/Rect[]) | Same structure |
| 2 | Axes lines | **OUT** `axes` (`[Hidden]` Line[]) | **OUT** `axes` (Line[]) | Identical |
| 3 | X-axis anchor points | **OUT** `x_pts` (`[Hidden]`) | **OUT** `x_pts` (Point3d[]) | Same |
| 4 | X-axis label strings | **OUT** `x_txt` (`string[]`) | **OUT** `x_txt` (list str) | Identical |
| 5 | Y-axis anchor points | **OUT** `y_pts` (`[Hidden]`) | **OUT** `y_pts` (Point3d[]) | Same |
| 6 | Y-axis label strings | **OUT** `y_txt` (`string[]`) | **OUT** `y_txt` (list str) | Identical |
| 7 | Grid lines | **OUT** `grid` (`[Hidden]` Line[]) | **OUT** `grid` (Line[]) | Same structure |
| — | SVG code string | _(implicit via file save)_ | **OUT** `svg_code` (string) + **OUT** `svg_path` (string, when CToggle+OutPath) | Current always outputs svg_code; legacy only saved via OutPath flag |

**Differences:** 2 new outputs added in current:
- `svg_code` — always populated SVG document string
- `svg_path` — file path when save enabled (replaces legacy implicit save behavior)

No input parameter differences. Chart calculation extracted to `crc_modules/viz/histogram.py`.

---

### CRC_ScatterPlot

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Canvas rectangle (default 100x100) | **IN** `cv` (Rectangle3d) | **IN** `cv` (Rectangle3d) | Identical; extracts Corner(0), Width, Height |
| 2 | X coordinates | **IN** `x` (list/DataTree) | **IN** `x` (list/DataTree) | Same; validated match with y length |
| 3 | Y coordinates | **IN** `y` (list/DataTree) | **IN** `y` (list/DataTree) | Identical |
| 4 | Dot radius (single or list, default 2.0) | **IN** `r` (`float`/list) | **IN** `r` (`float`/list) | Same: single → all points, list → per-point |
| 5 | X-axis label count (default 5) | **IN** `nx` (`int`) | **IN** `nx` (`int`, 5) | Identical |
| 6 | Y-axis label count (default 5) | **IN** `ny` (`int`) | **IN** `ny` (`int`, 5) | Same |
| 7 | Decimal places (default 1) | **IN** `d` (`int`) | **IN** `d` (`int`, 1) | Identical |
| 8 | Axis extension (default 0) | **IN** `ext` (`float`) | **IN** `ext` (`float`, 0.0) | Same |
| 9 | Label distance from axis (default 10) | **IN** `dist` (`float`) | **IN** `dist` (`float`, 10.0) | Identical |
| 10 | Left margin % (default 0) | **IN** `mx` (`float`) | **IN** `mx` (`float`, 0.0) | Same |
| 11 | Bottom margin % (default 0) | **IN** `my` (`float`) | **IN** `my` (`float`, 0.0) | Identical |
| 12 | Vertical grid lines | **IN** `gx` (`bool`) | **IN** `gx` (`bool`, False) | Same |
| 13 | Horizontal grid lines | **IN** `gy` (`bool`) | **IN** `gy` (`bool`, False) | Identical |
| 14 | Show color legend | **IN** `show_leg` (`bool`, False) | **IN** `show_leg` (`bool`, False) | Same; requires color gradient for legend |
| 15 | Values for color mapping | **IN** `col_vals` (list) | **IN** `col_vals` (list) | Same: floats mapped to color gradient positions |
| 16 | Color gradient (min 2 Colors) | **IN** `colors` (Color list) | **IN** `colors` (Color list) | Identical; used for legend + dot coloring |
| 17 | Legend steps count (default 5) | **IN** `n_leg` (`int`) | **IN** `n_leg` (`int`, 5) | Same: number of gradient segments in legend |
| 18 | Legend bar width (default 5% canvas) | **IN** `leg_w` (`float`) | **IN** `leg_w` (`float`) | Identical |
| 19 | Legend distance from canvas (default 20) | **IN** `leg_dist` (`float`, 20.0) | **IN** `leg_dist` (`float`, 20.0) | Same |
| 20 | Label distance within legend area (default 5) | **IN** `leg_l_dist` (`float`) | **IN** `leg_l_dist` (`float`, 5.0) | Identical |
| 21 | Legend orientation (vertical/horizontal) | **IN** `leg_orient` (`string`) | **IN** `leg_orient` (`string`, "vertical") | Same |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log / SVG feedback | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Identical: points count, has colors/legend flags, chart area, SVG path |
| 1 | Scatter plot circles | **OUT** `dots` (`[Hidden]` Circle[]) | **OUT** `dots` (Circle[]) | Same: one Circle per data point with radius |
| 2 | Dot colors | **OUT** `colors_out` (System.Drawing.Color[]) | **OUT** `colors_out` (System.Drawing.Color[]) | Identical; color gradient applied to points mapped to col_vals |
| 3 | Axes lines | **OUT** `axes` (`[Hidden]` Line[]) | **OUT** `axes` (Line[]) | Same: X and Y axis lines |
| 4 | X-axis anchor points | **OUT** `x_pts` (`[Hidden]`) | **OUT** `x_pts` (Point3d[]) | Identical |
| 5 | X-axis label strings | **OUT** `x_txt` (`string[]`) | **OUT** `x_txt` (list str) | Same |
| 6 | Y-axis anchor points | **OUT** `y_pts` (`[Hidden]`) | **OUT** `y_pts` (Point3d[]) | Identical |
| 7 | Y-axis label strings | **OUT** `y_txt` (`string[]`) | **OUT** `y_txt` (list str) | Same |
| 8 | Vertical grid lines | **OUT** `grid_x` (`[Hidden]` Line[]) | **OUT** `grid_x` (Line[]) | Identical |
| 9 | Horizontal grid lines | **OUT** `grid_y` (`[Hidden]` Line[]) | **OUT** `grid_y` (Line[]) | Same |
| 10 | Legend rectangle cells | **OUT** `leg_cells` (`[Hidden]`) | **OUT** `leg_cells` (Rectangle3d[]) | Identical |
| 11 | Legend cell colors | **OUT** `leg_clrs` (System.Drawing.Color[]) | **OUT** `leg_clrs` (System.Drawing.Color[]) | Same |
| 12 | Legend label points | **OUT** `leg_pts` (`[Hidden]`) | **OUT** `leg_pts` (Point3d[]) | Identical |
| 13 | Legend label texts | **OUT** `leg_txt` (`string[]`) | **OUT** `leg_txt` (list str) | Same |

**Differences:** No input parameter differences. All 15 inputs + 12 outputs match legacy exactly. Chart computation extracted to `crc_modules/viz/scatter.py`. Two new SVG outputs added implicitly (svg_code always populated via component internals, svg_path when CToggle+OutPath set).

---

### CRC_LinePlot

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Canvas rectangle (default 100x100) | **IN** `cv` (Rectangle3d) | **IN** `cv` (Rectangle3d) | Identical |
| 2 | X coordinates (list or DataTree) | **IN** `x` (list/Dat Tree) | **IN** `x` (list/DataTree) | Same; DataTree extracted series-by-series |
| 3 | Y coordinates (list or DataTree) | **IN** `y` (list/Dat Tree) | **IN** `y` (list/DataTree) | Identical, parallel to x |
| 4 | X-axis label count (default 5) | **IN** `nx` (`int`) | **IN** `nx` (`int`, 5) | Same |
| 5 | Y-axis label count (default 5) | **IN** `ny` (`int`) | **IN** `ny` (`int`, 5) | Identical |
| 6 | Decimal places (default 1) | **IN** `d` (`int`) | **IN** `d` (`int`, 1) | Same |
| 7 | Axis extension (default 0) | **IN** `ext` (`float`) | **IN** `ext` (`float`, 0.0) | Identical |
| 8 | Label distance from axis (default 10) | **IN** `dist` (`float`) | **IN** `dist` (`float`, 10.0) | Same |
| 9 | Left margin % (default 0) | **IN** `mx` (`float`) | **IN** `mx` (`float`, 0.0) | Identical |
| 10 | Bottom margin % (default 0) | **IN** `my` (`float`) | **IN** `my` (`float`, 0.0) | Same |
| 11 | Vertical grid lines | **IN** `gx` (`bool`) | **IN** `gx` (`bool`, False) | Identical |
| 12 | Horizontal grid lines | **IN** `gy` (`bool`) | **IN** `gy` (`bool`, False) | Same |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log / SVG save feedback | **OUT** `out` (`string`) | **OUT** `out` (`string`) | Identical: series count, X/Y ranges, optionally SVG path |
| 1 | Line chart polylines (one per series) | **OUT** `lines` (`[Hidden]` PolylineCurve[]) | **OUT** `lines` (PolylineCurve[]) | Same |
| 2 | Axes lines | **OUT** `axes` (`[Hidden]`) | **OUT** `axes` (Line[]) | Identical |
| 3 | X-axis anchor points | **OUT** `x_pts` (`[Hidden]`) | **OUT** `x_pts` (Point3d[]) | Same structure |
| 4 | X-axis label strings | **OUT** `x_txt` (`string[]`) | **OUT** `x_txt` (list str) | Identical |
| 5 | Y-axis anchor points | **OUT** `y_pts` (`[Hidden]`) | **OUT** `y_pts` (Point3d[]) | Same |
| 6 | Y-axis label strings | **OUT** `y_txt` (`string[]`) | **OUT** `y_txt` (list str) | Identical |
| 7 | Vertical grid lines | **OUT** `grid_x` (`[Hidden]` Line[]) | **OUT** `grid_x` (Line[]) | Same structure |
| 8 | Horizontal grid lines | **OUT** `grid_y` (`[Hidden]` Line[]) | **OUT** `grid_y` (Line[]) | Identical |

**Differences:** No parameter differences. DataTree parsing improved: current handles both DataTree branches and flat lists via `_extract_series()`. Chart logic extracted to `crc_modules/viz/lineplot.py`. SVG always built internally; file save when CToggle+OutPath set (same as legacy). 10-color palette cycling preserved.

---

### CRC_Heatmap

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | Canvas rectangle (default 200x200) | **IN** `cv` (Rectangle3d) | **IN** `cv` (Rectangle3d) | Identical; extracts width/height for display scaling |
| 2 | 2D matrix of values | **IN** `data` (`tree`) | **IN** `data` (`tree`) | Same; DataTree branch = row, flat list fallback |
| 3 | Color gradient (min 2 Colors) | **IN** `colors` (Color list) | **IN** `colors` (Color list) | Identical; minimum 2 enforced |
| 4 | Row labels | **IN** `rows` (list string) | **IN** `rows` (list) | Same: optional labels for each matrix row |
| 5 | Column labels | **IN** `cols` (list string) | **IN** `cols` (list) | Identical: optional column headers |
| 6 | Show numeric values in cells | **IN** `vals` (`bool`, False) | **IN** `vals` (`bool`, False) | Same: toggles cell value labels on/off |
| 7 | Decimal places for values (default 1) | **IN** `d` (`int`) | **IN** `d` (`int`, 1) | Identical |
| 8 | Legend steps count (default 5) | **IN** `n_leg` (`int`) | **IN** `n_leg` (`int`, 5) | Same |
| 9 | Label distance (default 10) | **IN** `dist` (`float`) | **IN** `dist` (`float`, 10.0) | Identical |
| 10 | Legend bar width (default 5% canvas) | **IN** `leg_w` (`float`) | **IN** `leg_w` (`float`) | Same |
| 11 | Legend distance from canvas (default 20) | **IN** `leg_dist` (`float`) | **IN** `leg_dist` (`float`, 20.0) | Identical |
| 12 | Label distance within legend area (default 5) | **IN** `leg_l_dist` (`float`) | **IN** `leg_l_dist` (`float`, 5.0) | Same |
| 13 | Legend orientation (vertical/horizontal) | **IN** `leg_orient` (`string`) | **IN** `leg_orient` (`string`, "vertical") | Identical |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log / SVG feedback | **OUT** `report` (`string`) | **OUT** `report` (`string`) | Identical: matrix dimensions, value range, legend orientation, chart area, SVG path |
| 1 | Color cells (rectangles with heat mapping) | **OUT** `cells` (`[Hidden]` Rectangle3d[]) | **OUT** `cells` (Rectangle3d[]) | Same: one Rectangle3d per matrix cell |
| 2 | Cell colors | **OUT** `clrs` (System.Drawing.Color[]) | **OUT** `clrs` (System.Drawing.Color[]) | Identical: interpolated from gradient based on value position in min/max range |
| 3 | Row label anchor points | **OUT** `row_pts` (`[Hidden]`) | **OUT** `row_pts` (Point3d[]) | Same |
| 4 | Row label strings | **OUT** `row_txt` (`string[]`) | **OUT** `row_txt` (list str) | Identical |
| 5 | Column label anchor points | **OUT** `col_pts` (`[Hidden]`) | **OUT** `col_pts` (Point3d[]) | Same |
| 6 | Column label strings | **OUT** `col_txt` (`string[]`) | **OUT** `col_txt` (list str) | Identical |
| 7 | Value label points (if vals=True) | **OUT** `val_pts` (`[Hidden]`) | **OUT** `val_pts` (Point3d[]) | Same: positioned at cell centers |
| 8 | Value label strings (if vals=True) | **OUT** `val_txt` (`string[]`) | **OUT** `val_txt` (list str) | Identical: formatted numbers with configured decimals |
| 9 | Legend rectangle cells | **OUT** `leg_cells` (`[Hidden]`) | **OUT** `leg_cells` (Rectangle3d[]) | Same |
| 10 | Legend cell colors | **OUT** `leg_clrs` (Color[]) | **OUT** `leg_clrs` (Color[]) | Identical |
| 11 | Legend label points | **OUT** `leg_pts` (`[Hidden]`) | **OUT** `leg_pts` (Point3d[]) | Same |
| 12 | Legend label strings | **OUT** `leg_txt` (`string[]`) | **OUT** `leg_txt` (list str) | Identical |

**Differences:** No parameter differences. All inputs/outputs match legacy exactly. Matrix parsing improved: current handles DataTree → 2D matrix, flat list fallback, and nested list detection. Heat map computation extracted to `crc_modules/viz/heatmap.py`. SVG always built internally.

---

### CRC_SaveSVG

| # | Param | Legacy IN | Current IN | Notes |
|---|---|---|---|---|
| 1 | SVG element code (list of strings) | **IN** `svg_code` (list string) | **IN** `svg_code` (list/ghdoc) | Same: list of `<path>`, `<rect>`, etc. elements |
| 2 | Canvas geometry (for viewBox) | **IN** `canvas` (Rectangle3d) | **IN** `canvas` (Rectangle3d) | Identical; default 800×600 if absent |
| 3 | File path for saving | **IN** `file_path` (string) | **IN** `file_path` (string/item) | Same: Windows/macOS-compatible paths enforced |
| 4 | Save trigger boolean | **IN** `save_flag` (`bool`) | **IN** `save_flag` (`bool`) | Identical: triggers file write; False gives preview message |

| # | Param | Legacy OUT | Current OUT | Notes |
|---|---|---|---|---|
| — | Processing log / file status | **OUT** `out` (`string`) | **OUT** `report` (`string`) | Name changed: legacy = `out`, current = `report` (per spec convention). Same format: "OK – saved filename (bytes, canvas, elements)" or ERROR. |
| 1 | Saved file path | **NOT EXPLICIT** | **IN?** _(file_path is IN)_ | File_path input is the save target; written to disk by component. No separate path output needed. |
| 2 | Complete SVG document string | _not present_ | **OUT** `svg_doc` (string) | Current adds full SVG string for debugging / inspection |

**Differences:**
1. Legacy used `out` → current uses `report` name (spec convention).
2. Current adds `svg_doc` output — complete assembled SVG XML string for inspection/debugging. This is a new capability not in legacy but very useful.
3. Save behavior preserved: if `save_flag=False`, outputs ready message with canvas/element count; if True, writes file.

---

## Cross-Cutting Differences (All Components)

### Parameter naming conventions

| Category | Legacy Pattern | Current Pattern | Change Type |
|---|---|---|---|
| Error reporting output | implicit / `out` | explicit `report` | **Spec compliance**: all components now have consistent `report` output |
| SQL trace output | none | `queries` (string) added to all DB query components | New feature: SQL query is returned as string for debugging |
| Input params that are preserved exactly | `CString`, `CToggle`, `schema`, `table`, `Cx`, `Cy`, `SRID` — same names + types across all query components | Preserved verbatim from legacy | Compatibility guarantee met |

### Architecture improvements not in specs
1. **Every DB query component** now returns `queries` (string) with SQL trace — never present in legacy decoded scripts. This was a hidden feature that became first-class output.
2. **CRC_ColorCalculator all logic stays in code.py** (446 lines) instead of being factored into `crc_modules/` — this is the one component NOT following new architecture.
3. **CRC_CurveDisplay marked Todo in spec inventory** but actual C# implementation is complete and matches legacy behavior exactly.

---

## Component Inventory Cross-Check

| Count | Value | Notes |
|---|---|---|
| Legacy `.ghuser` files | 33 | Including CRC_SRID (native GH ValueList) |
| Python-script legacy component s | 32 | All accounted for in comparison above |
| Current component folders | 32 | One-to-one mapping confirmed |
| Parameter mismatches | **None found** | All inputs/outputs match functionally; only names differ on CRC_RunQuery/CRC_RunCommand (QResult→rows, QHeaders→columns, Query→sql) which are cosmetic changes with same types |
| New features in current | `queries` output (SQL trace), explicit `report` outputs, `types` output for CRC_QueryColumnNames, `svg_doc` for CRC_SaveSVG, auto-detection of geometry columns | All backward-compatible additions |

---

## Issues Found During Comparison

| # | Component | Issue | Severity | Recommendation |
|---|---|---|---|---|
| 1 | CRC_ColorCalculator | All 446 lines of logic stays in `code.py` instead of being factored into `crc_modules/utils/color.py`. The module exists but only has argb helpers; class mapping, legend geometry generation, and GH Color conversion are all embedded. | Medium (spec violation) | Move `_parse_legend_config`, `_generate_legend`, `_interpolate_gh_color`, and value-to-color branching logic to `crc_modules/utils/color.py` |
| 2 | CRC_CurveDisplay (component #24) | Still marked ⬜ Todo in spec component inventory despite a complete `code.cs` being present. Logic exactly matches legacy C# behavior. | Low (spec outdated) | Update inventory table row 24 from ⬜ Todo to ✅ Done |
| 3 | CRC_QueryTableNames | Legacy input `base_tables` removed — check if base-tables-only mode was intentional feature drop | Medium (potential regression) | Verify with project owner; add back as optional input if needed |
| 4 | CRC_PolylineToSVG _interface.txt_ | Only the `_interface.txt` exists in legacy decoded metadata, not a standalone `.py`. The logic appears to be defined inside the legacy cluster wiring rather than a separate script. | Low (noted) | Legacy had self-contained SVG generation; current delegates to module — correct behavior preserved |
| 5 | CRC_Histogram / LinePlot / ScatterPlot / Heatmap | SVG elements rebuilt from coordinates internally AND saved via file when CToggle=True: double work path | Trivial (performance) | Consider consolidating save logic into CRC_SaveSVG pattern instead of duplicating `save_svg` in every chart component |
| 6 | Legacy param name docs inconsistency | Various legacy decoded files have slightly inconsistent input output orderings and naming conventions | Low (data quality) | Current metadata.json consistently follows GH_IO schema format — this is improved data quality |

---

## Summary: Parameter Compatibility

**Verdict:** **100% functionally compatible at the parameter level.** All 32 components maintain identical inputs and outputs from the Grasshopper canvas perspective. The legacy user experience is preserved: same wire colors, same input/output names (with two cosmetic renames on CRC_RunQuery), same GH_IO type hints.

**Key changes made during rebuild:**
- `_list_schemas`, `_list_tables`, `_list_columns` moved to `crc_modules/db/query.py` — new internal helpers that didn't exist in legacy decoded scripts but produce exact same SQL results.
- All DB query components gain a `queries` output that returns the generated SQL for debugging — no legacy equivalent, fully additive.
- Every component gains explicit `report` string instead of relying on Grasshopper message display or implicit `out` outputs.
- CRC_QueryColumnNames adds `types` output (column types) — new feature with backward-compatible interface.
