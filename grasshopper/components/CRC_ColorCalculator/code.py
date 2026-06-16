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

    # 2. STRIPPED STRICT TYPE HINTS TO FORCE COMPILATION
    def RunScript(self,
      val: Grasshopper.DataTree[object],
      col: object,
      cls: object,
      lin: bool,
      leg_cfg: str,
      leg_pln: Rhino.Geometry.Plane):

        # 3. INTERNAL COMPONENT TRACING
        out = ["--- INTERNAL RUNSCRIPT TRACE ---"]
        col_out = DataTree[object]()
        leg_geo = None
        txt_loc = []
        txt_con = []
        txt_siz = []
        stats = ""
        report = "Executing..."

        self._pv = None
        self.Hidden = True

        out.append("STEP 1: Checking inputs...")

        try:
            input_colors = list(col) if col else []
            if not input_colors:
                out.append("INFO: Using default gradient.")
                gradient_argb = default_gradient_argb()
            else:
                out.append("INFO: Parsing {} input colors.".format(len(input_colors)))
                gradient_argb = [_color_to_argb_tuple(c) for c in input_colors]

            input_lin = bool(lin) if lin is not None else True
            input_leg_cfg = str(leg_cfg) if leg_cfg else None
            input_leg_pln = leg_pln if leg_pln else rg.Plane.WorldXY
            cls_raw = list(cls) if cls else [0]

            if val is None or val.BranchCount == 0:
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
                for i in range(val.BranchCount):
                    path = val.Path(i)
                    branch = list(val.Branch(i))
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
                    col_out = DataTree[object]()
                    idx = 0
                    for path, branch in branches:
                        for _ in branch:
                            argb = argb_per_value[idx]
                            col_out.Add(_argb_to_color(argb) if argb is not None else Color.Gray, path)
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
                    leg_geo = mesh

                    out.append("STEP 6: Mapping text and stats...")
                    txt_loc = [input_leg_pln.PointAt(x, y, 0) for (x, y, _t, _s) in layout['labels']]
                    txt_con = [lbl[2] for lbl in layout['labels']]
                    txt_siz = [lbl[3] for lbl in layout['labels']]

                    stats = compute_statistics(valid_vals)

                    out.append("STEP 7: Binding PreviewPayload...")
                    pv = PreviewPayload()
                    pv.add_mesh(leg_geo)
                    _text_color = System.Drawing.Color.Black
                    for loc, txt, siz in zip(txt_loc, txt_con, txt_siz):
                        pv.add_text(str(txt), loc, float(siz), _text_color)
                    self._pv = pv

                    report = "OK - {} values processed".format(len(valid_vals))
                    out.append("SUCCESS: RunScript complete.")

        except Exception as _exc:
            import traceback
            _tb = traceback.format_exc()
            out.append("CRITICAL ERROR IN RUNSCRIPT:\n{}".format(_tb))
            report = "ERROR: See 'out' panel."

        return (out, col_out, leg_geo, txt_loc, txt_con, txt_siz, stats, report)

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
