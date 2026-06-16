<p align="center">
  <img src="docs/assets/logo_carcara.png" width="300" alt="Carcara logo">
</p>

<h1 align="center">Carcara</h1>

<p align="center">
  A Python-based Grasshopper plugin for <b>Rhino 8</b> that bridges PostGIS spatial
  databases with parametric design workflows — query, visualize, and export
  geospatial data directly from the Grasshopper canvas.
</p>

> Full development spec, component inventory, API contracts, and contribution
> rules live in [`CLAUDE.md`](CLAUDE.md).

***

## What it does

Carcara adds a **Carcara** ribbon to Grasshopper with **32 components** across four
subcategories. All domain logic is a pure-Python package (`crc_modules`) that is
importable and testable outside Rhino; the Grasshopper components are thin wrappers.

| Subcategory | Count | Components |
|---|---|---|
| **01.Modeling** | 6 | BuildingMeshes, OffsetPython, PointInsidePolygon, SortByContainer, IdentifyDuplicatePolylines, ColorCalculator |
| **02.Queries** | 9 | QuerySchemaNames, QueryTableNames, QueryColumnNames, QueryValues, GeometryEntities, GeometriesWithSpatialFilter, ValuesWithSpatialFilter, CreateTable, CreateShapefile |
| **03.Utilities** | 7 | ConnectionString, FindCorrectionParameters, SQLComposer, RunQuery, RunCommand, GrasshopperGeometryToWKT, WKTtoGrasshopperGeometry |
| **04.Dataviz** | 10 | CurveDisplay, PolylineToSVG, CircleToSVG, NurbsToSVG, TextToSVG, Histogram, ScatterPlot, LinePlot, Heatmap, SaveSVG (all use SDK-mode viewport preview except SaveSVG) |

`CRC_SRID` is a native Grasshopper ValueList added manually (not part of the build).

## Component reference

### 01.Modeling

#### CRC_BuildingMeshes · `BdgMsh`
Extrudes a list of building footprints by their heights.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `buildingFootprints` | `fp` | polyline | tree | Tree of building footprint polygons. Holes are auto-detected by containment. |
| `buildingHeights` | `h` | float | tree | Tree of building heights matching buildingFootprints tree structure. |

**Outputs:** `out`, `groundFaces`, `lateralFaces`, `rooftopFaces`

#### CRC_IdentifyDuplicatePolylines · `IdDupPol`
Computes a normalized signature for each polyline to handle differences in start point and direction. Groups those with identical signatures and outputs the duplicate indexes.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `polylines` | `pl` | ghdoc | list | List of polyline objects to check for duplicates. |

**Outputs:** `duplicateIndices`, `report`

#### CRC_OffsetPython · `OffPy`
Offsets planar polylines using given distances and a corner style mapping.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `curves` | `crv` | curve | tree | Planar polylines to offset |
| `distances` | `dist` | float | tree | Offset distances. Single value applies to all; list is cyclic. |
| `cornerStyle` | `cs` | int | item | Corner style: 0=None, 1=Sharp (default), 2=Round, 3=Smooth, 4=Chamfer |

**Outputs:** `out`, `offsetCurves`

#### CRC_PointInsidePolygon · `Pt_Plg`
Finds the pole of inaccessibility (polylabel) for a polygon — the deepest interior point from the boundary. Falls back to centroid only when polylabel is unavailable.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `polygon` | `pol` | curve | item | Closed planar polygon curve to be processed. |

**Outputs:** `interiorPoint`, `report`

#### CRC_SortByContainer · `Srt_Ctn`
Sorts a list of points by a list of containers. Output tree always matches curve count with empty branches for curves containing no points.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `containers` | `C` | curve | tree | Planar closed curves used as containers. Each curve becomes one output branch. |
| `points` | `P` | point | tree | Points to sort into the container curves. If your objects are not points, create representative points first. TIP: use 'Point Inside Polygon' to get interior points for polylines. |

**Outputs:** `indices`, `report`

