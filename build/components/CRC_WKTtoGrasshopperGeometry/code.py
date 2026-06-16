"""CRC_WKTtoGrasshopperGeometry: convert WKT strings to Grasshopper geometry."""
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

from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.rhino.wkt_conversion import wkt_to_rhino

geometry, report = DataTree[object](), "No WKT strings provided"

wkt_inputs = wktGeometry if isinstance(wktGeometry, (list, tuple)) else ([wktGeometry] if wktGeometry else [])

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
                    geometry.Add(g, path)
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
            geometry.Add(rh, path)
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
