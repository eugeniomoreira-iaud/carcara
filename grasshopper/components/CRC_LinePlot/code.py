"""CRC_LinePlot: Renders a line chart in the Rhino viewport and exports raw SVG body content.

SDK-mode (advanced) component -- subclasses executingcomponent so that
DrawViewportWires / DrawViewportMeshes / get_ClippingBox can be overridden
for a live Rhino viewport preview (colored series polylines, axis/grid wires,
text tags). Chain svgCode into CRC_SaveSVG to write the file.
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

from crc_modules.viz.lineplot import create_lineplot
from crc_modules.svg.export import polyline_to_svg, text_to_svg
from crc_modules.rhino.preview import PreviewPayload


# Matplotlib default cycle (same 10 colours used in SVG)
_SERIES_COLORS_HEX = [
    (31,  119, 180),   # #1f77b4
    (255, 127,  14),   # #ff7f0e
    (44,  160,  44),   # #2ca02c
    (214,  39,  40),   # #d62728
    (148, 103, 189),   # #9467bd
    (140,  86,  75),   # #8c564b
    (227, 119, 194),   # #e377c2
    (127, 127, 127),   # #7f7f7f
    (188, 189,  34),   # #bcbd22
    ( 23, 190, 207),   # #17becf
]

_AXIS_CLR = sd.Color.Black
_GRID_CLR = sd.Color.FromArgb(255, 204, 204, 204)
_TEXT_CLR = sd.Color.Black
GRID_DASH = "2,2"


class LinePlot(component):

    def RunScript(self, canvasRect, xValues, yValues, numXLabels, numYLabels, decimals, axisExtension, labelDist, marginLeft, marginBottom, drawGridX, drawGridY, lineWidth, axisLineWidth, gridLineWidth):
        self.Message = "v{{component_version}}-{{date}}"

        # -- Width defaults ----------------------------------------------------
        _lw = float(lineWidth)     if lineWidth     is not None else 2.0
        _aw = float(axisLineWidth) if axisLineWidth is not None else 2.0
        _gw = float(gridLineWidth) if gridLineWidth is not None else 1.0

        # -- Default demo data for instant preview -----------------------------
        _default_x      = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        _default_y_list = [2, 4, 1, 5, 8, 3, 7, 6, 9, 4]

        # -- Output defaults ---------------------------------------------------
        report   = "Rendering default line plot..."
        lines    = []
        axes     = []
        x_pts    = []
        x_txt    = []
        y_pts    = []
        y_txt    = []
        grid_x   = []
        grid_y   = []
        svg_code = ""

        pv = PreviewPayload()
        self._pv = pv

        try:
            # -- Canvas extraction ---------------------------------------------
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
            nx_val   = int(numXLabels)    if numXLabels    is not None else 5
            ny_val   = int(numYLabels)    if numYLabels    is not None else 5
            d_val    = int(decimals)      if decimals      is not None else 1
            ext_val  = float(axisExtension) if axisExtension is not None else 0.0
            dist_val = float(labelDist)   if labelDist     is not None else 10.0
            mx_val   = float(marginLeft)  if marginLeft    is not None else 0.0
            my_val   = float(marginBottom)if marginBottom  is not None else 0.0
            gx_val   = bool(drawGridX)    if drawGridX     is not None else False
            gy_val   = bool(drawGridY)    if drawGridY     is not None else False

            # -- Parse DataTree / flat list ----------------------------------
            def _extract_series(data_in):
                if data_in is None:
                    return []
                try:
                    if hasattr(data_in, 'BranchCount') and data_in.BranchCount > 0:
                        series = []
                        for i in range(data_in.BranchCount):
                            branch = data_in.Branch(i)
                            cleaned = [float(v) for v in branch if v is not None]
                            if cleaned:
                                series.append(cleaned)
                        return series
                except Exception:
                    pass
                try:
                    return [float(v) for v in data_in if v is not None]
                except Exception:
                    return []

            x_input = _extract_series(xValues) if xValues else []
            y_input = _extract_series(yValues) if yValues else []

            # Use defaults when no input provided
            if not x_input and len(_default_x):
                x_input = [_default_x]
            if not y_input:
                y_input = [_default_y_list]

            # -- Call pure module --------------------------------------------
            result = create_lineplot(
                canvas         = canvas_tuple,
                x_series       = x_input,
                y_series       = y_input,
                num_x_labels   = nx_val,
                num_y_labels   = ny_val,
                decimals       = d_val,
                extension      = ext_val,
                label_distance = dist_val,
                margin_x       = mx_val,
                margin_y       = my_val,
                grid_x         = gx_val,
                grid_y         = gy_val,
            )

            # -- Build Rhino geometry ----------------------------------------
            for series_pts in result["lines"]:
                rh_pts = [rg.Point3d(xp, yp, 0.0) for xp, yp in series_pts]
                pl = rg.Polyline(rh_pts)
                lines.append(pl.ToPolylineCurve())

            for (p0, p1) in result["axes"]:
                axes.append(rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                                    rg.Point3d(p1[0], p1[1], 0.0)))

            for (xp, yp) in result["x_pts"]:
                x_pts.append(rg.Point3d(xp, yp, 0.0))
            x_txt = result["x_txt"]

            for (xp, yp) in result["y_pts"]:
                y_pts.append(rg.Point3d(xp, yp, 0.0))
            y_txt = result["y_txt"]

            for (p0, p1) in result["grid_x"]:
                grid_x.append(rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                                      rg.Point3d(p1[0], p1[1], 0.0)))

            for (p0, p1) in result["grid_y"]:
                grid_y.append(rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                                      rg.Point3d(p1[0], p1[1], 0.0)))

            # -- Build SVG ---------------------------------------------------
            def to_svg_y(rhino_y):
                return (oy + ch) - (rhino_y - oy)

            svg_elements = []

            for (p0, p1) in result["grid_y"]:
                pts_svg = [(p0[0] - ox, to_svg_y(p0[1])),
                           (p1[0] - ox, to_svg_y(p1[1]))]
                svg_elements.append(
                    polyline_to_svg(pts_svg, stroke="#CCCCCC",
                                    stroke_width=0.5, fill="none", dash=GRID_DASH))

            for (p0, p1) in result["grid_x"]:
                pts_svg = [(p0[0] - ox, to_svg_y(p0[1])),
                           (p1[0] - ox, to_svg_y(p1[1]))]
                svg_elements.append(
                    polyline_to_svg(pts_svg, stroke="#CCCCCC",
                                    stroke_width=0.5, fill="none", dash=GRID_DASH))

            for (p0, p1) in result["axes"]:
                pts_svg = [(p0[0] - ox, to_svg_y(p0[1])),
                           (p1[0] - ox, to_svg_y(p1[1]))]
                svg_elements.append(
                    polyline_to_svg(pts_svg, stroke="black",
                                    stroke_width=1.0, fill="none"))

            for i, series_pts in enumerate(result["lines"]):
                clr = _SERIES_COLORS_HEX[i % len(_SERIES_COLORS_HEX)]
                pts_svg = [(xp - ox, to_svg_y(yp)) for xp, yp in series_pts]
                svg_elements.append(
                    polyline_to_svg(pts_svg, stroke=clr,
                                    stroke_width=1.5, fill="none"))

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

            svg_body = "\n".join(e for e in svg_elements if e)
            svg_code = svg_body

            meta = result["metadata"]
            report = ("OK -- {} series. X: {:.2f}-{:.2f}  "
                   "Y: {:.2f}-{:.2f}.".format(
                meta["num_series"],
                meta["x_range"][0], meta["x_range"][1],
                meta["y_range"][0], meta["y_range"][1],
            ))

            # -- Build PreviewPayload ----------------------------------------
            _text_h = max(cw, ch) * 0.025 if (cw > 0 and ch > 0) else 2.0

            # Series lines (colored)
            for i, crv in enumerate(lines):
                r_c, g_c, b_c = _SERIES_COLORS_HEX[i % len(_SERIES_COLORS_HEX)]
                series_clr = sd.Color.FromArgb(255, r_c, g_c, b_c)
                pv.add_curve(crv, series_clr, _lw)

            # Axes wires
            for ln in axes:
                pv.add_curve(rg.LineCurve(ln), _AXIS_CLR, _aw)

            # Grid wires
            for ln in grid_x + grid_y:
                pv.add_curve(rg.LineCurve(ln), _GRID_CLR, _gw, dash=GRID_DASH)

            # X/Y labels
            for pt, txt in zip(x_pts, x_txt):
                pv.add_text(txt, pt, _text_h, _TEXT_CLR)
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