#### CRC_ColorCalculator · `ColorCalc`
Calculates colors for mesh volumes based on numerical values. Supports continuous gradients, fixed class count, or custom class boundaries. Generates legend geometry and renders it directly in the Rhino viewport.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `valueTree` | `val` | ghdoc | tree | Tree of values for color mapping. One value per mesh. |
| `colorGrad` | `col` | color | list | Color gradient or list of colors (min 2, default: Ladybug gradient). |
| `classCount` | `cls` | ghdoc | list | Number of classes (int, 0=continuous) OR list of class boundary floats e.g. [0,5,10]. |
| `linear` | `lin` | bool | item | True=linear intervals, False=percentile-based (default: True). |
| `legendCfg` | `legCfg` | str | item | Legend config as 'key: value' pairs (title, min, max, segments, decimals, vertical, seg_height, seg_width, text_height, scale, etc.). |
| `legendPlane` | `legPln` | plane | item | Base plane for legend positioning (default: World XY) |

**Outputs:** `out`, `colors`, `legendGeo`, `textLocations`, `textContents`, `textSizes`, `stats`, `report`

### 02.Queries

#### CRC_QuerySchemaNames · `QS`
Lists all non-system schemas in a PostGIS database.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with plain-text password (libpq format) |
| `CToggle` | `tog` | bool | item | Set True to execute |

**Outputs:** `schemas`, `report`, `queries`

#### CRC_QueryTableNames · `QT`
Lists all tables in a specified schema.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with plain-text password (libpq format) |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `schema` | `sch` | str | item | Schema name |

**Outputs:** `tables`, `report`, `queries`

#### CRC_QueryColumnNames · `QC`
Lists all columns and their types in a specified table.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with plain-text password (libpq format) |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `schema` | `sch` | str | item | Schema name |
| `table` | `tbl` | str | item | Table name |

**Outputs:** `columns`, `types`, `report`, `queries`

#### CRC_QueryValues · `QV`
Queries a single column from a PostGIS table, replacing NULL values with a given replacement.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password (libpq format) |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `schema` | `sch` | str | item | Schema name |
| `table` | `tbl` | str | item | Table name |
| `column` | `col` | str | item | Column name(s) to query (comma-separated for multiple) |
| `nullReplacement` | `N` | str | item | Value to replace NULL with (optional) |

**Outputs:** `rows`, `columns`, `report`, `queries`

#### CRC_GeometryEntities · `GeoEnt`
Draws the geometric entities from a given table with coordinate correction (false origin).

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `schema` | `sch` | str | item | Schema where the table is located |
| `table` | `tbl` | str | item | Table to query |
| `Cx` | `cx` | str | item | Correction X (false origin) - default 0 |
| `Cy` | `cy` | str | item | Correction Y (false origin) - default 0 |

**Outputs:** `geometry`, `primaryKeys`, `report`, `queries`

#### CRC_GeometriesWithSpatialFilter · `Geo_SptFlt`
Returns geometries from a table filtered by a spatial boundary with coordinate correction.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `schema` | `sch` | str | item | Schema where the table is located |
| `table` | `tbl` | str | item | Table to be queried |
| `spatialFilter` | `flt` | ghdoc | list | Grasshopper geometries to act as spatial filter (list — all polygons dissolved into a single mask) |
| `srid` | `srid` | int | item | Spatial reference identifier for the spatial filter (default 4326) |
| `sqlFilter` | `fn` | int | item | Filter function: 0 = ST_Intersects, else = ST_Contains |
| `Cx` | `cx` | str | item | Correction X (false origin) - default 0 |
| `Cy` | `cy` | str | item | Correction Y (false origin) - default 0 |

**Outputs:** `geometry`, `primaryKeys`, `report`, `queries`

#### CRC_ValuesWithSpatialFilter · `ValSptFlt`
Returns a single column's values for rows intersecting a spatial filter boundary, with coordinate correction. Output is a DataTree (branch per row) parallel to CRC_GeometriesWithSpatialFilter.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `schema` | `sch` | str | item | Schema where the table is located |
| `table` | `tbl` | str | item | Table to be queried |
| `column` | `col` | str | item | Single column name to query |
| `nullReplacement` | `N` | str | item | Value to replace NULL items with |
| `spatialFilter` | `flt` | ghdoc | list | Grasshopper geometries to act as spatial filter (list — all polygons dissolved into a single mask) |
| `srid` | `srid` | int | item | Spatial reference identifier for the spatial filter (default 4326) |
| `sqlFilter` | `fn` | int | item | Filter function: 0 = ST_Intersects, else = ST_Contains |
| `Cx` | `cx` | str | item | Correction X (false origin) - default 0 |
| `Cy` | `cy` | str | item | Correction Y (false origin) - default 0 |

