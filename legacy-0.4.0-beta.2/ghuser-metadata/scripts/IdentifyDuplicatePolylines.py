"""Identify Duplicate Polylines - Geometric Duplicate Detection

This component identifies duplicate polylines using normalized geometric
signatures. The algorithm is invariant to starting point and direction,
accurately detecting duplicates even when vertices are ordered differently.
Returns indexes of duplicates organized by groups.

Typical usage:
    List of Polylines -> Duplicate Indexes (grouped)

Logic:
    1. Validate input polylines
    2. Extract and normalize points from each polyline
    3. Round coordinates based on document tolerance
    4. Compute canonical signature (invariant to start point/direction)
    5. Group polylines by identical signatures
    6. Output indexes of duplicates (excluding first occurrence)

Algorithm Details:
    - Rounds coordinates to tolerance precision
    - Normalizes start point to lexicographically smallest
    - Tests both forward and reverse orderings
    - Uses canonical signature for matching

Args (Component Inputs):
    p: (List[Polyline]) List of polyline objects to check
        - Type: list[Rhino.Geometry.Polyline/PolylineCurve/Curve]
        - Access: list
        - Optional: No
        - Note: Handles various polyline geometry types

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    i: (DataTree[int]) Indexes of duplicate polylines
        - Type: DataTree[int]
        - Structure: Each branch is one duplicate group
        - Note: First occurrence excluded from each group

Version: 3.2
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
import System


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "3.2"
COMPONENT_DATE = "2025/11/13"
DEFAULT_TOLERANCE = 1e-6

ghenv.Component.Name = "Identify Duplicate Polylines"
ghenv.Component.NickName = "IdDupPol.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '01.Modeling'
ghenv.Component.Description = (
    "Computes a normalized signature for each polyline—rounding and reordering its vertices to handle differences in start point and direction—and groups those with identical signatures. "
    "Duplicates are then identified by matching signatures, and only the duplicate indexes (excluding the first occurrence) are output in a list."
)
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "p"
ghenv.Component.Params.Input[0].NickName = "p"
ghenv.Component.Params.Input[0].Description = "List of polyline objects to check for duplicates."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "i"
ghenv.Component.Params.Output[1].NickName = "i"
ghenv.Component.Params.Output[1].Description = "List with the indexes of duplicate polylines (excluding the first occurrence)."


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


def convert_guid_to_geometry(poly):
    """
    Convert GUID reference to geometry object.
    
    Args:
        poly: Polyline object or GUID
    
    Returns:
        Geometry object or None if conversion fails
    """
    if isinstance(poly, System.Guid):
        try:
            obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find(poly)
            return obj.Geometry if obj else None
        except:
            return None
    return poly


def extract_polyline_points(poly, tol):
    """
    Extract points from various polyline geometry types.
    
    Handles PolylineCurve, Polyline, and general Curve types.
    Falls back to sampling for non-polyline curves.
    
    Args:
        poly: Polyline geometry object
        tol (float): Geometric tolerance
    
    Returns:
        list: List of Point3d objects, or None if extraction fails
    """
    try:
        pts = None
        
        if isinstance(poly, rg.PolylineCurve):
            pl = rg.Polyline()
            if poly.TryGetPolyline(pl):
                pts = list(pl)
            else:
                pts = [poly.PointAtNormalizedLength(t) for t in [0.0, 0.25, 0.5, 0.75, 1.0]]
        elif isinstance(poly, rg.Polyline):
            pts = list(poly)
        elif isinstance(poly, rg.Curve):
            pl = rg.Polyline()
            if poly.TryGetPolyline(pl):
                pts = list(pl)
            else:
                pts = [poly.PointAtNormalizedLength(t) for t in [0.0, 0.25, 0.5, 0.75, 1.0]]
        
        return pts if pts and len(pts) > 0 else None
        
    except Exception as e:
        log("Warning: Error extracting points from polyline: {}".format(e))
        return None


def round_point_coordinates(pt, factor):
    """
    Round point coordinates to tolerance precision.
    
    Args:
        pt (Point3d): Point to round
        factor (float): Rounding factor (1.0 / tolerance)
    
    Returns:
        tuple: (x, y, z) rounded coordinates
    """
    return (
        round(pt.X * factor) / factor,
        round(pt.Y * factor) / factor,
        round(pt.Z * factor) / factor
    )


def normalize_point_sequence(pts):
    """
    Normalize point sequence to canonical form.
    
    Starts with lexicographically smallest point and chooses
    between forward and reverse orderings.
    
    Args:
        pts (list): List of rounded point tuples
    
    Returns:
        tuple: Canonical point sequence
    """
    if len(pts) < 2:
        return tuple(pts)
    
    min_index = min(range(len(pts)), key=lambda i: pts[i])
    normalized = pts[min_index:] + pts[:min_index]
    reversed_normalized = list(reversed(normalized))
    
    return tuple(min(normalized, reversed_normalized))


def get_polyline_signature(poly, tol):
    """
    Compute normalized signature for polyline.
    
    Signature is invariant to starting point and direction.
    
    Args:
        poly: Polyline geometry object
        tol (float): Geometric tolerance
    
    Returns:
        tuple: Canonical signature or None if computation fails
    """
    try:
        poly = convert_guid_to_geometry(poly)
        if poly is None:
            return None
        
        pts = extract_polyline_points(poly, tol)
        if pts is None or len(pts) == 0:
            return None
        
        if len(pts) > 1 and pts[0].DistanceTo(pts[-1]) < tol:
            pts = pts[:-1]
        
        if len(pts) < 2:
            return None
        
        factor = 1.0 / tol
        rounded_pts = [round_point_coordinates(pt, factor) for pt in pts]
        
        return normalize_point_sequence(rounded_pts)
        
    except Exception as e:
        log("Warning: Error computing polyline signature: {}".format(e))
        return None


def analyze_duplicates(polylines, tolerance):
    """
    Analyze polylines for duplicates using signature matching.
    
    Args:
        polylines (list): List of polyline objects
        tolerance (float): Geometric tolerance
    
    Returns:
        tuple: (signature_dict, statistics_dict)
    """
    signature_dict = {}
    stats = {
        'total': len(polylines),
        'valid': 0,
        'invalid': 0
    }
    
    for idx, poly in enumerate(polylines):
        if poly is None:
            stats['invalid'] += 1
            continue
        
        try:
            signature = get_polyline_signature(poly, tolerance)
            if signature is None:
                stats['invalid'] += 1
                continue
            
            stats['valid'] += 1
            
            if signature in signature_dict:
                signature_dict[signature].append(idx)
            else:
                signature_dict[signature] = [idx]
                
        except Exception as e:
            log("Warning: Error processing polyline {}: {}".format(idx, e))
            stats['invalid'] += 1
    
    return signature_dict, stats


def create_duplicate_tree(signature_dict):
    """
    Create DataTree of duplicate indexes organized by group.
    
    Args:
        signature_dict (dict): Dictionary mapping signatures to index lists
    
    Returns:
        tuple: (duplicate_tree, duplicate_count, group_count)
    """
    duplicate_tree = Grasshopper.DataTree[int]()
    total_duplicates = 0
    duplicate_groups = 0
    
    branch_index = 0
    for signature, idx_list in signature_dict.items():
        if len(idx_list) > 1:
            duplicate_groups += 1
            path = GH_Path(branch_index)
            
            for duplicate_index in idx_list[1:]:
                duplicate_tree.Add(duplicate_index, path)
                total_duplicates += 1
            
            log("Duplicate group {}: {} polylines at indexes {}".format(
                branch_index, len(idx_list), idx_list))
            branch_index += 1
    
    return duplicate_tree, total_duplicates, duplicate_groups


def generate_summary_report(stats, total_duplicates, duplicate_groups):
    """
    Generate summary report from analysis statistics.
    
    Args:
        stats (dict): Statistics from analysis
        total_duplicates (int): Number of duplicate polylines
        duplicate_groups (int): Number of duplicate groups
    
    Returns:
        str: Summary message
    """
    unique_polylines = stats['valid'] - total_duplicates
    
    summary_parts = [
        "Analysis complete: {} unique polylines, {} duplicates in {} groups from {} total".format(
            unique_polylines,
            total_duplicates,
            duplicate_groups,
            stats['total']
        )
    ]
    
    if stats['invalid'] > 0:
        summary_parts.append(
            "({} polylines could not be processed)".format(stats['invalid'])
        )
    
    return ". ".join(summary_parts)


################
# INPUT HANDLING & VALIDATION
################
p = globals().get('p', [])

if not isinstance(p, (list, tuple)):
    if p:
        p = [p]
    else:
        p = []


################
# EXECUTION
################
duplicate_tree = Grasshopper.DataTree[int]()

try:
    if not p:
        report(RML.Warning, "No polylines provided")
    else:
        tolerance = get_document_tolerance()
        
        log("Analyzing {} polylines for duplicates...".format(len(p)))
        
        signature_dict, stats = analyze_duplicates(p, tolerance)
        
        duplicate_tree, total_duplicates, duplicate_groups = create_duplicate_tree(signature_dict)
        
        summary = generate_summary_report(stats, total_duplicates, duplicate_groups)
        log(summary)
        
        if stats['invalid'] > 0:
            report(
                RML.Warning,
                "{} polylines could not be processed (see 'out' for details).".format(stats['invalid'])
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
i = duplicate_tree
