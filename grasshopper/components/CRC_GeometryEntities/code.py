"""CRC_GeometryEntities: Query geometries from a PostGIS table with coordinate correction."""
import sys
import os

# Make the crc_modules package importable from a Grasshopper Python 3 component.
# GHPython runs this code from an in-memory string, so __file__ is undefined.
# The installer copies the whole deployable folder to:
#   %APPDATA%\Grasshopper\UserObjects\carcara\   (Windows)
# with the package at .../carcara/crc_modules. Put the PARENT (.../carcara) on
# sys.path so `import crc_modules` resolves.
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
from shapely import wkt as shapely_wkt

from crc_modules.db.spatial_query import get_geometries, detect_geometry_columns
from crc_modules.rhino.wkt_conversion import wkt_to_rhino

geometry, pk, report, queries = DataTree[object](), DataTree[object](), "Set 'CToggle' to True to execute", ""

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")

        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"

        executed_sql = []
        geom_cols = detect_geometry_columns(CString, schema, table, sql_log=executed_sql)

        wkt_list, pk_list = get_geometries(CString, schema, table, cx=cx, cy=cy, sql_log=executed_sql)

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
