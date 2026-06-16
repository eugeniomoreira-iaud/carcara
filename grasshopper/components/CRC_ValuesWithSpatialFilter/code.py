"""CRC_ValuesWithSpatialFilter: Query a single attribute column with spatial filter and coordinate correction."""
import sys
import os
import Grasshopper

# Dynamically route to the user objects folder via the Grasshopper API
_carcara_path = os.path.join(Grasshopper.Folders.DefaultUserObjectFolder, "carcara")

if os.path.isdir(_carcara_path) and _carcara_path not in sys.path:
    sys.path.insert(0, _carcara_path)

try:
    ghenv.Component.Message = "v{{component_version}}-{{date}}"
except Exception:
    pass


from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.db.spatial_query import get_values_with_spatial_filter
from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt

values, primaryKeys, report, queries = DataTree[object](), DataTree[object](), "Set 'CToggle' to True to execute", ""

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")
        if not column:
            raise ValueError("column is required")
        if not spatialFilter:
            raise ValueError("spatialFilter geometry list is required")

        null_val = str(nullReplacement) if nullReplacement else ""

        srid_val = int(srid) if srid else 4326
        func = int(sqlFilter) if sqlFilter else 0
        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"

        # Convert list of GH geometries to WKT strings for spatial filter
        filter_wkts = [rh_geometry_to_wkt(g) for g in spatialFilter if g is not None]
        filter_wkts = [w for w in filter_wkts if w]
        if not filter_wkts:
            raise ValueError("Failed to convert any spatial filter geometry to WKT")

        executed_sql = []
        values_list, pk_list = get_values_with_spatial_filter(
            CString, schema, table, str(column), filter_wkts,
            cx=cx, cy=cy, srid=srid_val, func=func, sql_log=executed_sql
        )

        # Output as DataTree: one branch per row (parallel to GeometriesWithSpatialFilter)
        for i, (val, pk_val) in enumerate(zip(values_list, pk_list)):
            p = GH_Path(i)
            if null_val != "" and val is None:
                val = null_val
            values.Add(str(val) if val is not None else "", p)
            primaryKeys.Add(pk_val, p)

        report = f"OK – {len(values_list)} rows returned"
        queries = "\n\n".join("-- query {}\n{}".format(i + 1, s) for i, s in enumerate(executed_sql))
    except Exception as e:
        report = f"ERROR: {e}"
