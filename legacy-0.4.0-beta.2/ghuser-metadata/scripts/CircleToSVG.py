"""Circle to SVG - Grasshopper Circle to SVG Converter

This component converts Grasshopper circle geometries to SVG circle elements.
Handles coordinate transformation from Rhino (Y-up) to SVG (Y-down) coordinate
systems and converts .NET Color objects to valid SVG color strings with
separate opacity for Adobe Illustrator compatibility.
Supports per-circle styling or constant styles across all circles.

Typical usage:
    Circles -> Stroke/Fill/Width Styling -> Canvas -> SVG Code

Args (Component Inputs):
    c: (Circle/List[Circle]) Circle geometry/geometries
        - Type: Rhino.Geometry.Circle or list
        - Access: item or list
        - Optional: Yes (empty returns empty string)
    
    sc: (Color/String/List) Stroke color(s)
        - Type: System.Drawing.Color, str, or list
        - Access: item or list
        - Optional: Yes (defaults to "none")
        - Format: Color object or CSS color (e.g., "black", "#FF0000")
    
    sw: (Float/List[Float]) Stroke width(s)
        - Type: float or list[float]
        - Access: item or list
        - Optional: Yes (defaults to 0)
    
    f: (Color/String/List) Fill color(s)
        - Type: System.Drawing.Color, str, or list
        - Access: item or list
        - Optional: Yes (defaults to "none")
        - Format: Color object or CSS color
    
    canvas: (Rectangle) Canvas boundary rectangle
        - Type: Rhino.Geometry geometry
        - Access: item
        - Optional: Yes (uses bounding box of circles if not provided)

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    svg_code: (String) SVG circle elements
        - Type: str
        - Note: Elements only, not complete SVG document

Version: 2.0
Date: 2025/11/14
Requires: carcara_dataviz v2.0+ module
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
COMPONENT_VERSION = "2.0"
COMPONENT_DATE = "2025/11/14"

ghenv.Component.Name = "Circle to SVG"
ghenv.Component.NickName = "circleSVG.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '04.Dataviz'
ghenv.Component.Description = "Converts Grasshopper circles into SVG using a canvas border if provided."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "c"
ghenv.Component.Params.Input[0].NickName = "c"
ghenv.Component.Params.Input[0].Description = "One or more Grasshopper circle geometries."

ghenv.Component.Params.Input[1].Name = "sc"
ghenv.Component.Params.Input[1].NickName = "sc"
ghenv.Component.Params.Input[1].Description = "Stroke color (can be a list or constant). Accepts Color objects or strings."

ghenv.Component.Params.Input[2].Name = "sw"
ghenv.Component.Params.Input[2].NickName = "sw"
ghenv.Component.Params.Input[2].Description = "Stroke width (can be a list or constant)."

ghenv.Component.Params.Input[3].Name = "f"
ghenv.Component.Params.Input[3].NickName = "f"
ghenv.Component.Params.Input[3].Description = "Fill color (can be a list or constant). Accepts Color objects or strings."

ghenv.Component.Params.Input[4].Name = "canvas"
ghenv.Component.Params.Input[4].NickName = "canvas"
ghenv.Component.Params.Input[4].Description = "A rectangle geometry defining the SVG canvas. If not provided, the bounding box of all geometries will be used."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "svg_code"
ghenv.Component.Params.Output[1].NickName = "svg_code"
ghenv.Component.Params.Output[1].Description = "The generated SVG code."


################
# INPUT HANDLING & VALIDATION
################
c = globals().get('c', None)
sc = globals().get('sc', None)
sw = globals().get('sw', None)
f = globals().get('f', None)
canvas = globals().get('canvas', None)


################
# EXECUTION
################
svg_code = ""

try:
    # Normalize input to list
    circles = svg.normalize_input_list(c)
    
    if not circles:
        print("No circles provided")
    else:
        print("Processing {} circle(s)...".format(len(circles)))
        
        # Get canvas dimensions
        anchor_pt, w, h = svg.get_canvas_dimensions(canvas, circles)
        
        if w == 0 or h == 0:
            print("Warning: Canvas has zero dimensions")
            ghenv.Component.AddRuntimeMessage(RML.Warning, "Canvas has zero dimensions")
        else:
            print("Canvas: {}x{} at ({:.2f}, {:.2f})".format(w, h, anchor_pt.X, anchor_pt.Y))
            
            # Generate SVG elements for each circle
            svg_elements = []
            for i, circle in enumerate(circles):
                try:
                    # Extract circle parameters (in Rhino coordinates)
                    cx, cy, r = svg.extract_circle_parameters(circle)
                    
                    # Transform to SVG coordinates
                    svg_x, svg_y = svg.transform_point_to_svg(cx, cy, anchor_pt, h)
                    
                    # Get styling values for this circle
                    stroke_raw = svg.get_indexed_value(sc, i, "none")
                    fill_raw = svg.get_indexed_value(f, i, "none")
                    stroke_width = svg.get_indexed_value(sw, i, 0)
                    
                    # Convert colors to SVG format (handles Color objects)
                    stroke, stroke_opacity = svg.convert_color_to_svg(stroke_raw)
                    fill, fill_opacity = svg.convert_color_to_svg(fill_raw)
                    
                    # Generate SVG circle element
                    element = svg.svg_circle(
                        svg_x, svg_y, r,
                        stroke=stroke,
                        fill=fill,
                        stroke_width=stroke_width,
                        fill_opacity=fill_opacity,
                        stroke_opacity=stroke_opacity
                    )
                    svg_elements.append(element)
                    
                    print("Circle {}: cx={:.2f}, cy={:.2f}, r={:.2f}, fill={}, opacity={}".format(
                        i, svg_x, svg_y, r, fill, fill_opacity
                    ))
                
                except Exception as e:
                    print("Warning: Error processing circle {}: {}".format(i, e))
            
            # Combine all elements
            svg_code = "".join(svg_elements)
            print("Generated {} circle elements ({} chars)".format(len(svg_elements), len(svg_code)))

except ImportError as e:
    ghenv.Component.AddRuntimeMessage(RML.Error, "Module import error - see 'out' for details.")
    print("Module import error: {}. Ensure carcara_dataviz v2.0+ is in modules folder.".format(e))
    svg_code = ""
except AttributeError as e:
    ghenv.Component.AddRuntimeMessage(RML.Error, "Module function error - see 'out' for details.")
    print("Module function error: {}. Check carcara_dataviz module version (need v2.0+).".format(e))
    svg_code = ""
except Exception as e:
    ghenv.Component.AddRuntimeMessage(RML.Error, "Unexpected error - see 'out' for details.")
    print("Unexpected error: {} (Type: {})".format(e, type(e).__name__))
    svg_code = ""
