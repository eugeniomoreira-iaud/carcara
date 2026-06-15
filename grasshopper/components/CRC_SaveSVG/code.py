"""CRC_SaveSVG: Assemble SVG element strings into a complete SVG document and write to disk."""
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

from crc_modules.svg.save import save_svg as _save_svg

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600

path = ""
svg_doc = ""
report = "Set 'save_flag' to True to write SVG file."

try:
    # Collect elements — svg_code arrives as list (scriptParamAccess: list)
    elements = [str(e) for e in svg_code if e] if svg_code else []

    # Derive width/height from canvas if provided
    w = DEFAULT_WIDTH
    h = DEFAULT_HEIGHT
    if canvas is not None:
        try:
            bbox = canvas.BoundingBox
            w = bbox.Max.X - bbox.Min.X
            h = bbox.Max.Y - bbox.Min.Y
        except Exception:
            pass

    # Build SVG document string (without writing)
    vb = "0 0 {} {}".format(w, h)
    body = "\n".join(e for e in elements if e)
    svg_doc = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"'
        ' width="{w}mm" height="{h}mm" viewBox="{vb}">\n'
        '{body}\n'
        '</svg>\n'
    ).format(w=w, h=h, vb=vb, body=body)

    if not save_flag:
        report = "Ready – {}x{} canvas, {} element(s). Activate save_flag to write.".format(
            w, h, len(elements))
    else:
        # Validate inputs
        if not file_path or not str(file_path).strip():
            raise ValueError("file_path must not be empty")
        if not elements:
            raise ValueError("svg_code is empty – nothing to save")

        fp = str(file_path).strip()
        written = _save_svg(elements, fp, w, h, units="mm")
        path = written
        size = os.path.getsize(written)
        report = "OK – saved {} ({} bytes, {}x{}, {} element(s))".format(
            os.path.basename(written), size, w, h, len(elements))

except Exception as e:
    report = "ERROR: {}".format(e)
