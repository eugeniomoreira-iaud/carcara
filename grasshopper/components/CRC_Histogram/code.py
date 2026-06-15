"""CRC_Histogram: Histogram chart as Rhino geometry + optional SVG export."""
import sys
import os

# ---------------------------------------------------------------------------
# sys.path bootstrap — make crc_modules importable inside GHPython
# ---------------------------------------------------------------------------
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
    ghenv.Component.Message = "v{{version}}"
except Exception:
    pass

# ---------------------------------------------------------------------------
# Rhino geometry imports (allowed in code.py)
# ---------------------------------------------------------------------------
import Rhino.Geometry as rg

# ---------------------------------------------------------------------------
# crc_modules imports
# ---------------------------------------------------------------------------
from crc_modules.viz.histogram import create_histogram
from crc_modules.svg.export import polyline_to_svg, text_to_svg
from crc_modules.svg.save import save_svg

# ---------------------------------------------------------------------------
# Initialise outputs
# ---------------------------------------------------------------------------
out      = "Provide values (v) to run"
bars     = []
axes     = []
x_pts    = []
x_txt    = []
y_pts    = []
y_txt    = []
grid     = []
svg_code = ""
svg_path = ""

# ---------------------------------------------------------------------------
# Guard: need at least values (v) to do anything
# ---------------------------------------------------------------------------
if v:
    try:
        # ------------------------------------------------------------------
        # 1. Extract canvas bounds from the Rhino Rectangle3d input
        # ------------------------------------------------------------------
        if cv is not None:
            origin = cv.Corner(0)
            ox = origin.X
            oy = origin.Y
            cw = cv.Width
            ch = cv.Height
        else:
            ox, oy, cw, ch = 0.0, 0.0, 100.0, 100.0

        canvas_tuple = (ox, oy, cw, ch)

        # ------------------------------------------------------------------
        # 2. Coerce inputs
        # ------------------------------------------------------------------
        bins_val    = int(b)    if b    is not None else 10
        nx_val      = int(nx)   if nx   is not None else None
        ny_val      = int(ny)   if ny   is not None else 5
        d_val       = int(d)    if d    is not None else 1
        ext_val     = float(ext)  if ext  is not None else 0.0
        dist_val    = float(dist) if dist is not None else 10.0
        gy_val      = bool(gy)  if gy   is not None else False

        values_list = [float(x) for x in v if x is not None]

        # ------------------------------------------------------------------
        # 3. Call pure module
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 4. Build Rhino geometry from coordinate data
        # ------------------------------------------------------------------
        z_plane = rg.Plane.WorldXY

        # Bars → Rectangle3d
        for (x0, y0, x1, y1) in result["bars"]:
            corner = rg.Point3d(x0, y0, 0.0)
            plane  = rg.Plane(corner, rg.Vector3d.ZAxis)
            rect   = rg.Rectangle3d(plane, x1 - x0, y1 - y0)
            bars.append(rect)

        # Axes → Line
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

        # Grid → Line
        for (p0, p1) in result["grid"]:
            ln = rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                         rg.Point3d(p1[0], p1[1], 0.0))
            grid.append(ln)

        # ------------------------------------------------------------------
        # 5. Build SVG elements from the same coordinate data
        #    SVG coordinate system: Y is flipped (SVG Y-down)
        #    svg_y = canvas_top - (rhino_y - canvas_bottom)
        #          = (oy + ch) - (rhino_y - oy)
        #          = oy + ch - rhino_y + oy
        #    simplified: svg_y = (oy + ch) - (rhino_y - oy)
        # ------------------------------------------------------------------
        def to_svg_y(rhino_y):
            return (oy + ch) - (rhino_y - oy)

        svg_elements = []

        # bars as closed polygons
        for (x0, y0, x1, y1) in result["bars"]:
            pts_svg = [
                (x0 - ox, to_svg_y(y0)),
                (x1 - ox, to_svg_y(y0)),
                (x1 - ox, to_svg_y(y1)),
                (x0 - ox, to_svg_y(y1)),
                (x0 - ox, to_svg_y(y0)),  # close
            ]
            svg_elements.append(
                polyline_to_svg(pts_svg,
                                stroke="black", stroke_width=0.5,
                                fill="#AAAAAA")
            )

        # axes as open polylines
        for (p0, p1) in result["axes"]:
            pts_svg = [
                (p0[0] - ox, to_svg_y(p0[1])),
                (p1[0] - ox, to_svg_y(p1[1])),
            ]
            svg_elements.append(
                polyline_to_svg(pts_svg,
                                stroke="black", stroke_width=1.0,
                                fill="none")
            )

        # grid lines
        for (p0, p1) in result["grid"]:
            pts_svg = [
                (p0[0] - ox, to_svg_y(p0[1])),
                (p1[0] - ox, to_svg_y(p1[1])),
            ]
            svg_elements.append(
                polyline_to_svg(pts_svg,
                                stroke="#CCCCCC", stroke_width=0.5,
                                fill="none")
            )

        # x labels
        for (xp, yp), label in zip(result["x_pts"], result["x_txt"]):
            svg_elements.append(
                text_to_svg(xp - ox, to_svg_y(yp), label,
                            fill="black", font_size=8,
                            text_anchor="middle", dominant_baseline="hanging")
            )

        # y labels
        for (xp, yp), label in zip(result["y_pts"], result["y_txt"]):
            svg_elements.append(
                text_to_svg(xp - ox, to_svg_y(yp), label,
                            fill="black", font_size=8,
                            text_anchor="end", dominant_baseline="middle")
            )

        # Assemble SVG string (always, even if not saving)
        from crc_modules.svg.save import save_svg as _sv
        svg_body_parts = [e for e in svg_elements if e]
        svg_code = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg"'
            ' width="{w}mm" height="{h}mm"'
            ' viewBox="0 0 {w} {h}">\n'
            '{body}\n'
            '</svg>\n'
        ).format(w=round(cw, 4), h=round(ch, 4),
                 body="\n".join(svg_body_parts))

        # ------------------------------------------------------------------
        # 6. Optionally save SVG to file
        # ------------------------------------------------------------------
        if CToggle and OutPath and OutPath.strip():
            out_abs = os.path.abspath(OutPath.strip())
            parent  = os.path.dirname(out_abs)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            with open(out_abs, "w", encoding="utf-8") as fh:
                fh.write(svg_code)
            svg_path = out_abs
            out = "OK — {} values, {} bins. SVG saved: {}".format(
                result["metadata"]["num_values"],
                result["metadata"]["num_bins"],
                svg_path,
            )
        else:
            out = "OK — {} values, {} bins. Range: {:.2f}–{:.2f}. Max count: {}.".format(
                result["metadata"]["num_values"],
                result["metadata"]["num_bins"],
                result["metadata"]["data_range"][0],
                result["metadata"]["data_range"][1],
                result["metadata"]["max_count"],
            )

    except Exception as e:
        import traceback
        out = "ERROR: {}\n{}".format(e, traceback.format_exc())
