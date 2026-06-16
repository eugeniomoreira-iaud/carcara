"""Save SVG - SVG File Export Component

This component exports SVG code to a file using canvas dimensions for proper
sizing. Combines SVG elements, sets viewBox, and saves to specified path.
Supports both absolute and relative file paths.

Typical usage:
    SVG Code -> Canvas Rectangle -> File Path -> Save Flag -> Status Message

Args (Component Inputs):
    svg_code: (String/List[String]) SVG element code
    canvas: (Rectangle) Rectangle geometry defining SVG canvas
    file_path: (String) File path for saving SVG
    save_flag: (Boolean) Activate file saving

Returns (Component Outputs):
    out: (str) Processing log
    status_msg: (String) Status message indicating save result
    svg_doc: (String) Complete SVG document for debugging

Version: 3.1
Date: 2025/11/20
Requires: carcara_dataviz v2.0+ module
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Grasshopper
import Rhino
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_dataviz as svg
importlib.reload(svg)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "3.1"
COMPONENT_DATE = "2025/11/20"
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
DEFAULT_FILENAME = "output.svg"

ghenv.Component.Name = "Save SVG"
ghenv.Component.NickName = "saveSVG.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '04.Export'
ghenv.Component.Description = "Save SVG using canvas border to define canvas dimensions."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "svg_code"
ghenv.Component.Params.Input[0].NickName = "svg_code"
ghenv.Component.Params.Input[0].Description = "SVG element code (already offset so that top-left is origin)."

ghenv.Component.Params.Input[1].Name = "canvas"
ghenv.Component.Params.Input[1].NickName = "canvas"
ghenv.Component.Params.Input[1].Description = "A rectangle geometry defining the SVG canvas. If not provided, a default size is used."

ghenv.Component.Params.Input[2].Name = "file_path"
ghenv.Component.Params.Input[2].NickName = "file_path"
ghenv.Component.Params.Input[2].Description = "Relative or absolute file path for saving the SVG file. Remember to include the name.svg at the end."

ghenv.Component.Params.Input[3].Name = "save_flag"
ghenv.Component.Params.Input[3].NickName = "save_flag"
ghenv.Component.Params.Input[3].Description = "Boolean: True to save the file."


################
# OUTPUT METADATA
################
ghenv.Component.Params.Output[1].Name = "status_msg"
ghenv.Component.Params.Output[1].NickName = "status_msg"
ghenv.Component.Params.Output[1].Description = "Status message indicating file save status."

ghenv.Component.Params.Output[2].Name = "svg_doc"
ghenv.Component.Params.Output[2].NickName = "svg_doc"
ghenv.Component.Params.Output[2].Description = "Complete SVG document for debugging and inspection."


################
# HELPER FUNCTIONS
################
def combine_svg_code(svg_code):
    """Combine SVG code from list or single string."""
    if isinstance(svg_code, list):
        return "".join(svg_code)
    return svg_code if svg_code else ""


def get_base_folder():
    """Get base folder from Grasshopper document path."""
    doc_path = getattr(ghdoc, "FilePath", None) or getattr(ghdoc, "Path", None)
    if doc_path and doc_path.strip() != "":
        base = os.path.dirname(doc_path)
        print("Base folder from document: {}".format(base))
        return base
    else:
        base = os.getcwd()
        print("Using current working directory: {}".format(base))
        return base


def resolve_file_path(file_path, base_folder):
    """Resolve file path to absolute path."""
    if not file_path or file_path.strip() == "":
        file_path = DEFAULT_FILENAME
        print("No file path provided, using default: {}".format(DEFAULT_FILENAME))
    
    if not os.path.isabs(file_path):
        file_path = os.path.join(base_folder, file_path)
        print("Resolved relative path to: {}".format(file_path))
    else:
        print("Using absolute path: {}".format(file_path))
    
    return file_path


################
# INPUT HANDLING & VALIDATION
################
svg_code = globals().get('svg_code', None)
canvas = globals().get('canvas', None)
file_path = globals().get('file_path', "")
save_flag = globals().get('save_flag', False)

if not isinstance(save_flag, bool):
    print("Warning: save_flag must be boolean, using False")
    save_flag = False


################
# EXECUTION
################
status_msg = ""
svg_doc = ""

try:
    # Validate SVG code
    if svg_code is None:
        print("Error: No SVG code provided")
        status_msg = "Error: No SVG code provided"
    else:
        combined_svg_body = combine_svg_code(svg_code)
        
        if not combined_svg_body or combined_svg_body.strip() == "":
            print("Error: SVG code is empty")
            status_msg = "Error: SVG code is empty"
        else:
            print("Validating SVG code...")
            print("SVG code length: {} characters".format(len(combined_svg_body)))
            print("SVG elements preview: {}...".format(combined_svg_body[:200]))
            
            # Get canvas dimensions
            if canvas is not None:
                try:
                    anchor_pt, w, h = svg.canvas_origin_info(canvas)
                    print("Canvas dimensions: {}x{}".format(w, h))
                    print("Canvas anchor: ({:.2f}, {:.2f})".format(anchor_pt.X, anchor_pt.Y))
                except Exception as e:
                    print("Warning: Error extracting canvas ({})".format(e))
                    w, h = DEFAULT_WIDTH, DEFAULT_HEIGHT
                    print("Using default: {}x{}".format(w, h))
            else:
                w, h = DEFAULT_WIDTH, DEFAULT_HEIGHT
                print("Using default: {}x{}".format(w, h))
            
            # Build SVG document
            viewBox = "0 0 {} {}".format(w, h)
            print("ViewBox: {}".format(viewBox))
            
            svg_document = svg.combine_svg(
                [combined_svg_body],
                width="{}px".format(w),
                height="{}px".format(h),
                viewBox=viewBox
            )
            
            # Store for debugging output (svg_doc output only)
            svg_doc = svg_document
            print("SVG document generated: {} characters".format(len(svg_doc)))
            
            # Resolve file path
            base_folder = get_base_folder()
            resolved_path = resolve_file_path(file_path, base_folder)
            
            # Save if flag is active
            if not save_flag:
                status_msg = "Ready to save ({}x{} canvas). Activate save_flag to write file.".format(w, h)
                print(status_msg)
                print("Target path: {}".format(resolved_path))
            else:
                print("Saving file...")
                try:
                    svg.save_svg(svg_document, resolved_path)
                    file_size = len(svg_document)
                    status_msg = "SVG saved successfully: {} ({} chars, {}x{})".format(
                        os.path.basename(resolved_path), 
                        file_size, 
                        w, 
                        h
                    )
                    print(status_msg)
                    print("Full path: {}".format(resolved_path))
                except IOError as e:
                    status_msg = "Error saving file: {}".format(str(e))
                    print(status_msg)
                    ghenv.Component.AddRuntimeMessage(RML.Error, "Error saving file - see 'out'")
                except OSError as e:
                    status_msg = "Error creating directory: {}".format(str(e))
                    print(status_msg)
                    ghenv.Component.AddRuntimeMessage(RML.Error, "Error creating directory - see 'out'")

except ImportError as e:
    status_msg = "Module import error - check 'out' for details"
    ghenv.Component.AddRuntimeMessage(RML.Error, status_msg)
    print("Import error: {}. Ensure carcara_dataviz v2.0+ in modules folder.".format(e))
except AttributeError as e:
    status_msg = "Module function error - check 'out' for details"
    ghenv.Component.AddRuntimeMessage(RML.Error, status_msg)
    print("Function error: {}. Check carcara_dataviz version (need v2.0+).".format(e))
except Exception as e:
    status_msg = "Unexpected error: {}".format(str(e))
    ghenv.Component.AddRuntimeMessage(RML.Error, "Unexpected error - see 'out'")
    print("Error: {} (Type: {})".format(e, type(e).__name__))
