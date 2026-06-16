"""CRC_WKTtoGrasshopperGeometry: convert WKT strings to Grasshopper geometry."""
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

from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.rhino.wkt_conversion import wkt_to_rhino

geom, report = DataTree[object](), "No WKT strings provided"

wkt_inputs = WKT_geom if isinstance(WKT_geom, (list, tuple)) else ([WKT_geom] if WKT_geom else [])

if wkt_inputs:
    built = failed = multipart = 0
    sample_fail = ""
    for i, wkt_str in enumerate(wkt_inputs):
        path = GH_Path(i)
        if not wkt_str or not str(wkt_str).strip():
            failed += 1
            continue
        try:
            rh = wkt_to_rhino(str(wkt_str))
        except Exception:
            rh = None
        if isinstance(rh, list):
            added = 0
            for g in rh:
                if g is not None:
                    geom.Add(g, path)
                    added += 1
            if added:
                built += 1
                if added > 1:
                    multipart += 1
            else:
                failed += 1
                if not sample_fail:
                    sample_fail = str(wkt_str)[:60]
        elif rh is not None:
            geom.Add(rh, path)
            built += 1
        else:
            failed += 1
            if not sample_fail:
                sample_fail = str(wkt_str)[:60]

    report = (
        "OK\n"
        "  WKT strings: {}\n"
        "  converted: {}\n"
        "  multipart: {}\n"
        "  failed: {}".format(len(wkt_inputs), built, multipart, failed)
    )
    if sample_fail:
        report += "\n  sample failed WKT: {}...".format(sample_fail)
