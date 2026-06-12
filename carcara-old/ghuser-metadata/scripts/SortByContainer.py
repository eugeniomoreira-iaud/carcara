"""Sort by Container - Point Sorting by Curve Containment

This component sorts a list of points by testing containment within planar
curves. Returns indexes organized in a DataTree where each branch represents
points contained in each curve. Useful for spatial sorting and filtering.

Typical usage:
    Container Curves -> Points -> Sorted Indexes (by container)

Logic:
    1. Validate input curves and points
    2. Get document tolerance or use fallback
    3. For each container curve, create a branch (empty or populated)
    4. Extract plane for each curve
    5. Test each point for containment using curve.Contains()
    6. Add point indexes to corresponding branch in output tree
    7. Empty curves produce empty branches for consistent structure
    8. Report statistics on sorted vs unsorted points

Important Note:
    The output always has the same number of branches as input curves,
    ensuring predictable tree structure even when curves contain no points.

Args (Component Inputs):
    crv: (List[Curve]) Planar curves to use as containers
        - Type: list[Rhino.Geometry.Curve]
        - Access: list
        - Optional: No
        - Note: Non-planar curves use WorldXY plane as fallback
    
    pt: (List[Point3d]) Points to sort by container
        - Type: list[Rhino.Geometry.Point3d]
        - Access: list
        - Optional: No
        - Tip: For polylines, use 'Point Inside Polygon' component first

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    i: (DataTree[int]) Indexes of points sorted by container
        - Type: DataTree[int]
        - Structure: Each branch corresponds to one container curve
        - Note: Empty branches for curves with no points
        - Usage: Use with 'List Item' component to reorder original lists

Version: 2.4
Date: 2025/11/13
"""

################
# IMPORTS
################
import Rhino
import Rhino.Geometry as rg
import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "2.4"
COMPONENT_DATE = "2025/11/13"
DEFAULT_TOLERANCE = 1e-6

ghenv.Component.Name = "Sort by Container"
ghenv.Component.NickName = "Srt_Ctn.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '01.Modeling'
ghenv.Component.Description = (
    "This component sorts a list of points by a list of containers. "
    "Output tree always matches curve count with empty branches for curves containing no points."
)
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "crv"
ghenv.Component.Params.Input[0].NickName = "crv"
ghenv.Component.Params.Input[0].Description = "List of planar curves to be used as containers."

ghenv.Component.Params.Input[1].Name = "pt"
ghenv.Component.Params.Input[1].NickName = "pt"
ghenv.Component.Params.Input[1].Description = (
    "List of points to order by the containers. "
    "If your objects are not points, create a set of ones to associate with.\n\n"
    "TIP: if you have a set of polylines, you should use the 'Point Inside Polygon' component."
)


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "i"
ghenv.Component.Params.Output[1].NickName = "i"
ghenv.Component.Params.Output[1].Description = (
    "Indexes of the list of points sorted by the containers. "
    "Each branch corresponds to one curve (empty if no points contained). "
    "Use with 'List Item' component to sort original lists."
)


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


def ensure_branch_exists(tree, path):
    """
    Ensure a branch exists in the tree, creating an empty branch if needed.
    
    Args:
        tree (DataTree): Tree to modify
        path (GH_Path): Path to ensure exists
    """
    if not tree.PathExists(path):
        tree.EnsurePath(path)


def get_document_tolerance():
    """
    Get Rhino document tolerance with fallback.
    
    Returns:
        float: Document tolerance or default if unavailable
    """
    try:
        tol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
        if tol <= 0:
            log("Document tolerance is invalid, using default: {}".format(DEFAULT_TOLERANCE))
            return DEFAULT_TOLERANCE
        log("Using document tolerance: {}".format(tol))
        return tol
    except Exception as e:
        log("Could not get document tolerance ({}), using default: {}".format(e, DEFAULT_TOLERANCE))
        return DEFAULT_TOLERANCE


def get_curve_plane(curve, tolerance):
    """
    Get plane of curve with fallback to WorldXY.
    
    Args:
        curve (Curve): Curve to extract plane from
        tolerance (float): Geometric tolerance
    
    Returns:
        Plane: Curve's plane or WorldXY if not planar
    """
    try:
        success, curve_plane = curve.TryGetPlane(tolerance)
        if success:
            return curve_plane
        else:
            log("Warning: Curve is not planar, using WorldXY plane as fallback")
            return rg.Plane.WorldXY
    except Exception as e:
        log("Warning: Error getting curve plane: {}, using WorldXY".format(e))
        return rg.Plane.WorldXY


