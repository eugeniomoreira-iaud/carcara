"""CRC_GeometriesWithSpatialFilter: Query geometries with spatial filter and coordinate correction."""
import sys
import os

# Make the crc_modules package importable from a Grasshopper Python 3 component.
_bases = []
_appdata = os.environ.get("APPDATA")
if _appdata:
    _bases.append(os.path.join(_appdata, "Grasshopper", "UserObjects", "carcara"))
_bases.append(os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "McNeel",
    "Rhinoceros", "8.0", "Plug-ins", "Grasshopper", "UserObjects", "carcara"))
for _b in _bases:
    if os.path.isdir(_b) and _b not in sys.path:
        sys.path.insert(0, _b)

try:
    ghenv.Component.Message = "v{{component_version}}"
except Exception:
    pass

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.db.spatial_query import get_geometries_with_spatial_filter, detect_geometry_columns
from crc_modules.rhino.wkt_conversion import wkt_to_rhino, rh_geometry_to_wkt

geometry, pk, report, queries = DataTree[object](), DataTree[object](), "Set 'CToggle' to True to execute", ""

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")
        if not spatial_filter:
            raise ValueError("spatial_filter geometry list is required")

        srid = int(SRID) if SRID else 4326
        func = int(function) if function else 0
        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"

        # Convert list of GH geometries to WKT strings for spatial filter
        filter_wkts = [rh_geometry_to_wkt(g) for g in spatial_filter if g is not None]
        filter_wkts = [w for w in filter_wkts if w]
        if not filter_wkts:
            raise ValueError("Failed to convert any spatial filter geometry to WKT")

        executed_sql = []
        geom_cols = detect_geometry_columns(CString, schema, table, sql_log=executed_sql)

        wkt_list, pk_list = get_geometries_with_spatial_filter(
            CString, schema, table, filter_wkts,
            cx=cx, cy=cy, srid=srid, func=func, sql_log=executed_sql
        )

        built = null_wkt = failed = 0
        sample_fail = ""
        for i, (wkt_str, pk_val) in enumerate(zip(wkt_list, pk_list)):
            path = GH_Path(i)
            if not wkt_str or not wkt_str.strip():
                null_wkt += 1
                if pk_val is not None:
                    pk.Add(pk_val, path)
                continue
            rh_geoms = wkt_to_rhino(wkt_str)
            if isinstance(rh_geoms, list):
                added = 0
                for rh_geom in rh_geoms:
                    if rh_geom is not None:
                        geometry.Add(rh_geom, path)
                        pk.Add(pk_val, path)
                        added += 1
                if added:
                    built += 1
                else:
                    failed += 1
                    if not sample_fail:
                        sample_fail = wkt_str[:60]
            elif rh_geoms is not None:
                geometry.Add(rh_geoms, path)
                pk.Add(pk_val, path)
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
