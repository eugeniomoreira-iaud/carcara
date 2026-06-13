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

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.db.spatial_query import get_geometries_with_spatial_filter
from crc_modules.rhino.wkt_conversion import wkt_to_rhino, rh_geometry_to_wkt

geometry, pk, report = DataTree[object](), DataTree[object](), "Set 'CToggle' to True to execute"

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")
        if spatial_filter is None:
            raise ValueError("spatial_filter geometry is required")

        srid = int(SRID) if SRID else 4326
        func = int(function) if function else 0
        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"
        sql_filter = sql_filter if sql_filter else None

        # Convert GH geometry to WKT for spatial filter
        filter_wkt = rh_geometry_to_wkt(spatial_filter)
        if not filter_wkt:
            raise ValueError("Failed to convert spatial filter geometry to WKT")

        wkt_list, pk_list = get_geometries_with_spatial_filter(
            CString, schema, table, filter_wkt,
            cx=cx, cy=cy, srid=srid, sql_filter=sql_filter, func=func
        )

        # Convert WKT to Rhino geometry, split multi-part on same branch
        for i, (wkt_str, pk_val) in enumerate(zip(wkt_list, pk_list)):
            path = GH_Path(i)

            if not wkt_str or not wkt_str.strip():
                if pk_val is not None:
                    pk.Add(pk_val, path)
                continue

            rh_geoms = wkt_to_rhino(wkt_str)

            if isinstance(rh_geoms, list):
                for rh_geom in rh_geoms:
                    if rh_geom is not None:
                        geometry.Add(rh_geom, path)
                        pk.Add(pk_val, path)
            elif rh_geoms is not None:
                geometry.Add(rh_geoms, path)
                pk.Add(pk_val, path)

        report = f"OK – {len(wkt_list)} rows returned"
    except Exception as e:
        report = f"ERROR: {e}"
