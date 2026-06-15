"""CRC_Heatmap: Heatmap chart — Rhino geometry + SVG export."""
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

from crc_modules.viz.heatmap import create_heatmap
from crc_modules.svg.export import polyline_to_svg, text_to_svg
from crc_modules.svg.save import save_svg

# ── Defaults ──────────────────────────────────────────────────────────────────
cells = []
clrs = []
row_pts = []
row_txt = []
col_pts = []
col_txt = []
val_pts = []
val_txt = []
leg_cells = []
leg_clrs = []
leg_pts = []
leg_txt = []
svg_code = ""
svg_path = ""
report = "Set 'CToggle' to True to execute"

# ── Input coercion ────────────────────────────────────────────────────────────
_cv = cv if cv is not None else None
_colors = list(colors) if colors else None
_rows = [str(v) for v in rows] if rows else None
_cols = [str(v) for v in cols] if cols else None
_vals = bool(vals) if vals is not None else False
_d = int(d) if d is not None else 1
_n_leg = int(n_leg) if n_leg else 5
_dist = float(dist) if dist is not None else 10.0
_leg_w = float(leg_w) if leg_w is not None else None
_leg_dist = float(leg_dist) if leg_dist is not None else 20.0
_leg_l_dist = float(leg_l_dist) if leg_l_dist is not None else 5.0
_leg_orient = str(leg_orient) if leg_orient else "vertical"
_show_leg = bool(show_leg) if show_leg is not None else True
_out_path = str(OutPath).strip() if OutPath else ""