**Outputs:** `values`, `primaryKeys`, `report`, `queries`

#### CRC_CreateTable · `CrtTbl`
CREATE TABLE in PostGIS and INSERT row data; always adds a primary key (from Id Values or auto-increment). Destructive when replace_table=True.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password |
| `CToggle` | `tog` | bool | item | Set True to CREATE the table and INSERT rows (destructive if replace_table=True) |
| `schema` | `sch` | str | item | Target schema |
| `table` | `tbl` | str | item | Table name to create |
| `columnNames` | `cols` | str | list | Column names (parallel to column_types) |
| `columnTypes` | `types` | str | list | SQL types parallel to column_names (e.g. text, integer, double precision) |
| `values` | `vals` | str | tree | DataTree of row data — branch per row; each branch holds values for all columns |
| `idValues` | `ids` | str | tree | Optional DataTree of primary-key values — branch per row (one id per branch); omit for auto-increment id |
| `replaceTable` | `rep` | bool | item | DROP TABLE IF EXISTS before CREATE (destructive) |

**Outputs:** `affected`, `report`

#### CRC_CreateShapefile · `CrtShp`
Creates a PostGIS table with attribute columns AND a geometry column named 'geom' (type auto-detected). Geometry is a DataTree: branch per row; more than one item per branch = multipart. Applies false-origin (Cx/Cy) add-back in SQL. Not a file export.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password |
| `CToggle` | `tog` | bool | item | Set True to CREATE the table and INSERT rows (destructive if replace_table=True) |
| `schema` | `sch` | str | item | Target schema |
| `table` | `tbl` | str | item | Table name to create |
| `columnNames` | `cols` | str | list | Attribute column names (parallel to column_types; optional — geometry-only table allowed) |
| `columnTypes` | `types` | str | list | SQL types parallel to column_names (e.g. text, integer, double precision) |
| `values` | `vals` | str | tree | Attribute DataTree — branch per row, parallel to geometry branches (optional) |
| `idValues` | `ids` | str | tree | Optional DataTree of primary-key values — branch per row (one id per branch); omit for auto-increment id |
| `geometry` | `geo` | ghdoc | tree | Rhino geometry DataTree — branch per row; >1 item per branch = multipart (required) |
| `srid` | `srid` | int | item | SRID of the geometries (default 4326) |
| `Cx` | `cx` | str | item | Correction X — false origin added back in SQL (numeric text, default '0') |
| `Cy` | `cy` | str | item | Correction Y — false origin added back in SQL (numeric text, default '0') |
| `replaceTable` | `rep` | bool | item | DROP TABLE IF EXISTS before CREATE (destructive) |

**Outputs:** `affected`, `report`

### 03.Utilities

#### CRC_ConnectionString · `ConnStr`
Builds a libpq connection string (CString) with plain-text password. Opens an Eto dialog to collect host/user/password; database and port come from canvas inputs.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `database` | `db` | str | item | Database name to connect to |
| `port` | `port` | int | item | Port (default 5432) |
| `CToggle` | `tog` | bool | item | Set True to open the credentials dialog and test the connection |

**Outputs:** `CString`, `ok`, `report`

#### CRC_FindCorrectionParameters · `FindCorr`
Finds the coordinate correction parameters (Cx, Cy) from a PostGIS table row. Returns the centroid of the selected row as text strings for use as false-origin correction in geometry query components.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | A database connection string. |
| `CToggle` | `tog` | bool | item | Set True to connect. |
| `schema` | `sch` | str | item | Schema where the table is located. |
| `table` | `tbl` | str | item | Table to be queried. |
| `column` | `col` | str | item | Column where a specific value can be searched (optional — omit for first row). |
| `value` | `val` | str | item | Value to be searched (optional — omit for first row). |

**Outputs:** `Cx`, `Cy`, `report`

