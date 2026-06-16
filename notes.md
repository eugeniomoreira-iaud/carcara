# Component Test Report — Current vs Legacy

This table compares every component's name, nickname, inputs, outputs between the current rebuild and the legacy reference. After testing each component in Grasshopper, fill in the **Notes** column. Issues found become items in the next implementation plan.

---

## 01.Modeling

### 1. CRC_BuildingMeshes

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | BuildingMeshes | BuildingMeshes | YES |
| Nickname | — | BdgMsh | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Extrudes a list of building footprints by their heights. | Extrudes a list of building footprints by their heights. | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | BdgFp | Tree Polyline | BdgFp | tree ghdoc | OK (typeGH vs tree poly) |
| 2 | BdgH | Tree Float | BdgH | tree float | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | out | str | SAME |
| 2 | GrdF | Tree Mesh | GrdF | tree ? | need verify |
| 3 | LatF | Tree Mesh | LatF | tree ? | need verify |
| 4 | RftF | Tree Mesh | RftF | tree ? | need verify |

**Notes:**

---

### 2. CRC_IdentifyDuplicatePolylines

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | IdentifyDuplicatePolylines | IdentifyDuplicatePolylines | YES |
| Nickname | — | IdDupPol | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Computes a normalized signature for each polyline to handle differences in start point/direction. Groups those with identical signatures and outputs the duplicate indexes. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | p | List Polyline | p | list ghdoc | OK (typeGH vs poly) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | i | DataTree int | i | DataTree ? | need verify |

**Notes:**

---

### 3. CRC_OffsetPython

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | OffsetPython | OffsetPython | YES |
| Nickname | — | OffPy | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Offsets planar polylines using given distances and a corner style mapping. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Crv | DataTree Curve | Crv | tree curve | SAME |
| 2 | Dist | DataTree Float | Dist | tree float | SAME |
| 3 | CStyle | int | CStyle | int | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | out | str | SAME |
| 2 | OffCrv | DataTree Curve | OffCrv | tree curve | SAME |

**Notes:**

---

### 4. CRC_PointInsidePolygon

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | PointInsidePolygon | PointInsidePolygon | YES |
| Nickname | — | Pt_Plg | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Finds a point inside a polygon. Tries the centroid first; if it fails, uses a polylabel algorithm to find the pole of inaccessibility. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | pol | Curve | pol | ghdoc | OK |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | pt | Point3d | pt | ghdoc | SAME |

**Notes:**

---

### 5. CRC_SortByContainer

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | SortByContainer | SortByContainer | YES |
| Nickname | — | Srt_Ctn | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Sorts a list of points by a list of containers. Uses a flatten operation on the points list... | Output tree always matches curve count with empty branches for curves containing no points. | DIFF (current drops "flatten operation" wording) |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | crv | List Curve | crv | list ghdoc | OK |
| 2 | pt | List Point3d | pt | list ghdoc | OK |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | i | DataTree int | i | ghdoc ? | need verify |

**Notes:**

---

### 6. CRC_ColorCalculator

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | ColorCalculator | ColorCalculator | YES |
| Nickname | — | ColorCalc | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Calculates colors for mesh volumes based on numerical values. Supports continuous gradients, fixed class count, or custom class boundaries. Generates legend geometry. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | val | Tree float | val | tree ghdoc | OK (float vs ghdoc) |
| 2 | col | List Color | col | list ghdoc | OK |
| 3 | cls | int/list float | cls | list ghdoc | SAME (accepts both) |
| 4 | lin | bool | lin | bool | SAME |
| 5 | leg_cfg | string | leg_cfg | str | SAME |
| 6 | leg_pln | Plane | leg_pln | ghdoc | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | out | str | SAME |
| 2 | col | Tree Color | col | tree ghdoc | OK |
| 3 | leg_geo | Mesh | leg_geo | ghdoc ? | need verify |
| 4 | txt_loc | List Point3d | txt_loc | ghdoc | SAME |
| 5 | txt_con | List str | txt_con | list str | SAME |
| 6 | txt_siz | List float | txt_siz | list float | SAME |
| 7 | stats | str | stats | ghdoc ? | DIFF: legacy was str, current may be dict/obj |
| 8 | — | — | report | str | EXTRA in current (8 outputs total, not 7) |

