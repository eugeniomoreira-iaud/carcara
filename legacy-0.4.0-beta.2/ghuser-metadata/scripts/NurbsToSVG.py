"""Nurbs to SVG - NURBS Curve to SVG Path Converter

This component converts Grasshopper NURBS curves to SVG path elements using
linear segment approximation. Handles coordinate transformation from Rhino
(Y-up) to SVG (Y-down) systems with proper color conversion and separate
opacity for Adobe Illustrator compatibility. Supports per-curve styling 
and sample count control for approximation precision.

Typical usage:
    NURBS Curves -> Sample Count -> Stroke/Fill Styling -> Canvas -> SVG Code

Args (Component Inputs):
    n: (Curve/List[Curve]) NURBS curve(s) to convert
        - Type: Rhino.Geometry.Curve or list
        - Access: item or list
        - Optional: Yes (empty returns empty string)
    
    s: (Integer/List[Integer]) Sample count for approximation
        - Type: int or list[int]
        - Access: item or list
        - Optional: Yes (defaults to 50)
        - Note: Higher values = smoother curves, larger output
    
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
        - Optional: Yes (uses bounding box of curves if not provided)

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    svg_code: (String) SVG path elements
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
DEFAULT_SAMPLE_COUNT = 50

ghenv.Component.Name = "Nurbs to SVG"
ghenv.Component.NickName = "nurbsSVG.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '04.Dataviz'
ghenv.Component.Description = "Converts Grasshopper Nurbs curves into SVG using approximate linear segments and a canvas border if provided."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "n"
ghenv.Component.Params.Input[0].NickName = "n"
ghenv.Component.Params.Input[0].Description = "One or more Grasshopper Nurbs curves."

ghenv.Component.Params.Input[1].Name = "s"
ghenv.Component.Params.Input[1].NickName = "s"
ghenv.Component.Params.Input[1].Description = "Sample count for the precision of the nurbs."

ghenv.Component.Params.Input[2].Name = "sc"
ghenv.Component.Params.Input[2].NickName = "sc"
ghenv.Component.Params.Input[2].Description = "Stroke color (can be a list or constant). Accepts Color objects or strings."

ghenv.Component.Params.Input[3].Name = "sw"
ghenv.Component.Params.Input[3].NickName = "sw"
ghenv.Component.Params.Input[3].Description = "Stroke width (can be a list or constant)."

ghenv.Component.Params.Input[4].Name = "f"
ghenv.Component.Params.Input[4].NickName = "f"
ghenv.Component.Params.Input[4].Description = "Fill color (can be a list or constant). Accepts Color objects or strings."

ghenv.Component.Params.Input[5].Name = "canvas"
ghenv.Component.Params.Input[5].NickName = "canvas"
ghenv.Component.Params.Input[5].Description = "A rectangle geometry defining the SVG canvas. If not provided, the bounding box of all curves will be used."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "svg_code"
ghenv.Component.Params.Output[1].NickName = "svg_code"
ghenv.Component.Params.Output[1].Description = "The generated SVG code."


################
# INPUT HANDLING & VALIDATION
################
n = globals().get('n', None)
s = globals().get('s', DEFAULT_SAMPLE_COUNT)
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
    curves = svg.normalize_input_list(n)
    
    if not curves:
        print("No curves provided")
    else:
        print("Processing {} curve(s)...".format(len(curves)))
        
        # Get canvas dimensions
        anchor_pt, w, h = svg.get_canvas_dimensions(canvas, curves)
        
        if w == 0 or h == 0:
            print("Warning: Canvas has zero dimensions")
            ghenv.Component.AddRuntimeMessage(RML.Warning, "Canvas has zero dimensions")
        else:
            print("Canvas: {}x{} at ({:.2f}, {:.2f})".format(w, h, anchor_pt.X, anchor_pt.Y))
            
            # Statistics tracking
            stats = {'processed': 0, 'successful': 0, 'failed': 0}
            svg_elements = []
            
            # Generate SVG elements for each curve
            for i, curve in enumerate(curves):
                stats['processed'] += 1
                
                try:
                    # Get sample count for this curve
                    sample_count = svg.get_indexed_value(s, i, DEFAULT_SAMPLE_COUNT)
                    
                    # Extract path data (includes coordinate transformation)
                    path_data = svg.extract_nurbs_path_data(curve, sample_count, anchor_pt, h)
                    
                    if not path_data or path_data.strip() == "":
                        print("Warning: Curve {} produced empty path data".format(i))
                        stats['failed'] += 1
                        continue
                    
                    # Get styling values for this curve
                    stroke_raw = svg.get_indexed_value(sc, i, "none")
                    fill_raw = svg.get_indexed_value(f, i, "none")
                    stroke_width = svg.get_indexed_value(sw, i, 0)
                    
                    # Convert colors to SVG format (handles Color objects)
                    stroke, stroke_opacity = svg.convert_color_to_svg(stroke_raw)
                    fill, fill_opacity = svg.convert_color_to_svg(fill_raw)
                    
                    # Generate SVG path element
                    element = svg.svg_path(
                        path_data,
                        stroke=stroke,
                        fill=fill,
                        stroke_width=stroke_width,
                        fill_opacity=fill_opacity,
                        stroke_opacity=stroke_opacity
                    )
                    svg_elements.append(element)
                    stats['successful'] += 1
                    
                    print("Curve {}: {} samples, fill={}, opacity={}".format(
                        i, sample_count, fill, fill_opacity
                    ))
                
                except Exception as e:
                    print("Warning: Error processing curve {}: {}".format(i, e))
                    stats['failed'] += 1
            
            # Combine all elements
            svg_code = "".join(svg_elements)
            
            # Generate summary
            summary_parts = []
            summary_parts.append("Generated {} of {} curves".format(stats['successful'], stats['processed']))
            if stats['failed'] > 0:
                summary_parts.append("{} failed".format(stats['failed']))
            summary_parts.append("({} chars)".format(len(svg_code)))
            print(", ".join(summary_parts))
            
            # Warnings if needed
            if stats['successful'] == 0 and stats['processed'] > 0:
                ghenv.Component.AddRuntimeMessage(RML.Warning, "No valid SVG paths created (see 'out' for details).")
            elif stats['failed'] > 0:
                ghenv.Component.AddRuntimeMessage(RML.Warning, "Some curves failed (see 'out' for details).")

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
