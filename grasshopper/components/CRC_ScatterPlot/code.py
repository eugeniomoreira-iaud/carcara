"""CRC_ScatterPlot: Scatter chart — Rhino geometry + SVG export."""
import sys
import os

# Make crc_modules importable inside Grasshopper Python 3.
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

import Rhino.Geometry as rg
import System.Drawing as sd

from crc_modules.viz.scatter import create_scatterplot
from crc_modules.svg.export import circle_to_svg, polyline_to_svg, text_to_svg
from crc_modules.svg.save import save_svg

# ── Defaults ──────────────────────────────────────────────────────────────────
dots = []
colors_out = []
axes = []
x_pts = []
x_txt = []
y_pts = []
y_txt = []
grid_x = []
grid_y = []
leg_cells = []
leg_clrs = []
leg_pts = []
leg_txt = []
svg_code = ""
svg_path = ""
report = "Set 'CToggle' to True to execute"

# ── Input coercion ────────────────────────────────────────────────────────────
_cv = cv if cv is not None else None
_x = list(x) if x else []
_y = list(y) if y else []
_r = list(r) if r else 2.0
_nx = int(nx) if nx else 5
_ny = int(ny) if ny else 5
_d = int(d) if d is not None else 1
_ext = float(ext) if ext is not None else 0.0
_dist = float(dist) if dist is not None else 10.0
_mx = float(mx) if mx is not None else 0.0
_my = float(my) if my is not None else 0.0
_gx = bool(gx) if gx is not None else False
_gy = bool(gy) if gy is not None else False
_show_leg = bool(show_leg) if show_leg is not None else False
_col_vals = list(col_vals) if col_vals else None
_colors = list(colors) if colors else None
_n_leg = int(n_leg) if n_leg else 5
_leg_w = float(leg_w) if leg_w is not None else None
_leg_dist = float(leg_dist) if leg_dist is not None else 20.0
_leg_l_dist = float(leg_l_dist) if leg_l_dist is not None else 5.0
_leg_orient = str(leg_orient) if leg_orient else "vertical"
_out_path = str(OutPath).strip() if OutPath else ""

