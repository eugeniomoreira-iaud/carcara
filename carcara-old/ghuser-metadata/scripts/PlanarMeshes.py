"""Planar Meshes - Planar Curve to Mesh Converter

This component creates planar meshes from closed, planar curves. Handles both
single curves and DataTree structures. Validates curve closure and planarity
before mesh generation. Uses Rhino's optimized planar boundary meshing.

Typical usage:
    Closed Planar Curves -> Planar Meshes

Logic:
    1. Get document tolerance for planarity testing
    2. Process curves from DataTree or list structure
    3. Validate each curve (closed and planar)
    4. Create mesh from planar boundary using simple plane meshing
    5. Preserve input tree structure in output
    6. Skip invalid curves with warnings

Args (Component Inputs):
    Crvs: (DataTree[Curve]/List[Curve]) Input curves to mesh
        - Type: DataTree[Rhino.Geometry.Curve] or list
        - Access: tree or list
        - Optional: No
        - Note: Curves must be closed and planar

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    Msh: (DataTree[Mesh]) Planar meshes from valid curves
        - Type: DataTree[Rhino.Geometry.Mesh]
        - Structure: Preserves input tree structure
        - Note: Invalid curves produce no output in their position

Version: 1.1
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
import System


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "1.1"
COMPONENT_DATE = "2025/11/13"

ghenv.Component.Name = "Planar Meshes"
ghenv.Component.NickName = "PlnMsh.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '04.Dataviz'
ghenv.Component.Description = "This component creates planar meshes from planar curves."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "Crvs"
ghenv.Component.Params.Input[0].NickName = "Crvs"
ghenv.Component.Params.Input[0].Description = "Input curves to create planar meshes."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "Msh"
ghenv.Component.Params.Output[1].NickName = "Msh"
ghenv.Component.Params.Output[1].Description = "Planar meshes generated from closed, planar curves."


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
        float: Document tolerance or default (1e-6) if unavailable
    """
    try:
        tol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
        if tol <= 0:
            log("Invalid document tolerance, using default: 1e-6")
            return 1e-6
        log("Using document tolerance: {}".format(tol))
        return tol
    except Exception as e:
        log("Could not get document tolerance ({}), using default: 1e-6".format(e))
        return 1e-6


def create_meshing_parameters():
    """
    Create optimized meshing parameters for planar surfaces.
    
    Returns:
        MeshingParameters: Configured for simple planar meshing
    """
    mp = rg.MeshingParameters()
    mp.SimplePlanes = True
    return mp


def normalize_curve_input(input_curves):
    """
    Normalize various curve input types to list.
    
    Handles .NET collections, single curves, and lists.
    
    Args:
        input_curves: Various curve input types
    
    Returns:
        list: List of curve objects
    """
    if isinstance(input_curves, System.Collections.IEnumerable):
        return [c for c in input_curves]
    elif isinstance(input_curves, rg.Curve):
        return [input_curves]
    elif isinstance(input_curves, list):
        return input_curves
    else:
        return []


