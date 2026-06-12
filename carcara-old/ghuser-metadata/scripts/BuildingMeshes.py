"""Building Meshes with Holes - 3D Building Extrusion Component


This component extrudes 2D building footprint polygons to 3D meshes with
automatic hole detection. Creates separate ground, lateral wall, and rooftop
meshes for each building, properly handling courtyard holes and voids.
Supports both single height for all buildings or individual heights per building.


Typical usage:
    Building Footprints -> Height(s) -> Ground/Wall/Roof Meshes


Logic:
    1. Validate input footprints and height value(s)
    2. Match heights to buildings (single height or list)
    3. Analyze polygon containment to detect holes (courtyards)
    4. Group exterior polygons with their interior holes
    5. Create single-face ngon meshes for ground and roof (optimized)
    6. Extrude edges to create lateral wall meshes with individual heights
    7. Return separate mesh lists for ground, walls, and roofs
    8. Preserve empty branches for data structure consistency


Args (Component Inputs):
    BdgFp: (Tree[Polyline]) Tree of polygon footprints
        - Type: tree[Rhino.Geometry.Polyline]
        - Access: tree
        - Optional: No
        - Note: Holes are auto-detected by containment analysis
        - Empty branches are preserved in output
    
    BdgH: (Tree[Float]) Tree of height value(s) for buildings
        - Type: tree[float]
        - Access: tree
        - Optional: No
        - Unit: Model units (typically meters)
        - Note: Must match BdgFp tree structure


Returns (Component Outputs):
    out: (str) Performance analysis report
        - Type: str
    
    GrdF: (Tree[Mesh]) Ground faces with holes (single ngon per building)
        - Type: tree[Rhino.Geometry.Mesh]
        - Note: Empty branches preserved for matching input structure
    
    LatF: (Tree[Mesh]) Lateral wall faces
        - Type: tree[Rhino.Geometry.Mesh]
        - Note: Empty branches preserved for matching input structure
    
    RftF: (Tree[Mesh]) Rooftop faces with holes (single ngon per building)
        - Type: tree[Rhino.Geometry.Mesh]
        - Note: Empty branches preserved for matching input structure


Version: 3.3
Date: 2025/10/31
"""


####################
# IMPORTS
####################
import Rhino.Geometry as rg
import time
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML
import Grasshopper.Kernel as gh


#########################
# COMPONENT METADATA
#########################
COMPONENT_VERSION = "3.3"
COMPONENT_DATE = "2025/10/31"


ghenv.Component.Name = "Building Meshes with Holes"
ghenv.Component.NickName = "BdgMsh.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Description = "Extrudes building footprints with hole detection (preserves empty branches)"


########################
# INPUT METADATA
########################
ghenv.Component.Params.Input[0].Name = "Building Footprints"
ghenv.Component.Params.Input[0].NickName = "BdgFp"
ghenv.Component.Params.Input[0].Description = "Tree of polygon footprints (holes auto-detected)."
ghenv.Component.Params.Input[0].Access = gh.GH_ParamAccess.tree


ghenv.Component.Params.Input[1].Name = "Building Height"
ghenv.Component.Params.Input[1].NickName = "BdgH"
ghenv.Component.Params.Input[1].Description = "Tree of heights matching footprint tree structure."
ghenv.Component.Params.Input[1].Access = gh.GH_ParamAccess.tree


########################
# OUTPUT METADATA
########################
ghenv.Component.Params.Output[0].Name = "Performance Report"
ghenv.Component.Params.Output[0].NickName = "out"
ghenv.Component.Params.Output[0].Description = "Performance analysis summary."


ghenv.Component.Params.Output[1].Name = "Ground Faces"
ghenv.Component.Params.Output[1].NickName = "GrdF"
ghenv.Component.Params.Output[1].Description = "Tree of Ground Faces with holes (ngons)."


ghenv.Component.Params.Output[2].Name = "Lateral Faces"
ghenv.Component.Params.Output[2].NickName = "LatF"
ghenv.Component.Params.Output[2].Description = "Tree of Lateral Faces with holes."


ghenv.Component.Params.Output[3].Name = "Rooftop Faces"
ghenv.Component.Params.Output[3].NickName = "RftF"
ghenv.Component.Params.Output[3].Description = "Tree of Rooftop Faces with holes (ngons)."


