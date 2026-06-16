"""WKT to Grasshopper Geometry - Well-Known Text to Geometry Converter

This component converts Well-Known Text (WKT) format from PostGIS databases
to Grasshopper geometry. Handles single geometries and MULTI* variants with
proper branch organization in DataTrees.

Typical usage:
    WKT String(s) from Database -> Grasshopper Geometry for Visualization

Logic:
    1. Validate input WKT string(s)
    2. Parse WKT using carcara_geometry module
    3. Detect if geometry is real multipart (multiple items) or forced MULTI*
    4. Real multipart: Place all parts in same branch
    5. Single/forced multipart: Place in separate branches
    6. Return organized DataTree of Grasshopper geometry
    7. Handle conversion errors gracefully with empty branches

Args (Component Inputs):
    WKT_geom: (List[String]) List of WKT strings to convert
        - Type: list[str]
        - Access: list
        - Optional: Yes (empty input returns empty DataTree)
        - Format: Standard WKT (POINT, LINESTRING, POLYGON, MULTI*)

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    geom: (DataTree[Geometry]) Converted Grasshopper geometry
        - Type: DataTree[Rhino.Geometry]
        - Structure: Real multiparts in single branch, singles in separate branches
        - Note: Failed conversions result in empty branches

Version: 1.3
Date: 2025/11/13
Requires: carcara_geometry module with construct_gh_geom
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Grasshopper
from ghpythonlib import treehelpers
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_geometry
from carcara_geometry import construct_gh_geom
importlib.reload(carcara_geometry)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "1.3"
COMPONENT_DATE = "2025/11/13"

ghenv.Component.Name = "WKT to Grasshopper Geometry"
ghenv.Component.NickName = "wktToGH.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '03.Utilities'
ghenv.Component.Description = "Converts Well-Known Text format to Grasshopper geometry with proper multipart handling."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "WKT_geom"
ghenv.Component.Params.Input[0].NickName = "WKT_geom"
ghenv.Component.Params.Input[0].Description = "List of WKT strings to convert to Grasshopper geometry."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "geom"
ghenv.Component.Params.Output[1].NickName = "geom"
ghenv.Component.Params.Output[1].Description = "Converted Grasshopper geometry as DataTree."


################
# HELPER FUNCTIONS
################
def log(message):
    """
    Print message to default 'out' output.
    
    Args:
        message (str): Message text to log
    """
    print(message)


def report(level, message):
    """
    Send runtime message to Grasshopper component (warnings/errors only).
    
    Args:
        level (GH_RuntimeMessageLevel): Message severity level
        message (str): Message text to display
    """
    ghenv.Component.AddRuntimeMessage(level, message)
    log(message)


def is_real_multipart(geom_result):
    """
    Determine if result represents real multipart geometry.
    
    Real multipart: Multiple actual geometries (list with >1 items)
    Forced multipart: Single geometry wrapped in MULTI* (list with 1 item or single object)
    
    Args:
        geom_result: Result from construct_gh_geom function
    
    Returns:
        bool: True if real multipart (multiple items), False otherwise
    """
    if isinstance(geom_result, list):
        return len(geom_result) > 1
    return False


def validate_wkt_string(wkt_str):
    """
    Basic validation of WKT string format.
    
    Args:
        wkt_str (str): WKT string to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not wkt_str or not isinstance(wkt_str, str):
        return False, "Invalid WKT: must be non-empty string"
    
    wkt_upper = wkt_str.strip().upper()
    valid_prefixes = [
        "POINT", "MULTIPOINT",
        "LINESTRING", "MULTILINESTRING",
        "POLYGON", "MULTIPOLYGON",
        "GEOMETRYCOLLECTION"
    ]
    
    if not any(wkt_upper.startswith(prefix) for prefix in valid_prefixes):
        return False, "Invalid WKT: unrecognized geometry type"
    
    if '(' not in wkt_str:
        return False, "Invalid WKT: missing coordinate data"
    
    return True, None