def validate_curve_for_meshing(curve, tolerance):
    """
    Validate if curve is suitable for planar meshing.
    
    Checks for None, closure, and planarity.
    
    Args:
        curve (Curve): Curve to validate
        tolerance (float): Planarity tolerance
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if curve is None:
        return False, "Curve is None"
    
    if not curve.IsClosed:
        return False, "Curve is not closed"
    
    if not curve.IsPlanar(tolerance):
        return False, "Curve is not planar"
    
    return True, None


def create_mesh_from_curve(curve, mesh_params, tolerance):
    """
    Create mesh from single planar curve.
    
    Args:
        curve (Curve): Input curve
        mesh_params (MeshingParameters): Meshing parameters
        tolerance (float): Geometric tolerance
    
    Returns:
        Mesh: Created mesh or None if failed
    """
    try:
        mesh = rg.Mesh.CreateFromPlanarBoundary(
            curve,
            mesh_params,
            tolerance
        )
        return mesh
    except Exception as e:
        log("Warning: Error creating mesh: {}".format(e))
        return None


def create_planar_meshes(input_curves, tolerance):
    """
    Process curves and create planar meshes.
    
    Validates each curve and creates mesh if suitable.
    
    Args:
        input_curves: Curve(s) from various input types
        tolerance (float): Geometric tolerance
    
    Returns:
        tuple: (meshes_list, statistics_dict)
    """
    meshes = []
    stats = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped_open': 0,
        'skipped_nonplanar': 0
    }
    
    mesh_params = create_meshing_parameters()
    curves_to_process = normalize_curve_input(input_curves)
    
    for idx, curve in enumerate(curves_to_process):
        stats['processed'] += 1
        
        is_valid, error_msg = validate_curve_for_meshing(curve, tolerance)
        
        if not is_valid:
            log("Curve {}: Skipped - {}".format(idx, error_msg))
            if "not closed" in error_msg:
                stats['skipped_open'] += 1
            elif "not planar" in error_msg:
                stats['skipped_nonplanar'] += 1
            else:
                stats['failed'] += 1
            continue
        
        mesh = create_mesh_from_curve(curve, mesh_params, tolerance)
        
        if mesh:
            meshes.append(mesh)
            stats['successful'] += 1
            log("Curve {}: Mesh created ({} vertices, {} faces)".format(
                idx, mesh.Vertices.Count, mesh.Faces.Count
            ))
        else:
            stats['failed'] += 1
            log("Curve {}: Mesh creation failed".format(idx))
    
    return meshes, stats


def process_tree_structure(input_tree, tolerance):
    """
    Process DataTree structure preserving branches.
    
    Args:
        input_tree (DataTree): Input DataTree of curves
        tolerance (float): Geometric tolerance
    
    Returns:
        tuple: (output_tree, total_statistics)
    """
    output_tree = DataTree[object]()
    total_stats = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped_open': 0,
        'skipped_nonplanar': 0
    }
    
    log("Processing DataTree with {} branch(es)...".format(input_tree.Paths.Count))
    
    for branch_idx, path in enumerate(input_tree.Paths):
        branch_data = input_tree.Branch(path)
        log("Branch {}: Processing {} curve(s)".format(branch_idx, len(branch_data)))
        
        processed_meshes, branch_stats = create_planar_meshes(branch_data, tolerance)
        output_tree.AddRange(processed_meshes, path)
        
        for key in total_stats:
            total_stats[key] += branch_stats[key]
    
    return output_tree, total_stats


def generate_summary_report(stats):
    """
    Generate summary report from processing statistics.
    
    Args:
        stats (dict): Statistics dictionary
    
    Returns:
        str: Summary message
    """
    summary_parts = [
        "Processed {} curve(s): {} successful".format(
            stats['processed'],
            stats['successful']
        )
    ]
    
    if stats['skipped_open'] > 0:
        summary_parts.append("{} open (skipped)".format(stats['skipped_open']))
    
    if stats['skipped_nonplanar'] > 0:
        summary_parts.append("{} non-planar (skipped)".format(stats['skipped_nonplanar']))
    
    if stats['failed'] > 0:
        summary_parts.append("{} failed".format(stats['failed']))
    
    return ", ".join(summary_parts) + "."


################
# INPUT HANDLING & VALIDATION
################
Crvs = globals().get('Crvs', None)


################
# EXECUTION
################
output_tree = DataTree[object]()

try:
    if not Crvs:
        log("No curves provided")
    else:
        tolerance = get_document_tolerance()
        
        if hasattr(Crvs, "Paths"):
            output_tree, stats = process_tree_structure(Crvs, tolerance)
        else:
            log("Processing list of {} curve(s)...".format(
                len(Crvs) if isinstance(Crvs, (list, tuple)) else 1
            ))
            processed_meshes, stats = create_planar_meshes(Crvs, tolerance)
            output_tree.AddRange(processed_meshes, GH_Path(0))
        
        summary = generate_summary_report(stats)
        log(summary)
        
        if stats['successful'] == 0 and stats['processed'] > 0:
            report(RML.Warning, "No valid meshes created (see 'out' for details).")
        elif stats['skipped_open'] > 0 or stats['skipped_nonplanar'] > 0 or stats['failed'] > 0:
            report(RML.Warning, "Some curves skipped/failed (see 'out' for details).")

except AttributeError as e:
    report(
        RML.Error,
        "Attribute error - see 'out' for details."
    )
    log("Attribute error: {}. Check input data types.".format(e))
except Exception as e:
    report(
        RML.Error,
        "Unexpected error - see 'out' for details."
    )
    log("Unexpected error: {} (Type: {}).".format(e, type(e).__name__))


################
# OUTPUTS (index 0 is default 'out', custom outputs start at 1)
################
Msh = output_tree
