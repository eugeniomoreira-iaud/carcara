"""Grasshopper Geometry to WKT - Geometry to Well-Known Text Converter

This component converts Grasshopper geometry to Well-Known Text (WKT) format
for storage in PostGIS databases. Accepts points, lines/polylines, and polygons.
Enforces uniform type across all branches and outputs single or MULTI variants.

Typical usage:
    Grasshopper Geometry -> WKT String for Database Storage

Logic:
    1. Validate input geometry and check for uniform types
    2. Resolve GUID references to actual geometry objects
    3. Determine if geometry is point, linestring, or polygon
    4. Convert single items to standard WKT, multiple items to MULTI* WKT
    5. Handle DataTree structures preserving branch organization
    6. Return WKT string(s) matching input structure

Args (Component Inputs):
    geom: (Geometry/DataTree) Geometry to convert to WKT
        - Type: Rhino.Geometry or DataTree[Rhino.Geometry]
        - Access: item/list/tree
        - Optional: Yes (empty input returns None)
        - Supported: Points, Lines, Polylines, Polygons
        - Note: All geometries must be of uniform type

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    WKT: (String/DataTree) Well-Known Text representation
        - Type: str or DataTree[str]
        - Format: WKT standard (POINT, LINESTRING, POLYGON, MULTI*)
        - Structure: Mirrors input structure for DataTrees

Version: 1.3
Date: 2025/11/13
Requires: carcara_geometry module with gh_polygon_to_wkt, gh_multipolygon_to_wkt
"""

################
# IMPORTS
################
import sys
import os
import importlib
import scriptcontext as sc
import Grasshopper
from ghpythonlib import treehelpers
import Rhino.Geometry as rg
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_geometry
from carcara_geometry import construct_wkt
importlib.reload(carcara_geometry)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "1.3"
COMPONENT_DATE = "2025/11/13"

ghenv.Component.Name = "Grasshopper Geometry to WKT"
ghenv.Component.NickName = "GhToWkt.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '03.Utilities'
ghenv.Component.Description = "Converts Grasshopper geometry to WKT. Accepts only points, lines/polylines, and polygons. Enforces uniform type across all branches and outputs single or MULTI variants accordingly."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "geom"
ghenv.Component.Params.Input[0].NickName = "geom"
ghenv.Component.Params.Input[0].Description = "Geometry or DataTree of geometries to convert."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "WKT"
ghenv.Component.Params.Output[1].NickName = "WKT"
ghenv.Component.Params.Output[1].Description = "Geometry in Well-Known Text format."


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


def resolve_geometry(obj):
    """
    Convert GUID references to actual geometry objects.
    
    Args:
        obj: Geometry object or GUID reference
    
    Returns:
        Rhino.Geometry object or None if resolution fails
    """
    try:
        if str(type(obj)).endswith("System.Guid'>"):
            rh_obj = sc.doc.Objects.Find(obj)
            return rh_obj.Geometry if rh_obj else None
        return obj
    except Exception:
        return None


def is_wkt_multipart(wkt_str):
    """
    Detect if WKT is already MULTI* or GEOMETRYCOLLECTION.
    
    Args:
        wkt_str (str): WKT string to check
    
    Returns:
        bool: True if multipart, False otherwise
    """
    if not isinstance(wkt_str, str):
        return False
    s = wkt_str.strip().upper()
    return s.startswith("MULTI") or s.startswith("GEOMETRYCOLLECTION")


def to_multipart_wkt(wkt_str):
    """
    Convert single-part WKT to MULTI* form.
    
    Adds MULTI prefix and wraps coordinates in extra parentheses.
    
    Args:
        wkt_str (str): Single-part WKT string
    
    Returns:
        str: MULTI* WKT string
    """
    if not isinstance(wkt_str, str):
        return wkt_str
    src = wkt_str.strip()
    if not src:
        return src
    
    up = src.upper()
    if up.startswith("MULTI") or up.startswith("GEOMETRYCOLLECTION"):
        return src
    
    try:
        i = src.index('(')
    except ValueError:
        return src
    
    geom_type = src[:i].strip().upper()
    coords = src[i:].strip()
    
    if not (coords.startswith('(') and coords.endswith(')')):
        return src
    
    type_map = {
        "POINT": "MULTIPOINT",
        "LINESTRING": "MULTILINESTRING",
        "POLYGON": "MULTIPOLYGON",
    }
    
    if geom_type not in type_map:
        return src
    
    multi_type = type_map[geom_type]
    new_coords = "(" + coords + ")"
    return "{} {}".format(multi_type, new_coords)


