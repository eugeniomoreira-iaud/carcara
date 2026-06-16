"""Text to SVG - Text to SVG Element Converter with Rotation

This component converts text strings with insertion points/planes to SVG text elements.
Supports both Point3d and Plane inputs for position and rotation control.
Handles coordinate transformation from Rhino (Y-up) to SVG (Y-down) systems.

Typical usage:
    Text Strings -> Insertion Points/Planes -> Font/Size/Color -> Canvas -> SVG Code

Justification Mapping:
    1: Top Left       2: Top Center      3: Top Right
    4: Middle Left    5: Middle Center   6: Middle Right
    7: Bottom Left    8: Bottom Center   9: Bottom Right

Args (Component Inputs):
    t: Text string(s) to render
    pt: Insertion point(s) OR plane(s) for text (Point3d or Plane)
    ff: Font family name (default "Arial")
    fs: Font size in pixels (default 12)
    fC: Fill color (default "black")
    canvas: Canvas boundary rectangle (optional)
    j: Text justification value(s) (default 6 - Middle Right)

Returns (Component Outputs):
    out: Processing log
    svg_code: SVG text elements

Version: 3.0
Date: 2025/11/19
Requires: carcara_dataviz v2.1+ module
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Grasshopper
import Rhino.Geometry as rg
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML
import System.Drawing

user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_dataviz as svg
importlib.reload(svg)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "3.0"
COMPONENT_DATE = "2025/11/19"
DEFAULT_FONT_FAMILY = "Arial"
DEFAULT_FONT_SIZE = 12
DEFAULT_FILL_COLOR = "black"
DEFAULT_JUSTIFICATION = 6

ghenv.Component.Name = "Text to SVG"
ghenv.Component.NickName = "textSVG.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '04.Dataviz'
ghenv.Component.Description = "Converts text to SVG with rotation support via planes."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "t"
ghenv.Component.Params.Input[0].NickName = "t"
ghenv.Component.Params.Input[0].Description = "Text string(s) to render."

ghenv.Component.Params.Input[1].Name = "pt"
ghenv.Component.Params.Input[1].NickName = "pt"
ghenv.Component.Params.Input[1].Description = "Insertion point(s) or plane(s) for text (Point3d or Plane)."

ghenv.Component.Params.Input[2].Name = "ff"
ghenv.Component.Params.Input[2].NickName = "ff"
ghenv.Component.Params.Input[2].Description = "Font family (default 'Arial')."

ghenv.Component.Params.Input[3].Name = "fs"
ghenv.Component.Params.Input[3].NickName = "fs"
ghenv.Component.Params.Input[3].Description = "Font size (default 12)."

ghenv.Component.Params.Input[4].Name = "fC"
ghenv.Component.Params.Input[4].NickName = "fC"
ghenv.Component.Params.Input[4].Description = "Fill color (default 'black')."

ghenv.Component.Params.Input[5].Name = "canvas"
ghenv.Component.Params.Input[5].NickName = "canvas"
ghenv.Component.Params.Input[5].Description = "Canvas rectangle (optional)."

ghenv.Component.Params.Input[6].Name = "j"
ghenv.Component.Params.Input[6].NickName = "j"
ghenv.Component.Params.Input[6].Description = "Text justification (1-9, default 6)."


################
# OUTPUT METADATA
################
ghenv.Component.Params.Output[1].Name = "svg_code"
ghenv.Component.Params.Output[1].NickName = "svg_code"
ghenv.Component.Params.Output[1].Description = "Generated SVG text elements."


################
# HELPER FUNCTIONS
################
def map_justification(just_val):
    """Map justification integer to SVG alignment attributes."""
    mapping = {
        1: ("start", "hanging"),      # Top Left
        2: ("middle", "hanging"),     # Top Center
        3: ("end", "hanging"),        # Top Right
        4: ("start", "middle"),       # Middle Left
        5: ("middle", "middle"),      # Middle Center
        6: ("end", "middle"),         # Middle Right
        7: ("start", "baseline"),     # Bottom Left
        8: ("middle", "baseline"),    # Bottom Center
        9: ("end", "baseline")        # Bottom Right
    }
    
    try:
        j = int(just_val)
        if j < 1 or j > 9:
            return mapping[DEFAULT_JUSTIFICATION]
    except:
        return mapping[DEFAULT_JUSTIFICATION]
    
    return mapping.get(j, mapping[DEFAULT_JUSTIFICATION])


def normalize_text_list(input_data):
    """Normalize text input to list format."""
    if input_data is None:
        return []
    if isinstance(input_data, str):
        return [input_data]
    if hasattr(input_data, '__iter__'):
        return list(input_data)
    return [input_data]


def is_plane(obj):
    """Check if object is a Plane."""
    return isinstance(obj, rg.Plane) or (hasattr(obj, 'Origin') and hasattr(obj, 'XAxis'))


################
# INPUT HANDLING
################
t = globals().get('t', None)
pt = globals().get('pt', None)
ff = globals().get('ff', DEFAULT_FONT_FAMILY)
fs = globals().get('fs', DEFAULT_FONT_SIZE)
fC = globals().get('fC', DEFAULT_FILL_COLOR)
canvas = globals().get('canvas', None)
j = globals().get('j', DEFAULT_JUSTIFICATION)


################
# EXECUTION
################
svg_code = ""

try:
    # Normalize inputs
    texts = normalize_text_list(t)
    insertion_data = svg.normalize_input_list(pt)
    
    if not texts:
        print("No text strings provided")
    else:
        print("Processing {} text string(s)...".format(len(texts)))
        print("Font: {} {}px".format(ff, fs))
        
        # Get canvas info
        anchor_pt = None
        canvas_height = 0
        if canvas is not None:
            try:
                anchor_pt, w, canvas_height = svg.canvas_origin_info(canvas)
                print("Canvas: {}x{} at ({:.2f}, {:.2f})".format(w, canvas_height, anchor_pt.X, anchor_pt.Y))
            except Exception as e:
                print("Warning: Canvas error: {}".format(e))
        else:
            print("No canvas - using absolute coordinates")
        
        # Convert fill color
        fill_color, fill_opacity = svg.convert_color_to_svg(fC)
        print("Fill: {}, opacity: {}".format(fill_color, fill_opacity))
        
        # Generate SVG elements
        svg_elements = []
        stats = {'processed': 0, 'successful': 0, 'failed': 0}
        
        for i, txt in enumerate(texts):
            stats['processed'] += 1
            
            try:
                # Get insertion data (point or plane)
                if insertion_data:
                    ins_data = svg.get_indexed_value(insertion_data, i, rg.Point3d(0, 0, 0))
                else:
                    ins_data = rg.Point3d(0, 0, 0)
                
                # Check if it's a plane or point
                if is_plane(ins_data):
                    # Extract position and rotation from plane
                    x, y, rotation = svg.extract_plane_transform(ins_data, anchor_pt, canvas_height)
                    print("Text {}: Plane at ({:.2f}, {:.2f}), rot={:.1f}°".format(i, x, y, rotation))
                else:
                    # It's a point - no rotation
                    if anchor_pt and canvas_height > 0:
                        x, y = svg.transform_point_to_svg(ins_data.X, ins_data.Y, anchor_pt, canvas_height)
                    else:
                        x, y = ins_data.X, ins_data.Y
                    rotation = 0
                    print("Text {}: Point at ({:.2f}, {:.2f})".format(i, x, y))
                
                # Get justification
                just_val = svg.get_indexed_value(j, i, DEFAULT_JUSTIFICATION)
                text_anchor, dominant_baseline = map_justification(just_val)
                
                # Generate SVG text element with rotation
                element = svg.svg_text_with_transform(
                    x, y, txt,
                    rotation=rotation,
                    font_family=ff if ff else DEFAULT_FONT_FAMILY,
                    font_size=fs,
                    fill=fill_color,
                    text_anchor=text_anchor,
                    dominant_baseline=dominant_baseline,
                    fill_opacity=fill_opacity
                )
                svg_elements.append(element)
                stats['successful'] += 1
                
            except Exception as e:
                print("Warning: Error processing text {}: {}".format(i, e))
                stats['failed'] += 1
        
        # Combine elements
        svg_code = "".join(svg_elements)
        
        print("Generated {} of {} text elements ({} chars)".format(
            stats['successful'], stats['processed'], len(svg_code)
        ))
        
        if stats['failed'] > 0:
            ghenv.Component.AddRuntimeMessage(RML.Warning, "{} text(s) failed".format(stats['failed']))

except Exception as e:
    ghenv.Component.AddRuntimeMessage(RML.Error, "Error - see 'out'")
    print("Error: {} (Type: {})".format(e, type(e).__name__))
    import traceback
    traceback.print_exc()
    svg_code = ""
