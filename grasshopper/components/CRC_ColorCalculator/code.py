"""CRC_ColorCalculator: Data-driven color assignment with legend generation.

Maps a tree of numeric values to colors via a gradient. Supports:
  - Continuous gradient (cls=0)
  - Fixed number of classes (cls = positive int)
  - Custom class boundaries (cls = list of floats)

Outputs a color tree matching input structure, plus legend mesh, text
anchor points, label strings, text heights, and statistics summary.
"""
import sys
import os
import math

# Make the crc_modules package importable from a Grasshopper Python 3 component.
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
    ghenv.Component.Message = "v{{version}} - {{date}}"
except Exception:
    pass

import clr
clr.AddReference("Grasshopper")
clr.AddReference("System.Drawing")
clr.AddReference("RhinoCommon")

from System.Drawing import Color
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import Rhino.Geometry as rg

from crc_modules.utils.color import (
    default_gradient_argb,
    parse_legend_config,
    compute_color_assignment,
    compute_statistics,
    legend_layout,
)


def _color_to_argb_tuple(c):
    """Convert System.Drawing.Color to (A, R, G, B) tuple."""
    return (int(c.A), int(c.R), int(c.G), int(c.B))


def _argb_to_color(t):
    return Color.FromArgb(int(t[0]), int(t[1]), int(t[2]), int(t[3]))


def _is_valid_number(x):
    try:
        fv = float(x)
        return not math.isnan(fv) and not math.isinf(fv)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Outputs (defaults)
# ---------------------------------------------------------------------------

out = []
col_out = DataTree[object]()
leg_geo = None
txt_loc = []
txt_con = []
txt_siz = []
stats = ""
report = "Provide val and col inputs to execute"

try:
    # --- Input coercion ---
    input_colors = list(col) if col else []
    if not input_colors:
        gradient_argb = default_gradient_argb()
    else:
        gradient_argb = [_color_to_argb_tuple(c) for c in input_colors]

    input_lin = bool(lin) if lin is not None else True
    input_leg_cfg = str(leg_cfg) if leg_cfg else None
    input_leg_pln = leg_pln if leg_pln else rg.Plane.WorldXY

    cls_raw = list(cls) if cls else [0]

    if val is None or val.BranchCount == 0:
        report = "No values provided"
    elif len(gradient_argb) < 2:
        report = "At least 2 colors required"
    else:
        cfg = parse_legend_config(input_leg_cfg)

        # Collect tree structure + flat list of values
        branches = []
        values_flat = []
        for i in range(val.BranchCount):
            path = val.Path(i)
            branch = list(val.Branch(i))
            branches.append((path, branch))
            values_flat.extend(branch)

        # Collect valid numeric floats for stats and report count
        valid_vals = [float(item) for item in values_flat
                      if item is not None and _is_valid_number(item)]

        if not valid_vals:
            report = "No valid numeric values"
        else:
            # Delegate all computation to pure module
            argb_per_value, leg_ranges, leg_colors_argb = compute_color_assignment(
                values_flat, gradient_argb, cls_raw, input_lin, cfg
            )

            # Rebuild DataTree of colors (parallel to values_flat order)
            col_out = DataTree[object]()
            idx = 0
            for path, branch in branches:
                for _ in branch:
                    argb = argb_per_value[idx]
                    col_out.Add(_argb_to_color(argb) if argb is not None else Color.Gray, path)
                    idx += 1

            # Legend geometry from pure layout data
            layout = legend_layout(cfg, leg_ranges, leg_colors_argb)
            mesh = rg.Mesh()
            for quad, argb in zip(layout['segment_quads'], layout['segment_argb']):
                col_gh = _argb_to_color(argb)
                pts = [input_leg_pln.PointAt(x, y, 0) for (x, y) in quad]
                v0 = mesh.Vertices.Add(pts[0])
                v1 = mesh.Vertices.Add(pts[1])
                v2 = mesh.Vertices.Add(pts[2])
                v3 = mesh.Vertices.Add(pts[3])
                mesh.Faces.AddFace(v0, v1, v2, v3)
                for _ in range(4):
                    mesh.VertexColors.Add(col_gh)
            mesh.FaceNormals.ComputeFaceNormals()
            mesh.Normals.ComputeNormals()
            mesh.UnifyNormals()
            mesh.Compact()
            leg_geo = mesh

            txt_loc = [input_leg_pln.PointAt(x, y, 0) for (x, y, _t, _s) in layout['labels']]
            txt_con = [lbl[2] for lbl in layout['labels']]
            txt_siz = [lbl[3] for lbl in layout['labels']]

            stats = compute_statistics(valid_vals)

            out.append("Processed {} values".format(len(values_flat)))
            report = "OK - {} values processed, {} legend segments".format(
                len(valid_vals), len(leg_ranges)
            )

    col = col_out

except Exception as _exc:
    import traceback
    _tb = traceback.format_exc()
    report = "ERROR: {}".format(_exc)
    out.append("Error: {}\n{}".format(_exc, _tb))
    col = DataTree[object]()
    leg_geo = None
    txt_loc = []
    txt_con = []
    txt_siz = []
    stats = ""