#### CRC_SQLComposer · `SQLComp`
Generates SQL statements by replacing variable placeholders with corresponding values.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `sql` | `sql` | str | item | SQL template with placeholders (e.g., 'SELECT * FROM #table# WHERE col = #value#'). |
| `variables` | `var` | str | list | List of placeholder strings to be replaced. |
| `values` | `val` | str | list | List of replacement values corresponding to the placeholders. |

**Outputs:** `out`, `statement`, `report`

#### CRC_RunQuery · `RQ`
Runs a raw SQL SELECT against a PostGIS database and returns results as a DataTree organised by column.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `sql` | `sql` | str | item | SQL SELECT statement to execute |

**Outputs:** `rows`, `columns`, `report`

#### CRC_RunCommand · `RC`
Runs a SQL DDL/DML command (non-SELECT) against a PostGIS database and returns execution feedback.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `CString` | `cs` | str | item | Connection string with encoded password |
| `CToggle` | `tog` | bool | item | Set True to execute |
| `sql` | `sql` | str | item | SQL DDL/DML command to execute (non-SELECT) |

**Outputs:** `report`

#### CRC_GrasshopperGeometryToWKT · `ghToWkt`
Converts Grasshopper geometry (points, lines/polylines, polygons) to Well-Known Text. A branch with one geometry yields a single WKT; multiple uniform geometries yield a MULTI* WKT. No coordinate correction (geometry stays local).

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `geometry` | `geo` | ghdoc | tree | Geometry or DataTree of geometries to convert (points, lines/polylines, polygons) |

**Outputs:** `WKT`, `report`

#### CRC_WKTtoGrasshopperGeometry · `wktToGH`
Converts Well-Known Text (WKT) strings into Grasshopper geometry. Real multipart members share a branch; singles get their own branch. No coordinate correction (WKT is already local).

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `wktGeometry` | `wkt` | str | list | List of WKT strings to convert to Grasshopper geometry |

**Outputs:** `geometry`, `report`

### 04.Dataviz

#### CRC_CurveDisplay · `CrvDpl`
Custom viewport preview (lineweight, color, dash) for curves — CPython SDK-mode port of CRC_CurveDisplay.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `curves` | `crv` | curve | list | Curves to preview |
| `colours` | `col` | color | list | Color per curve (last value repeats for remaining curves) |
| `widths` | `w` | float | list | Lineweight per curve in pixels (last value repeats) |
| `dashes` | `dash` | str | list | Dash pattern per curve: space-separated dash/gap values (e.g. '2 1'); last value repeats |

**Outputs:** none (viewport preview only)

#### CRC_PolylineToSVG · `PolySVG`
Converts Grasshopper polylines/polygons to SVG `<polyline>`/`<polygon>` element strings. Closed polylines emit `<polygon>`; open polylines emit `<polyline>`. Coordinates are transformed from Rhino Y-up to SVG Y-down using the canvas anchor.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `polylines` | `pl` | curve | list | Polyline geometry or list of polylines |
| `strokeColor` | `sc` | color | list | Stroke color or list of stroke colors. Default: none |
| `strokeWidth` | `sw` | float | list | Stroke width or list of stroke widths. Default: 0 |
| `fillColor` | `f` | color | list | Fill color or list of fill colors. Default: none |
| `canvas` | `canvas` | rectangle | item | Rectangle defining the SVG canvas (optional; uses bounding box if not provided) |
| `dashPattern` | `dash` | str | list | Stroke dash pattern or list (e.g. '5,5'). Default: '' (solid) |

**Outputs:** `svgCode`, `report`

#### CRC_CircleToSVG · `CircSVG`
Converts Grasshopper Circle geometries to SVG `<circle>` element strings. Transforms center from Rhino Y-up to SVG Y-down using the canvas anchor.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `circle` | `c` | circle | list | Circle geometry or list of circles |
| `strokeColor` | `sc` | color | list | Stroke color or list of stroke colors. Default: none |
| `strokeWidth` | `sw` | float | list | Stroke width or list of stroke widths. Default: 0 |
| `fillColor` | `f` | color | list | Fill color or list of fill colors. Default: none |
| `canvas` | `canvas` | rectangle | item | Canvas rectangle for Y-axis flipping. Default: (0,0,100,100) |