def get_geometry_type(geom):
    """
    Determine simplified geometry type for allowed types.
    
    Args:
        geom: Grasshopper geometry object
    
    Returns:
        str: 'point', 'linestring', 'polygon', or None if unsupported
    """
    rh_geom = resolve_geometry(geom)
    if rh_geom is None:
        return None
    
    if isinstance(rh_geom, rg.Point3d):
        return "point"
    if hasattr(rh_geom, "Location") and isinstance(rh_geom.Location, rg.Point3d):
        return "point"
    
    if isinstance(rh_geom, rg.LineCurve):
        return "linestring"
    if isinstance(rh_geom, rg.NurbsCurve):
        return "linestring"
    
    if isinstance(rh_geom, rg.Curve):
        try:
            if rh_geom.IsLinear():
                return "linestring"
        except Exception:
            pass
    
    if isinstance(rh_geom, rg.Polyline):
        if len(rh_geom) >= 3 and rh_geom.IsClosed:
            return "polygon"
        else:
            return "linestring"
    if isinstance(rh_geom, rg.PolylineCurve):
        if rh_geom.IsClosed:
            return "polygon"
        else:
            return "linestring"
    
    if isinstance(rh_geom, rg.Line):
        return "linestring"
    
    return None


def uniform_types_in_branches(geom):
    """
    Check if all branches have uniform geometry type.
    
    Args:
        geom: DataTree of geometries
    
    Returns:
        tuple: (is_uniform: bool, geometry_type: str or None)
    """
    if not hasattr(geom, 'BranchCount'):
        t = get_geometry_type(geom) if geom else None
        return (True if t else False, t)
    
    branch_types = set()
    for i in range(geom.BranchCount):
        branch = geom.Branch(i)
        if not branch or len(branch) == 0:
            continue
        
        first_type = None
        for g in branch:
            t = get_geometry_type(g)
            if t is None:
                return (False, None)
            first_type = t
            break
        
        if first_type is None:
            continue
        
        for g in branch:
            if get_geometry_type(g) != first_type:
                return (False, None)
        
        branch_types.add(first_type)
    
    if len(branch_types) == 1:
        return (True, branch_types.pop())
    else:
        return (False, None)


def convert_branch_clean(branch_geoms, force_multipart=False):
    """
    Convert branch of geometries to WKT with type filtering.
    
    Args:
        branch_geoms (list): List of geometry objects
        force_multipart (bool): Force MULTI* output even for single items
    
    Returns:
        str: WKT string or error message
    """
    resolved = []
    for g in branch_geoms:
        rgm = resolve_geometry(g)
        if rgm is not None:
            t = get_geometry_type(rgm)
            if t is None:
                return None
            resolved.append(rgm)
    
    if not resolved:
        return "No valid geometries found"
    
    first_type = get_geometry_type(resolved[0])
    for rgm in resolved:
        current_type = get_geometry_type(rgm)
        if current_type != first_type:
            return None
    
    try:
        if first_type == "polygon":
            if len(resolved) == 1 and not force_multipart:
                wkt = carcara_geometry.gh_polygon_to_wkt(resolved[0])
            else:
                wkt = carcara_geometry.gh_multipolygon_to_wkt(resolved)
            return wkt
        
        if len(resolved) == 1 and not force_multipart:
            return construct_wkt(resolved)
        
        wkt = construct_wkt(resolved)
        if not is_wkt_multipart(wkt):
            wkt = to_multipart_wkt(wkt)
        return wkt
    except Exception as e:
        return "Error: {}".format(e)


################
# INPUT HANDLING & VALIDATION
################
geom = globals().get('geom', [])