########################
# PERFORMANCE TRACKING
########################
class PerformanceTracker:
    """Track execution time of different operations."""
    
    def __init__(self):
        self.timings = {}
        self.total_start = None
        self.empty_branches_count = 0
    
    def start_total(self):
        """Start total execution timing."""
        self.total_start = time.time()
    
    def get_total_time(self):
        """Get total execution time."""
        if self.total_start is None:
            return 0.0
        return time.time() - self.total_start
    
    def increment_empty_branches(self):
        """Increment empty branch counter."""
        self.empty_branches_count += 1
    
    def start(self, operation_name):
        """Start timing an operation."""
        if operation_name not in self.timings:
            self.timings[operation_name] = {'count': 0, 'total_time': 0.0, 'start': None}
        self.timings[operation_name]['start'] = time.time()
    
    def end(self, operation_name):
        """End timing an operation."""
        if operation_name in self.timings and self.timings[operation_name]['start'] is not None:
            elapsed = time.time() - self.timings[operation_name]['start']
            self.timings[operation_name]['total_time'] += elapsed
            self.timings[operation_name]['count'] += 1
            self.timings[operation_name]['start'] = None
    
    def report_summary(self, total_branches, total_buildings, successful, failed):
        """Generate performance summary report."""
        lines = ["\n" + "=" * 50]
        lines.append("PERFORMANCE ANALYSIS".center(50))
        lines.append("=" * 50)
        
        lines.append("\nProcessing Summary:")
        lines.append("  Total branches: {}".format(total_branches))
        lines.append("  Empty branches: {}".format(self.empty_branches_count))
        lines.append("  Processed branches: {}".format(total_branches - self.empty_branches_count))
        lines.append("  Total buildings: {}".format(total_buildings))
        lines.append("  Successful: {}".format(successful))
        lines.append("  Failed: {}".format(failed))
        
        if not self.timings:
            lines.append("\nNo performance data collected.")
        else:
            lines.append("\nOperation Breakdown:")
            lines.append("-" * 50)
            
            sorted_ops = sorted(
                self.timings.items(),
                key=lambda x: x[1]['total_time'],
                reverse=True
            )
            
            operation_time = sum(t['total_time'] for t in self.timings.values())
            
            for op_name, data in sorted_ops:
                avg_time = data['total_time'] / data['count'] if data['count'] > 0 else 0
                percentage = (data['total_time'] / operation_time * 100) if operation_time > 0 else 0
                
                lines.append(
                    "  {:<30} {:>8.3f}s ({:>5.1f}%)".format(
                        op_name + ":",
                        data['total_time'],
                        percentage
                    )
                )
                lines.append(
                    "    {} calls - {:.4f}s avg".format(
                        data['count'],
                        avg_time
                    )
                )
        
        total_time = self.get_total_time()
        lines.append("-" * 50)
        lines.append("Total Execution Time: {:.3f}s".format(total_time))
        lines.append("=" * 50)
        
        return "\n".join(lines)


perf = PerformanceTracker()


######################
# HELPER FUNCTIONS
######################
def report(level, message):
    """
    Send runtime message to Grasshopper component.
    
    Displays message in both component bubble and output panel.
    
    Args:
        level (GH_RuntimeMessageLevel): Message severity level
        message (str): Message text to display
    """
    ghenv.Component.AddRuntimeMessage(level, message)
    print(message)


def ensure_branch_exists(tree, path):
    """
    Ensure a branch exists in the tree, creating an empty branch if needed.
    
    Args:
        tree (DataTree): Tree to modify
        path (GH_Path): Path to ensure exists
    """
    if not tree.PathExists(path):
        tree.EnsurePath(path)