**Outputs:** `svgCode`, `report`

#### CRC_NurbsToSVG · `NurbsSVG`
Converts Grasshopper NURBS curves to SVG `<path>` elements via linear-segment approximation at a configurable sample count (default 50). Coordinates are transformed from Rhino Y-up to SVG Y-down using the canvas anchor.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `nurbsCurves` | `n` | curve | list | NURBS curve or list of curves |
| `sampleCount` | `s` | int | list | Sample count per curve (default 50). Higher = smoother |
| `strokeColor` | `sc` | color | list | Stroke color or list of stroke colors. Default: none |
| `strokeWidth` | `sw` | float | list | Stroke width or list of stroke widths. Default: 0 |
| `fillColor` | `f` | color | list | Fill color or list of fill colors. Default: none |
| `canvas` | `canvas` | rectangle | item | Rectangle defining the SVG canvas (optional; uses bounding box if not provided) |

**Outputs:** `svgCode`, `report`

#### CRC_TextToSVG · `TxtSVG`
Converts text strings with Point3d or Plane insertion to SVG `<text>` elements. Plane input yields rotation from the plane X-axis angle. Justification 1–9 maps to SVG text-anchor/dominant-baseline pairs.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `texts` | `t` | str | list | Text string(s) to render |
| `points` | `pt` | ghdoc | list | Insertion point(s) or plane(s) for text (Point3d or Plane) |
| `fontFamily` | `ff` | str | item | Font family (default 'Arial') |
| `fontSize` | `fs` | float | item | Font size in pixels (default 12) |
| `fillColor` | `fc` | color | item | Fill color (default black) |
| `canvas` | `canvas` | rectangle | item | Rectangle defining the SVG canvas (optional) |
| `justification` | `j` | int | list | Justification 1–9 (1=TL 2=TC 3=TR 4=ML 5=MC 6=MR 7=BL 8=BC 9=BR). Default 6 |

**Outputs:** `svgCode`, `report`

#### CRC_Histogram · `Hist`
Renders a histogram chart in the Rhino viewport and exports raw SVG body content. Chain svgCode into CRC_SaveSVG to write the file.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `canvasRect` | `cnv` | rectangle | item | Canvas boundary Rectangle3d (default 100x100 at origin) |
| `dataValues` | `val` | float | list | Data values to histogram (uses demo data if absent) |
| `numBins` | `bins` | int | item | Number of histogram bins (default 10) |
| `numXLabels` | `nxL` | int | item | Number of X-axis labels (default: all bin edges) |
| `numYLabels` | `nyL` | int | item | Number of Y-axis labels (default 5) |
| `decimals` | `dec` | int | item | Decimal places for labels (default 1) |
| `axisExtension` | `axE` | float | item | Axis extension beyond canvas (default 0) |
| `labelDist` | `lblD` | float | item | Label distance from axis (default 10) |
| `drawGridY` | `gY` | bool | item | Draw horizontal grid lines at Y labels (default False) |
| `barOutlineWidth` | `barW` | float | item | Bar outline width in pixels (default 1) |
| `axisLineWidth` | `axW` | float | item | Axis line width in pixels (default 2) |
| `gridLineWidth` | `grdW` | float | item | Grid line width in pixels (default 1) |

**Outputs:** `svgCode`, `report`

