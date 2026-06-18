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

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
from Grasshopper import DataTree

def _unwrap(g):
    return g.Value if hasattr(g, "Value") else g

def _in_item(i):
    for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True):
        return _unwrap(g)
    return None

def _in_list(i):
    return [_unwrap(g) for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True)]

def _in_tree(i):
    src = ghenv.Component.Params.Input[i].VolatileData
    t = DataTree[object]()
    for p in src.Paths:
        for g in src[p]:
            t.Add(_unwrap(g), p)
    return t
# ========================================================================================

# INPUT MAPPING: 0:svg(svgCode/list), 1:canvas(canvas/item), 2:path(filePath/item), 3:save(saveFlag/item)
svg_int    = _in_list(0)
canvas_int = _in_item(1)
path_int   = _in_item(2)
save_int   = _in_item(3)

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600

path = ""
svgDoc = ""
report = "Set 'saveFlag' to True to write SVG file."

try:
    # Collect elements — svgCode arrives as list (scriptParamAccess: list)
    elements = [str(e) for e in svg_int if e] if svg_int else []

    # Derive width/height from canvas if provided
    w = DEFAULT_WIDTH
    h = DEFAULT_HEIGHT
    if canvas_int is not None:
        try:
            bbox = canvas_int.BoundingBox
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

    if not save_int:
        report = "Ready – {}x{} canvas, {} element(s). Activate saveFlag to write.".format(
            w, h, len(elements))
    else:
        # Validate inputs
        if not path_int or not str(path_int).strip():
            raise ValueError("filePath must not be empty")
        if not elements:
            raise ValueError("svgCode is empty – nothing to save")

        fp = str(path_int).strip()
        written = _save_svg(elements, fp, w, h, units="mm")
        path = written
        size = os.path.getsize(written)
        report = "OK – saved {} ({} bytes, {}x{}, {} element(s))".format(
            os.path.basename(written), size, w, h, len(elements))

except Exception as e:
    report = "ERROR: {}".format(e)
