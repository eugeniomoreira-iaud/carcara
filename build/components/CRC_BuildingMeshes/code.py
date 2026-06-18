"""CRC_BuildingMeshes: Extrude building footprints to Ground / Lateral / Roof meshes.

No CToggle — executes on data arrival (matches legacy).
DataTree iteration, height fan-out, empty-branch preservation, and the
performance summary are handled here (GH plumbing).
Mesh algorithms live in crc_modules/rhino/building_mesh.py.
"""
import sys
import os
import time
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
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

from crc_modules.rhino.building_mesh import (
    group_polygons_with_holes_and_heights,
    create_building_mesh_with_holes,
)

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

# INPUT MAPPING  0:fp:tree  1:h:tree
fp_int = _in_tree(0)
h_int  = _in_tree(1)

groundFaces = DataTree[object]()
lateralFaces = DataTree[object]()
rooftopFaces = DataTree[object]()

_t0 = time.time()
_total_branches = _empty_branches = _total_bldg = _ok_bldg = _fail_bldg = 0
_log = []


def _unwrap(v):
    return v.Value if hasattr(v, "Value") else v


def _get_h_branch(tree, path):
    """Return height branch for path; fall back to the sole branch."""
    if tree.PathExists(path):
        return [_unwrap(x) for x in tree.Branch(path)]
    if tree.BranchCount == 1:
        return [_unwrap(x) for x in tree.Branch(tree.Path(0))]
    return []


def _resolve_heights(raw_heights, fp_count):
    """Return list of floats (one per footprint) or raise ValueError."""
    if len(raw_heights) == 0:
        raise ValueError("Height branch is empty.")
    if len(raw_heights) == 1:
        h = float(raw_heights[0])
        if h <= 0:
            raise ValueError("Height must be positive; got {}.".format(h))
        return [h] * fp_count
    if len(raw_heights) != fp_count:
        raise ValueError(
            "Height count ({}) != footprint count ({}).".format(len(raw_heights), fp_count)
        )
    heights = [float(h) for h in raw_heights]
    for i, h in enumerate(heights):
        if h <= 0:
            raise ValueError("Height[{}] must be positive; got {}.".format(i, h))
    return heights


try:
    if fp_int.BranchCount == 0:
        _log.append("WARNING: No footprints provided.")
    elif h_int.BranchCount == 0:
        _log.append("WARNING: No heights provided.")
    else:
        _total_branches = fp_int.BranchCount

        for _i in range(fp_int.BranchCount):
            _path = fp_int.Path(_i)

            # Ensure branch exists in all output trees (preserves empty branches)
            groundFaces.EnsurePath(_path)
            lateralFaces.EnsurePath(_path)
            rooftopFaces.EnsurePath(_path)

            _fps = [_unwrap(x) for x in fp_int.Branch(_path)]

            if not _fps:
                _empty_branches += 1
                continue

            _raw_h = _get_h_branch(h_int, _path)

            try:
                _heights = _resolve_heights(_raw_h, len(_fps))
            except ValueError as _ve:
                _log.append("Branch {}: {}".format(_path, _ve))
                _fail_bldg += len(_fps)
                continue

            _groups = group_polygons_with_holes_and_heights(_fps, _heights)
            _total_bldg += len(_groups)

            for _ext, _holes, _h in _groups:
                try:
                    _grd, _lat, _rft = create_building_mesh_with_holes(_ext, _holes, _h)
                    if _grd and _lat and _rft:
                        groundFaces.Add(_grd, _path)
                        lateralFaces.Add(_lat, _path)
                        rooftopFaces.Add(_rft, _path)
                        _ok_bldg += 1
                    else:
                        _fail_bldg += 1
                        _log.append("Branch {}: mesh creation returned None.".format(_path))
                except Exception as _be:
                    _fail_bldg += 1
                    _log.append("Branch {}: {}".format(_path, _be))

except Exception as _ex:
    _log.append("ERROR: {} ({})".format(_ex, type(_ex).__name__))

_elapsed = time.time() - _t0

_summary = (
    "=== BuildingMeshes ===\n"
    "  Branches:  {} total / {} empty / {} processed\n"
    "  Buildings: {} total / {} OK / {} failed\n"
    "  Time:      {:.3f}s".format(
        _total_branches,
        _empty_branches,
        _total_branches - _empty_branches,
        _total_bldg,
        _ok_bldg,
        _fail_bldg,
        _elapsed,
    )
)
if _log:
    _summary += "\n--- Details ---\n" + "\n".join(_log)

out = _summary
