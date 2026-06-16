"""CRC_GrasshopperGeometryToWKT: convert Grasshopper geometry to WKT strings."""
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

from Grasshopper import DataTree

from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt
from crc_modules.geometry.wkt import combine_to_multipart

WKT, report = DataTree[object](), "No geometry provided"

if geom is not None and hasattr(geom, "BranchCount") and geom.BranchCount > 0:
    branches = geom.BranchCount
    converted = empty = errors = 0
    err_msg = ""
    for i in range(branches):
        path = geom.Path(i)
        members = list(geom.Branch(i))
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
