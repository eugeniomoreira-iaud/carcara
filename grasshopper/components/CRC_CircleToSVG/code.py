"""CRC_CircleToSVG: Convert Grasshopper Circle geometries to SVG <circle> element strings.

CPython SDK-mode (advanced) component: subclass of executingcomponent that also
draws a Rhino-viewport preview of the input circles via PreviewPayload.
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

from ghpythonlib.componentbase import executingcomponent as component
import Rhino
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import System
from System.Drawing import Color

from crc_modules.svg.export import circle_to_svg
from crc_modules.rhino.preview import PreviewPayload, color_to_hex


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


class CircleToSVG(component):

    def RunScript(self, c, sc, sw, f, canvas):
        self.Message = "v{{component_version}}-{{date}}"
        svgCode = []
        report = "Provide circles on input 'c'."
        pv = PreviewPayload()

        try:
            circles = c if c else []
            if not circles:
                report = "No circles provided on input 'c'."
            else:
                # Determine canvas anchor and height for Y-flip
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

                if canvas_h == 0.0:
                    combined = rg.BoundingBox.Empty
                    for circ in circles:
                        if circ is None:
                            continue
                        try:
                            pt = circ.Center
                            r = circ.Radius
                            pt_bbox = rg.BoundingBox(
                                rg.Point3d(pt.X - r, pt.Y - r, 0),
                                rg.Point3d(pt.X + r, pt.Y + r, 0)
                            )
                            combined = rg.BoundingBox.Union(combined, pt_bbox)
                        except Exception:
                            pass
                    if combined.IsValid:
                        anchor_x = combined.Min.X
                        anchor_y = combined.Min.Y
                        canvas_h = combined.Max.Y - combined.Min.Y

                elements = []
                ok = failed = 0
                first_err = None
                for i, circ in enumerate(circles):
                    if circ is None:
                        failed += 1
                        continue
                    try:
                        cx_rhino = circ.Center.X
                        cy_rhino = circ.Center.Y
                        r = circ.Radius

                        svg_x = cx_rhino - anchor_x
                        svg_y = canvas_h - (cy_rhino - anchor_y)

                        # Colors arrive as System.Drawing.Color or None
                        stroke_color = _get(sc, i, None)
                        sw_val = float(_get(sw, i, 0) or 0)
                        if sw_val <= 0:
                            sw_val = 1.0
                        fill_color = _get(f, i, None)

                        stroke_hex = color_to_hex(stroke_color) if stroke_color is not None else "#000000"
                        fill_hex = color_to_hex(fill_color) if fill_color is not None else "none"

                        elem = circle_to_svg(
                            svg_x, svg_y, r,
                            stroke=stroke_hex,
                            stroke_width=sw_val,
                            fill=fill_hex,
                        )
                        elements.append(elem)
                        ok += 1

                        # Viewport preview — always draw; use stroke color or default black
                        crv = rg.ArcCurve(circ)
                        _preview_clr = stroke_color if stroke_color is not None else Color.Black
                        _preview_w = max(1, int(sw_val)) if sw_val else 1
                        pv.add_curve(crv, _preview_clr, _preview_w)
                        # Circles are always closed
                        if fill_color is not None:
                            pv.add_filled_curve(crv, fill_color)

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
