"""Polygon to SVG - Polyline to SVG Converter

This component converts Grasshopper polyline/polygon geometries to SVG polyline
or polygon elements. Handles coordinate transformation from Rhino (Y-up) to SVG
(Y-down) coordinate systems. Supports per-polyline styling including stroke,
fill, width, dash patterns, and transparency for Adobe Illustrator compatibility.

Typical usage:
    Polylines -> Stroke/Fill/Width/Dash Styling -> Canvas -> SVG Code

Args (Component Inputs):
    p: (Polyline/List[Polyline]) Polyline geometry/geometries
        - Type: Rhino.Geometry.Polyline/PolylineCurve or list
        - Access: item or list
        - Optional: Yes (empty returns empty string)
        - Note: Closed polylines create polygons, open create polylines
    
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
        - Optional: Yes (uses bounding box of polylines if not provided)
    
    dash: (String/List[String]) Dash pattern(s)
        - Type: str or list[str]
        - Access: item or list
        - Optional: Yes (defaults to "" - solid line)
        - Format: SVG dash pattern (e.g., "5,5" or "10,5,2,5")

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    svg_code: (String) SVG polyline/polygon elements
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

ghenv.Component.Name = "Polygon to SVG"
ghenv.Component.NickName = "polygonSVG.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '04.Dataviz'
ghenv.Component.Description = "Converts Grasshopper polygons into SVG using a canvas border if provided."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "p"
ghenv.Component.Params.Input[0].NickName = "p"
ghenv.Component.Params.Input[0].Description = "One or more Grasshopper polyline geometries."

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

ghenv.Component.Params.Input[5].Name = "dash"
ghenv.Component.Params.Input[5].NickName = "dash"
ghenv.Component.Params.Input[5].Description = "Optional dash pattern for the stroke (e.g., '5,5'). Can be a list or a constant."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "svg_code"
ghenv.Component.Params.Output[1].NickName = "svg_code"
ghenv.Component.Params.Output[1].Description = "The generated SVG code."


################
# INPUT HANDLING & VALIDATION
################
p = globals().get('p', None)
sc = globals().get('sc', None)
sw = globals().get('sw', None)
f = globals().get('f', None)
canvas = globals().get('canvas', None)
dash = globals().get('dash', None)


################
# EXECUTION
################
svg_code = ""

try:
    # Normalize input to list
    polylines = svg.normalize_input_list(p)
    
    if not polylines:
        print("No polylines provided")
    else:
        print("Processing {} polyline(s)...".format(len(polylines)))
        
        # Get canvas dimensions
        anchor_pt, w, h = svg.get_canvas_dimensions(canvas, polylines)
        
        if w == 0 or h == 0:
            print("Warning: Canvas has zero dimensions")
            ghenv.Component.AddRuntimeMessage(RML.Warning, "Canvas has zero dimensions")
        else:
            print("Canvas: {}x{} at ({:.2f}, {:.2f})".format(w, h, anchor_pt.X, anchor_pt.Y))
            
            # Statistics tracking
            stats = {'processed': 0, 'successful': 0, 'failed': 0}
            svg_elements = []
            
            # Generate SVG elements for each polyline
            for i, poly in enumerate(polylines):
                stats['processed'] += 1
                
                try:
                    # Extract points (includes coordinate transformation)
                    points = svg.extract_polyline_points(poly, anchor_pt, h)
                    
                    if not points or len(points) < 2:
                        print("Warning: Polyline {} has insufficient points".format(i))
                        stats['failed'] += 1
                        continue
                    
                    # Get styling values for this polyline
                    stroke_raw = svg.get_indexed_value(sc, i, "none")
                    fill_raw = svg.get_indexed_value(f, i, "none")
                    stroke_width = svg.get_indexed_value(sw, i, 0)
                    dash_pattern = svg.get_indexed_value(dash, i, "")
                    
                    # Convert colors to SVG format (handles Color objects)
                    stroke, stroke_opacity = svg.convert_color_to_svg(stroke_raw)
                    fill, fill_opacity = svg.convert_color_to_svg(fill_raw)
                    
                    # Generate SVG polyline/polygon element
                    element = svg.svg_polyline(
                        points,
                        stroke=stroke,
                        fill=fill,
                        stroke_width=stroke_width,
                        dash=dash_pattern,
                        fill_opacity=fill_opacity,
                        stroke_opacity=stroke_opacity
                    )
                    svg_elements.append(element)
                    stats['successful'] += 1
                    
                    print("Polyline {}: {} points, fill={}, opacity={}, dash={}".format(
                        i, len(points), fill, fill_opacity, dash_pattern if dash_pattern else "none"
                    ))
                
                except Exception as e:
                    print("Warning: Error processing polyline {}: {}".format(i, e))
                    stats['failed'] += 1
            
            # Combine all elements
            svg_code = "".join(svg_elements)
            
            # Generate summary
            summary_parts = []
            summary_parts.append("Generated {} of {} polylines".format(stats['successful'], stats['processed']))
            if stats['failed'] > 0:
                summary_parts.append("{} failed".format(stats['failed']))
            summary_parts.append("({} chars)".format(len(svg_code)))
            print(", ".join(summary_parts))
            
            # Warnings if needed
            if stats['successful'] == 0 and stats['processed'] > 0:
                ghenv.Component.AddRuntimeMessage(RML.Warning, "No valid SVG polylines created (see 'out' for details).")
            elif stats['failed'] > 0:
                ghenv.Component.AddRuntimeMessage(RML.Warning, "Some polylines failed (see 'out' for details).")

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
