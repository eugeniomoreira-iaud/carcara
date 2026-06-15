"""CRC_LinePlot: Line chart as Rhino geometry + optional SVG export."""
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
    ghenv.Component.Message = "v{{version}} - {{date}}"
except Exception:
    pass

# ---------------------------------------------------------------------------
# Rhino geometry imports (allowed in code.py)
# ---------------------------------------------------------------------------
import Rhino.Geometry as rg

# ---------------------------------------------------------------------------
# crc_modules imports
# ---------------------------------------------------------------------------
from crc_modules.viz.lineplot import create_lineplot
from crc_modules.svg.export import polyline_to_svg, text_to_svg

# ---------------------------------------------------------------------------
# Initialise outputs
# ---------------------------------------------------------------------------
out      = "Provide x and y data to run"
lines    = []
axes     = []
x_pts    = []
x_txt    = []
y_pts    = []
y_txt    = []
grid_x   = []
grid_y   = []
svg_code = ""
svg_path = ""

# ---------------------------------------------------------------------------
# Guard: need at least x and y
# ---------------------------------------------------------------------------
if x and y:
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
        nx_val   = int(nx)    if nx   is not None else 5
        ny_val   = int(ny)    if ny   is not None else 5
        d_val    = int(d)     if d    is not None else 1
        ext_val  = float(ext) if ext  is not None else 0.0
        dist_val = float(dist)if dist is not None else 10.0
        mx_val   = float(mx)  if mx   is not None else 0.0
        my_val   = float(my)  if my   is not None else 0.0
        gx_val   = bool(gx)   if gx   is not None else False
        gy_val   = bool(gy)   if gy   is not None else False

        # ------------------------------------------------------------------
        # 3. Parse DataTree inputs (x and y may arrive as GH DataTree or flat list)
        #    GH passes list inputs as flat lists when access=list.
        #    For DataTree access we would need tree access; since metadata.json
        #    declares scriptParamAccess="list" the component receives a flat list
        #    for single-series usage. To handle multi-series DataTree the user
        #    should pass via the x/y inputs with DataTree access.
        #    We pass the raw value to create_lineplot which calls _parse_series.
        # ------------------------------------------------------------------
        # Try DataTree branch extraction first (GHPython DataTree)
        def _extract_series(data_in):
            """Try to extract list-of-lists from GH DataTree or plain list."""
            if data_in is None:
                return []
            # GH DataTree
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
            # Plain flat list
            try:
                return [float(v) for v in data_in if v is not None]
            except Exception:
                return []

        x_input = _extract_series(x)
        y_input = _extract_series(y)

        # ------------------------------------------------------------------
        # 4. Call pure module
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 5. Build Rhino geometry
        # ------------------------------------------------------------------
        # Lines → PolylineCurve (one per series)
        for series_pts in result["lines"]:
            rh_pts = [rg.Point3d(xp, yp, 0.0) for xp, yp in series_pts]
            pl = rg.Polyline(rh_pts)
            lines.append(pl.ToPolylineCurve())

        # Axes → Line
        for (p0, p1) in result["axes"]:
            axes.append(rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                                rg.Point3d(p1[0], p1[1], 0.0)))

        # X labels
        for (xp, yp) in result["x_pts"]:
            x_pts.append(rg.Point3d(xp, yp, 0.0))
        x_txt = result["x_txt"]

        # Y labels
        for (xp, yp) in result["y_pts"]:
            y_pts.append(rg.Point3d(xp, yp, 0.0))
        y_txt = result["y_txt"]

        # Grid X → Line
        for (p0, p1) in result["grid_x"]:
            grid_x.append(rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                                  rg.Point3d(p1[0], p1[1], 0.0)))

        # Grid Y → Line
        for (p0, p1) in result["grid_y"]:
            grid_y.append(rg.Line(rg.Point3d(p0[0], p0[1], 0.0),
                                  rg.Point3d(p1[0], p1[1], 0.0)))

        # ------------------------------------------------------------------
        # 6. Build SVG elements
        #    SVG Y-down: svg_y = (oy + ch) - (rhino_y - oy)
        # ------------------------------------------------------------------
        def to_svg_y(rhino_y):
            return (oy + ch) - (rhino_y - oy)

        svg_elements = []

        # Grid Y lines (draw behind series)
        for (p0, p1) in result["grid_y"]:
            pts_svg = [(p0[0] - ox, to_svg_y(p0[1])),
                       (p1[0] - ox, to_svg_y(p1[1]))]
            svg_elements.append(
                polyline_to_svg(pts_svg, stroke="#CCCCCC", stroke_width=0.5, fill="none")
            )

        # Grid X lines
        for (p0, p1) in result["grid_x"]:
            pts_svg = [(p0[0] - ox, to_svg_y(p0[1])),
                       (p1[0] - ox, to_svg_y(p1[1]))]
            svg_elements.append(
                polyline_to_svg(pts_svg, stroke="#CCCCCC", stroke_width=0.5, fill="none")
            )

        # Axes
        for (p0, p1) in result["axes"]:
            pts_svg = [(p0[0] - ox, to_svg_y(p0[1])),
                       (p1[0] - ox, to_svg_y(p1[1]))]
            svg_elements.append(
                polyline_to_svg(pts_svg, stroke="black", stroke_width=1.0, fill="none")
            )

        # Line series
        _stroke_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                          "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        for i, series_pts in enumerate(result["lines"]):
            clr = _stroke_colors[i % len(_stroke_colors)]
            pts_svg = [(xp - ox, to_svg_y(yp)) for xp, yp in series_pts]
            svg_elements.append(
                polyline_to_svg(pts_svg, stroke=clr, stroke_width=1.5, fill="none")
            )

        # X labels
        for (xp, yp), label in zip(result["x_pts"], result["x_txt"]):
            svg_elements.append(
                text_to_svg(xp - ox, to_svg_y(yp), label,
                            fill="black", font_size=8,
                            text_anchor="middle", dominant_baseline="hanging")
            )

        # Y labels
        for (xp, yp), label in zip(result["y_pts"], result["y_txt"]):
            svg_elements.append(
                text_to_svg(xp - ox, to_svg_y(yp), label,
                            fill="black", font_size=8,
                            text_anchor="end", dominant_baseline="middle")
            )

        # Assemble SVG document string
        svg_body = "\n".join(e for e in svg_elements if e)
        svg_code = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg"'
            ' width="{w}mm" height="{h}mm"'
            ' viewBox="0 0 {w} {h}">\n'
            '{body}\n'
            '</svg>\n'
        ).format(w=round(cw, 4), h=round(ch, 4), body=svg_body)

        # ------------------------------------------------------------------
        # 7. Optionally save SVG to file
        # ------------------------------------------------------------------
        meta = result["metadata"]
        if CToggle and OutPath and OutPath.strip():
            out_abs = os.path.abspath(OutPath.strip())
            parent  = os.path.dirname(out_abs)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            with open(out_abs, "w", encoding="utf-8") as fh:
                fh.write(svg_code)
            svg_path = out_abs
            out = "OK — {} series. X: {:.2f}–{:.2f}  Y: {:.2f}–{:.2f}. SVG saved: {}".format(
                meta["num_series"],
                meta["x_range"][0], meta["x_range"][1],
                meta["y_range"][0], meta["y_range"][1],
                svg_path,
            )
        else:
            out = "OK — {} series. X: {:.2f}–{:.2f}  Y: {:.2f}–{:.2f}.".format(
                meta["num_series"],
                meta["x_range"][0], meta["x_range"][1],
                meta["y_range"][0], meta["y_range"][1],
            )

    except Exception as e:
        import traceback
        out = "ERROR: {}\n{}".format(e, traceback.format_exc())
