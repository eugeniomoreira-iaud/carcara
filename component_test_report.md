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
| Description | Offsets planar polylines using given distances and a corner style mapping. | Offsets planar polylines using given distances and a corner style mapping. | SAME |

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
| Description | Sorts a list of points by a list of containers. Uses a flatten operation on the points list... | Same as legacy | SAME |

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

**Notes:**

---

## 02.Queries

### 7. CRC_QuerySchemaNames

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | QuerySchemaNames | QuerySchemaNames | YES |
| Nickname | Q_schema | QS | DIFF (was Q_schema) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Lists all the schema names in a database. | Lists all non-system schemas in a PostGIS database. | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME (typeGH=str) |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Schemas | list str | schemas | list ? | SAME shape |
| 2 | Exceptions | str | report | str | DIFF naming (Exceptions -> report) |

**Extra output in current:** `queries` — all SQL executed (structured) — NEW, not in legacy.

**Notes:**

---

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
| 1 | columns | list str | columns | list ? | SAME |
| 2 | Exceptions | str | report | str | DIFF naming (Exceptions -> report) |

**Extra output in current:** `types` (list of column data types), `queries` — NEW.

**Notes:**

---

### 10. CRC_QueryValues

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | QueryValues | QueryValues | YES |
| Nickname | Q_values | QV | DIFF (was Q_values) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Lists all values in a specific column of a specific table. | Queries a single column from a PostGIS table, replacing NULL values with a given replacement. | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Connection String | CString | CString | str | SAME |
| 2 | Connection Toggle | CToggle bool | CToggle | bool | SAME |
| 3 | Schema | str | schema | str | SAME |
| 4 | table | str | table | str | SAME |
| 5 | Column | str | column | str | SAME |
| 6 | Null Items | any | N | str | DIFF: legacy was flexible 'any', current typed as str |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Values | list any | rows | list? (str) | DIFF naming + type (legacy: any, current: str coercion?) |
| 2 | Exceptions | str | report | str | DIFF naming |

**Extra output in current:** `columns` (column names), `queries` — NEW.

**Notes:**

---

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
| 1 | Geometry | list geom | geom (DataTree) | DataTree ? | DIFF shape (list vs DataTree) |
| 2 | Exceptions | str | report | str | DIFF naming |
| 3 | Primary keys | list int | pk (DataTree) | DataTree ? | DIFF naming + shape |

**Notes:**

---

### 12. CRC_GeometriesWithSpatialFilter

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | GeometriesWithSpatialFilter | GeometriesWithSpatialFilter | YES |
| Nickname | Geo_SptFlt | GeoSptFlt | DIFF (was Geo_SptFlt) |
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

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Exceptions | str | report | str | DIFF naming (order changed too) |
| 2 | Primary keys | list int | pk (DataTree) | DataTree ? | DIFF shape |
| 3 | Geometry | list geom | geom (DataTree) | DataTree ? | DIFF shape |

**Extra output in current:** `queries` — NEW.

**Notes:**

---

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
| Nickname | Create Table | CrtTbl | DIFF (was Create Table, long nickname) |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Creates a new table (with no geometries) on the database. | CREATE TABLE in PostGIS, optionally with a geometry column. | DIFF: current adds geom support not in legacy description |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | CString | CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | replace table | bool | replace_table | bool | SAME |
| 4 | schema | str | schema | str | SAME |
| 5 | table name | str | table | str | SAME |
| 6 | list of columns | list str | column_names | list str | SAME shape |
| 7 | variable types | list str | column_types | list str | SAME shape |
| 8 | values | list any | — | — | MISSING in current |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| | out | str | affected (int) + report (str) | DIFF: legacy single out, current split into affected + report | 

**Current has extra inputs:** `geom_column`, `geom_type`, `srid` — for geometry column support.

**Notes:**

---

