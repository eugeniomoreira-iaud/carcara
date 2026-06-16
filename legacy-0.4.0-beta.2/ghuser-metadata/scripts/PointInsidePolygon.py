"""Point Inside Polygon - Interior Point Locator

This component finds a point guaranteed to be inside a polygon. First attempts
to use the centroid, falling back to a polylabel algorithm (pole of 
inaccessibility) if the centroid lies outside. Useful for labeling, point
placement, and polygon analysis.

Typical usage:
    Polygon -> Interior Point

Logic:
    1. Validate input polygon
    2. Extract vertices and ensure polygon closure
    3. Compute geometric centroid
    4. Test if centroid is inside polygon
    5. If inside: use centroid
    6. If outside: compute pole of inaccessibility using polylabel algorithm
    7. Return interior point with distance to nearest edge

Algorithm:
    - Centroid: Average of all vertex coordinates
    - Polylabel: Iterative grid search for point farthest from edges
    - Distance: Perpendicular distance to closest polygon edge

Args (Component Inputs):
    pol: (Curve) Polygon curve to process
        - Type: Rhino.Geometry.Curve
        - Access: item
        - Optional: No
        - Note: Must be convertible to polyline

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    pt: (Point3d) Point guaranteed to be inside polygon
        - Type: Rhino.Geometry.Point3d
        - Note: At Z=0, with maximum distance to edges

Version: 2.2
Date: 2025/11/13
Requires: carcara_geometry module with polylabel, point_in_polygon functions
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Grasshopper
from ghpythonlib import treehelpers
import Rhino.Geometry as rg
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_geometry as cg
importlib.reload(cg)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "2.2"
COMPONENT_DATE = "2025/11/13"
POLYLABEL_TOLERANCE = 0.01

ghenv.Component.Name = "Point Inside Polygon"
ghenv.Component.NickName = "Pt_Plg.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '01.Modeling'
ghenv.Component.Description = (
    "Finds a point inside a polygon. Tries the centroid first. "
    "If it doesn't work, implements a polylabel algorithm to find the pole of inaccessibility."
)
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "pol"
ghenv.Component.Params.Input[0].NickName = "pol"
ghenv.Component.Params.Input[0].Description = "Polygons to be processed."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "pt"
ghenv.Component.Params.Output[1].NickName = "pt"
ghenv.Component.Params.Output[1].Description = "Resultant points"


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


def extract_polygon_vertices(polygon):
    """
    Extract vertices from polygon curve and ensure closure.
    
    Converts curve to polyline and extracts (x, y) coordinates.
    Ensures polygon is closed by adding first point at end if needed.
    
    Args:
        polygon (Curve): Input polygon curve
    
    Returns:
        list: List of (x, y) tuples representing vertices
        
    Raises:
        Exception: If curve cannot be converted to polyline
    """
    try:
        success, pline = polygon.TryGetPolyline()
        if not success:
            nurbs = polygon.ToNurbsCurve()
            success, pline = nurbs.TryGetPolyline()
        
        if not success:
            raise Exception("Input curve could not be converted to a polyline.")
        
        pts = list(pline)
        vertices = [(pt.X, pt.Y) for pt in pts]
        
        if vertices[0] != vertices[-1]:
            vertices.append(vertices[0])
        
        log("Extracted {} vertices from polygon".format(len(vertices)))
        return vertices
        
    except Exception as e:
        raise Exception("Error extracting vertices: {}".format(e))


def compute_centroid(vertices):
    """
    Compute geometric centroid of polygon vertices.
    
    Calculates simple arithmetic mean of vertex coordinates,
    excluding duplicate closing point.
    
    Args:
        vertices (list): List of (x, y) tuples
    
    Returns:
        tuple: (x, y) coordinates of centroid
    """
    unique_vertices = vertices[:-1]
    sum_x = sum(pt[0] for pt in unique_vertices)
    sum_y = sum(pt[1] for pt in unique_vertices)
    count = len(unique_vertices)
    
    centroid = (sum_x / count, sum_y / count)
    log("Computed centroid: ({:.3f}, {:.3f})".format(centroid[0], centroid[1]))
    return centroid


def find_interior_point(vertices, tolerance):
    """
    Find optimal interior point for polygon.
    
    First tries centroid. If centroid is outside, uses polylabel
    algorithm to find pole of inaccessibility.
    
    Args:
        vertices (list): List of (x, y) vertex tuples
        tolerance (float): Tolerance for polylabel algorithm
    
    Returns:
        tuple: ((x, y), distance, method)
            - (x, y): Interior point coordinates
            - distance: Distance to nearest edge
            - method: "centroid" or "polylabel"
    """
    centroid = compute_centroid(vertices)
    
    if cg.point_in_polygon(centroid[0], centroid[1], vertices):
        distance = cg.point_to_polygon_distance(centroid[0], centroid[1], vertices)
        log("Centroid is inside polygon (distance to edge: {:.3f})".format(distance))
        return centroid, distance, "centroid"
    else:
        log("Centroid is outside polygon, computing polylabel...")
        (pole_x, pole_y), distance = cg.polylabel(vertices, tolerance)
        log("Polylabel found at ({:.3f}, {:.3f}) with distance {:.3f}".format(
            pole_x, pole_y, distance))
        return (pole_x, pole_y), distance, "polylabel"


def validate_polygon(polygon):
    """
    Validate polygon input.
    
    Args:
        polygon: Input polygon object
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if polygon is None:
        return False, "No polygon input provided"
    
    if not isinstance(polygon, rg.Curve):
        return False, "Input must be a Curve object"
    
    if not polygon.IsClosed:
        return False, "Input curve must be closed"
    
    return True, None


################
# INPUT HANDLING & VALIDATION
################
pol = globals().get('pol', None)


################
# EXECUTION
################
pt = None

try:
    is_valid, error_msg = validate_polygon(pol)
    
    if not is_valid:
        report(RML.Warning, error_msg)
    else:
        log("Processing polygon...")
        
        vertices = extract_polygon_vertices(pol)
        
        (pole_x, pole_y), distance, method = find_interior_point(
            vertices,
            POLYLABEL_TOLERANCE
        )
        
        pt = rg.Point3d(pole_x, pole_y, 0)
        
        log("Interior point found using {} method (distance to edge: {:.3f})".format(
            method,
            distance
        ))

except ImportError as e:
    report(
        RML.Error,
        "Module import error: {} - see 'out' for details.".format(e)
    )
except AttributeError as e:
    report(
        RML.Error,
        "Module function error: {} - see 'out' for details.".format(e)
    )
except ValueError as e:
    report(
        RML.Error,
        "Value error: {} - see 'out' for details.".format(e)
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
pt