def process_height_input(height_input, footprint_count):
    """
    Process height input to support both single and multiple heights.
    
    Handles three scenarios:
    1. Single value: Apply to all buildings
    2. List matching footprint count: One height per building
    3. List not matching: Error with clear message
    
    Args:
        height_input: Single value or list of heights
        footprint_count (int): Number of footprints provided
    
    Returns:
        tuple: (height_list, error_message)
            height_list: List of heights (one per footprint), or None if error
            error_message: Error string or None if successful
    """
    perf.start("process_height_input")
    
    if isinstance(height_input, (list, tuple)):
        if len(height_input) == 0:
            perf.end("process_height_input")
            return None, "Height list is empty."
        
        if len(height_input) == 1:
            try:
                single_height = float(height_input[0])
                if single_height <= 0:
                    perf.end("process_height_input")
                    return None, "Height must be positive. Got: {}".format(single_height)
                perf.end("process_height_input")
                return [single_height] * footprint_count, None
            except (ValueError, TypeError):
                perf.end("process_height_input")
                return None, "Invalid height value: {}".format(height_input[0])
        
        if len(height_input) != footprint_count:
            perf.end("process_height_input")
            return None, "Height list length ({}) does not match footprint count ({}). Provide either 1 height or {} heights.".format(
                len(height_input), footprint_count, footprint_count
            )
        
        try:
            height_list = [float(h) for h in height_input]
            
            for i, h in enumerate(height_list):
                if h <= 0:
                    perf.end("process_height_input")
                    return None, "Height at index {} must be positive. Got: {}".format(i, h)
            
            perf.end("process_height_input")
            return height_list, None
            
        except (ValueError, TypeError) as e:
            perf.end("process_height_input")
            return None, "Invalid height values in list: {}".format(e)
    else:
        try:
            single_height = float(height_input)
            if single_height <= 0:
                perf.end("process_height_input")
                return None, "Height must be positive. Got: {}".format(single_height)
            perf.end("process_height_input")
            return [single_height] * footprint_count, None
        except (ValueError, TypeError):
            perf.end("process_height_input")
            return None, "Invalid height value: {}".format(height_input)


def is_polygon_inside(inner_poly, outer_poly):
    """
    Check if inner polygon is completely inside outer polygon.
    
    Tests multiple points (vertices and midpoints) for containment.
    
    Args:
        inner_poly (Polyline): Polygon to test if inside
        outer_poly (Polyline): Potential container polygon
    
    Returns:
        bool: True if inner is completely inside outer
    """
    perf.start("is_polygon_inside")
    
    try:
        inner_curve = inner_poly.ToPolylineCurve() if hasattr(inner_poly, 'ToPolylineCurve') else rg.PolylineCurve(inner_poly)
        outer_curve = outer_poly.ToPolylineCurve() if hasattr(outer_poly, 'ToPolylineCurve') else rg.PolylineCurve(outer_poly)
        
        test_points = []
        inner_pts = list(inner_poly)
        
        for i in range(len(inner_pts) - 1):
            test_points.append(inner_pts[i])
            mid_pt = rg.Point3d(
                (inner_pts[i].X + inner_pts[i+1].X) / 2,
                (inner_pts[i].Y + inner_pts[i+1].Y) / 2,
                (inner_pts[i].Z + inner_pts[i+1].Z) / 2
            )
            test_points.append(mid_pt)
        
        for pt in test_points:
            containment = outer_curve.Contains(pt, rg.Plane.WorldXY, 1e-6)
            if containment != rg.PointContainment.Inside:
                perf.end("is_polygon_inside")
                return False
        
        perf.end("is_polygon_inside")
        return True
        
    except Exception as e:
        perf.end("is_polygon_inside")
        return False


def group_polygons_with_holes_and_heights(polygons, heights):
    """
    Group polygons with holes and associate heights.
    
    When polygons are grouped (exterior + holes), the height comes from
    the exterior polygon's original index.
    
    Args:
        polygons (list): List of Polyline objects
        heights (list): List of heights (one per polygon)
    
    Returns:
        list: List of (exterior_polygon, [hole_polygons], height) tuples
    """
    perf.start("group_polygons_with_holes_and_heights")
    
    if not polygons or len(polygons) < 2:
        perf.end("group_polygons_with_holes_and_heights")
        return [(poly, [], heights[i]) for i, poly in enumerate(polygons)]
    
    contained_in = {}
    
    for i in range(len(polygons)):
        for j in range(len(polygons)):
            if i != j:
                if is_polygon_inside(polygons[i], polygons[j]):
                    contained_in[i] = j
                    break
    
    groups = []
    used_indices = set()
    
    for i, poly in enumerate(polygons):
        if i in used_indices:
            continue
        
        if i not in contained_in:
            holes = []
            for j, other_poly in enumerate(polygons):
                if j != i and contained_in.get(j) == i:
                    holes.append(other_poly)
                    used_indices.add(j)
            
            groups.append((poly, holes, heights[i]))
            used_indices.add(i)
    
    perf.end("group_polygons_with_holes_and_heights")
    return groups