def is_point_in_curve(point, curve, plane, tolerance):
    """
    Test if point is inside curve boundary.
    
    Uses Rhino's robust containment checking method.
    
    Args:
        point (Point3d): Point to test
        curve (Curve): Container curve
        plane (Plane): Plane for containment test
        tolerance (float): Geometric tolerance
    
    Returns:
        bool: True if point is inside, False otherwise
    """
    try:
        containment = curve.Contains(point, plane, tolerance)
        return containment == rg.PointContainment.Inside
    except Exception as e:
        log("Warning: Error in point containment test: {}".format(e))
        return False


def validate_inputs(curves, points):
    """
    Validate input data.
    
    Args:
        curves (list): List of curves
        points (list): List of points
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not curves:
        return False, "No container curves provided"
    if not points:
        return False, "No points provided"
    return True, None


def sort_points_by_containers(curves, points, tolerance):
    """
    Sort points into containers and return indexed tree.
    
    Creates a branch for every curve, even if empty.
    
    Args:
        curves (list): Container curves
        points (list): Points to sort
        tolerance (float): Geometric tolerance
    
    Returns:
        tuple: (indexed_tree, statistics_dict)
    """
    indexed_tree = Grasshopper.DataTree[int]()
    
    stats = {
        'total_points': len(points),
        'total_curves': len(curves),
        'points_sorted': 0,
        'empty_branches': 0,
        'container_stats': []
    }
    
    for curve_index, curve in enumerate(curves):
        path = GH_Path(curve_index)
        
        # Ensure branch exists even if curve is None or contains no points
        ensure_branch_exists(indexed_tree, path)
        
        if curve is None:
            log("Warning: Curve at index {} is None, creating empty branch".format(curve_index))
            stats['empty_branches'] += 1
            stats['container_stats'].append({
                'index': curve_index,
                'count': 0
            })
            continue
        
        curve_plane = get_curve_plane(curve, tolerance)
        points_in_curve = 0
        
        for point_index, point in enumerate(points):
            if point is None:
                continue
            
            try:
                if is_point_in_curve(point, curve, curve_plane, tolerance):
                    indexed_tree.Add(point_index, path)
                    points_in_curve += 1
                    stats['points_sorted'] += 1
            except Exception as e:
                log(
                    "Warning: Error testing point {} against curve {}: {}".format(
                        point_index,
                        curve_index,
                        e
                    )
                )
        
        stats['container_stats'].append({
            'index': curve_index,
            'count': points_in_curve
        })
        
        if points_in_curve > 0:
            log("Container {}: {} point(s) found".format(curve_index, points_in_curve))
        else:
            stats['empty_branches'] += 1
            log("Container {}: empty (no points)".format(curve_index))
    
    return indexed_tree, stats


def generate_summary_report(stats):
    """
    Generate summary report from sorting statistics.
    
    Args:
        stats (dict): Statistics dictionary
    
    Returns:
        str: Summary message
    """
    summary_parts = [
        "Sorting complete: {} of {} point(s) sorted into {} container(s)".format(
            stats['points_sorted'],
            stats['total_points'],
            stats['total_curves']
        )
    ]
    
    if stats['empty_branches'] > 0:
        summary_parts.append(
            "({} empty branch(es))".format(stats['empty_branches'])
        )
    
    unsorted_count = stats['total_points'] - stats['points_sorted']
    if unsorted_count > 0:
        summary_parts.append(
            "({} point(s) not contained in any curve)".format(unsorted_count)
        )
    
    return ". ".join(summary_parts)


################
# INPUT HANDLING & VALIDATION
################
crv = globals().get('crv', [])
pt = globals().get('pt', [])

if not isinstance(crv, (list, tuple)):
    if crv:
        crv = [crv]
    else:
        crv = []

if not isinstance(pt, (list, tuple)):
    if pt:
        pt = [pt]
    else:
        pt = []


################
# EXECUTION
################
indexed_tree = Grasshopper.DataTree[int]()

try:
    is_valid, error_msg = validate_inputs(crv, pt)
    
    if not is_valid:
        report(RML.Warning, error_msg)
    else:
        tolerance = get_document_tolerance()
        
        log("Processing {} point(s) against {} container curve(s)...".format(len(pt), len(crv)))
        
        indexed_tree, stats = sort_points_by_containers(crv, pt, tolerance)
        
        summary = generate_summary_report(stats)
        log(summary)
        
        unsorted_count = stats['total_points'] - stats['points_sorted']
        if unsorted_count > 0:
            report(
                RML.Warning,
                "{} point(s) not contained in any curve (see 'out' for details).".format(unsorted_count)
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
i = indexed_tree
