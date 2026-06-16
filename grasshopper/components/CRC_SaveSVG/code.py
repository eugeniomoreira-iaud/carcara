"""CRC_SaveSVG: Assemble SVG element strings into a complete SVG document and write to disk."""
import sys
import os
import Grasshopper

# Dynamically route to the user objects folder via the Grasshopper API
_carcara_path = os.path.join(Grasshopper.Folders.DefaultUserObjectFolder, "carcara")

if os.path.isdir(_carcara_path) and _carcara_path not in sys.path:
    sys.path.insert(0, _carcara_path)

try:
    ghenv.Component.Message = "v{{component_version}}-{{date}}"
except Exception:
    pass

from crc_modules.svg.save import save_svg as _save_svg

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600

path = ""
svgDoc = ""
report = "Set 'saveFlag' to True to write SVG file."

try:
    # Collect elements — svgCode arrives as list (scriptParamAccess: list)
    elements = [str(e) for e in svgCode if e] if svgCode else []

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
    svgDoc = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"'
        ' width="{w}mm" height="{h}mm" viewBox="{vb}">\n'
        '{body}\n'
        '</svg>\n'
    ).format(w=w, h=h, vb=vb, body=body)

    if not saveFlag:
        report = "Ready – {}x{} canvas, {} element(s). Activate saveFlag to write.".format(
            w, h, len(elements))
    else:
        # Validate inputs
        if not filePath or not str(filePath).strip():
            raise ValueError("filePath must not be empty")
        if not elements:
            raise ValueError("svgCode is empty – nothing to save")

        fp = str(filePath).strip()
        written = _save_svg(elements, fp, w, h, units="mm")
        path = written
        size = os.path.getsize(written)
        report = "OK – saved {} ({} bytes, {}x{}, {} element(s))".format(
            os.path.basename(written), size, w, h, len(elements))

except Exception as e:
    report = "ERROR: {}".format(e)
