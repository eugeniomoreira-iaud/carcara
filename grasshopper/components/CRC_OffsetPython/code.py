"""CRC_OffsetPython: Offset planar curves using Rhino's Curve.Offset.

No CToggle — executes on data arrival (matches legacy).
DataTree fan-out, distance cyclic mapping, and None-fill for failures
are handled here (GH plumbing). Offset algorithm lives in crc_modules/rhino/offset.py.
"""
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
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

from crc_modules.rhino.offset import get_corner_style, offset_curve, DEFAULT_TOLERANCE

# ── Resolve inputs ────────────────────────────────────────────────────────────
# curves and distances arrive as DataTrees via GHPython tree access.
# cornerStyle is a single item (may be None → default to 1 = Sharp).

_style_int = int(cornerStyle) if cornerStyle is not None else 1
_corner_style = get_corner_style(_style_int)

_curves_tree  = ghenv.Component.Params.Input[0].VolatileData
_dist_tree    = ghenv.Component.Params.Input[1].VolatileData

offsetCurves = DataTree[object]()

_log_lines = ["Corner style: {}".format(_style_int)]
_total = _ok = _fail = 0


def _unwrap(v):
    return v.Value if hasattr(v, "Value") else v


def _get_branch(tree, path):
    """Return branch as list; falls back to the sole branch if path absent."""
    if tree.PathExists(path):
        return [_unwrap(x) for x in tree[path]]
    if tree.PathCount == 1:
        return [_unwrap(x) for x in tree[tree.Path(0)]]
    return []


try:
    if _curves_tree.PathCount == 0:
        _log_lines.append("WARNING: No curves provided.")
    else:
        _log_lines.append("Processing {} branch(es)...".format(_curves_tree.PathCount))

        for _path in _curves_tree.Paths:
            _curves   = [_unwrap(c) for c in _curves_tree[_path]]
            _dists    = _get_branch(_dist_tree, _path)

            # Cyclic distance mapping
            if len(_dists) == 0:
                _mapped = [0.0] * len(_curves)
            elif len(_dists) == 1:
                _mapped = _dists * len(_curves)
            elif len(_dists) != len(_curves):
                _log_lines.append(
                    "Branch {}: dist count ({}) != crv count ({}); cyclic mapping.".format(
                        _path, len(_dists), len(_curves)))
                _mapped = [_dists[i % len(_dists)] for i in range(len(_curves))]
            else:
                _mapped = _dists

            for _i, _crv in enumerate(_curves):
                _total += 1
                _d = float(_mapped[_i]) if _i < len(_mapped) else 0.0
                _result, _err = offset_curve(_crv, _d, _corner_style, DEFAULT_TOLERANCE)

                if _result is not None:
                    offsetCurves.Add(_result, _path)
                    _ok += 1
                else:
                    offsetCurves.Add(None, _path)
                    _fail += 1
                    if _err:
                        _log_lines.append("  [{} #{}]: {}".format(_path, _i, _err))

        _log_lines.append("Offset: {}/{} curves successful.".format(_ok, _total))
        if _fail:
            _log_lines.append("WARNING: {} curve(s) failed — see details above.".format(_fail))

except Exception as _ex:
    _log_lines.append("ERROR: {} ({})".format(_ex, type(_ex).__name__))

out = "\n".join(_log_lines)
