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

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree
from shapely import wkt as shapely_wkt

from crc_modules.db.spatial_query import get_geometries
from crc_modules.rhino.wkt_conversion import wkt_to_rhino

geometry, pk, report = DataTree[object](), DataTree[object](), "Set 'CToggle' to True to execute"

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")

        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"

        wkt_list, pk_list = get_geometries(CString, schema, table, cx=cx, cy=cy)

        # Convert WKT to Rhino geometry, split multi-part on same branch
        for i, (wkt_str, pk_val) in enumerate(zip(wkt_list, pk_list)):
            path = GH_Path(i)

            if not wkt_str or not wkt_str.strip():
                if pk_val is not None:
                    pk.Add(pk_val, path)
                continue

            rh_geoms = wkt_to_rhino(wkt_str)

            if isinstance(rh_geoms, list):
                # Multi-part: each member on same branch
                for rh_geom in rh_geoms:
                    if rh_geom is not None:
                        geometry.Add(rh_geom, path)
                        pk.Add(pk_val, path)
            elif rh_geoms is not None:
                geometry.Add(rh_geoms, path)
                # PK value goes once on the branch for single-part too
                pk.Add(pk_val, path)

        report = f"OK – {len(wkt_list)} rows returned"
    except Exception as e:
        report = f"ERROR: {e}"