def create_mesh_from_polyline_fast(polyline):
    """
    Fast single-face mesh creation from closed polyline using Rhino API.
    
    Uses Mesh.CreateFromClosedPolyline which is optimized and fast.
    
    Args:
        polyline (Polyline): Closed polyline
    
    Returns:
        Rhino.Geometry.Mesh: Triangulated mesh or None if failed
    """
    perf.start("create_mesh_from_polyline_fast")
    
    try:
        mesh = rg.Mesh.CreateFromClosedPolyline(polyline)
        perf.end("create_mesh_from_polyline_fast")
        return mesh
    except Exception as e:
        perf.end("create_mesh_from_polyline_fast")
        return None


def create_ngon_mesh_with_holes(exterior_poly, hole_polys):
    """
    Create a single mesh with triangulated faces and ngon structure.
    
    First triangulates the polygon with holes, then groups all faces
    into a single ngon for cleaner visualization.
    
    Args:
        exterior_poly (Polyline): Exterior boundary polygon
        hole_polys (list): List of hole polygons
    
    Returns:
        Rhino.Geometry.Mesh: Mesh with ngon structure, or None if failed
    """
    perf.start("create_ngon_mesh_with_holes")
    
    try:
        if not hole_polys:
            mesh = create_mesh_from_polyline_fast(exterior_poly)
            if mesh:
                vertex_indices = list(range(mesh.Vertices.Count))
                face_indices = list(range(mesh.Faces.Count))
                ngon = rg.MeshNgon.Create(vertex_indices, face_indices)
                if ngon:
                    mesh.Ngons.AddNgon(ngon)
            perf.end("create_ngon_mesh_with_holes")
            return mesh
        
        exterior_curve = exterior_poly.ToPolylineCurve() if hasattr(exterior_poly, 'ToPolylineCurve') else rg.PolylineCurve(exterior_poly)
        
        hole_curves = []
        for hole_poly in hole_polys:
            if isinstance(hole_poly, rg.PolylineCurve):
                hole_curve = hole_poly
            else:
                pts = list(hole_poly)
                if pts[0].DistanceTo(pts[-1]) > 1e-6:
                    pts.append(pts[0])
                hole_curve = rg.PolylineCurve(pts)
            hole_curves.append(hole_curve)
        
        all_curves = [exterior_curve] + hole_curves
        brep = rg.Brep.CreatePlanarBreps(all_curves, 1e-6)
        
        if not brep or len(brep) == 0:
            perf.end("create_ngon_mesh_with_holes")
            return None
        
        mesh_params = rg.MeshingParameters.Default
        mesh_params.MaximumEdgeLength = 10.0
        
        meshes = rg.Mesh.CreateFromBrep(brep[0], mesh_params)
        if not meshes or len(meshes) == 0:
            perf.end("create_ngon_mesh_with_holes")
            return None
        
        final_mesh = rg.Mesh()
        for mesh in meshes:
            final_mesh.Append(mesh)
        
        vertex_indices = list(range(final_mesh.Vertices.Count))
        face_indices = list(range(final_mesh.Faces.Count))
        ngon = rg.MeshNgon.Create(vertex_indices, face_indices)
        if ngon:
            final_mesh.Ngons.AddNgon(ngon)
        
        perf.end("create_ngon_mesh_with_holes")
        return final_mesh
        
    except Exception as e:
        perf.end("create_ngon_mesh_with_holes")
        return None


