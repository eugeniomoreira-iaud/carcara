"""CRC_PolylineToSVG: Convert Grasshopper polylines/polygons to SVG element strings."""
import sys
import os

# Make crc_modules importable from GHPython environment.
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

from crc_modules.svg.export import polyline_to_svg

svg_code = []
report = "Provide polylines on input 'p'."

try:
    if not p:
        report = "No polylines provided on input 'p'."
    else:
        # Determine canvas anchor and height for Y-flip
        # Canvas is an optional Rectangle3d; if absent use bounding box of all geoms
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
            # Build bounding box from all polylines
            combined = rg.BoundingBox.Empty
            for poly in p:
                if poly is None:
                    continue
                if hasattr(poly, 'GetBoundingBox'):
                    bbox = poly.GetBoundingBox(False)
                    combined = rg.BoundingBox.Union(combined, bbox)
            if combined.IsValid:
                anchor_x = combined.Min.X
                anchor_y = combined.Min.Y
                canvas_h = combined.Max.Y - combined.Min.Y

        # Ensure lists for per-item style lookup
        def _get(lst, i, default):
            if lst is None:
                return default
            if isinstance(lst, (list, tuple)):
                if len(lst) == 0:
                    return default
                return lst[i] if i < len(lst) else lst[-1]
            return lst  # single value — constant

        elements = []
        ok = failed = 0
        for i, poly in enumerate(p):
            if poly is None:
                failed += 1
                continue
            try:
                # Extract vertices
                if hasattr(poly, 'ToPolyline'):
                    pl = poly.ToPolyline()
                elif hasattr(poly, 'IsPolyline'):
                    success, pl = poly.TryGetPolyline()
                    if not success:
                        pl = None
                else:
                    pl = poly  # assume Polyline already

                if pl is None:
                    failed += 1
                    continue

                pts_rhino = list(pl)
                if len(pts_rhino) < 2:
                    failed += 1
                    continue

                # Y-flip: svg_y = canvas_h - (rhino_y - anchor_y)
                pts_svg = [
                    (pt.X - anchor_x, canvas_h - (pt.Y - anchor_y))
                    for pt in pts_rhino
                ]

                # Per-item styling
                stroke_val = _get(sc, i, "none") or "none"
                sw_val = float(_get(sw, i, 0) or 0)
                fill_val = _get(f, i, "none") or "none"
                dash_val = _get(dash, i, "") or ""

                elem = polyline_to_svg(
                    pts_svg,
                    stroke=str(stroke_val),
                    stroke_width=sw_val,
                    fill=str(fill_val),
                    dash=dash_val,
                )
                elements.append(elem)
                ok += 1
            except Exception as e:
                failed += 1

        svg_code = elements
        report = "OK – {} element(s) generated".format(ok)
        if failed:
            report += ", {} failed".format(failed)

except Exception as e:
    report = "ERROR: {}".format(e)