def convert_wkt_to_geometry(wkt_str):
    """
    Convert single WKT string to Grasshopper geometry.
    
    Args:
        wkt_str (str): WKT string to convert
    
    Returns:
        tuple: (geometry_list, error_message)
            geometry_list: List of geometries or single geometry
            error_message: Error string or None if successful
    """
    is_valid, error_msg = validate_wkt_string(wkt_str)
    if not is_valid:
        return None, error_msg
    
    try:
        geom_converted = construct_gh_geom(wkt_str)
        return geom_converted, None
    except ValueError as e:
        return None, "Value error: {}".format(e)
    except Exception as e:
        return None, "Conversion error: {}".format(e)


def organize_geometry_branch(geom_converted):
    """
    Organize converted geometry into appropriate branch structure.
    
    Args:
        geom_converted: Result from construct_gh_geom
    
    Returns:
        list: Properly organized geometry list for branch
    """
    if is_real_multipart(geom_converted):
        return geom_converted
    else:
        if isinstance(geom_converted, list):
            if len(geom_converted) == 1:
                return [geom_converted[0]]
            else:
                return []
        else:
            return [geom_converted]


################
# INPUT HANDLING & VALIDATION
################
WKT_geom = globals().get('WKT_geom', [])

if not isinstance(WKT_geom, (list, tuple)):
    if WKT_geom:
        WKT_geom = [WKT_geom]
    else:
        WKT_geom = []


################
# EXECUTION
################
geom = None

try:
    if not WKT_geom:
        log("No WKT strings provided")
        geom = treehelpers.list_to_tree([], source=[0])
    else:
        log("Processing {} WKT string(s)...".format(len(WKT_geom)))
        
        gh_geometries_tree = []
        successful_conversions = 0
        failed_conversions = 0
        real_multipart_count = 0
        
        for idx, wkt_str in enumerate(WKT_geom):
            log("WKT[{}]: {}".format(idx, wkt_str[:80] + "..." if len(wkt_str) > 80 else wkt_str))
            
            geom_converted, error_msg = convert_wkt_to_geometry(wkt_str)
            
            if error_msg:
                log("  Error: {}".format(error_msg))
                gh_geometries_tree.append([])
                failed_conversions += 1
            else:
                branch_geoms = organize_geometry_branch(geom_converted)
                gh_geometries_tree.append(branch_geoms)
                successful_conversions += 1
                
                if is_real_multipart(geom_converted):
                    log("  Converted: {} parts (real multipart)".format(len(branch_geoms)))
                    real_multipart_count += 1
                else:
                    log("  Converted: 1 geometry")
        
        geom = treehelpers.list_to_tree(gh_geometries_tree, source=[0])
        
        log("Conversion complete:")
        log("  Successful: {}".format(successful_conversions))
        log("  Failed: {}".format(failed_conversions))
        log("  Real multiparts: {}".format(real_multipart_count))
        
        if failed_conversions > 0:
            report(
                RML.Warning,
                "{} of {} conversions failed (see 'out' for details).".format(
                    failed_conversions,
                    len(WKT_geom)
                )
            )

except ImportError as e:
    report(
        RML.Error,
        "Module import error - see 'out' for details."
    )
    log("Module import error: {}. Ensure carcara_geometry is in the modules folder.".format(e))
    geom = treehelpers.list_to_tree([], source=[0])
except AttributeError as e:
    report(
        RML.Error,
        "Module function error - see 'out' for details."
    )
    log("Module function error: {}. Check carcara_geometry module version.".format(e))
    geom = treehelpers.list_to_tree([], source=[0])
except Exception as e:
    report(
        RML.Error,
        "Unexpected error - see 'out' for details."
    )
    log("Unexpected error: {} (Type: {}).".format(e, type(e).__name__))
    geom = treehelpers.list_to_tree([], source=[0])
