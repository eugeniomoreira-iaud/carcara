"""CRC_Histogram: Renders a histogram chart in the Rhino viewport and exports raw SVG body content.

SDK-mode (advanced) component -- subclasses executingcomponent so that
DrawViewportWires / DrawViewportMeshes / get_ClippingBox can be overridden
for a live Rhino viewport preview (colored bar fills, axis/grid wires, text
tags). Chain svgCode into CRC_SaveSVG to write the file.
"""
import sys
import os
import Rhino
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
import System
import Rhino.Geometry as rg
import System.Drawing as sd

from crc_modules.viz.histogram import create_histogram
from crc_modules.svg.export import polyline_to_svg, text_to_svg
from crc_modules.rhino.preview import PreviewPayload


# Matplotlib-cycle colours used for bar fills in viewport (same grey as SVG)
_BAR_FILL  = sd.Color.FromArgb(255, 170, 170, 170)   # #AAAAAA
_BAR_EDGE  = sd.Color.Black
_AXIS_CLR  = sd.Color.Black
_GRID_CLR  = sd.Color.FromArgb(255, 204, 204, 204)   # #CCCCCC
_TEXT_CLR  = sd.Color.Black


class Histogram(component):

    def RunScript(self, canvasRect, dataValues, numBins, numXLabels, numYLabels, decimals, axisExtension, labelDist, drawGridY, barOutlineWidth, axisLineWidth, gridLineWidth):
        self.Message = "v{{component_version}}-{{date}}"

        # -- Width defaults --------------------------------------------------
        _bw = float(barOutlineWidth) if barOutlineWidth is not None else 1.0
        _aw = float(axisLineWidth) if axisLineWidth is not None else 2.0
        _gw = float(gridLineWidth) if gridLineWidth is not None else 1.0

        # -- Default demo data for instant preview ---------------------------
        _default_values = [12, 19, 25, 30, 42, 38, 27, 20, 15, 10]

        # -- Output defaults -------------------------------------------------
        report   = "Rendering default histogram..."
        bars     = []
        axes     = []
        x_pts    = []
        x_txt    = []
        y_pts    = []
        y_txt    = []
        grid     = []
        svg_code = ""

        pv = PreviewPayload()
        self._pv = pv

        try:
            values_list = ([float(x) for x in dataValues if x is not None]
                           if dataValues else _default_values)

            # -- Canvas extraction -------------------------------------------
            if canvasRect is not None:
                origin = canvasRect.Corner(0)
                ox = origin.X
                oy = origin.Y
                cw = canvasRect.Width
                ch = canvasRect.Height
            else:
                ox, oy, cw, ch = 0.0, 0.0, 100.0, 100.0

            canvas_tuple = (ox, oy, cw, ch)

            # -- Coerce inputs -----------------------------------------------
            bins_val  = int(numBins)    if numBins    is not None else 10
            nx_val    = int(numXLabels) if numXLabels is not None else None
            ny_val    = int(numYLabels) if numYLabels is not None else 5
            d_val     = int(decimals)   if decimals   is not None else 1
            ext_val   = float(axisExtension) if axisExtension is not None else 0.0
            dist_val  = float(labelDist)     if labelDist     is not None else 10.0
            gy_val    = bool(drawGridY)      if drawGridY     is not None else False

            # -- Call pure module --------------------------------------------
            result = create_histogram(
                canvas        = canvas_tuple,
                values        = values_list,
                bins          = bins_val,
                num_x_labels  = nx_val,
                num_y_labels  = ny_val,
                decimals      = d_val,
                extension     = ext_val,
                label_distance= dist_val,
                grid_y        = gy_val,
            )

            # -- Build Rhino geometry ----------------------------------------
            # Bars > Rectangle3d
            for (x0, y0, x1, y1) in result["bars"]:
                corner = rg.Point3d(x0, y0, 0.0)
                plane  = rg.Plane(corner, rg.Vector3d.ZAxis)
                rect   = rg.Rectangle3d(plane, x1 - x0, y1 - y0)
                bars.append(rect)

            # Axes > Line
            for (p0, p1) in result["axes"]:
                ln = rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                             rg.Point3d(p1[0], p1[1], 0.0))
                axes.append(ln)

            # X label points
            for (xp, yp) in result["x_pts"]:
                x_pts.append(rg.Point3d(xp, yp, 0.0))
            x_txt = result["x_txt"]

            # Y label points
            for (xp, yp) in result["y_pts"]:
                y_pts.append(rg.Point3d(xp, yp, 0.0))
            y_txt = result["y_txt"]

            # Grid > Line
            for (p0, p1) in result["grid"]:
                ln = rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                             rg.Point3d(p1[0], p1[1], 0.0))
                grid.append(ln)

            # -- Build SVG ---------------------------------------------------
            def to_svg_y(rhino_y):
                return (oy + ch) - (rhino_y - oy)

            svg_elements = []

            for (x0, y0, x1, y1) in result["bars"]:
                pts_svg = [
                    (x0 - ox, to_svg_y(y0)),
                    (x1 - ox, to_svg_y(y0)),
                    (x1 - ox, to_svg_y(y1)),
                    (x0 - ox, to_svg_y(y1)),
                    (x0 - ox, to_svg_y(y0)),
                ]
                svg_elements.append(
                    polyline_to_svg(pts_svg, stroke="black",
                                   stroke_width=0.5, fill="#AAAAAA"))

            for (p0, p1) in result["axes"]:
                pts_svg = [
                    (p0[0] - ox, to_svg_y(p0[1])),
                    (p1[0] - ox, to_svg_y(p1[1])),
                ]
                svg_elements.append(
                    polyline_to_svg(pts_svg, stroke="black",
                                   stroke_width=1.0, fill="none"))

            for (p0, p1) in result["grid"]:
                pts_svg = [
                    (p0[0] - ox, to_svg_y(p0[1])),
                    (p1[0] - ox, to_svg_y(p1[1])),
                ]
                svg_elements.append(
                    polyline_to_svg(pts_svg, stroke="#CCCCCC",
                                   stroke_width=0.5, fill="none"))

            for (xp, yp), label in zip(result["x_pts"], result["x_txt"]):
                svg_elements.append(
                    text_to_svg(xp - ox, to_svg_y(yp), label,
                                fill="black", font_size=8,
                                text_anchor="middle",
                                dominant_baseline="hanging"))

            for (xp, yp), label in zip(result["y_pts"], result["y_txt"]):
                svg_elements.append(
                    text_to_svg(xp - ox, to_svg_y(yp), label,
                                fill="black", font_size=8,
                                text_anchor="end",
                                dominant_baseline="middle"))

            svg_body_parts = [e for e in svg_elements if e]
            svg_code = "\n".join(svg_body_parts)

            report = "OK -- {} values, {} bins. Range: {:.2f}-{:.2f}. Max count: {}.".format(
                result["metadata"]["num_values"],
                result["metadata"]["num_bins"],
                result["metadata"]["data_range"][0],
                result["metadata"]["data_range"][1],
                result["metadata"]["max_count"],
            )

            # -- Build PreviewPayload ----------------------------------------
            _text_h = max(cw, ch) * 0.025 if (cw > 0 and ch > 0) else 2.0

            # Bar fills + outlines
            for rect in bars:
                crv = rect.ToNurbsCurve()
                pv.add_filled_curve(crv, _BAR_FILL)
                pv.add_curve(crv, _BAR_EDGE, _bw)

            # Axes wires
            for ln in axes:
                pv.add_curve(rg.LineCurve(ln), _AXIS_CLR, _aw)

            # Grid wires
            for ln in grid:
                pv.add_curve(rg.LineCurve(ln), _GRID_CLR, _gw)

            # X labels
            for pt, txt in zip(x_pts, x_txt):
                pv.add_text(txt, pt, _text_h, _TEXT_CLR)

            # Y labels
            for pt, txt in zip(y_pts, y_txt):
                pv.add_text(txt, pt, _text_h, _TEXT_CLR)

        except Exception as e:
            import traceback
            report = "ERROR: {}\n{}".format(e, traceback.format_exc())

        self.Hidden = True
        return (svg_code, report)

    def DrawViewportWires(self, args):
        if hasattr(self, "_pv") and self._pv:
            self._pv.draw_wires(args)

    def DrawViewportMeshes(self, args):
        if hasattr(self, "_pv") and self._pv:
            self._pv.draw_meshes(args)

    def get_ClippingBox(self):
        if hasattr(self, "_pv") and self._pv:
            return self._pv.clipping_box
        import Rhino.Geometry as _rg
        return _rg.BoundingBox.Empty
