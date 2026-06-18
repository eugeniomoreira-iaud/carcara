"""CRC_SortByContainer: Sort points into DataTree branches by container curves."""
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

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt
from crc_modules.geometry.containment import sort_points_by_containers

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
def _unwrap(v):
    return v.Value if hasattr(v, "Value") else v

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

# INPUT MAPPING: 0:C(containers/tree), 1:P(points/tree)
C_int = _in_tree(0)
P_int = _in_tree(1)


def _flatten_tree(tree):
    """Return flat Python list from a DataTree (all branches concatenated)."""
    result = []
    for bi in range(tree.PathCount):
        path = tree.Path(bi)
        for item in tree.Branch(path):
            result.append(_unwrap(item))
    return result


indices = DataTree[object]()
report = "Provide container curves (containers) and points (points)."

try:
    _containers_empty = (C_int is None or C_int.PathCount == 0 or
                         all(len(C_int.Branch(C_int.Path(bi))) == 0
                             for bi in range(C_int.PathCount)))
    _points_empty = (P_int is None or P_int.PathCount == 0 or
                     all(len(P_int.Branch(P_int.Path(bi))) == 0
                         for bi in range(P_int.PathCount)))

    if _containers_empty or _points_empty:
        report = "ERROR: Both containers and points inputs are required."
    else:
        # Flatten both trees to plain Python lists (global indices)
        flat_containers = _flatten_tree(C_int)
        flat_points = _flatten_tree(P_int)

        # Convert Rhino curves → WKT strings (None for unconvertible)
        container_wkts = []
        for c in flat_containers:
            if c is None:
                container_wkts.append(None)
            else:
                container_wkts.append(rh_geometry_to_wkt(c))

        # Convert Rhino Point3d → (x, y) tuples
        import Rhino.Geometry as rg
        point_coords = []
        for p in flat_points:
            if p is None:
                point_coords.append((0.0, 0.0))
            elif isinstance(p, rg.Point3d):
                point_coords.append((p.X, p.Y))
            else:
                point_coords.append((float(p.X), float(p.Y)))

        # Run containment sort (pure Python) — returns list of lists of global indices
        branches = sort_points_by_containers(container_wkts, point_coords)

        # Build DataTree output — branch k ↔ containers[k]
        indices = DataTree[object]()
        for branch_idx, idx_list in enumerate(branches):
            path = GH_Path(branch_idx)
            indices.EnsurePath(path)
            for pt_idx in idx_list:
                indices.Add(pt_idx, path)

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
