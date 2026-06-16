"""CRC_TextToSVG: Convert text strings with Point3d or Plane insertion to SVG <text> elements.

CPython SDK-mode (advanced) component: subclass of executingcomponent that also
draws a Rhino-viewport preview of the text annotations via PreviewPayload.
"""
import sys
import os
import math
import Grasshopper

# Dynamically route to the user objects folder via the Grasshopper API
_carcara_path = os.path.join(Grasshopper.Folders.DefaultUserObjectFolder, "carcara")

if os.path.isdir(_carcara_path) and _carcara_path not in sys.path:
    sys.path.insert(0, _carcara_path)

try:
    ghenv.Component.Message = "v{{component_version}}-{{date}}"
except Exception:
    pass

from ghpythonlib.componentbase import executingcomponent as component
import Rhino
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import System
from System.Drawing import Color
from Rhino.DocObjects import TextHorizontalAlignment, TextVerticalAlignment

from crc_modules.svg.export import text_to_svg
from crc_modules.rhino.preview import PreviewPayload, color_to_hex

# Justification mapping: int 1-9 → (text-anchor, dominant-baseline)
_JUST_MAP = {
    1: ("start",  "hanging"),   # Top Left
    2: ("middle", "hanging"),   # Top Center
    3: ("end",    "hanging"),   # Top Right
    4: ("start",  "middle"),    # Middle Left
    5: ("middle", "middle"),    # Middle Center
    6: ("end",    "middle"),    # Middle Right
    7: ("start",  "baseline"),  # Bottom Left
    8: ("middle", "baseline"),  # Bottom Center
    9: ("end",    "baseline"),  # Bottom Right
}

# Justification → Rhino TextHorizontalAlignment
_H_ALIGN_MAP = {
    1: TextHorizontalAlignment.Left,
    2: TextHorizontalAlignment.Center,
    3: TextHorizontalAlignment.Right,
    4: TextHorizontalAlignment.Left,
    5: TextHorizontalAlignment.Center,
    6: TextHorizontalAlignment.Right,
    7: TextHorizontalAlignment.Left,
    8: TextHorizontalAlignment.Center,
    9: TextHorizontalAlignment.Right,
}

# Justification → Rhino TextVerticalAlignment
_V_ALIGN_MAP = {
    1: TextVerticalAlignment.Top,
    2: TextVerticalAlignment.Top,
    3: TextVerticalAlignment.Top,
    4: TextVerticalAlignment.Middle,
    5: TextVerticalAlignment.Middle,
    6: TextVerticalAlignment.Middle,
    7: TextVerticalAlignment.Bottom,
    8: TextVerticalAlignment.Bottom,
    9: TextVerticalAlignment.Bottom,
}

DEFAULT_JUST = 6
DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_FONT_SIZE = 12
DEFAULT_FILL_COLOR = Color.Black


def _get(seq, i, default):
    if seq is None:
        return default
    if isinstance(seq, str):
        return seq
    try:
        n = len(seq)          # works for Python list AND .NET List[T]
    except TypeError:
        return seq            # scalar: Color, number, single geometry
    if n == 0:
        return default
    return seq[i] if i < n else seq[n - 1]


class TextToSVG(component):

    def RunScript(self, texts, points, fontFamily, fontSize, fillColor, canvas, justification):
        self.Message = "v{{component_version}}-{{date}}"
        svgCode = []
        report = "Provide text on input 'texts'."
        pv = PreviewPayload()

        try:
            texts_list = texts if texts else []
            if not texts_list:
                report = "No text provided on input 'texts'."
            else:
                # Canvas anchor for Y-flip
                anchor_x = 0.0
                anchor_y = 0.0
                canvas_h = 0.0

                if canvas is not None:
                    try:
                        bbox = canvas.BoundingBox
                        anchor_x = bbox.Min.X
                        anchor_y = bbox.Min.Y
                        canvas_h = bbox.Max.Y - bbox.Min.Y
                    except Exception:
                        pass

                # Resolved style constants (same for all text items)
                font_family = str(fontFamily) if fontFamily else DEFAULT_FONT_FAMILY
                font_size = float(fontSize) if fontSize else DEFAULT_FONT_SIZE
                # fillColor arrives as System.Drawing.Color or None
                fill_color = fillColor if fillColor is not None else DEFAULT_FILL_COLOR
                fill_hex = color_to_hex(fill_color) if fill_color is not None else "black"

                elements = []
                ok = failed = 0
                first_err = None
                for i, txt in enumerate(texts_list):
                    if txt is None:
                        failed += 1
                        continue
                    try:
                        ins_raw = _get(points, i, None) if points else None
                        ins = rs.coercegeometry(ins_raw) if ins_raw is not None and not isinstance(ins_raw, (rg.Plane, rg.Point3d)) else ins_raw

                        # Defaults
                        x_svg = 0.0
                        y_svg = 0.0
                        rotation = 0.0
                        preview_pt_or_plane = None

                        if ins is not None:
                            if isinstance(ins, rg.Plane):
                                rx = ins.Origin.X
                                ry = ins.Origin.Y
                                xa = ins.XAxis
                                rotation = math.degrees(math.atan2(xa.Y, xa.X))
                                rotation = -rotation  # negate for SVG Y-down
                                preview_pt_or_plane = ins
                            elif isinstance(ins, rg.Point3d):
                                rx = ins.X
                                ry = ins.Y
                                preview_pt_or_plane = ins
                            else:
                                rx = float(getattr(ins, 'X', 0))
                                ry = float(getattr(ins, 'Y', 0))
                                preview_pt_or_plane = rg.Point3d(rx, ry, 0)

                            # Y-flip
                            x_svg = rx - anchor_x
                            if canvas_h > 0:
                                y_svg = canvas_h - (ry - anchor_y)
                            else:
                                y_svg = ry

                        just_val = int(_get(justification, i, DEFAULT_JUST) or DEFAULT_JUST)
                        anchor, baseline = _JUST_MAP.get(just_val, _JUST_MAP[DEFAULT_JUST])
                        h_align = _H_ALIGN_MAP.get(just_val, TextHorizontalAlignment.Right)
                        v_align = _V_ALIGN_MAP.get(just_val, TextVerticalAlignment.Middle)

                        elem = text_to_svg(
                            x_svg, y_svg, str(txt),
                            fill=fill_hex,
                            font_family=font_family,
                            font_size=font_size,
                            text_anchor=anchor,
                            dominant_baseline=baseline,
                            rotation=rotation,
                        )
                        elements.append(elem)
                        ok += 1

                        # Viewport preview
                        if preview_pt_or_plane is not None and fill_color is not None:
                            pv.add_text(str(txt), preview_pt_or_plane, font_size, fill_color, h_align, v_align)

                    except Exception as _e:
                        failed += 1
                        if first_err is None:
                            first_err = str(_e)

                svgCode = elements
                report = "OK – {} element(s) generated".format(ok)
                if failed:
                    report += ", {} failed".format(failed)
                    if first_err is not None:
                        report += " (first: {})".format(first_err)

        except Exception as e:
            report = "ERROR: {}".format(e)

        self._pv = pv
        self.Hidden = True
        return (svgCode, report)

    def DrawViewportWires(self, args):
        if hasattr(self, "_pv"):
            self._pv.draw_wires(args)

    def DrawViewportMeshes(self, args):
        if hasattr(self, "_pv"):
            self._pv.draw_meshes(args)

    def get_ClippingBox(self):
        return self._pv.clipping_box if hasattr(self, "_pv") else Rhino.Geometry.BoundingBox.Empty
