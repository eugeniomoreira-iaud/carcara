"""CRC_CircleToSVG: Convert Grasshopper Circle geometries to SVG <circle> element strings."""
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
    ghenv.Component.Message = "v{{version}}"
except Exception:
    pass

import Rhino.Geometry as rg

from crc_modules.svg.export import circle_to_svg

svg_code = []
report = "Provide circles on input 'c'."

try:
    if not c:
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
            for circ in c:
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

        def _get(lst, i, default):
            if lst is None:
                return default
            if isinstance(lst, (list, tuple)):
                if len(lst) == 0:
                    return default
                return lst[i] if i < len(lst) else lst[-1]
            return lst

        elements = []
        ok = failed = 0
        for i, circ in enumerate(c):
            if circ is None:
                failed += 1
                continue
            try:
                cx_rhino = circ.Center.X
                cy_rhino = circ.Center.Y
                r = circ.Radius

                svg_x = cx_rhino - anchor_x
                svg_y = canvas_h - (cy_rhino - anchor_y)

                stroke_val = str(_get(sc, i, "none") or "none")
                sw_val = float(_get(sw, i, 0) or 0)
                fill_val = str(_get(f, i, "none") or "none")

                elem = circle_to_svg(
                    svg_x, svg_y, r,
                    stroke=stroke_val,
                    stroke_width=sw_val,
                    fill=fill_val,
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
