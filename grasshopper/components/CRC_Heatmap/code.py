"""CRC_Heatmap: Renders a heatmap chart in the Rhino viewport and exports raw SVG body content.

SDK-mode (advanced) component — subclasses executingcomponent so that
DrawViewportWires / DrawViewportMeshes / get_ClippingBox can be overridden
for a live Rhino viewport preview (colored cell fills, legend fills, text
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

from crc_modules.viz.heatmap import create_heatmap
from crc_modules.svg.export import polyline_to_svg, text_to_svg

from crc_modules.rhino.preview import PreviewPayload

_EDGE_CLR = sd.Color.Black
_TEXT_CLR = sd.Color.Black


class Heatmap(component):

    def RunScript(self, canvasRect, dataMatrix, gradientColors, rowLabels, colLabels, showCellValues, decimals, legendSteps, labelDist, legendBarW, legendDist, legendLabelDist, legendOrientation, showLegend, cellOutlineWidth, legendCellOutlineWidth):
        self.Message = "v{{component_version}}-{{date}}"

        # ── Width defaults ───────────────────────────────────────────────────
        _cell_ow = float(cellOutlineWidth) if cellOutlineWidth is not None else 0.5   # cell outline width
        _lcell_ow = float(legendCellOutlineWidth) if legendCellOutlineWidth is not None else 0.5   # legend cell outline width

        # ── Default matrix (instant preview when no data) ─────────────────────
        _default_matrix = [
            [0.12, 0.73, 0.45, 0.89, 0.31],
            [0.67, 0.24, 0.91, 0.15, 0.58],
            [0.88, 0.36, 0.52, 0.77, 0.09],
            [0.41, 0.95, 0.18, 0.63, 0.84],
        ]

        # ── Output defaults ──────────────────────────────────────────────────
        cells       = []
        clrs        = []
        row_pts     = []
        row_txt     = []
        col_pts     = []
        col_txt     = []
        val_pts     = []
        val_txt     = []
        leg_cells   = []
        leg_clrs    = []
        leg_pts     = []
        leg_txt     = []
        svg_code    = ""
        report      = "Rendering default heatmap..."

        pv = PreviewPayload()
        self._pv = pv

        # ── Input coercion ───────────────────────────────────────────────────
        _canvas     = canvasRect if canvasRect is not None else None
        _colors     = list(gradientColors) if gradientColors else None
        _rows       = [str(v) for v in rowLabels] if rowLabels else None
        _cols       = [str(v) for v in colLabels] if colLabels else None
        _vals       = bool(showCellValues) if showCellValues is not None else False
        _dec        = int(decimals) if decimals is not None else 1
        _n_leg      = int(legendSteps) if legendSteps else 5
        _dist       = float(labelDist) if labelDist is not None else 10.0
        _leg_w      = float(legendBarW) if legendBarW is not None else None
        _leg_dist   = float(legendDist) if legendDist is not None else 20.0
        _leg_l_dist = float(legendLabelDist) if legendLabelDist is not None else 5.0
        _leg_orient = str(legendOrientation) if legendOrientation else "vertical"
        _show_leg   = bool(showLegend) if showLegend is not None else True

        _default_colors = [
            sd.Color.FromArgb(255, 0, 191, 255),
            sd.Color.FromArgb(255, 255, 255, 255),
            sd.Color.FromArgb(255, 178, 24, 43),
        ]
        _colors = _default_colors if not _colors or len(_colors) < 2 else list(_colors)

        # ── Use default matrix when no data is truly provided ─────────────────
        if dataMatrix is None \
                or (hasattr(dataMatrix, "IsEmpty") and dataMatrix.IsEmpty) \
                or (hasattr(dataMatrix, "BranchCount") and dataMatrix.BranchCount == 0):
            _matrix_data = _default_matrix
        elif hasattr(dataMatrix, "__iter__"):
            _flat = [v for v in dataMatrix if v is not None]
            if (_flat and hasattr(_flat[0], "__iter__")
                    and not isinstance(_flat[0], (str, float, int))):
                _matrix_data = [[float(v) for v in _sub if v is not None] for _sub in _flat]
            else:
                _matrix_data = [[float(v) for v in _flat]]
        else:
            _matrix_data = []

        try:
            _matrix = []
            if _matrix_data and len(_matrix_data) > 0:
                if hasattr(dataMatrix, "BranchCount") and dataMatrix.BranchCount > 0:
                    for _i in range(dataMatrix.BranchCount):
                        _branch = dataMatrix.Branch(_i)
                        _row = [float(v) for v in _branch if v is not None]
                        if _row:
                            _matrix.append(_row)
                elif hasattr(_matrix_data, '__iter__'):
                    for _sub in _matrix_data:
                        if isinstance(_sub, (list, tuple)):
                            _row = [float(v) for v in _sub if v is not None]
                            if _row:
                                _matrix.append(_row)
                        else:
                            _row = [float(_matrix_data)]
                            if _row:
                                _matrix.append(_row)

            if not _matrix:
                raise ValueError(
                    "dataMatrix is empty or could not be parsed into a 2D matrix")

            # ── Canvas extraction ─────────────────────────────────────────
            if _canvas is None:
                _ox, _oy, _cw, _ch, _z = 0.0, 0.0, 200.0, 200.0, 0.0
            else:
                _corner = _canvas.Corner(0)
                _ox, _oy, _z = _corner.X, _corner.Y, _corner.Z
                _cw, _ch = float(_canvas.Width), float(_canvas.Height)
            _canvas_tuple = (_ox, _oy, _cw, _ch)

            # ── Convert colors ────────────────────────────────────────────
            _color_list = [(c.R, c.G, c.B, c.A) for c in _colors]

            # ── Call pure module ──────────────────────────────────────────
            res = create_heatmap(
                canvas=_canvas_tuple,
                data_matrix=_matrix,
                color_list=_color_list,
                row_labels=_rows,
                col_labels=_cols,
                show_values=_vals,
                decimals=_dec,
                num_legend_steps=_n_leg,
                label_distance=_dist,
                legend_width=_leg_w,
                legend_label_distance=_leg_l_dist,
                legend_orientation=_leg_orient,
                legend_distance=_leg_dist,
                show_legend=_show_leg,
            )

            # ── Build Rhino geometry ──────────────────────────────────────
            for (cx_c, cy_c, cw_c, ch_c) in res["cells"]:
                _corner_pt = rg.Point3d(cx_c, cy_c, _z)
                _pl = rg.Plane(_corner_pt, rg.Vector3d.ZAxis)
                cells.append(rg.Rectangle3d(_pl, cw_c, ch_c))

            for (rr, gg, bb, aa) in res["colors"]:
                clrs.append(
                    sd.Color.FromArgb(int(aa), int(rr), int(gg), int(bb)))

            for (px, py) in res["row_pts"]:
                row_pts.append(rg.Point3d(px, py, _z))
            row_txt = res["row_txt"]

            for (px, py) in res["col_pts"]:
                col_pts.append(rg.Point3d(px, py, _z))
            col_txt = res["col_txt"]

            for (px, py) in res["value_pts"]:
                val_pts.append(rg.Point3d(px, py, _z))
            val_txt = res["value_txt"]

            for (lx, ly, lw_r, lh_r) in res["legend_cells"]:
                _corner_pt = rg.Point3d(lx, ly, _z)
                _pl = rg.Plane(_corner_pt, rg.Vector3d.ZAxis)
                leg_cells.append(rg.Rectangle3d(_pl, lw_r, lh_r))

            for (rr, gg, bb, aa) in res["legend_colors"]:
                leg_clrs.append(
                    sd.Color.FromArgb(int(aa), int(rr), int(gg), int(bb)))

            for (px, py) in res["legend_pts"]:
                leg_pts.append(rg.Point3d(px, py, _z))
            leg_txt = res["legend_txt"]

            # ── Build SVG ─────────────────────────────────────────────────
            _svg_elems = []

            def _to_svg_xy(xs, ys):
                return xs - _ox, _ch - (ys - _oy)

            def _rect_pts(cx_c, cy_c, cw_c, ch_c):
                sx0, sy0 = _to_svg_xy(cx_c, cy_c)
                sx1, sy1 = _to_svg_xy(cx_c + cw_c, cy_c)
                sx2, sy2 = _to_svg_xy(cx_c + cw_c, cy_c + ch_c)
                sx3, sy3 = _to_svg_xy(cx_c, cy_c + ch_c)
                return [(sx0, sy0), (sx1, sy1), (sx2, sy2),
                        (sx3, sy3), (sx0, sy0)]

            for j, (cx_c, cy_c, cw_c, ch_c) in enumerate(res["cells"]):
                rr, gg, bb, aa = res["colors"][j]
                _fill = "rgb({},{},{})".format(rr, gg, bb)
                _op = round(aa / 255.0, 4)
                _svg_elems.append(polyline_to_svg(
                    _rect_pts(cx_c, cy_c, cw_c, ch_c),
                    fill=_fill, fill_opacity=_op, stroke="none",
                ))

            for j, (px, py) in enumerate(res["row_pts"]):
                sx, sy = _to_svg_xy(px, py)
                _svg_elems.append(text_to_svg(
                    sx, sy, res["row_txt"][j],
                    font_size=8, fill="black", text_anchor="end",
                ))

            for j, (px, py) in enumerate(res["col_pts"]):
                sx, sy = _to_svg_xy(px, py)
                _svg_elems.append(text_to_svg(
                    sx, sy, res["col_txt"][j],
                    font_size=8, fill="black", text_anchor="middle",
                ))

            for j, (px, py) in enumerate(res["value_pts"]):
                sx, sy = _to_svg_xy(px, py)
                _svg_elems.append(text_to_svg(
                    sx, sy, res["value_txt"][j],
                    font_size=7, fill="black", text_anchor="middle",
                    dominant_baseline="middle",
                ))

            for j, (lx, ly, lw_r, lh_r) in enumerate(res["legend_cells"]):
                rr, gg, bb, aa = res["legend_colors"][j]
                _fill = "rgb({},{},{})".format(rr, gg, bb)
                _op = round(aa / 255.0, 4)
                _svg_elems.append(polyline_to_svg(
                    _rect_pts(lx, ly, lw_r, lh_r),
                    fill=_fill, fill_opacity=_op, stroke="none",
                ))

            for j, (px, py) in enumerate(res["legend_pts"]):
                sx, sy = _to_svg_xy(px, py)
                _svg_elems.append(text_to_svg(
                    sx, sy, res["legend_txt"][j],
                    font_size=8, fill="black",
                ))

            svg_code = "\n".join(e for e in _svg_elems if e)

            report = "OK\n" \
                "  matrix: {}x{}\n" \
                "  value range: {:.2f} – {:.2f}\n" \
                "  legend: {}\n" \
                "  chart area: {:.1f} x {:.1f}".format(
                    res["metadata"].get("num_rows", 0),
                    res["metadata"].get("num_cols", 0),
                    res["metadata"].get("value_range", (0, 0))[0],
                    res["metadata"].get("value_range", (0, 0))[1],
                    (res["metadata"].get("legend_orientation", "n/a")
                     if res["metadata"].get("has_legend") else "off"),
                    res["metadata"].get("chart_area", (0, 0))[0],
                    res["metadata"].get("chart_area", (0, 0))[1],
                )

            # ── Build PreviewPayload ───────────────────────────────────────
            _text_h = (max(_cw, _ch) * 0.025
                       if (_cw > 0 and _ch > 0) else 2.0)

            # Cell fills + outlines
            for i, rect in enumerate(cells):
                crv = rect.ToNurbsCurve()
                fill_clr = clrs[i] if i < len(clrs) else _EDGE_CLR
                pv.add_filled_curve(crv, fill_clr)
                pv.add_curve(crv, _EDGE_CLR, _cell_ow)

            # Legend cell fills + outlines
            for i, rect in enumerate(leg_cells):
                crv = rect.ToNurbsCurve()
                fill_clr = leg_clrs[i] if i < len(leg_clrs) else _EDGE_CLR
                pv.add_filled_curve(crv, fill_clr)
                pv.add_curve(crv, _EDGE_CLR, _lcell_ow)

            # Row / col / value / legend labels
            for pt, txt in zip(row_pts, row_txt):
                pv.add_text(txt, pt, _text_h, _TEXT_CLR)
            for pt, txt in zip(col_pts, col_txt):
                pv.add_text(txt, pt, _text_h, _TEXT_CLR)
            for pt, txt in zip(val_pts, val_txt):
                pv.add_text(txt, pt, _text_h * 0.85, _TEXT_CLR)
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
