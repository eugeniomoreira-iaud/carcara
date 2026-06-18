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

# INPUT MAPPING  0:geo:tree
geo_int = _in_tree(0)

WKT, report = DataTree[object](), "No geometry provided"

if geo_int is not None and hasattr(geo_int, "BranchCount") and geo_int.BranchCount > 0:
    branches = geo_int.BranchCount
    converted = empty = errors = 0
    err_msg = ""
    for i in range(branches):
        path = geo_int.Path(i)
        members = list(geo_int.Branch(i))
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