if CToggle:
    try:
        # ── Validate required inputs ──────────────────────────────────────────
        if _colors is None or len(_colors) < 2:
            raise ValueError("colors is required with at least 2 Color values")

        # ── Parse DataTree → 2D matrix ────────────────────────────────────────
        # data input is declared as 'tree' access so it arrives as a DataTree
        _matrix = []
        if data is not None:
            if hasattr(data, "BranchCount") and data.BranchCount > 0:
                for _i in range(data.BranchCount):
                    _branch = data.Branch(_i)
                    _row = [float(v) for v in _branch if v is not None]
                    if _row:
                        _matrix.append(_row)
            elif hasattr(data, "__iter__"):
                # Flat list or nested list (fallback)
                _flat = [v for v in data if v is not None]
                if _flat and hasattr(_flat[0], "__iter__") and not isinstance(_flat[0], (str, float, int)):
                    for _sub in _flat:
                        _row = [float(v) for v in _sub if v is not None]
                        if _row:
                            _matrix.append(_row)
                else:
                    # Treat flat list as a single row
                    _row = [float(v) for v in _flat]
                    if _row:
                        _matrix.append(_row)

        if not _matrix:
            raise ValueError("data is empty or could not be parsed into a 2D matrix")

        # ── Canvas extraction ─────────────────────────────────────────────────
        if _cv is None:
            _ox, _oy, _cw, _ch, _z = 0.0, 0.0, 200.0, 200.0, 0.0
        else:
            _corner = _cv.Corner(0)
            _ox, _oy, _z = _corner.X, _corner.Y, _corner.Z
            _cw, _ch = float(_cv.Width), float(_cv.Height)
        _canvas_tuple = (_ox, _oy, _cw, _ch)

        # ── Convert System.Drawing.Color → (r,g,b,a) tuples ─────────────────
        _color_list = [(c.R, c.G, c.B, c.A) for c in _colors]

        # ── Call pure module ──────────────────────────────────────────────────
        res = create_heatmap(
            canvas=_canvas_tuple,
            data_matrix=_matrix,
            color_list=_color_list,
            row_labels=_rows,
            col_labels=_cols,
            show_values=_vals,
            decimals=_d,
            num_legend_steps=_n_leg,
            label_distance=_dist,
            legend_width=_leg_w,
            legend_label_distance=_leg_l_dist,
            legend_orientation=_leg_orient,
            legend_distance=_leg_dist,
            show_legend=_show_leg,
        )

        # ── Build Rhino geometry from returned plain coords ───────────────────
        # Cells → Rectangle3d
        for (cx_c, cy_c, cw_c, ch_c) in res["cells"]:
            _corner_pt = rg.Point3d(cx_c, cy_c, _z)
            _pl = rg.Plane(_corner_pt, rg.Vector3d.ZAxis)
            cells.append(rg.Rectangle3d(_pl, cw_c, ch_c))

        # Cell colors → System.Drawing.Color
        for (rr, gg, bb, aa) in res["colors"]:
            clrs.append(sd.Color.FromArgb(int(aa), int(rr), int(gg), int(bb)))

        # Row label pts + texts
        for (px, py) in res["row_pts"]:
            row_pts.append(rg.Point3d(px, py, _z))
        row_txt = res["row_txt"]

        # Col label pts + texts
        for (px, py) in res["col_pts"]:
            col_pts.append(rg.Point3d(px, py, _z))
        col_txt = res["col_txt"]

        # Value label pts + texts
        for (px, py) in res["value_pts"]:
            val_pts.append(rg.Point3d(px, py, _z))
        val_txt = res["value_txt"]

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

        def _to_svg_xy(x, y):
            """Convert Rhino canvas coords to SVG (Y-flipped) coords."""
            return x - _ox, _ch - (y - _oy)

        def _rect_pts(cx_c, cy_c, cw_c, ch_c):
            """Return closed polygon point list for a rect in SVG coords."""
            sx0, sy0 = _to_svg_xy(cx_c, cy_c)
            sx1, sy1 = _to_svg_xy(cx_c + cw_c, cy_c)
            sx2, sy2 = _to_svg_xy(cx_c + cw_c, cy_c + ch_c)
            sx3, sy3 = _to_svg_xy(cx_c, cy_c + ch_c)
            return [(sx0, sy0), (sx1, sy1), (sx2, sy2), (sx3, sy3), (sx0, sy0)]

        # Cells
        for j, (cx_c, cy_c, cw_c, ch_c) in enumerate(res["cells"]):
            rr, gg, bb, aa = res["colors"][j]
            _fill = "rgb({},{},{})".format(rr, gg, bb)
            _op = round(aa / 255.0, 4)
            _svg_elems.append(polyline_to_svg(
                _rect_pts(cx_c, cy_c, cw_c, ch_c),
                fill=_fill, fill_opacity=_op, stroke="none",
            ))

        # Row labels
        for j, (px, py) in enumerate(res["row_pts"]):
            sx, sy = _to_svg_xy(px, py)
            _svg_elems.append(text_to_svg(
                sx, sy, res["row_txt"][j],
                font_size=8, fill="black", text_anchor="end",
            ))

        # Col labels
        for j, (px, py) in enumerate(res["col_pts"]):
            sx, sy = _to_svg_xy(px, py)
            _svg_elems.append(text_to_svg(
                sx, sy, res["col_txt"][j],
                font_size=8, fill="black", text_anchor="middle",
            ))

        # Value labels
        for j, (px, py) in enumerate(res["value_pts"]):
            sx, sy = _to_svg_xy(px, py)
            _svg_elems.append(text_to_svg(
                sx, sy, res["value_txt"][j],
                font_size=7, fill="black", text_anchor="middle",
                dominant_baseline="middle",
            ))

        # Legend cells
        for j, (lx, ly, lw, lh) in enumerate(res["legend_cells"]):
            rr, gg, bb, aa = res["legend_colors"][j]
            _fill = "rgb({},{},{})".format(rr, gg, bb)
            _op = round(aa / 255.0, 4)
            _svg_elems.append(polyline_to_svg(
                _rect_pts(lx, ly, lw, lh),
                fill=_fill, fill_opacity=_op, stroke="none",
            ))

        # Legend labels
        for j, (px, py) in enumerate(res["legend_pts"]):
            sx, sy = _to_svg_xy(px, py)
            _svg_elems.append(text_to_svg(
                sx, sy, res["legend_txt"][j],
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
            "  matrix: {}×{}\n"
            "  value range: {:.2f} – {:.2f}\n"
            "  legend: {}\n"
            "  chart area: {:.1f} x {:.1f}\n"
            "  SVG saved: {}".format(
                meta.get("num_rows", 0),
                meta.get("num_cols", 0),
                meta.get("value_range", (0, 0))[0],
                meta.get("value_range", (0, 0))[1],
                meta.get("legend_orientation", "n/a") if meta.get("has_legend") else "off",
                meta.get("chart_area", (0, 0))[0],
                meta.get("chart_area", (0, 0))[1],
                svg_path if svg_path else "(not saved)",
            )
        )

    except Exception as e:
        import traceback
        report = "ERROR: {}\n{}".format(e, traceback.format_exc())
