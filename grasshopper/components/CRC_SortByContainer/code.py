"""CRC_SortByContainer: Sort points into DataTree branches by container curves."""
import sys
import os

# Make crc_modules importable from Grasshopper UserObjects path.
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
    ghenv.Component.Message = "v{{version}}"
except Exception:
    pass

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt
from crc_modules.geometry.containment import sort_points_by_containers

i = DataTree[object]()
report = "Provide container curves (crv) and points (pt)."

try:
    if not crv or not pt:
        report = "ERROR: Both crv and pt inputs are required."
    else:
        # Convert Rhino curves → WKT strings (None for unconvertible)
        container_wkts = []
        for c in crv:
            if c is None:
                container_wkts.append(None)
            else:
                container_wkts.append(rh_geometry_to_wkt(c))

        # Convert Rhino Point3d → (x, y) tuples
        import Rhino.Geometry as rg
        point_coords = []
        for p in pt:
            if p is None:
                point_coords.append((0.0, 0.0))
            elif isinstance(p, rg.Point3d):
                point_coords.append((p.X, p.Y))
            else:
                # Try treating as a generic object with X/Y attributes
                point_coords.append((float(p.X), float(p.Y)))

        # Run containment sort (pure Python)
        branches = sort_points_by_containers(container_wkts, point_coords)

        # Build DataTree output
        i = DataTree[object]()
        for branch_idx, idx_list in enumerate(branches):
            path = GH_Path(branch_idx)
            i.EnsurePath(path)
            for pt_idx in idx_list:
                i.Add(pt_idx, path)

        total_sorted = sum(len(b) for b in branches)
        empty_branches = sum(1 for b in branches if not b)
        report = (
            "OK — {sorted} of {total} point(s) sorted into {n} container(s)"
            " ({empty} empty branch(es)).".format(
                sorted=total_sorted,
                total=len(point_coords),
                n=len(branches),
                empty=empty_branches,
            )
        )

except Exception as e:
    report = "ERROR: {}".format(e)
