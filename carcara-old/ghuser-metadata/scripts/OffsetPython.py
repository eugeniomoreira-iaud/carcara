"""Offset Python - Planar Curve Offset Component

This component offsets planar polylines using specified distances and corner
styles. Supports DataTree structures with flexible distance and style mapping.
Handles non-planar curves with appropriate warnings.

Typical usage:
    Planar Curves -> Offset Distances -> Corner Style -> Offset Curves

Logic:
    1. Validate input curves, distances, and corner style
    2. Process each branch in DataTree structure
    3. Match distances to curves (single, multiple, or cyclic mapping)
    4. Test curve planarity before offsetting
    5. Apply offset operation with specified corner style
    6. Return offset curves preserving tree structure
    7. Handle errors gracefully with None placeholders

Args (Component Inputs):
    Crv: (DataTree[Curve]) Planar polylines to offset
        - Type: DataTree[Rhino.Geometry.Curve]
        - Access: tree
        - Optional: No
        - Note: Non-planar curves produce warnings and None output
    
    Dist: (DataTree[Float]) Offset distances for curves
        - Type: DataTree[float]
        - Access: tree
        - Optional: No
        - Mapping: Single value applies to all, list matches curves
    
    CStyle: (Integer) Corner style for offset operation
        - Type: int
        - Access: item
        - Optional: Yes (defaults to 1 - Sharp)
        - Values: 0=None, 1=Sharp, 2=Round, 3=Smooth, 4=Chamfer

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    OffCrv: (DataTree[Curve]) Offset curves
        - Type: DataTree[Rhino.Geometry.Curve]
        - Structure: Preserves input tree structure
        - Note: Failed offsets return None

Version: 3.2
Date: 2025/11/13
"""

################
# IMPORTS
################
import Rhino
import Rhino.Geometry as rg
import Grasshopper as gh
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "3.2"
COMPONENT_DATE = "2025/11/13"
DEFAULT_TOLERANCE = 1e-6

ghenv.Component.Name = "Offset Python"
ghenv.Component.NickName = "offset.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '01.Modeling'
ghenv.Component.Description = "Offsets planar polylines using given distances and a corner style mapping."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "Crv"
ghenv.Component.Params.Input[0].NickName = "Crv"
ghenv.Component.Params.Input[0].Description = "Planar polylines to offset."

ghenv.Component.Params.Input[1].Name = "Dist"
ghenv.Component.Params.Input[1].NickName = "Dist"
ghenv.Component.Params.Input[1].Description = "Offset distances for the curves."

ghenv.Component.Params.Input[2].Name = "CStyle"
ghenv.Component.Params.Input[2].NickName = "CStyle"
ghenv.Component.Params.Input[2].Description = "Corner style mapping: 0=None, 1=Sharp, 2=Round, 3=Smooth, 4=Chamfer."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "OffCrv"
ghenv.Component.Params.Output[1].NickName = "OffCrv"
ghenv.Component.Params.Output[1].Description = "Offset curves."


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


def get_branch(tree, path):
    """
    Retrieve branch data with fallback behavior.
    
    If branch exists for this path, use it. If tree has exactly
    one branch, use that regardless of path. Otherwise return empty list.
    
    Args:
        tree (DataTree): Input DataTree
        path (GH_Path): Path to retrieve
    
    Returns:
        list: Branch data or empty list
    """
    if tree.Paths.Contains(path):
        return list(tree[path])
    elif tree.Paths.Count == 1:
        return list(tree[tree.Paths[0]])
    return []


def get_corner_style_enum(style_value):
    """
    Map corner style integer to RhinoCommon enum.
    
    Args:
        style_value (int): Integer representing corner style
    
    Returns:
        CurveOffsetCornerStyle: RhinoCommon enum value
    """
    style_map = {
        0: rg.CurveOffsetCornerStyle(0),
        1: rg.CurveOffsetCornerStyle.Sharp,
        2: rg.CurveOffsetCornerStyle.Round,
        3: rg.CurveOffsetCornerStyle.Smooth,
        4: rg.CurveOffsetCornerStyle.Chamfer
    }
    return style_map.get(style_value, rg.CurveOffsetCornerStyle.Sharp)


def unwrap_gh_value(value):
    """
    Unwrap Grasshopper wrapper objects to get actual values.
    
    Args:
        value: Potentially wrapped Grasshopper value
    
    Returns:
        Unwrapped value
    """
    return value.Value if hasattr(value, "Value") else value