#### CRC_ScatterPlot · `Scatter`
Renders a scatter chart in the Rhino viewport and exports raw SVG body content. Chain svgCode into CRC_SaveSVG to write the file.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `canvasRect` | `cnv` | rectangle | item | Canvas boundary Rectangle3d |
| `xValues` | `x` | float | list | X coordinates of data points (default demo data if absent) |
| `yValues` | `y` | float | list | Y coordinates of data points (default demo data if absent) |
| `dotRadius` | `r` | float | list | Dot radius — single value or list for variable sizes (default 2.0) |
| `numXLabels` | `nxL` | int | item | Number of X-axis labels (default 5) |
| `numYLabels` | `nyL` | int | item | Number of Y-axis labels (default 5) |
| `decimals` | `dec` | int | item | Decimal places for labels (default 1) |
| `axisExtension` | `axE` | float | item | Axis extension beyond canvas (default 0) |
| `labelDist` | `lblD` | float | item | Label distance from axis (default 10.0) |
| `marginLeft` | `mL` | float | item | Left margin as % of X range (default 0) |
| `marginBottom` | `mB` | float | item | Bottom margin as % of Y range (default 0) |
| `drawGridX` | `gX` | bool | item | Draw vertical grid lines (default False) |
| `drawGridY` | `gY` | bool | item | Draw horizontal grid lines (default False) |
| `showLegend` | `leg` | bool | item | Generate color legend (default False) |
| `colorValues` | `cVal` | float | list | Values for color mapping; if None uses Y values |
| `gradientColors` | `grad` | color | list | Color gradient list for legend (min 2 System.Drawing.Color). Defaults cool-to-warm if absent. |
| `numLegendSteps` | `legN` | int | item | Number of legend steps (default 5) |
| `legendBarWidth` | `legW` | float | item | Legend bar width (default 5% of canvas) |
| `legendDist` | `legD` | float | item | Distance from chart to legend (default 20) |
| `legendLabelDist` | `legLD` | float | item | Distance from legend bar to labels (default 5) |
| `legendOrientation` | `legO` | str | item | Legend orientation: vertical or horizontal (default vertical) |
| `dotOutlineWidth` | `dotW` | float | item | Dot outline width in pixels (default 0.5) |
| `axisLineWidth` | `axW` | float | item | Axis line width in pixels (default 2) |
| `gridLineWidth` | `grdW` | float | item | Grid line width in pixels (default 1) |

**Outputs:** `svgCode`, `report`

#### CRC_LinePlot · `LinePlt`
Renders a line chart in the Rhino viewport and exports raw SVG body content. Chain svgCode into CRC_SaveSVG to write the file.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `canvasRect` | `cnv` | rectangle | item | Canvas boundary Rectangle3d (default 100x100 at origin) |
| `xValues` | `x` | float | list | X coordinates (flat list = 1 series; DataTree = multi). Uses demo data if absent. |
| `yValues` | `y` | float | list | Y coordinates (same shape as xValues). Uses demo data if absent. |
| `numXLabels` | `nxL` | int | item | Number of X-axis labels (default 5) |
| `numYLabels` | `nyL` | int | item | Number of Y-axis labels (default 5) |
| `decimals` | `dec` | int | item | Decimal places for labels (default 1) |
| `axisExtension` | `axE` | float | item | Axis extension beyond canvas (default 0) |
| `labelDist` | `lblD` | float | item | Label distance from axis (default 10) |
| `marginLeft` | `mL` | float | item | Left margin as % of X range (default 0) |
| `marginBottom` | `mB` | float | item | Bottom margin as % of Y range (default 0) |
| `drawGridX` | `gX` | bool | item | Draw vertical grid lines at X labels (default False) |
| `drawGridY` | `gY` | bool | item | Draw horizontal grid lines at Y labels (default False) |
| `lineWidth` | `lnW` | float | item | Series line width in pixels (default 2) |
| `axisLineWidth` | `axW` | float | item | Axis line width in pixels (default 2) |
| `gridLineWidth` | `grdW` | float | item | Grid line width in pixels (default 1) |

**Outputs:** `svgCode`, `report`