def create_building_mesh_with_holes(exterior_poly, hole_polys, height):
    """
    Create building meshes with hole support using optimized ngon approach.
    
    Generates ground, lateral wall, and roof meshes for a building
    with potential courtyard holes. Uses ngons for single-face representation.
    
    Args:
        exterior_poly (Polyline): Exterior building footprint
        hole_polys (list): List of hole polygons
        height (float): Building height
    
    Returns:
        tuple: (ground_mesh, lateral_mesh, roof_mesh) or (None, None, None) if failed
    """
    perf.start("create_building_mesh_with_holes")
    
    try:
        perf.start("create_ground_roof_ngon")
        ground_mesh = create_ngon_mesh_with_holes(exterior_poly, hole_polys)
        if not ground_mesh:
            perf.end("create_ground_roof_ngon")
            perf.end("create_building_mesh_with_holes")
            return None, None, None
        
        roof_mesh = ground_mesh.Duplicate()
        roof_mesh.Translate(rg.Vector3d(0, 0, height))
        perf.end("create_ground_roof_ngon")
        
        perf.start("create_lateral_walls")
        lateral_mesh = rg.Mesh()
        all_polys = [exterior_poly] + hole_polys
        
        for poly in all_polys:
            pts = list(poly)
            if pts[0].DistanceTo(pts[-1]) > 1e-6:
                pts.append(pts[0])
            
            unique_pts = pts[:-1]
            n = len(unique_pts)
            
            base_start = lateral_mesh.Vertices.Count
            for pt in unique_pts:
                lateral_mesh.Vertices.Add(pt)
            for pt in unique_pts:
                roof_pt = rg.Point3d(pt.X, pt.Y, pt.Z + height)
                lateral_mesh.Vertices.Add(roof_pt)
            
            for i in range(n):
                next_i = (i + 1) % n
                lateral_mesh.Faces.AddFace(
                    base_start + i,
                    base_start + i + n,
                    base_start + next_i + n,
                    base_start + next_i
                )
        
        lateral_mesh.Normals.ComputeNormals()
        perf.end("create_lateral_walls")
        
        perf.end("create_building_mesh_with_holes")
        return ground_mesh, lateral_mesh, roof_mesh
        
    except Exception as e:
        perf.end("create_building_mesh_with_holes")
        return None, None, None


#################################
# INPUT HANDLING & VALIDATION
#################################
BdgFp = globals().get('BdgFp', DataTree[object]())
BdgH = globals().get('BdgH', DataTree[object]())


##################
# EXECUTION
##################
GrdF = DataTree[object]()
LatF = DataTree[object]()
RftF = DataTree[object]()

total_branches = 0
total_buildings = 0
successful_buildings = 0
failed_buildings = 0

perf.start_total()

try:
    if BdgFp.BranchCount == 0:
        report(RML.Warning, "No footprints provided.")
    elif BdgH.BranchCount == 0:
        report(RML.Warning, "No heights provided.")
    elif BdgFp.BranchCount != BdgH.BranchCount:
        report(
            RML.Error,
            "Tree structure mismatch: BdgFp has {} branches, BdgH has {} branches.".format(
                BdgFp.BranchCount,
                BdgH.BranchCount
            )
        )
    else:
        total_branches = BdgFp.BranchCount
        
        for i in range(BdgFp.BranchCount):
            path = BdgFp.Path(i)
            footprints = list(BdgFp.Branch(path))
            heights = list(BdgH.Branch(path))
            
            ensure_branch_exists(GrdF, path)
            ensure_branch_exists(LatF, path)
            ensure_branch_exists(RftF, path)
            
            if not footprints:
                perf.increment_empty_branches()
                continue
            
            total_buildings += len(footprints)
            
            height_list, height_error = process_height_input(heights, len(footprints))
            
            if height_error:
                report(
                    RML.Error,
                    "Branch {}: {}".format(path, height_error)
                )
                failed_buildings += len(footprints)
                continue
            
            grouped_polygons = group_polygons_with_holes_and_heights(footprints, height_list)
            
            for j, (exterior_poly, hole_polys, building_height) in enumerate(grouped_polygons):
                try:
                    ground, walls, roof = create_building_mesh_with_holes(
                        exterior_poly,
                        hole_polys,
                        building_height
                    )
                    
                    if ground and walls and roof:
                        GrdF.Add(ground, path)
                        LatF.Add(walls, path)
                        RftF.Add(roof, path)
                        successful_buildings += 1
                    else:
                        failed_buildings += 1
                        
                except Exception as e:
                    report(
                        RML.Error,
                        "Branch {} building {}: {}".format(path, j, e)
                    )
                    failed_buildings += 1

except Exception as e:
    report(
        RML.Error,
        "Unexpected error: {} (Type: {}).".format(
            e,
            type(e).__name__
        )
    )

out = perf.report_summary(total_branches, total_buildings, successful_buildings, failed_buildings)
print(out)