################
# EXECUTION
################
WKT = None

try:
    if not geom or (hasattr(geom, 'BranchCount') and geom.BranchCount == 0):
        log("No geometry provided")
    else:
        if hasattr(geom, 'BranchCount'):
            log("Processing DataTree with {} branches...".format(geom.BranchCount))
            
            is_uniform, geom_type = uniform_types_in_branches(geom)
            if not is_uniform or geom_type is None:
                report(
                    RML.Error,
                    "Geometry types not uniform or unsupported (see 'out' for details)."
                )
                log("Error: Geometry types are not uniform or contain unsupported types")
                log("Only points, lines, polygons allowed")
            else:
                log("Detected uniform geometry type: {}".format(geom_type))
                
                force_multi = False
                for i in range(geom.BranchCount):
                    if len(geom.Branch(i)) > 1:
                        force_multi = True
                        break
                
                log("Output mode: {}".format("MULTI*" if force_multi else "single"))
                
                wkt_tree_list = []
                error_occurred = False
                for i in range(geom.BranchCount):
                    branch = list(geom.Branch(i))
                    wkt_str = convert_branch_clean(branch, force_multipart=force_multi)
                    if wkt_str is None:
                        log("Error: Branch {} contains unsupported or mixed geometry types".format(i))
                        report(
                            RML.Error,
                            "Branch {} has mixed types (see 'out' for details).".format(i)
                        )
                        error_occurred = True
                        break
                    wkt_tree_list.append([wkt_str])
                    log("Branch {}: converted {} geometries".format(i, len(branch)))
                
                if not error_occurred:
                    WKT = treehelpers.list_to_tree(wkt_tree_list)
                    log("Successfully converted {} branches of type '{}'".format(
                        geom.BranchCount,
                        geom_type
                    ))
        else:
            geom_list = geom if isinstance(geom, (list, tuple)) else [geom]
            log("Processing {} geometry item(s)...".format(len(geom_list)))
            
            types = set()
            resolved = []
            error_occurred = False
            for g in geom_list:
                rgm = resolve_geometry(g)
                if rgm is None:
                    continue
                t = get_geometry_type(rgm)
                if t is None:
                    log("Error: Unsupported geometry type detected in input list")
                    report(RML.Error, "Unsupported geometry type (see 'out' for details).")
                    error_occurred = True
                    break
                types.add(t)
                resolved.append(rgm)
            
            if not error_occurred:
                if len(types) != 1:
                    log("Error: Input geometries must be of uniform type")
                    log("Detected types: {}".format(types))
                    report(
                        RML.Error,
                        "Mixed geometry types not allowed (see 'out' for details)."
                    )
                else:
                    geom_type = types.pop()
                    log("Detected uniform geometry type: {}".format(geom_type))
                    
                    force_multi = len(resolved) > 1
                    log("Output mode: {}".format("MULTI*" if force_multi else "single"))
                    
                    wkt_str = None
                    if force_multi:
                        wkt_str = construct_wkt(resolved)
                        if not is_wkt_multipart(wkt_str):
                            wkt_str = to_multipart_wkt(wkt_str)
                    elif len(resolved) == 1:
                        wkt_str = construct_wkt(resolved[0])
                    else:
                        wkt_str = "No valid geometries found"
                    WKT = wkt_str
                    log("Successfully converted {} item(s) of type '{}'".format(
                        len(resolved),
                        geom_type
                    ))
                    log("WKT preview: {}".format(wkt_str[:100] + "..." if len(wkt_str) > 100 else wkt_str))

except ImportError as e:
    report(
        RML.Error,
        "Module import error - see 'out' for details."
    )
    log("Module import error: {}. Ensure carcara_geometry is in the modules folder.".format(e))
except AttributeError as e:
    report(
        RML.Error,
        "Module function error - see 'out' for details."
    )
    log("Module function error: {}. Check carcara_geometry module version.".format(e))
except Exception as e:
    report(
        RML.Error,
        "Unexpected error - see 'out' for details."
    )
    log("Unexpected error: {} (Type: {}).".format(e, type(e).__name__))