#### CRC_Heatmap · `HeatMap`
Renders a heatmap chart in the Rhino viewport and exports raw SVG body content. Chain svgCode into CRC_SaveSVG to write the file.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `canvasRect` | `cnv` | rectangle | item | Canvas boundary rectangle (Rectangle3d) |
| `dataMatrix` | `mtx` | ghdoc | tree | 2D data matrix (DataTree one branch-per-row or nested list). Defaults to demo data if empty. |
| `gradientColors` | `grad` | color | list | Color gradient (min 2 System.Drawing.Color). Defaults cool-to-warm if absent. |
| `rowLabels` | `rLbl` | str | list | Row labels as strings (e.g. R1, R2) |
| `colLabels` | `cLbl` | str | list | Column labels as strings (e.g. C1, C2) |
| `showCellValues` | `cVal` | bool | item | Show numeric values inside cells (default False) |
| `decimals` | `dec` | int | item | Decimal places for displayed numbers (default 1) |
| `legendSteps` | `legN` | int | item | Number of legend gradient steps (default 5) |
| `labelDist` | `lblD` | float | item | Distance from axis labels to chart edge (default 10.0) |
| `legendBarW` | `legW` | float | item | Legend bar width (default auto, ~5% canvas dim) |
| `legendDist` | `legD` | float | item | Distance from chart area to legend (default 20.0) |
| `legendLabelDist` | `legLD` | float | item | Distance from legend bar to its labels (default 5.0) |
| `legendOrientation` | `legO` | str | item | Legend orientation: vertical or horizontal (default vertical) |
| `showLegend` | `leg` | bool | item | Display legend panel (default True) |
| `cellOutlineWidth` | `cellW` | float | item | Heatmap cell-border width in pixels (default 0.5) |
| `legendCellOutlineWidth` | `lcW` | float | item | Legend cell border width in pixels (default 0.5) |

**Outputs:** `svgCode`, `report`

#### CRC_SaveSVG · `Save`
Assembles SVG element strings into a complete SVG document (viewBox from canvas dimensions) and writes it to disk. File is only written when save_flag is True.

| Input | Nick | Type | Access | Description |
|---|---|---|---|---|
| `svgCode` | `svg` | str | list | SVG element string(s) to assemble (list or single string) |
| `canvas` | `canvas` | ghdoc | item | Rectangle geometry defining canvas width/height (optional; uses 800x600 default if absent) |
| `filePath` | `path` | str | item | Output file path including filename (e.g. C:\output.svg) |
| `saveFlag` | `save` | bool | item | Set True to write the file to disk |

**Outputs:** `path`, `svgDoc`, `report`

***

### Highlights

- **Connection model** — `CRC_ConnectionString` builds a single `CString` (libpq
  conninfo) that travels on a canvas wire into every DB component, alongside a
  `CToggle` trigger.
- **Coordinate correction** — projected coordinates (UTM / SIRGAS) are shifted by a
  false origin `(Cx, Cy)` **inside SQL** (`ST_Translate`) so full-magnitude values
  never reach Rhino and lose precision. `Cx`/`Cy` are numeric text, never parsed to float.
- **Dataviz** — charts are built as real Rhino geometry (visible in the viewport)
  **and** exported as fully-configured SVG, mirroring the legacy plugin.

***

## Repo layout

```
<repo>/                                 ← git repo root
├── carcara/                            ← THE deployable folder (copied as-is to UserObjects)
│   ├── crc_modules/                    ← pure-Python package = the code (no Rhino imports)
│   │   ├── db/                         ← connection, query, spatial_query, writer
│   │   ├── geometry/                   ← wkt, polylabel, containment, duplicates, dash
│   │   ├── rhino/                      ← Rhino-only: offset, building_mesh, curve_display, wkt_conversion (excluded from pytest)
│   │   ├── svg/                        ← export, save
│   │   ├── utils/                      ← color, sql_composer, correction
│   │   └── viz/                        ← histogram, scatter, lineplot, heatmap
│   ├── userobjects/                    ← all built .ghuser files (committed; shipped to users)
│   └── version.txt                     ← generated by make_release.py; installer reads this
│
├── grasshopper/
│   ├── components/                     ← component SOURCE bundles (metadata.json, code.py, icon.png)
│   ├── icons/                          ← source artwork
│   └── installer/                      ← self-contained bootstrap installers (delivered in a .gh)
│       ├── install_python_libs.py      ← installs pip deps into Rhino 8 CPython
│       └── install_carcara.py          ← downloads repo, copies carcara/ → UserObjects
│
├── tests/                              ← pytest (imports crc_modules.*; DB mocked)
├── specs/                              ← componentizer + ghuser-decoding references
├── implementation/                     ← phase-by-phase rebuild plans (00–13)
├── docs/                               ← reports + branding assets
├── tools/                              ← dev utilities (decode_ghuser.py)
├── vendor/                             ← componentizer + GH_IO.dll (build toolchain)
├── carcara-old/                        ← LEGACY, read-only reference of the original plugin
├── build_userobjects.py               ← builds bundles → carcara/userobjects/*.ghuser
├── make_release.py                     ← build + write version.txt (run before a release)
├── deploy.ps1                          ← dev convenience: copy carcara/ → UserObjects/carcara/
├── pyproject.toml  requirements.txt
└── CLAUDE.md  README.md
```

