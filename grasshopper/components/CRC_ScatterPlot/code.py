"""CRC_ScatterPlot: Renders a scatter chart in the Rhino viewport and exports raw SVG body content.

SDK-mode (advanced) component — subclasses executingcomponent so that
DrawViewportWires / DrawViewportMeshes / get_ClippingBox can be overridden
for a live Rhino viewport preview (colored dot fills, axis/grid wires, legend
cells, text tags). Chain svgCode into CRC_SaveSVG to write the file.
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

from crc_modules.viz.scatter import create_scatterplot
from crc_modules.svg.export import circle_to_svg, polyline_to_svg, text_to_svg
from crc_modules.rhino.preview import PreviewPayload

_AXIS_CLR = sd.Color.Black
_GRID_CLR = sd.Color.FromArgb(255, 204, 204, 204)
_TEXT_CLR = sd.Color.Black
_DOT_EDGE = sd.Color.Black


class ScatterPlot(component):

    def RunScript(self, canvasRect, xValues, yValues, dotRadius, numXLabels, numYLabels, decimals, axisExtension, labelDist, marginLeft, marginBottom, drawGridX, drawGridY,
                  showLegend, colorValues, gradientColors, numLegendSteps, legendBarWidth, legendDist,
                  legendLabelDist, legendOrientation, dotOutlineWidth, axisLineWidth, gridLineWidth):
        self.Message = "v{{component_version}}-{{date}}"

        # ── Width defaults ───────────────────────────────────────────────────
        _dw = float(dotOutlineWidth) if dotOutlineWidth is not None else 0.5
        _aw = float(axisLineWidth)   if axisLineWidth   is not None else 2.0
        _gw = float(gridLineWidth)   if gridLineWidth   is not None else 1.0

        # ── Output defaults ──────────────────────────────────────────────────
        dots       = []
        colors_out = []
        axes       = []
        x_pts      = []
        x_txt      = []
        y_pts      = []
        y_txt      = []
        grid_x     = []
        grid_y     = []
        leg_cells  = []
        leg_clrs   = []
        leg_pts    = []
        leg_txt    = []
        svg_code   = ""
        report     = "Ready"

        pv = PreviewPayload()
        self._pv = pv

        # ── Input coercion ───────────────────────────────────────────────────
        _cv          = canvasRect if canvasRect is not None else None
        _x_input     = list(xValues) if xValues else None
        _y_input     = list(yValues) if yValues else None

        # Default data for instant preview
        if not _x_input or not _y_input:
            import math
            _default_x = [round(i * 0.5, 1) for i in range(20)]
            _default_y = [round(0.1 * (i ** 2) + 2 * math.sin(i) + 5, 2) for i in range(20)]
        else:
            _default_x = _x_input
            _default_y = _y_input

        _x = _default_x
        _y = _default_y
        _r           = list(dotRadius) if dotRadius else [2.0]
        _nx          = int(numXLabels) if numXLabels else 5
        _ny          = int(numYLabels) if numYLabels else 5
        _d           = int(decimals) if decimals is not None else 1
        _ext         = float(axisExtension) if axisExtension is not None else 0.0
        _dist        = float(labelDist) if labelDist is not None else 10.0
        _mx          = float(marginLeft) if marginLeft is not None else 0.0
        _my          = float(marginBottom) if marginBottom is not None else 0.0
        _gx          = bool(drawGridX) if drawGridX is not None else False
        _gy          = bool(drawGridY) if drawGridY is not None else False
        _show_leg    = bool(showLegend) if showLegend is not None else False
        _col_vals    = list(colorValues) if colorValues else None
        _colors      = list(gradientColors) if gradientColors else None
        _n_leg       = int(numLegendSteps) if numLegendSteps else 5
        _leg_w       = float(legendBarWidth) if legendBarWidth is not None else None
        _leg_dist    = float(legendDist) if legendDist is not None else 20.0
        _leg_l_dist  = float(legendLabelDist) if legendLabelDist is not None else 5.0
        _leg_orient  = str(legendOrientation) if legendOrientation else "vertical"

        try:
            # ── Canvas extraction ────────────────────────────────────────
            if _cv is None:
                _ox, _oy, _cw, _ch = 0.0, 0.0, 100.0, 100.0
                _z = 0.0
            else:
                _corner = _cv.Corner(0)
                _ox, _oy = _corner.X, _corner.Y
                _cw, _ch = float(_cv.Width), float(_cv.Height)
                _z = _corner.Z
            _canvas_tuple = (_ox, _oy, _cw, _ch)

            # ── Validate required inputs ──────────────────────────────────
            if not _x or not _y:
                raise ValueError("xValues and yValues are required")
            if len(_x) != len(_y):
                raise ValueError(
                    "xValues and yValues must have the same length ({} vs {})".format(
                        len(_x), len(_y)))

            # ── Convert System.Drawing.Color → (r,g,b,a) tuples ─────────
            default_legend_colors = [
                sd.Color.FromArgb(255, 0, 191, 255),
                sd.Color.FromArgb(255, 255, 255, 255),
                sd.Color.FromArgb(255, 178, 24, 43),
            ]
            _color_list = None
            if _colors and len(_colors) >= 2:
                _color_list = [(c.R, c.G, c.B, c.A) for c in _colors]

            if _show_leg and (_color_list is None or len(_color_list) < 2):
                # Use default gradient for legend
                _color_list = [(c.R, c.G, c.B, c.A) for c in default_legend_colors]

            if _show_leg and _color_list is None:
                report = ("WARNING: Legend enabled but no valid color "
                          "gradient provided (min 2 colors)")

            # ── Radii ─────────────────────────────────────────────────────
            if len(_r) == 1:
                _radii = float(_r[0])
            elif len(_r) > 1:
                _radii = [float(v) for v in _r]
            else:
                _radii = 2.0

            # ── Call pure module ──────────────────────────────────────────
            res = create_scatterplot(
                canvas=_canvas_tuple,
                x_values=[float(v) for v in _x],
                y_values=[float(v) for v in _y],
                radii=_radii,
                num_x_labels=_nx,
                num_y_labels=_ny,
                decimals=_d,
                extension=_ext,
                label_distance=_dist,
                margin_x=_mx,
                margin_y=_my,
                grid_x=_gx,
                grid_y=_gy,
                show_legend=_show_leg,
                color_values=[float(v) for v in _col_vals] if _col_vals else None,
                color_list=_color_list,
                num_legend_steps=_n_leg,
                legend_width=_leg_w,
                legend_distance=_leg_dist,
                legend_label_distance=_leg_l_dist,
                legend_orientation=_leg_orient,
            )

            # ── Build Rhino geometry ─────────────────────────────────────
            for (cx_c, cy_c, r_c) in res["dots"]:
                _pt = rg.Point3d(cx_c, cy_c, _z)
                _pl = rg.Plane(_pt, rg.Vector3d.ZAxis)
                dots.append(rg.Circle(_pl, r_c))

            for (rr, gg, bb, aa) in res["colors"]:
                colors_out.append(
                    sd.Color.FromArgb(int(aa), int(rr), int(gg), int(bb)))

            for (p0, p1) in res["axes"]:
                axes.append(rg.Line(
                    rg.Point3d(p0[0], p0[1], _z),
                    rg.Point3d(p1[0], p1[1], _z),
                ))

            for (px, py) in res["x_pts"]:
                x_pts.append(rg.Point3d(px, py, _z))
            x_txt = res["x_txt"]

            for (px, py) in res["y_pts"]:
                y_pts.append(rg.Point3d(px, py, _z))
            y_txt = res["y_txt"]

            for (p0, p1) in res["grid_x_lines"]:
                grid_x.append(rg.Line(
                    rg.Point3d(p0[0], p0[1], _z),
                    rg.Point3d(p1[0], p1[1], _z),
                ))
            for (p0, p1) in res["grid_y_lines"]:
                grid_y.append(rg.Line(
                    rg.Point3d(p0[0], p0[1], _z),
                    rg.Point3d(p1[0], p1[1], _z),
                ))

            for (lx, ly, lw, lh) in res["legend_cells"]:
                _corner_pt = rg.Point3d(lx, ly, _z)
                _pl = rg.Plane(_corner_pt, rg.Vector3d.ZAxis)
                leg_cells.append(rg.Rectangle3d(_pl, lw, lh))

            for (rr, gg, bb, aa) in res["legend_colors"]:
                leg_clrs.append(
                    sd.Color.FromArgb(int(aa), int(rr), int(gg), int(bb)))

            for (px, py) in res["legend_pts"]:
                leg_pts.append(rg.Point3d(px, py, _z))
            leg_txt = res["legend_txt"]

            # ── Build SVG ────────────────────────────────────────────────
            _svg_elems = []

            for (p0, p1) in res["axes"]:
                _svg_y0 = _ch - (p0[1] - _oy)
                _svg_y1 = _ch - (p1[1] - _oy)
                _svg_elems.append(polyline_to_svg(
                    [(p0[0] - _ox, _svg_y0), (p1[0] - _ox, _svg_y1)],
                    stroke="black", stroke_width=1,
                ))

            for (p0, p1) in res["grid_x_lines"] + res["grid_y_lines"]:
                _svg_elems.append(polyline_to_svg(
                    [(p0[0] - _ox, _ch - (p0[1] - _oy)),
                     (p1[0] - _ox, _ch - (p1[1] - _oy))],
                    stroke="#cccccc", stroke_width=0.5,
                ))

            _dot_colors = res["colors"]
            for i, (cx_c, cy_c, r_c) in enumerate(res["dots"]):
                _scx = cx_c - _ox
                _scy = _ch - (cy_c - _oy)
                if _dot_colors:
                    rr, gg, bb, aa = _dot_colors[i]
                    _fill = "rgb({},{},{})".format(rr, gg, bb)
                    _op = round(aa / 255.0, 4)
                else:
                    _fill = "none"
                    _op = 1.0
                _svg_elems.append(circle_to_svg(
                    _scx, _scy, r_c,
                    stroke="black", stroke_width=0.3,
                    fill=_fill, fill_opacity=_op,
                ))

            for j, (px, py) in enumerate(res["x_pts"]):
                _svg_elems.append(text_to_svg(
                    px - _ox, _ch - (py - _oy),
                    res["x_txt"][j],
                    font_size=8, fill="black", text_anchor="middle",
                ))

            for j, (px, py) in enumerate(res["y_pts"]):
                _svg_elems.append(text_to_svg(
                    px - _ox, _ch - (py - _oy),
                    res["y_txt"][j],
                    font_size=8, fill="black", text_anchor="end",
                ))

            for j, (lx, ly, lw, lh) in enumerate(res["legend_cells"]):
                rr, gg, bb, aa = res["legend_colors"][j]
                _fill = "rgb({},{},{})".format(rr, gg, bb)
                _op = round(aa / 255.0, 4)
                _svg_elems.append(polyline_to_svg(
                    [
                        (lx - _ox,        _ch - (ly - _oy)),
                        (lx - _ox + lw,   _ch - (ly - _oy)),
                        (lx - _ox + lw,   _ch - (ly + lh - _oy)),
                        (lx - _ox,        _ch - (ly + lh - _oy)),
                        (lx - _ox,        _ch - (ly - _oy)),
                    ],
                    fill=_fill, fill_opacity=_op, stroke="none",
                ))
            for j, (px, py) in enumerate(res["legend_pts"]):
                _svg_elems.append(text_to_svg(
                    px - _ox, _ch - (py - _oy),
                    res["legend_txt"][j],
                    font_size=8, fill="black",
                ))

            svg_code = "\n".join(e for e in _svg_elems if e)

            meta = res["metadata"]
            report = (
                "OK\n"
                "  points: {}\n"
                "  has colors: {}\n"
                "  has legend: {}\n"
                "  chart area: {:.1f} x {:.1f}".format(
                    meta.get("num_points", 0),
                    meta.get("has_colors", False),
                    meta.get("has_legend", False),
                    meta.get("chart_area", (0, 0))[0],
                    meta.get("chart_area", (0, 0))[1],
                )
            )

            # ── Build PreviewPayload ─────────────────────────────────────
            _text_h = max(_cw, _ch) * 0.025 if (_cw > 0 and _ch > 0) else 2.0

            # Dot fills + outlines
            for i, circ in enumerate(dots):
                crv = circ.ToNurbsCurve()
                fill_clr = colors_out[i] if i < len(colors_out) else _DOT_EDGE
                pv.add_filled_curve(crv, fill_clr)
                pv.add_curve(crv, _DOT_EDGE, _dw)

            # Axes wires
            for ln in axes:
                pv.add_curve(rg.LineCurve(ln), _AXIS_CLR, _aw)

            # Grid wires
            for ln in grid_x + grid_y:
                pv.add_curve(rg.LineCurve(ln), _GRID_CLR, _gw)

            # Legend cell fills + outlines
            for i, rect in enumerate(leg_cells):
                crv = rect.ToNurbsCurve()
                fill_clr = leg_clrs[i] if i < len(leg_clrs) else _GRID_CLR
                pv.add_filled_curve(crv, fill_clr)
                pv.add_curve(crv, _DOT_EDGE, _gw)

            # X/Y labels
            for pt, txt in zip(x_pts, x_txt):
                pv.add_text(txt, pt, _text_h, _TEXT_CLR)
            for pt, txt in zip(y_pts, y_txt):
                pv.add_text(txt, pt, _text_h, _TEXT_CLR)

            # Legend labels
            for pt, txt in zip(leg_pts, leg_txt):
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
