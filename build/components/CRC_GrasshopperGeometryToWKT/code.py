"""CRC_GrasshopperGeometryToWKT: convert Grasshopper geometry to WKT strings."""
# r: shapely
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

from Grasshopper import DataTree

from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt
from crc_modules.geometry.wkt import combine_to_multipart

WKT, report = DataTree[object](), "No geometry provided"

if geometry is not None and hasattr(geometry, "BranchCount") and geometry.BranchCount > 0:
    branches = geometry.BranchCount
    converted = empty = errors = 0
    err_msg = ""
    for i in range(branches):
        path = geometry.Path(i)
        members = list(geometry.Branch(i))
        wkt_parts = []
        for g in members:
            w = rh_geometry_to_wkt(g)
            if w:
                wkt_parts.append(w)
        if not wkt_parts:
            empty += 1
            continue
        try:
            out = wkt_parts[0] if len(wkt_parts) == 1 else combine_to_multipart(wkt_parts)
            WKT.Add(out, path)
            converted += 1
        except Exception as e:
            errors += 1
            if not err_msg:
                err_msg = "branch {}: {}".format(i, e)

    report = (
        "OK\n"
        "  branches: {}\n"
        "  converted: {}\n"
        "  empty: {}\n"
        "  errors: {}".format(branches, converted, empty, errors)
    )
    if err_msg:
        report += "\n  first error: {}".format(err_msg)