### 15. CRC_CreateShapefile

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | CreateShapefile | CreateShapefile | YES |
| Nickname | Create Shapefile | CrtShp | DIFF (was Create Shapefile) |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Creates a new entry (with geometry) on a given database. | INSERT WKT geometries into an existing PostGIS table, adding the false-origin correction back in SQL. | SAME behavior |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | CString | CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | replace table | bool | replace_table | bool | SAME (no-op) |
| 4 | schema | str | schema | str | SAME |
| 5 | table name | str | table | str |SAME |
| 6 | list of columns | list str | column_names (optional) | list str | same (optional) |
| 7 | variable types | list str | — | — | MISSING in current |
| 8 | values | list any | values (tree: branch per geom) | tree str | DIFF shape |
| 9 | geometry | list geom | geometry | list str (WKT) | DIFF format but same intent |
| 10 | SRID | int | srid | int | SAME |
| 11 | Correction X | str | Cx | str | SAME |
| 12 | Correction Y | str | Cy | str | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | report | str | DIFF naming (out -> report only) |
| 2 | Fb | str | — | — | MISSING in current |

**Notes:**

---

## 03.Utilities

### 16. CRC_ConnectionString

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | ConnectionString | ConnectionString | YES |
| Nickname | — | ConnStr | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Builds the connection string CString that carries the base64-encoded password from the DB connection parameters. Shows an Eto dialog to collect host/user/password; database and port come from canvas inputs. | Same as legacy, describes libpq format now | SAME behavior |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CToggle | bool | CToggle | bool | SAME |
| 2 | DB | str (database name) | database | str | SAME |
| (implicit) | host/user/password via Eto dialog | — | Same | — | SAME |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | CString | str | CString | str | SAME |

**Current has extra output:** `ok` (bool if connection test succeeded) — NEW.

**Notes:**

---

### 17. CRC_FindCorrectionParameters

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | FindCorrectionParameters | FindCorrectionParameters | YES |
| Nickname | — | FindCorr | — |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Computes a suitable (Cx, Cy) coordinate-correction false origin for a study area. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | CString | str | CString | str | SAME |
| 2 | CToggle | bool | CToggle | bool | SAME |
| 3 | Schema | str | Schema | str | SAME |
| 4 | Table | str | Table | str | SAME |
| 5 | Column | str (optional) | Column | str | SAME |
| 6 | Value | str (optional) | Value | str | SAME |

Current lists Correction X/Y as inputs too — legacy had Cx/Cy only as outputs → CHECK IF current has extra inputs.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | Exceptions | str | report | str | DIFF naming (Exceptions -> report) |
| 2 | Correction X | str | Cx | str | SAME |
| 3 | Correction Y | str | Cy | str | SAME |

**Notes:**

---

### 18. CRC_SQLComposer

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | SQLComposer | SQLComposer | YES |
| Nickname | — | SQLComp.py | — |
| Exposure | 2 | 4 | DIFF (was 2) |
| Description | Substitutes named placeholders (var) with values (val) inside a SQL template string. | Same as legacy | SAME |

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
| Name | RunODBCQuery | RunQuery | DIFF name (legacy: RunODBCQuery, current: RunQuery) |
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
| Name | RunODBCCommand | RunCommand | DIFF name |
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
| Nickname | — | GH2WKT | — |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Converts GH geometry to WKT, enforcing uniform type across branches. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | geom | geometry/tree | geometry | ghdoc ? | DIFF naming (geom -> geometry) |

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | WKT | str/tree | wkt | str ? | DIFF naming (WKT -> wkt), may be different shape |

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
| 2 | geom | tree geom | geom | DataTree ? | DIFF shape (legacy: tree, current: DataTree) |

**Notes:**

---

## 04.Dataviz

