"""CRC_ColorCalculator: Data-driven color assignment with legend generation."""
import sys
import os
import math
import Rhino

# 1. ROOT LEVEL TRACING
Rhino.RhinoApp.WriteLine("--- MODULE LOAD START ---")

try:
    import System
    import clr
    clr.AddReference("System.Drawing")
    import System.Drawing
    import System.Collections.Generic
    Rhino.RhinoApp.WriteLine("SUCCESS: System namespaces loaded.")
except Exception as e:
    Rhino.RhinoApp.WriteLine("FATAL ERROR: System import failed: {}".format(e))

try:
    import Grasshopper
    from Grasshopper import DataTree
    from Grasshopper.Kernel.Data import GH_Path
    import Rhino.Geometry as rg
    from ghpythonlib.componentbase import executingcomponent as component
    from System.Drawing import Color
    Rhino.RhinoApp.WriteLine("SUCCESS: Grasshopper/Rhino namespaces loaded.")
except Exception as e:
    Rhino.RhinoApp.WriteLine("FATAL ERROR: Grasshopper/Rhino import failed: {}".format(e))

Rhino.RhinoApp.WriteLine("ACTION: Appending to sys.path...")

# Dynamically route to the user objects folder via the Grasshopper API
_carcara_path = os.path.join(Grasshopper.Folders.DefaultUserObjectFolder, "carcara")

if os.path.isdir(_carcara_path) and _carcara_path not in sys.path:
    sys.path.insert(0, _carcara_path)

try:
    ghenv.Component.Message = "v{{component_version}}-{{date}}"
    ghenv.Component.Params.Output[3].Hidden = True
except Exception:
    pass

try:
    from crc_modules.utils.color import (
        default_gradient_argb,
        parse_legend_config,
        compute_color_assignment,
        compute_statistics,
        legend_layout,
    )
    from crc_modules.rhino.preview import PreviewPayload
    Rhino.RhinoApp.WriteLine("SUCCESS: crc_modules imported.")
except Exception as e:
    Rhino.RhinoApp.WriteLine("FATAL ERROR: crc_modules import failed: {}".format(e))

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
from Grasshopper import DataTree

def _unwrap(g):
    if g is None:
        return None
    try:
        return g.ScriptVariable()
    except Exception:
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

def _color_to_argb_tuple(c):
    return (int(c.A), int(c.R), int(c.G), int(c.B))

def _argb_to_color(t):
    return Color.FromArgb(int(t[0]), int(t[1]), int(t[2]), int(t[3]))

def _is_valid_number(x):
    try:
        fv = float(x)
        return not math.isnan(fv) and not math.isinf(fv)
    except Exception:
        return False

Rhino.RhinoApp.WriteLine("ACTION: Defining ColorCalculator class...")

class ColorCalculator(component):

    def RunScript(self,
      valueTree: Grasshopper.DataTree[object],
      colorGrad,
      classCount,
      linear,
      legendCfg,
      legendPlane):
        self.Message = "v{{component_version}}-{{date}}"
        # ── INPUT MAPPING (index-based) ──────────────────────────────────────
        val_int    = _in_tree(0)
        col_int    = _in_list(1)
        cls_int    = _in_list(2)
        lin_int    = _in_item(3)
        legCfg_int = _in_item(4)
        legPln_int = _in_item(5)
        # ────────────────────────────────────────────────────────────────────

        # INTERNAL COMPONENT TRACING
        out = ["--- INTERNAL RUNSCRIPT TRACE ---"]
        out = ["--- INTERNAL RUNSCRIPT TRACE ---"]
        colors = DataTree[object]()
        legendGeo = None
        textLocations = []
        textContents = []
        textSizes = []
        stats = ""
        report = "Executing..."

        self._pv = None
        self.Hidden = True

        out.append("STEP 1: Checking inputs...")

        try:
            input_colors = list(col_int) if col_int else []
            if not input_colors:
                out.append("INFO: Using default gradient.")
                gradient_argb = default_gradient_argb()
            else:
                out.append("INFO: Parsing {} input colors.".format(len(input_colors)))
                gradient_argb = [_color_to_argb_tuple(c) for c in input_colors]

            input_lin = bool(lin_int) if lin_int is not None else True
            input_leg_cfg = str(legCfg_int) if legCfg_int else None
            input_leg_pln = legPln_int if legPln_int else rg.Plane.WorldXY
            cls_raw = list(cls_int) if cls_int else [0]

            if val_int is None or val_int.BranchCount == 0:
                out.append("STOP: No values provided.")
                report = "No values provided"
            elif len(gradient_argb) < 2:
                out.append("STOP: Not enough colors.")
                report = "At least 2 colors required"
            else:
                out.append("STEP 2: Parsing config & flattening tree...")
                cfg = parse_legend_config(input_leg_cfg)

                branches = []
                values_flat = []
                for i in range(val_int.BranchCount):
                    path = val_int.Path(i)
                    branch = list(val_int.Branch(i))
                    branches.append((path, branch))
                    values_flat.extend(branch)

                valid_vals = [float(item) for item in values_flat
                              if item is not None and _is_valid_number(item)]

                if not valid_vals:
                    out.append("STOP: No valid numeric floats found in tree.")
                    report = "No valid numeric values"
                else:
                    out.append("STEP 3: Hitting compute_color_assignment module...")
                    argb_per_value, leg_ranges, leg_colors_argb = compute_color_assignment(
                        values_flat, gradient_argb, cls_raw, input_lin, cfg
                    )

                    out.append("STEP 4: Rebuilding color DataTree...")
                    colors = DataTree[object]()
                    idx = 0
                    for path, branch in branches:
                        for _ in branch:
                            argb = argb_per_value[idx]
                            colors.Add(_argb_to_color(argb) if argb is not None else Color.Gray, path)
                            idx += 1

                    out.append("STEP 5: Generating legend mesh layout...")
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
                    legendGeo = mesh

                    out.append("STEP 7: Mapping text and stats...")
                    textLocations = [input_leg_pln.PointAt(x, y, 0) for (x, y, _t, _s) in layout['labels']]
                    textContents = [lbl[2] for lbl in layout['labels']]
                    textSizes = [lbl[3] for lbl in layout['labels']]

                    stats = compute_statistics(valid_vals)

                    out.append("STEP 8: Binding PreviewPayload...")
                    pv = PreviewPayload()
                    pv.add_mesh(legendGeo)
                    _text_color = System.Drawing.Color.Black
                    for loc, txt, siz in zip(textLocations, textContents, textSizes):
                        pv.add_text(str(txt), loc, float(siz), _text_color)
                    self._pv = pv

                    report = "OK - {} values processed".format(len(valid_vals))
                    out.append("SUCCESS: RunScript complete.")

        except Exception as _exc:
            import traceback
            _tb = traceback.format_exc()
            out.append("CRITICAL ERROR IN RUNSCRIPT:\n{}".format(_tb))
            report = "ERROR: See 'out' panel."

        return (out, colors, legendGeo, textLocations, textContents, textSizes, stats, report)

    def DrawViewportWires(self, args):
        if getattr(self, "_pv", None):
            self._pv.draw_wires(args)

    def DrawViewportMeshes(self, args):
        if getattr(self, "_pv", None):
            self._pv.draw_meshes(args)

    def get_ClippingBox(self):
        if getattr(self, "_pv", None):
            return self._pv.clipping_box
        return rg.BoundingBox.Empty

Rhino.RhinoApp.WriteLine("--- MODULE LOAD COMPLETE ---")