if CToggle:
    try:
        # ── Canvas extraction ─────────────────────────────────────────────────
        if _cv is None:
            _ox, _oy, _cw, _ch = 0.0, 0.0, 100.0, 100.0
        else:
            _corner = _cv.Corner(0)
            _ox, _oy = _corner.X, _corner.Y
            _cw, _ch = float(_cv.Width), float(_cv.Height)
        _canvas_tuple = (_ox, _oy, _cw, _ch)

        # ── Validate required inputs ──────────────────────────────────────────
        if not _x or not _y:
            raise ValueError("x and y data are required")
        if len(_x) != len(_y):
            raise ValueError("x and y must have the same length ({} vs {})".format(
                len(_x), len(_y)))

        # ── Convert System.Drawing.Color → (r,g,b,a) tuples ─────────────────
        _color_list = None
        if _colors and len(_colors) >= 2:
            _color_list = [(c.R, c.G, c.B, c.A) for c in _colors]

        if _show_leg and _color_list is None:
            report = "WARNING: Legend enabled but no valid color gradient provided (min 2 colors)"

        # ── Radii — single value or list ─────────────────────────────────────
        if len(_r) == 1:
            _radii = float(_r[0])
        elif len(_r) > 1:
            _radii = [float(v) for v in _r]
        else:
            _radii = 2.0

        # ── Call pure module ──────────────────────────────────────────────────
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

        _z = _corner.Z if _cv is not None else 0.0

        # ── Build Rhino geometry from returned plain coords ───────────────────
        # Dots → Circle
        for (cx_c, cy_c, r_c) in res["dots"]:
            _pt = rg.Point3d(cx_c, cy_c, _z)
            _pl = rg.Plane(_pt, rg.Vector3d.ZAxis)
            dots.append(rg.Circle(_pl, r_c))

        # Colors → System.Drawing.Color
        for (rr, gg, bb, aa) in res["colors"]:
            colors_out.append(sd.Color.FromArgb(int(aa), int(rr), int(gg), int(bb)))

        # Axes → Line
        for (p0, p1) in res["axes"]:
            axes.append(rg.Line(
                rg.Point3d(p0[0], p0[1], _z),
                rg.Point3d(p1[0], p1[1], _z),
            ))

        # X label points + texts
        for (px, py) in res["x_pts"]:
            x_pts.append(rg.Point3d(px, py, _z))
        x_txt = res["x_txt"]

        # Y label points + texts
        for (px, py) in res["y_pts"]:
            y_pts.append(rg.Point3d(px, py, _z))
        y_txt = res["y_txt"]

        # Grid lines
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

        # Legend cells → Rectangle3d
        for (lx, ly, lw, lh) in res["legend_cells"]:
            _corner_pt = rg.Point3d(lx, ly, _z)
            _pl = rg.Plane(_corner_pt, rg.Vector3d.ZAxis)
            leg_cells.append(rg.Rectangle3d(_pl, lw, lh))

        # Legend colors
        for (rr, gg, bb, aa) in res["legend_colors"]:
            leg_clrs.append(sd.Color.FromArgb(int(aa), int(rr), int(gg), int(bb)))

        # Legend pts + txt
        for (px, py) in res["legend_pts"]:
            leg_pts.append(rg.Point3d(px, py, _z))
        leg_txt = res["legend_txt"]

        # ── Build SVG ─────────────────────────────────────────────────────────
        _svg_elems = []

        # Axes
        for (p0, p1) in res["axes"]:
            # SVG Y-down: flip y relative to canvas top
            _svg_y0 = _ch - (p0[1] - _oy)
            _svg_y1 = _ch - (p1[1] - _oy)
            _svg_x0 = p0[0] - _ox
            _svg_x1 = p1[0] - _ox
            _svg_elems.append(polyline_to_svg(
                [(_svg_x0, _svg_y0), (_svg_x1, _svg_y1)],
                stroke="black", stroke_width=1,
            ))

        # Grid lines
        for (p0, p1) in res["grid_x_lines"] + res["grid_y_lines"]:
            _svg_elems.append(polyline_to_svg(
                [(p0[0] - _ox, _ch - (p0[1] - _oy)),
                 (p1[0] - _ox, _ch - (p1[1] - _oy))],
                stroke="#cccccc", stroke_width=0.5,
            ))

        # Dots
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

        # X labels
        for j, (px, py) in enumerate(res["x_pts"]):
            _svg_elems.append(text_to_svg(
                px - _ox, _ch - (py - _oy),
                res["x_txt"][j],
                font_size=8, fill="black", text_anchor="middle",
            ))

        # Y labels
        for j, (px, py) in enumerate(res["y_pts"]):
            _svg_elems.append(text_to_svg(
                px - _ox, _ch - (py - _oy),
                res["y_txt"][j],
                font_size=8, fill="black", text_anchor="end",
            ))

        # Legend cells + labels
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

        # Assemble SVG document
        svg_code = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg"'
            ' width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">\n'
            '{body}\n'
            '</svg>\n'
        ).format(w=_cw, h=_ch, body="\n".join(e for e in _svg_elems if e))

        # Save to file
        if _out_path:
            svg_path = save_svg(_svg_elems, _out_path, _cw, _ch)

        meta = res["metadata"]
        report = (
            "OK\n"
            "  points: {}\n"
            "  has colors: {}\n"
            "  has legend: {}\n"
            "  chart area: {:.1f} x {:.1f}\n"
            "  SVG saved: {}".format(
                meta.get("num_points", 0),
                meta.get("has_colors", False),
                meta.get("has_legend", False),
                meta.get("chart_area", (0, 0))[0],
                meta.get("chart_area", (0, 0))[1],
                svg_path if svg_path else "(not saved)",
            )
        )

    except Exception as e:
        import traceback
        report = "ERROR: {}\n{}".format(e, traceback.format_exc())