The source package lives *inside* the deployable folder (`carcara/crc_modules/`).
There is no separate `release/` copy — the committed `carcara/` folder **is** what
users download. Components import `from crc_modules.db.connection import ...`; the
unique name avoids clashing with a generic `import modules` in the Rhino session.

***

## Install (end users)

Open **`grasshopper/installer/`** and drag the `.gh` file onto the Grasshopper
canvas. It contains two `Boolean Toggle`-triggered installers — run them once per
machine, in order:

1. **`install_python_libs.py`** — pip-installs runtime deps (`psycopg2`, `shapely`,
   `svgwrite`, `matplotlib`) into Rhino 8 CPython.
2. **`install_carcara.py`** — downloads the repo zip from
   `eugeniomoreira-iaud/carcara` (master) and copies `carcara/` →
   `UserObjects/carcara/`. Version-checks against the installed `version.txt`, keeps
   a timestamped backup, and rolls back on failure.

After step 2, restart Grasshopper — the **Carcara** ribbon appears with all
components. The committed `.ghuser` files are copied as-is; no compilation on the
user machine. Both installers are self-contained (no `import crc_modules`, since they
run before the package exists).

### Deployed layout
```
%APPDATA%\Grasshopper\UserObjects\
└── carcara\                            ← the whole folder, copied by the installer
    ├── crc_modules\                    ← package; sys.path points at the PARENT (…\UserObjects\carcara)
    ├── userobjects\*.ghuser            ← Grasshopper scans UserObjects recursively, so these load
    └── version.txt
```
Each `code.py` puts `…\UserObjects\carcara` on `sys.path` (GHPython has no
`__file__`), then `import crc_modules`.

***

## Develop

Full spec: [`CLAUDE.md`](CLAUDE.md) (architecture, component inventory, API
contracts, rules). Per-phase plans: [`implementation/`](implementation/).

Use the conda environment `carcara` (or any CPython 3.11+ with the deps):

```powershell
# install dev deps
pip install -r requirements.txt          # or: pip install -e ".[dev]"

# run the tests (DB mocked; no live database needed)
conda run -n carcara python -m pytest tests/ -q

# build the .ghuser files, then deploy to the local UserObjects folder
conda run -n carcara python build_userobjects.py
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

> On Windows PowerShell, prefix Python commands with `conda run -n carcara` — the bare
> `python` resolves to the Windows Store stub unless the env is activated.

`.ghuser` files are binary `GH_Archive` artifacts produced by the componentizer
(`vendor/componentizer/`); never hand-edit them. Restart Grasshopper after deploying.

***

## Acknowledgements

Carcara's build pipeline and component architecture draw on patterns established by
two upstream open-source projects. The `.ghuser` build step uses the same
`metadata.json` + `code.py` + `icon.png` bundle layout and componentizer approach
pioneered by **COMPAS** in
[`compas-actions.ghpython_components`](https://github.com/compas-dev/compas-actions.ghpython_components),
which converts these bundles into binary `.ghuser` files. The component-bundle layout
and the SDK-mode viewport-preview component pattern used by the data-viz and
color-calculator components were inspired by
[**Ladybug Tools**](https://github.com/ladybug-tools), whose structural conventions
were adopted (not its code). The COMPAS componentizer scripts are vendored under
[`vendor/componentizer/`](vendor/componentizer/) and used as the build toolchain.

***

## Requirements

| | |
|---|---|
| Rhino | 8 |
| Python | CPython 3.11+ (Rhino 8 ScriptEditor) |
| Database | PostgreSQL 14+ with PostGIS 3+ |
| DB driver | `psycopg2` (no ODBC) |
| Runtime deps | `psycopg2`, `shapely`, `svgwrite`, `matplotlib` |
| Build/dev deps | `pythonnet`, `pytest`, `python-dotenv`, `requests` |
| OS | Windows 10/11 (primary), macOS (secondary) |
