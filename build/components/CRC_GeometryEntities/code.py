"""CRC_GeometryEntities: Query geometries from a PostGIS table with coordinate correction."""
# r: psycopg2-binary, shapely
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

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree
from shapely import wkt as shapely_wkt

from crc_modules.db.spatial_query import get_geometries, detect_geometry_columns
from crc_modules.rhino.wkt_conversion import wkt_to_rhino

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

# INPUT MAPPING  0:cs:item  1:tog:item  2:sch:item  3:tbl:item  4:cx:item  5:cy:item
cs_int  = _in_item(0)
tog_int = _in_item(1)
sch_int = _in_item(2)
tbl_int = _in_item(3)
cx_int  = _in_item(4)
cy_int  = _in_item(5)

geometry, primaryKeys, report, queries = DataTree[object](), DataTree[object](), "Set 'CToggle' to True to execute", ""

if tog_int:
    try:
        if not cs_int:
            raise ValueError("CString is required")
        if not sch_int or not tbl_int:
            raise ValueError("schema and table are required")

        cx = str(cx_int) if cx_int else "0"
        cy = str(cy_int) if cy_int else "0"

        executed_sql = []
        geom_cols = detect_geometry_columns(cs_int, sch_int, tbl_int, sql_log=executed_sql)

        wkt_list, pk_list = get_geometries(cs_int, sch_int, tbl_int, cx=cx, cy=cy, sql_log=executed_sql)

        built = null_wkt = failed = 0
        sample_fail = ""
        for i, (wkt_str, pk_val) in enumerate(zip(wkt_list, pk_list)):
            path = GH_Path(i)
            if not wkt_str or not wkt_str.strip():
                null_wkt += 1
                if pk_val is not None:
                    primaryKeys.Add(pk_val, path)
                continue
            rh_geoms = wkt_to_rhino(wkt_str)
            if isinstance(rh_geoms, list):
                added = 0
                for rh_geom in rh_geoms:
                    if rh_geom is not None:
                        geometry.Add(rh_geom, path)
                        primaryKeys.Add(pk_val, path)
                        added += 1
                if added:
                    built += 1
                else:
                    failed += 1
                    if not sample_fail:
                        sample_fail = wkt_str[:60]
            elif rh_geoms is not None:
                geometry.Add(rh_geoms, path)
                primaryKeys.Add(pk_val, path)
                built += 1
            else:
                failed += 1
                if not sample_fail:
                    sample_fail = wkt_str[:60]

        report = (
            "OK\n"
            "  rows: {}\n"
            "  geometries built: {}\n"
            "  null WKT: {}\n"
            "  unconvertible: {}\n"
            "  geom columns detected: {}".format(
                len(wkt_list), built, null_wkt, failed,
                ", ".join(geom_cols) if geom_cols else "(none)")
        )
        if sample_fail:
            report += "\n  sample unconvertible WKT: {}...".format(sample_fail)
        queries = "\n\n".join("-- query {}\n{}".format(i + 1, s) for i, s in enumerate(executed_sql))
    except Exception as e:
        report = f"ERROR: {e}"
