"""CRC_TextToSVG: Convert text strings with Point3d or Plane insertion to SVG <text> elements."""
import sys
import os
import math

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

from crc_modules.svg.export import text_to_svg

# Justification mapping: int 1-9 → (text-anchor, dominant-baseline)
_JUST_MAP = {
    1: ("start",  "hanging"),   # Top Left
    2: ("middle", "hanging"),   # Top Center
    3: ("end",    "hanging"),   # Top Right
    4: ("start",  "middle"),    # Middle Left
    5: ("middle", "middle"),    # Middle Center
    6: ("end",    "middle"),    # Middle Right
    7: ("start",  "baseline"),  # Bottom Left
    8: ("middle", "baseline"),  # Bottom Center
    9: ("end",    "baseline"),  # Bottom Right
}
DEFAULT_JUST = 6
DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_FONT_SIZE = 12
DEFAULT_FILL = "black"

svg_code = []
report = "Provide text on input 't'."

try:
    texts = t if t else []
    if not texts:
        report = "No text provided on input 't'."
    else:
        # Canvas anchor for Y-flip
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

        # Resolved style constants (same for all text items in this call)
        font_family = str(ff) if ff else DEFAULT_FONT_FAMILY
        font_size = float(fs) if fs else DEFAULT_FONT_SIZE
        fill_color = str(fC) if fC else DEFAULT_FILL

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
        for i, txt in enumerate(texts):
            if txt is None:
                failed += 1
                continue
            try:
                ins = _get(pt, i, None) if pt else None

                # Defaults
                x_svg = 0.0
                y_svg = 0.0
                rotation = 0.0

                if ins is not None:
                    if isinstance(ins, rg.Plane):
                        # Extract position from plane origin
                        rx = ins.Origin.X
                        ry = ins.Origin.Y
                        # Rotation from X-axis angle in XY plane
                        xa = ins.XAxis
                        rotation = math.degrees(math.atan2(xa.Y, xa.X))
                        # Negate for SVG Y-down
                        rotation = -rotation
                    elif isinstance(ins, rg.Point3d):
                        rx = ins.X
                        ry = ins.Y
                    else:
                        # Try to get .X, .Y attributes
                        rx = float(getattr(ins, 'X', 0))
                        ry = float(getattr(ins, 'Y', 0))

                    # Y-flip
                    x_svg = rx - anchor_x
                    if canvas_h > 0:
                        y_svg = canvas_h - (ry - anchor_y)
                    else:
                        y_svg = ry

                just_val = int(_get(j, i, DEFAULT_JUST) or DEFAULT_JUST)
                anchor, baseline = _JUST_MAP.get(just_val, _JUST_MAP[DEFAULT_JUST])

                elem = text_to_svg(
                    x_svg, y_svg, str(txt),
                    fill=fill_color,
                    font_family=font_family,
                    font_size=font_size,
                    text_anchor=anchor,
                    dominant_baseline=baseline,
                    rotation=rotation,
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