### 23. CRC_CurveDisplay

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | CurveDisplay | CurveDisplay | YES |
| Nickname | — | CrvDpl.cs | — (C# script) |
| Exposure | 1 | 2 | DIFF (was 1) |
| Description | Custom Rhino-viewport preview of curves with lineweight, color, and dash pattern (C#). Display-only. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | Curve | curve | Curve | curve/item | SAME |
| 2 | Width | int | Width | int | SAME |
| 3 | Colour | color | Colour | colour | SAME (spelling) |
| 4 | Dash | str ("dash gap") | Dash | ghdoc/item ? | DIFF type (was str, now ghdoc?) |

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
| Description | Converts polylines/polygons to SVG <polyline>/<polygon> elements. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | p | polyline/list | p | list ghdoc | OK (polyline=ghdoc) |
| 2 | sc | color/str/list | sc | list str | DIFF (missing color, has list) |
| 3 | sw | float/list | sw | list float | SAME |
| 4 | f | color/str/list | f | list str | DIFF |
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
| Description | Converts circles to SVG <circle> elements. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | c | circle/list | c | list ghdoc | OK |
| 2 | sc | color/str/list | sc | list str | DIFF |
| 3 | sw | float/list | sw | list float | SAME |
| 4 | f | color/str/list | f | list str | DIFF |
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
| Description | Converts NURBS curves to SVG <path> elements via linear-segment approximation. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | n | curve/list | n | list ghdoc | OK |
| 2 | s | int/list (default 50) | s | list int | SAME (but legacy default not declared in current?) |
| 3 | sc | color/str/list | sc | list str | DIFF |
| 4 | sw | float/list | sw | list float | SAME |
| 5 | f | color/str/list | f | list str | DIFF |
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
| Description | Converts text to SVG <text> elements; Point3d or Plane insertion. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | t | str/list | t | list str | SAME |
| 2 | pt | point/plane/list | pt | list ghdoc | OK |
| 3 | ff | str (default 'Arial') | ff | str/item | SAME |
| 4 | fs | float (default 12) | fs | float/item | SAME |
| 5 | fC | color/str (default 'black') | fC | str/item | DIFF (color stripped) |
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
| (legacy has no OutPath/CToggle) | — | — | OutPath (str), CToggle (bool) | NEW inputs for SVG export |

Current has extra outputs: `svg_code`, `svg_path` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | out | str | SAME |
| 2 | bars | list rect | bars | ghdoc ? | same shape |
| 3 | axes | list line | axes | ghdoc ? | same shape |
| 4 | x_pts/x_txt | — | x_pts (ghdoc), x_txt (list str) | same shape | SAME |
| 5 | y_pts/y_txt | — | y_pts (ghdoc), y_txt (list str) | same shape | SAME |
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

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | cv | rect | cv | ghdoc/item | SAME |
| 2 | x | list num | x | list float | SAME (num=float) |
| 3 | y | list num | y | list float | SAME |
| 4 | r | float/list (default 2.0) | r | list float | SAME |
| 5 | nx | int | nx | int/item | SAME |
| 6 | ny | int | ny | int/item | SAME |
| 7 | d | int | d | int/item | SAME |
| 8 | ext | float | ext | float/item | SAME |
| 9 | dist | float (default 10.0) | dist | float/item | SAME |
| 10 | mx/my | float % (default 0) | mx, my | float/item each | SAME |
| 11 | gx/gy | bool (default False) | gx, gy | bool/item each | SAME |
| 12 | show_leg | bool (default False) | show_leg | bool/item | SAME |
| 13 | col_vals | list num | col_vals | list float | SAME |
| 14 | colors | list color (req if show_leg) | colors | list ghdoc | SAME |
| 15 | n_leg | int (default 5) | n_leg | int/item | SAME |
| 16 | leg_w/leg_dist/leg_l_dist | float each | leg_w, leg_dist, leg_l_dist | float/item each | SAME |
| 17 | leg_orient | str ('vertical') | leg_orient | str/item | SAME |
| (legacy has no OutPath/CToggle) | — | — | OutPath (str), CToggle (bool) | NEW inputs for SVG export |

Current has extra outputs: `svg_code`, `svg_path` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | report (str) + dots, colors_out, axes... | DIFF: legacy output 'out' mapped to current 'report', but many more outputs in current |

Legacy outputs included: `dots` (circles), `colors_out`, `axes`, `x_pts/x_txt`, `y_pts/y_txt`, `grid_x/grid_y`, `leg_cells/clrs/pts/txt`.
Current includes all of these plus `svg_code`, `svg_path`, `report`.

**Notes:**

---

### 30. CRC_LinePlot

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | LinePlot | LinePlot | YES |
| Nickname | — | LinePlt | — |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Line chart from X/Y lists or DataTrees (one series per branch). | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | cv | rect | cv | ghdoc/item | SAME |
| 2 | x/y | list or tree num | x, y | list float each | SAME (tree handled by list) |
| 3 | nx/ny | int (default 5) | nx, ny | int/item each | SAME |
| 4 | d | int (decimal, default ?) | d | int/item | need check default |
| 5 | ext | float (axis extension) | ext | float/item | SAME |
| 6 | dist | float (label distance) | dist | float/item | SAME |
| 7 | mx/my | float % | mx, my | float/item each | SAME |
| 8 | gx/gy | bool (grid lines) | gx, gy | bool/item each | SAME |
| (legacy has no OutPath/CToggle/nx2-style margin params named differently) | — | — | OutPath (str), CToggle (bool) | NEW for SVG export |

Current has extra outputs: `svg_code`, `svg_path` — NEW.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | out + lines, axes, x_pts/x_txt, y_pts/y_txt, grid_x/grid_y, svg_code, svg_path | DIFF: legacy only had `out`, current has many outputs |

**Notes:**

---

### 31. CRC_Heatmap

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | Heatmap | Heatmap | YES |
| Nickname | — | Heatmap | SAME |
| Exposure | 3 | 8 | DIFF (was 3) |
| Description | Heatmap from a 2D matrix with custom color gradient + legend. | Same as legacy | SAME |

Current has extra inputs over legacy: `show_leg`, `OutPath`, `CToggle` — NEW.
All core params match: cv, data, colors, rows/cols, vals, d, n_leg, dist, leg_w, leg_dist, leg_l_dist, leg_orient.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | report (str) + cells, clrs, row_pts/txt, col_pts/txt, val_pts/txt..., leg_cells/clrs/pts/txt, svg_code, svg_path | DIFF: legacy only had `out`, current has many outputs |

**Notes:**

---

### 32. CRC_SaveSVG

| Property | Legacy | Current | Match? |
|----------|--------|---------|--------|
| Name | SaveSVG | SaveSVG | YES |
| Nickname | — | SaveSVG | SAME nickname |
| Exposure | 4 | 16 | DIFF (was 4, now 16 = quaternary/obscure) |
| Description | Assembles SVG fragments into a complete document and writes to disk. | Same as legacy | SAME |

| # | Legacy Input | Legacy Type | Current Input | Current Type | Match? |
|---|-------------|-------------|--------------|-------------|--------|
| 1 | svg_code | str/list | svg_code | list str | SAME (legacy: str/list, current: list — legacy str may be auto-wrapped) |
| 2 | canvas | rect | canvas | ghdoc/item | SAME |
| 3 | file_path | str | file_path | str | SAME |
| 4 | save_flag | bool | save_flag | bool | SAME |

Current has different output names than legacy.

| # | Legacy Output | Legacy Type | Current Output | Current Type | Match? |
|---|--------------|-------------|---------------|-------------|--------|
| 1 | out | str | — | — | MISSING in current |
| 2 | status_msg | str | report | str | DIFF naming (status_msg -> report) |

Current has extra output: `path` (abs path), `svg_doc` (complete doc string).

**Notes:**

---

## Global Observations / Patterns Found

### Common discrepancies across all components:

1. **Exposure values**: Almost every component that had exposure 1, 2, or 3 in legacy was set to a higher number (usually 4, 8, or 16) in the current build — toolbar placement changed significantly.

2. **Nickname changes**: Legacy nicknames were longer/more descriptive (e.g., `Q_schema`, `Q_table`, `Q_column`). Current nicknames are shorter/abbreviated (`QS`, `QT`, `QC`) — still readable but could cause confusion for legacy users.

3. **Input "out" -> "report"**: Legacy components that had an output called "Exceptions" or "out" (for error/status messages) were standardized to `report` in the current build. This is a spec requirement (CLAUDE.md § Design Principles: "fail visibly") — not technically wrong, but changes parameter names for legacy users.

4. **Missing "Exceptions"/"out" output on modeling components**: Components 2, 4, 5 (IdentifyDuplicatePolylines, PointInsidePolygon, SortByContainer) in the legacy table had an `out` (str) status message output. Current metadata does not declare it. **These need verification.**

5. **Color types stripped to strings**: SVG components that originally accepted both Color objects AND hex strings as inputs were standardized to accept only string values — may break user scripts that pass System.Drawing.Color directly.

6. **Default values not declared in metadata.json**: Several components have default values for inputs (e.g., `s` = 50 for sample count, `lin` = True for ColorCalculator) that are set in code.py but not guaranteed by the typeHintID — users may need to supply them explicitly if they don't use defaults.

7. **New outputs added**: Almost every query component now has an extra `queries` output (all SQL executed), and most SVG/chart components have `svg_code`/`svg_path`. These are backwards-compatible additions, not breaking changes.

8. **Legacy had separate "out" + "Fb" for CreateTable/CreateShapefile** — current merged this into a single `report` string + `affected` int, which is a behavior change worth verifying.

---

## Test Status Summary

| # | Component | Tested (Y/N) | Issues Found |
|---|-----------|-------------|--------------|
| 1 | BuildingMeshes | | |
| 2 | IdentifyDuplicatePolylines | | |
| 3 | OffsetPython | | |
| 4 | PointInsidePolygon | | |
| 5 | SortByContainer | | |
| 6 | ColorCalculator | | |
| 7 | QuerySchemaNames | | |
| 8 | QueryTableNames | | |
| 9 | QueryColumnNames | | |
| 10 | QueryValues | | |
| 11 | GeometryEntities | | |
| 12 | GeometriesWithSpatialFilter | | |
| 13 | ValuesWithSpatialFilter | | |
| 14 | CreateTable | | |
| 15 | CreateShapefile | | |
| 16 | ConnectionString | | |
| 17 | FindCorrectionParameters | | |
| 18 | SQLComposer | | |
| 19 | RunQuery | | |
| 20 | RunCommand | | |
| 21 | GrasshopperGeometryToWKT | | |
| 22 | WKTtoGrasshopperGeometry | | |
| 23 | CurveDisplay | | |
| 24 | PolylineToSVG | | |
| 25 | CircleToSVG | | |
| 26 | NurbsToSVG | | |
| 27 | TextToSVG | | |
| 28 | Histogram | | |
| 29 | ScatterPlot | | |
| 30 | LinePlot | | |
| 31 | Heatmap | | |
| 32 | SaveSVG | | |

---

## Next Implementation Plan (from test notes above)

Issues to address after testing:

1. **Exposure reassignment**: Decide if legacy exposure values (1,2) should be restored for primary components — many are too hidden at exposure 8/16 now.
2. **Nickname audit**: Short nicknames (`QS`, `QT`, `QC`, `QV`) may collide or be hard to find in toolbar filter. Consider reverting to more descriptive names.
3. **Missing status message outputs** on components #2, #4, #5 (IdentifyDuplicatePolylines, PointInsidePolygon, SortByContainer) — verify if `out` is missing from code.py or just not in metadata.json.
4. **Color type input regression**: SVG components no longer accept System.Drawing.Color — may need to restore this functionality.
5. **Default values check**: Confirm defaults for inputs like sample count (NurbsToSVG), classification mode (ColorCalculator) are properly enforced in code.py.
6. **Component #30 naming**: CRC_CurveDisplay has nickname `CrvDpl.cs` which looks like a filename — should be shortened (e.g., `CrvDpl`).
7. **CRC_BuildingMeshes exposure**: Set to 2 but legacy had 1 — may need adjustment.