**Notes:**

---

## 02.Queries

### 7. CRC_QuerySchemaNames

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | QuerySchemaNames | QuerySchemaNames | YES |
| Nickname | Q_schema | QS | DIFF (was Q_schema) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Lists all the schema names in a database. | Lists all non-system schemas in a PostGIS database. | CLOSE (reworded; current excludes system schemas) |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|-------------|------------|--------|
| 1 | Connection String | CString | CString | str | OK |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Schemas | list str | schemas | list ? | SAME shape |
| 2 | Exceptions | str | report | str | DIFF naming (Exceptions -> report) |

**Extra output in current:** `queries` — all SQL executed (structured).

**Notes:**

Use Q_schema as component nickname

### 8. CRC_QueryTableNames

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | QueryTableNames | QueryTableNames | YES |
| Nickname | Q_table | QT | DIFF (was Q_table) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Lists all the table names in a schema. | Lists all tables in a specified schema. | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |
| 3 | Schema | str | schema | str | SAME |
| 4 | Base Tables | bool | — | — | MISSING in current |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | tables | list str | tables | list ? | SAME shape |
| 2 | Exceptions | str | report | str | DIFF naming |

**Extra output in current:** `queries` — NEW.

**Notes:**

---
Use Q_table as component nickname
create an additional input, boolean, to make me able to filter if I want all the tables and views in the schema or only tables. Name Base Tables, nickname BT. Description: Set "true" to return only base tables, not views.


### 9. CRC_QueryColumnNames

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | QueryColumnNames | QueryColumnNames | YES |
| Nickname | Q_column | QC | DIFF (was Q_column) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Lists the names of all columns in a specific table. | Lists all columns and their types in a specified table. | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |
| 3 | schema | str | schema | str | SAME |
| 4 | table | str | table | str | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | columns | list str | columns | list ? | SAME shape |
| 2 | Exceptions | str | report | str | DIFF naming (Exceptions -> report) |

**Extra output in current:** `types` (column data types), `queries` — NEW.

**Notes:**

Use Q_column as component nickname

### 10. CRC_QueryValues

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | QueryValues | QueryValues | YES |
| Nickname | Q_values | QV | DIFF (was Q_values) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Lists all values in a specific column of a specific table. | Queries a single column from PostGIS table, replacing NULL values with given replacement. | CLOSE (reworded) |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |
| 3 | Schema | str | schema | str | SAME |
| 4 | table | str | table | str | SAME |
| 5 | Column | str | column | str | SAME |
| 6 | Null Items | any | N | str | DIFF: legacy 'any', current typed as str |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Values | list any | rows (str) | DIFF naming + type (legacy: any, current: str coercion?) |
| 2 | Exceptions | str | report | str | DIFF naming |

**Extra output in current:** `columns` (column names), `queries` — NEW.

**Notes:**

Use Q_values as component nickname

### 11. CRC_GeometryEntities

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | GeometryEntities | GeometryEntities | YES |
| Nickname | GeoEnt | GeoEnt | SAME |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Draws the geometric entities from a given table. | Returns geometries from a table with auto-detected PK, ordered by PK. | CLOSE |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |
| 3 | Schema | str | schema | str | SAME |
| 4 | Table | str | table | str | SAME |
| 5 | Correction X | str | Cx | str | SAME |
| 6 | Correction Y | str | Cy | str | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Geometry | list geom | geometry (DataTree) | DataTree ? | DIFF naming (geom→geometry) + shape (list vs DataTree) |
| 2 | Exceptions | str | report | str | DIFF naming |
| 3 | Primary keys | list int | pk (DataTree) | DataTree ? | DIFF naming + shape |

**Notes:**