def validate_and_map_distances(branch_curves, branch_distances, path):
    """
    Validate and map distance values to curves.
    
    Handles single value, matching lists, and cyclic mapping.
    
    Args:
        branch_curves (list): List of curves in branch
        branch_distances (list): List of distance values
        path (GH_Path): Current branch path for error reporting
    
    Returns:
        list: Mapped distance values (one per curve)
    """
    if len(branch_distances) == 0:
        return [0.0] * len(branch_curves)
    elif len(branch_distances) == 1:
        return branch_distances * len(branch_curves)
    elif len(branch_distances) != len(branch_curves):
        log(
            "Branch {}: Distance count ({}) != curve count ({}). Using modulo mapping.".format(
                path,
                len(branch_distances),
                len(branch_curves)
            )
        )
        return [branch_distances[i % len(branch_distances)] for i in range(len(branch_curves))]
    else:
        return branch_distances


def offset_curve(curve, distance, corner_style, tolerance):
    """
    Offset single curve with validation.
    
    Args:
        curve (Curve): Curve to offset
        distance (float): Offset distance
        corner_style (CurveOffsetCornerStyle): Corner style enum
        tolerance (float): Geometric tolerance
    
    Returns:
        tuple: (offset_curve, error_message)
            offset_curve: Offset curve or None if failed
            error_message: Error string or None if successful
    """
    if curve is None:
        return None, "Input curve is None"
    
    try:
        result, plane = curve.TryGetPlane(tolerance)
        if not result:
            return None, "Curve is non-planar"
        
        offsets = curve.Offset(plane, distance, tolerance, corner_style)
        if offsets and len(offsets) > 0:
            return offsets[0], None
        else:
            return None, "Offset operation returned no results"
            
    except Exception as e:
        return None, "Offset error: {}".format(e)


################
# INPUT HANDLING & VALIDATION
################
Crv = globals().get('Crv', [])
Dist = globals().get('Dist', [])
CStyle = globals().get('CStyle', 1)

curves_tree = ghenv.Component.Params.Input[0].VolatileData
dist_tree = ghenv.Component.Params.Input[1].VolatileData
cstyle_tree = ghenv.Component.Params.Input[2].VolatileData


################
# EXECUTION
################
offCrv_tree = DataTree[rg.Curve]()

try:
    cs_values = get_branch(cstyle_tree, curves_tree.Paths[0]) if cstyle_tree.Paths.Count > 0 else []
    if len(cs_values) > 0:
        corner_style_value = unwrap_gh_value(cs_values[0])
    else:
        corner_style_value = 1
    
    corner_style_enum = get_corner_style_enum(corner_style_value)
    log("Using corner style: {}".format(corner_style_value))
    
    if curves_tree.Paths.Count == 0:
        report(RML.Warning, "No curves provided.")
    else:
        total_curves = 0
        successful_offsets = 0
        failed_offsets = 0
        
        log("Processing {} branch(es)...".format(curves_tree.Paths.Count))
        
        for path in curves_tree.Paths:
            branch_curves = curves_tree[path]
            branch_distances = get_branch(dist_tree, path)
            
            mapped_distances = validate_and_map_distances(
                branch_curves,
                branch_distances,
                path
            )
            
            for i, c in enumerate(branch_curves):
                total_curves += 1
                curve = unwrap_gh_value(c)
                distance = unwrap_gh_value(mapped_distances[i]) if i < len(mapped_distances) else 0.0
                
                offset_result, error_msg = offset_curve(
                    curve,
                    distance,
                    corner_style_enum,
                    DEFAULT_TOLERANCE
                )
                
                if offset_result is not None:
                    offCrv_tree.Add(offset_result, path)
                    successful_offsets += 1
                else:
                    offCrv_tree.Add(None, path)
                    failed_offsets += 1
                    if error_msg:
                        log("Branch {} index {}: {}".format(path, i, error_msg))
        
        log("Successfully offset {} of {} curve(s).".format(successful_offsets, total_curves))
        
        if failed_offsets > 0:
            report(
                RML.Warning,
                "{} curve(s) failed to offset (see 'out' for details).".format(failed_offsets)
            )

except IndexError as e:
    report(
        RML.Error,
        "Index error: {} - see 'out' for details.".format(e)
    )
except AttributeError as e:
    report(
        RML.Error,
        "Attribute error: {} - see 'out' for details.".format(e)
    )
except Exception as e:
    report(
        RML.Error,
        "Unexpected error: {} (Type: {}) - see 'out' for details.".format(
            e,
            type(e).__name__
        )
    )


################
# OUTPUTS (index 0 is default 'out', custom outputs start at 1)
################
OffCrv = offCrv_tree
