"""CRC_ValuesWithSpatialFilter: Query a single attribute column with spatial filter and coordinate correction."""
# r: psycopg2-binary
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

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
def _unwrap(g):
    return g.Value if hasattr(g, "Value") else g

def _in_item(i):
    for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True):
        return _unwrap(g)
    return None

def _in_list(i):
    return [_unwrap(g) for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True)]

def _in_tree(i):
    src = ghenv.Component.Params.Input[i].VolatileData
    t = DataTree[object]()
    for p in src.Paths:
        for g in src[p]:
            t.Add(_unwrap(g), p)
    return t
# ========================================================================================

# INPUT MAPPING:
#   0:cs(CString/item), 1:tog(CToggle/item), 2:sch(schema/item), 3:tbl(table/item),
#   4:col(column/item), 5:N(nullReplacement/item), 6:flt(spatialFilter/list),
#   7:srid(srid/item), 8:fn(sqlFilter/item), 9:cx(Cx/item), 10:cy(Cy/item)
cs_int   = _in_item(0)
tog_int  = _in_item(1)
sch_int  = _in_item(2)
tbl_int  = _in_item(3)
col_int  = _in_item(4)
N_int    = _in_item(5)
flt_int  = _in_list(6)
srid_int = _in_item(7)
fn_int   = _in_item(8)
cx_int   = _in_item(9)
cy_int   = _in_item(10)

values, primaryKeys, report, queries = DataTree[object](), DataTree[object](), "Set 'CToggle' to True to execute", ""

if tog_int:
    try:
        if not cs_int:
            raise ValueError("CString is required")
        if not sch_int or not tbl_int:
            raise ValueError("schema and table are required")
        if not col_int:
            raise ValueError("column is required")
        if not flt_int:
            raise ValueError("spatialFilter geometry list is required")

        null_val = str(N_int) if N_int else ""

        srid_val = int(srid_int) if srid_int else 4326
        func = int(fn_int) if fn_int else 0
        cx = str(cx_int) if cx_int else "0"
        cy = str(cy_int) if cy_int else "0"

        # Convert list of GH geometries to WKT strings for spatial filter
        filter_wkts = [rh_geometry_to_wkt(g) for g in flt_int if g is not None]
        filter_wkts = [w for w in filter_wkts if w]
        if not filter_wkts:
            raise ValueError("Failed to convert any spatial filter geometry to WKT")

        executed_sql = []
        values_list, pk_list = get_values_with_spatial_filter(
            cs_int, sch_int, tbl_int, str(col_int), filter_wkts,
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