(No `sql_filter` input on this component — that input is only on #12 and #13.)


### 12. CRC_GeometriesWithSpatialFilter

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | GeometriesWithSpatialFilter | GeometriesWithSpatialFilter | YES |
| Nickname | Geo_SptFlt | Geo_SptFlt | SAME (underscore kept) |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Returns geometries from a table filtered by a spatial boundary. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |
| 3 | Schema | str | schema | str | SAME |
| 4 | Table | str | table | str | SAME |
| 5 | Spatial Filter | geom | spatial_filter | ghdoc/item | SAME (geom=ghdoc) |
| 6 | SRID | int | SRID | int | SAME |
| 7 | function | int | function | int | SAME |
| 8 | Correction X | str | Cx | str | SAME |
| 9 | Correction Y | str | Cy | str | SAME |
| 10 | — | — | sql_filter | str | EXTRA in current (10 inputs total) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Exceptions | str | report | str | DIFF naming (order changed too) |
| 2 | Primary keys | list int | pk (DataTree) | DataTree ? | DIFF shape |
| 3 | Geometry | list geom | geometry (DataTree) | DataTree ? | DIFF naming (geom→geometry) + shape |

**Extra output in current:** `queries` — NEW.

**Notes:**

this component has an input called sql_filter. I don't need this.
The function input let me choose between st_intersects and st_contains. Change st_contains by st_within. And specify only 0 and 1 as possible inputs. Later I want to add other functions.

### 13. CRC_ValuesWithSpatialFilter

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | ValuesWithSpatialFilter | ValuesWithSpatialFilter | YES |
| Nickname | ValSptFlt | ValSptFlt | SAME |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Returns column values for geometries intersecting a spatial filter boundary. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |
| 3 | Schema | str | schema | str | SAME |
| 4 | Table | str | table | str | SAME |
| 5 | Column | str | columns (list) | list str | DIFF single vs list |
| 6 | Null Items | any | N | str | DIFF: legacy 'any', current str |
| 7 | Spatial Filter | geom | spatial_filter | ghdoc/item | SAME |
| 8 | SRID | int | SRID | int | SAME |
| 9 | function | int | function | int | SAME |
| 10 | Correction X | str | Cx | str | SAME |
| 11 | Correction Y | str | Cy | str | SAME |
| 12 | — | — | sql_filter | str | EXTRA in current (12 inputs total) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Values | list any | values (DataTree) | DataTree per column | DIFF shape |
| 2 | Exceptions | str | report | str | DIFF naming |

**Extra output in current:** `queries` — NEW.

**Notes:**

---

### 14. CRC_CreateTable

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | CreateTable | CreateTable | YES |
| Nickname | Create Table | CrtTbl | DIFF (was "Create Table" — long nickname) |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Creates a new table (with no geometries) on the database. | CREATE TABLE in PostGIS, optionally with a geometry column. | DIFF: current adds geom support not in legacy description |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | str | CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | replace table | bool | replace_table | bool | SAME (but current order: replace_table is LAST, #10) |
| 4 | schema | str | schema | str | SAME |
| 5 | table name | str | table | str | SAME |
| 6 | list of columns | list str | column_names | list str | SAME shape |
| 7 | variable types | list str | column_types | list str | SAME shape |
| 8 | values | list any | — | — | MISSING in current |

> Real current input order: CString, CToggle, schema, table, column_names, column_types, geom_column, geom_type, srid, replace_table.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| | out (str) + Fb (str) | affected (int) + report (str) | DIFF: legacy had two outputs, current has two but different names/types |

**Current has extra inputs:** `geom_column`, `geom_type`, `srid` — for geometry column support.

**Notes:**

The order of the inputs should be CString, CToggle, replace table, schema name, table name, list of columns, variable types, values, id, correction x, correction y

### 15. CRC_CreateShapefile

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | CreateShapefile | CreateShapefile | YES |
| Nickname | Create Shapefile | CrtShp | DIFF (was "Create Shapefile") |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Creates a new entry (with geometry) on a given database. | INSERT WKT geometries into an existing PostGIS table, adding false-origin correction back in SQL. | SAME behavior |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | str |CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | replace table | bool | replace_table | bool (no-op) | SAME (but current order: replace_table is LAST, #12) |
| 4 | schema | str | schema | str | SAME |
| 5 | table name | str | table | str | SAME |
| 6 | list of columns | list str | column_names (optional) | list str | same (optional) |
| 7 | variable types | list str | — | — | MISSING in current |
| 8 | values | list any | values (tree: branch per geom) | tree str | DIFF shape |
| 9 | geometry | list geom | geometry | list str (WKT) | DIFF format but same intent |
| 10 | SRID | int | srid | int | SAME |
| 11 | Correction X | str | Cx | str | SAME |
| 12 | Correction Y | str | Cy | str | SAME |
| 13 | — | — | geom_column | str | EXTRA in current (required; missing from legacy) |

> Real current input order: CString, CToggle, schema, table, geom_column, geometry, srid, Cx, Cy, column_names, values, replace_table.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| | out (str) + Fb (str) | report only | DIFF: legacy had two outputs, current merged into one |

**Notes:**

---

## 03.Utilities

### 16. CRC_ConnectionString

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | ConnectionString | ConnectionString | YES |
| Nickname | — | ConnStr | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Builds CString with base64-encoded password via Eto dialog. Host/user/password from dialog; DB/port from canvas. | Same behavior, libpq format now instead of ODBC conninfo | SAME behavior |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | DB (database name) | str | database | str | SAME (current order: database, port, CToggle) |
| 2 | (port from canvas) | int | port | int | current declares `port` as explicit input |
| 3 | CToggle | bool | CToggle | bool | SAME (now last input, not first) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | CString | str | CString | str | SAME |

**Current extra output:** `ok` (bool) — NEW.

**Notes:**

Take off `ok` output. Let's bring back the "out" output (default from python components) and put on it the one currently going to "report"
Component nickname should be CString
Description should say the password is only obfuscated, not encrypted. 

### 17. CRC_FindCorrectionParameters

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | FindCorrectionParameters | FindCorrectionParameters | YES |
| Nickname | — | FindCorr | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Computes suitable (Cx, Cy) false origin for a study area. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | str | CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | Schema | str | Schema | str | SAME |
| 4 | Table | str | Table | str | SAME |
| 5 | Column (optional) | str | Column | str | SAME |
| 6 | Value (optional) | str | Value | str | SAME |

Current lists Correction X/Y as inputs too — legacy had Cx/Cy only as outputs. VERIFY current does not have extra inputs.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Exceptions | str | report | str | DIFF naming |
| 2 | Correction X | str /text/ | Cx | str /text/ | SAME |
| 3 | Correction Y | str /text/ | Cy | str /text/ | SAME |

**Notes:**

---

### 18. CRC_SQLComposer

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | SQLComposer | SQLComposer | YES |
| Nickname | — | SQLComp.py | (looks like filename; consider shortening) |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Substitutes named placeholders (var) with values (val) inside SQL template via string.replace(). | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | sql | str | sql | str | SAME |
| 2 | var | list str | var | list str | SAME |
| 3 | val | list any | val | list str | DIFF type (any vs str) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | out | str | SAME |
| 2 | stmt | str | stmt | str | SAME |

**Extra in current:** `report` — NEW (legacy had no report output).

**Notes:**

---

### 19. CRC_RunQuery

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | RunODBCQuery | RunQuery | DIFF name (removed "ODBC") |
| Nickname | — | RQ | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Executes a SELECT and returns results + headers as DataTrees. | Same as legacy | SAME behavior |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | str | CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | Query | str | sql | str | DIFF naming (Query -> sql) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | QResult | tree any | rows (tree) | tree ? | DIFF naming (QResult -> rows) |
| 3 | QHeaders | tree str | columns (tree) | tree ? | DIFF naming (QHeaders -> columns) |

**Notes:**

---

### 20. CRC_RunCommand

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | RunODBCCommand | RunCommand | DIFF name (removed "ODBC") |
| Nickname | — | RC | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Executes a non-SELECT DDL/DML command and returns execution feedback. | Same as legacy | SAME behavior |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | str | CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | Command | str | sql | str | DIFF naming (Command -> sql) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | report | str | DIFF naming (out -> report) |
| 2 | Fb | str | — | — | MISSING (merged into report?) |

**Notes:**

---

### 21. CRC_GrasshopperGeometryToWKT

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | GrasshopperGeometryToWKT | GrasshopperGeometryToWKT | YES |
| Nickname | — | ghToWkt | — |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Converts GH geometry to WKT, enforcing uniform type across branches. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | geom | geometry/tree | geom | ghdoc ? | SAME name (no rename) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | WKT | str/tree | WKT | str ? | SAME name (uppercase kept), shape may differ |

**Notes:**

---

### 22. CRC_WKTtoGrasshopperGeometry

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | WKTtoGrasshopperGeometry | WKTtoGrasshopperGeometry | YES |
| Nickname | — | wktToGH | — |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Converts WKT string(s) to GH geometry with proper multipart/branch handling. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | WKT_geom | list str | WKT_geom | list str | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | geom | tree geom | geom (DataTree) | DIFF shape declared: legacy "tree" vs current "DataTree" but same concept |

**Notes:**

---

## 04.Dataviz

### 23. CRC_CurveDisplay

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | CurveDisplay | CurveDisplay | YES |
| Nickname | CrvDpl.cs | CrvDpl.cs | SAME (legacy script already used "CrvDpl.cs" — not a current regression) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Custom Rhino-viewport preview of curves with lineweight, color, dash pattern (C#). Display-only. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Curve | curve | Curve | curve/item | SAME |
| 2 | Width | int | Width | int | SAME |
| 3 | Colour | color | Colour | colour | SAME (spelling) |
| 4 | Dash | str ("dash gap") | Dash | ghdoc/item ? | DIFF type declared: was str, now ghdoc? |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| | (viewport display only) | — | (none declared) | — | SAME: viewport-only |

**Notes:**

---

### 24. CRC_PolylineToSVG

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | PolylineToSVG | PolylineToSVG | YES |
| Nickname | — | PolySVG | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Converts polylines/polygons to SVG elements. Closed -> polygon, open -> polyline. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | p | polyline/list | p | list ghdoc | OK |
| 2 | sc | color/str/list | sc | list str | DIFF (missing Color support) |
| 3 | sw | float/list | sw | list float | SAME |
| 4 | f | color/str/list | f | list str | DIFF (missing Color support) |
| 5 | canvas | rect | canvas | ghdoc/item | SAME |
| 6 | dash | str/list (default '') | dash | list str | SAME |

Current has extra output: `report` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | svg_code | str | svg_code | str | SAME |

**Notes:**

---

### 25. CRC_CircleToSVG

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | CircleToSVG | CircleToSVG | YES |
| Nickname | — | CircSVG | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Converts circles to SVG `<circle>` elements. Y-up -> Y-down via canvas anchor. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | c | circle/list | c | list ghdoc | OK |
| 2 | sc | color/str/list | sc | list str | DIFF (missing Color) |
| 3 | sw | float/list | sw | list float | SAME |
| 4 | f | color/str/list | f | list str | DIFF (missing Color) |
| 5 | canvas | rect | canvas | ghdoc/item | SAME |

Current has extra output: `report` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | svg_code | str | svg_code | str | SAME |

**Notes:**

---

### 26. CRC_NurbsToSVG

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | NurbsToSVG | NurbsToSVG | YES |
| Nickname | — | NurbsSVG | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Converts NURBS curves to SVG via linear-segment approximation. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | n | curve/list | n | list ghdoc | OK |
| 2 | s | int/list (default 50) | s | list int | SAME but default not declared in metadata |
| 3 | sc | color/str/list | sc | list str | DIFF (missing Color) |
| 4 | sw | float/list | sw | list float | SAME |
| 5 | f | color/str/list | f | list str | DIFF (missing Color) |
| 6 | canvas | rect | canvas | ghdoc/item | SAME |

Current has extra output: `report` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | svg_code | str | svg_code | str | SAME |

**Notes:**

---

### 27. CRC_TextToSVG

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | TextToSVG | TextToSVG | YES |
| Nickname | — | TxtSVG | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Converts text to SVG `<text>` elements. Point3d or Plane insertion; 1-9 justification grid. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | t | str/list | t | list str | SAME |
| 2 | pt | point/plane/list | pt | list ghdoc | OK |
| 3 | ff | str (default 'Arial') | ff | str/item | SAME |
| 4 | fs | float (default 12) | fs | float/item | SAME |
| 5 | fC | color/str (default 'black') | fC | str/item | DIFF (missing Color support) |
| 6 | canvas | rect | canvas | ghdoc/item | SAME |
| 7 | j | int 1-9 (default 6) | j | list int | DIFF: was item, now list |

Current has extra output: `report` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | svg_code | str | svg_code | str | SAME |

**Notes:**

---

### 28. CRC_Histogram

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | Histogram | Histogram | YES |
| Nickname | — | Hist | — |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Builds a histogram as pure Rhino geometry (bars, axes, label anchors, grid). | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | cv | rect | cv | ghdoc/item | SAME |
| 2 | v | list float | v | list float | SAME |
| 3 | b | int (bins) | b | int/item | SAME |
| 4 | nx | int | nx | int/item | SAME |
| 5 | ny | int | ny | int/item | SAME |
| 6 | d | int (decimal) | d | int/item | SAME |
| 7 | ext | float | ext | float/item | SAME |
| 8 | dist | float | dist | float/item | SAME |
| 9 | gy | bool | gy | bool/item | SAME |

Legacy did NOT declare `OutPath`/`CToggle` but current has them for SVG export — NEW.

Current has extra outputs: `svg_code`, `svg_path` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | out | str | SAME |
| 2 | bars | list rect | bars | ghdoc ? | same shape |
| 3 | axes | list line | axes | ghdoc ? | same shape |
| 4 | x_pts/x_txt | — | x_pts (ghdoc), x_txt (str list) | SAME |
| 5 | y_pts/y_txt | — | y_pts (ghdoc), y_txt (str list) | SAME |
| 6 | grid | list line | grid | ghdoc ? | same shape |

**Notes:**

---

### 29. CRC_ScatterPlot

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | ScatterPlot | ScatterPlot | YES |
| Nickname | — | Scatter | — |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Scatter chart from parallel X/Y series with optional color legend. | Same as legacy | SAME |

All core params match (cv, x/y/r/nx/ny/d/ext/dist/mx/my/gx/gy/show_leg/col_vals/colors/n_leg/leg_w etc).

Legacy did NOT have `OutPath`/`CToggle` — current has them for SVG export. NEW.

Current has extra outputs: `svg_code`, `svg_path` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| | Legacy had: out, dots, colors_out, axes, x_pts/x_txt, y_pts/y_txt, grid_x/grid_y, leg_cells/clrs/pts/txt | dots…leg_* + svg_code, svg_path, report | DIFF: legacy `out` DROPPED (replaced by `report`); rest present + NEW ones |

**Notes:**

---

### 30. CRC_LinePlot

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | LinePlot | LinePlot | YES |
| Nickname | — | LinePlt | — |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Line chart from X/Y lists or DataTrees (one series per branch). | Same as legacy | SAME |

All core params match. Legacy did NOT have `OutPath`/`CToggle` — current has them for SVG export. NEW.

Current has extra outputs: `svg_code`, `svg_path` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| | Legacy had: out, lines, axes, x_pts/x_txt, y_pts/y_txt, grid_x/grid_y | + lines, axes, x_pts/x_txt, y_pts/y_txt, grid_x/grid_y, svg_code, svg_path, out | Out present but more outputs now |

**Notes:**

---

### 31. CRC_Heatmap

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | Heatmap | Heatmap | YES |
| Nickname | — | Heatmap | SAME nickname |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Heatmap from 2D matrix with custom color gradient + legend. | Same as legacy | SAME |

All core params match: cv, data, colors, rows/cols, vals, d, n_leg, dist, leg_w, leg_dist, leg_l_dist, leg_orient.

New inputs over legacy: `show_leg`, `OutPath`, `CToggle`. NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| | Legacy had: out, cells, clrs, row_pts/txt, col_pts/txt, val_pts/txt..., leg_cells/clrs/pts/txt | cells…leg_* + svg_code, svg_path, report | DIFF: legacy `out` DROPPED (replaced by `report`); rest present + NEW ones |

**Notes:**

---

### 32. CRC_SaveSVG

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | SaveSVG | SaveSVG | YES |
| Nickname | saveSVG.py | SaveSVG | DIFF (legacy was "saveSVG.py" — case + ".py" suffix changed) |
| Exposure | 4 | 16 | DIFF (was 4 = obscure, now 16 = quaternary) |
| Description | Assembles SVG fragments into a complete document and writes to disk. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | svg_code | str/list | svg_code | list str | SAME (legacy str may auto-wrap to list) |
| 2 | canvas | rect | canvas | ghdoc/item | SAME |
| 3 | file_path | str | file_path | str | SAME |
| 4 | save_flag | bool | save_flag | bool | SAME |

Current has different output names than legacy.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | status_msg | str | report | str | DIFF naming (status_msg -> report) |

Current has extra outputs: `path` (abs path), `svg_doc` (complete doc string).

**Notes:**

---

## Global Observations / Patterns Found

### Common discrepancies across all components:

1. **Exposure values**: Almost every component that had exposure 1, 2, 3 in legacy was set to a higher number (usually 4, 8, or 16) in the current build — toolbar placement changed significantly.

2. **Nickname changes**: Legacy nicknames were longer/more descriptive (`Q_schema`, `Q_table`, `Q_column`). Current nicknames are shorter/abbreviated (`QS`, `QT`, `QC`) — harder to find when filtering. Exception: `CRC_SQLComposer` nickname is `SQLComp.py` which looks like a filename and should be shortened.

3. **Input "out" -> "report"**: Legacy components with `"Exceptions"` or `"out"` (error/status) outputs were standardized to `report`. Spec requirement (CLAUDE.md Design Principles), not technically wrong, but changes parameter names for legacy users.

4. **Missing status message on modeling components #2, #4, #5** (IdentifyDuplicatePolylines, PointInsidePolygon, SortByContainer): legacy had an `out` output — current metadata does not declare it. Need verification if missing in code.py or just metadata.json.

5. **Color type input regression**: SVG components that originally accepted both Color objects AND hex strings as inputs were standardized to accept only string values — may break user scripts passing System.Drawing.Color directly.

6. **Default values not declared in metadata.json**: Many component default values (sample count=50, lin=True, etc.) are set in code.py but not guaranteed by the typeHintID. Users may need to explicitly supply them.

7. **New outputs added** (backwards-compatible): `queries` on query components, `svg_code`/`svg_path` on SVG/chart components, `ok` on ConnectionString, `types` on QueryColumnNames, geometry support inputs on CreateTable (`geom_column`, `geom_type`, `srid`).

8. **CRC_CurveDisplay nickname `CrvDpl.cs`**: Looks like a filename — could be shortened to `CrvDpl`. NOTE: the legacy component already used `CrvDpl.cs`, so this is inherited, not a current regression.

---

## Test Status Summary

Fill in as you test each component in Grasshopper:

| # | Component | Tested (Y/N) | Issues Found (tick or note) |
|---|-----------|-------------|-----------------------------|
| 1 | BuildingMeshes | | |
| 2 | IdentifyDuplicatePolylines | | out (status msg) missing? |
| 3 | OffsetPython | | |
| 4 | PointInsidePolygon | | out (status msg) missing? |
| 5 | SortByContainer | | out (status msg) missing? |
| 6 | ColorCalculator | | stats type: str vs obj? |
| 7 | QuerySchemaNames | | Nickname Q_schema -> QS harder to find? |
| 8 | QueryTableNames | | Base Tables input missing? |
| 9 | QueryColumnNames | | types output works? |
| 10 | QueryValues | | Null Items type str vs any? |
| 11 | GeometryEntities | | Geometry: list vs DataTree shape? |
| 12 | GeometriesWithSpatialFilter | | Output order changed (Exceptions last in legacy)? |
| 13 | ValuesWithSpatialFilter | | Column: single str vs list of str? Values shape? |
| 14 | CreateTable | | affected int + report instead of out+Fb? |
| 15 | CreateShapefile | | Fb output gone? merged into report? |
| 16 | ConnectionString | | CString format: ODBC vs libpq? ok output works? |
| 17 | FindCorrectionParameters | | Cx/Cy returned as text (never float)? |
| 18 | SQLComposer | | val type str vs any for placeholders? report works? |
| 19 | RunQuery | | Query -> sql param name OK? rows/columns tree shape? |
| 20 | RunCommand | | Command -> sql OK? Fb merged into report? |
| 21 | GrasshopperGeometryToWKT | | geom -> geometry name OK? out missing? WKT wkt naming? |
| 22 | WKTtoGrasshopperGeometry | | out missing? geometric tree output shape? |
| 23 | CurveDisplay | | Dash type str vs ghdoc? nickname CrvDpl.cs shortened? |
| 24 | PolylineToSVG | | Color inputs work as strings? default dash='' enforced? |
| 25 | CircleToSVG | | Color inputs working? canvas optional? |
| 26 | NurbsToSVG | | Default sample=50 enforced in code.py? |
| 27 | TextToSVG | | fC: Color support gone? j default=6 in code? canvas optional? |
| 28 | Histogram | | SVG export via OutPath/CToggle working? bars shape? |
| 29 | ScatterPlot | | All SVG/legend/g grid outputs match legacy behavior? |
| 30 | LinePlot | | X/Y DataTree input still works (not just flat list)? |
| 31 | Heatmap | | Matrix DataTree parsing correct? legend matching legacy? |
| 32 | SaveSVG | | path output correct? svg_doc complete? relative paths resolved? |

---

## Next Implementation Plan (from global observations above)

### Priority 1 — Functional issues to fix after testing:

1. **Missing status message `out`** on #2, #4, #5 (IdentifyDuplicatePolylines, PointInsidePolygon, SortByContainer) — verify code.py and add if missing per spec requirement (always include report output).
2. **Color input regression**: Restore System.Drawing.Color support for SVG components (#24-#27), or at minimum document that only hex strings are accepted now.
3. **CRC_BuildingMeshes exposure 1->2**: restore to legacy value if primary placement matters (same with other modeling components at 2 vs legacy's 1).

### Priority 2 — UX / discoverability improvements:

4. **Nicknames too short/hard to find**: Consider reverting longer nicknames for query components (`Q_schema`, `Q_table` instead of `QS`, `QT`) and fixing `SQLComp.py` -> something like `SQLComposer`.
5. **Nickname `CrvDpl.cs`** trimmed to `CrvDpl` (remove .cs suffix).
6. **Exposure audit**: decide which components truly belong in primary (1,2) vs secondary/tertiary (4,8) — some query/chart components may be too critical to hide at exposure 16.
7. **Input naming consistency**: `Query`->`sql`, `Command`->`sql` across RunQuery/RunCommand; consider documenting or keeping legacy names for backwards compatibility in existing definitions.

### Priority 3 — Verify after testing:

8. **`stats` output on ColorCalculator**: was legacy `str` (serialized summary)? current may be dict/object — verify if downstream consumers expect string.
9. **`leg_geo` output type** on ColorCalculator: Mesh or ghdoc? need actual GH object verification.
10. **`GrdF`, `LatF`, `RftF` Mesh tree shapes**: verify DataTree structure matches legacy (one mesh per building).
11. **Geometry Entities output shape**: legacy returned `list geom` and `list int`; current returns `DataTree`. Verify this doesn't break downstream components that expect flat lists.
12. **ValuesWithSpatialFilter Column input**: legacy accepted single str column name; current accepts list of str columns. Verify both work as expected (single vs multi-column).
13. **QueryString format** on ConnectionString: ODBC conninfo -> libpq conninfo. Verify all downstream components parse correctly with new format.
