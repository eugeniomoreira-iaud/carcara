"""Rhino-dependent building mesh extrusion helpers for CRC_BuildingMeshes.

This module runs ONLY inside Rhino 8's Grasshopper Python 3 environment.
It is excluded from pytest. Do not import from plain CPython.

Functions:
    is_polygon_inside(inner_poly, outer_poly) -> bool
    group_polygons_with_holes_and_heights(polygons, heights) -> list
    create_ngon_mesh_with_holes(exterior_poly, hole_polys) -> Mesh or None
    create_building_mesh_with_holes(exterior_poly, hole_polys, height)
        -> (ground_mesh, lateral_mesh, roof_mesh) or (None, None, None)
"""

import Rhino.Geometry as rg


# ---------------------------------------------------------------------------
# Hole detection
# ---------------------------------------------------------------------------

def is_polygon_inside(inner_poly, outer_poly):
    """Test whether inner_poly is completely inside outer_poly.

    Tests every vertex and every edge midpoint of ``inner_poly`` for
    containment against ``outer_poly`` using
    ``PolylineCurve.Contains(pt, WorldXY, 1e-6)``.  A single point
    outside is enough to return False.

    Args:
        inner_poly: Rhino.Geometry.Polyline (or PolylineCurve) to test.
        outer_poly: Rhino.Geometry.Polyline (or PolylineCurve) container.

    Returns:
        bool: True if every tested point is Inside the outer polygon.
    """
    try:
        # Accept both Polyline and PolylineCurve
        if hasattr(outer_poly, 'ToPolylineCurve'):
            outer_curve = outer_poly.ToPolylineCurve()
        else:
            outer_curve = rg.PolylineCurve(outer_poly)

        # Collect test points: vertices + midpoints of each segment
        inner_pts = list(inner_poly)
        test_points = []
        for i in range(len(inner_pts) - 1):
            test_points.append(inner_pts[i])
            mid = rg.Point3d(
                (inner_pts[i].X + inner_pts[i + 1].X) / 2.0,
                (inner_pts[i].Y + inner_pts[i + 1].Y) / 2.0,
                (inner_pts[i].Z + inner_pts[i + 1].Z) / 2.0,
            )
            test_points.append(mid)

        for pt in test_points:
            containment = outer_curve.Contains(pt, rg.Plane.WorldXY, 1e-6)
            if containment != rg.PointContainment.Inside:
                return False

        return True

    except Exception:
        return False


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def group_polygons_with_holes_and_heights(polygons, heights):
    """Group exterior polygons with their interior hole polygons and heights.

    A polygon is a *hole* if it is contained inside another polygon in the
    same list.  The height assigned to a building group comes from the
    exterior polygon's index in the original ``heights`` list.

    Args:
        polygons (list): List of Rhino.Geometry.Polyline objects.
        heights (list): Parallel list of heights (one per polygon).

    Returns:
        list: List of (exterior_poly, [hole_polys], height) tuples.
              Exterior polygons only; holes are collected under their parent.
    """
    if not polygons:
        return []

    if len(polygons) < 2:
        return [(polygons[0], [], heights[0])]

    # For each polygon, find the first other polygon that contains it
    contained_in = {}
    for i in range(len(polygons)):
        for j in range(len(polygons)):
            if i != j:
                if is_polygon_inside(polygons[i], polygons[j]):
                    contained_in[i] = j
                    break  # first containing polygon wins

    groups = []
    used = set()

    for i, poly in enumerate(polygons):
        if i in used:
            continue
        if i in contained_in:
            # This polygon is a hole — it will be picked up by its parent
            continue

        # Exterior polygon: collect all direct holes
        holes = []
        for j in range(len(polygons)):
            if j != i and contained_in.get(j) == i:
                holes.append(polygons[j])
                used.add(j)

        groups.append((poly, holes, heights[i]))
        used.add(i)

    return groups


# ---------------------------------------------------------------------------
# Mesh creation
# ---------------------------------------------------------------------------

def _to_polyline_curve(poly):
    """Coerce a Polyline or PolylineCurve to a closed PolylineCurve."""
    if isinstance(poly, rg.PolylineCurve):
        return poly
    pts = list(poly)
    if pts[0].DistanceTo(pts[-1]) > 1e-6:
        pts.append(pts[0])
    return rg.PolylineCurve(pts)


def create_ngon_mesh_with_holes(exterior_poly, hole_polys):
    """Create a single planar mesh with an ngon that covers the exterior polygon,
    with holes cut out.

    For polygons without holes: uses ``Mesh.CreateFromClosedPolyline`` (fast).
    For polygons with holes: builds a planar Brep from exterior + hole curves,
    meshes it, and wraps all faces in a single ``MeshNgon``.

    Args:
        exterior_poly: Exterior Rhino.Geometry.Polyline.
        hole_polys (list): List of interior hole Polyline objects.

    Returns:
        Rhino.Geometry.Mesh or None on failure.
    """
    try:
        if not hole_polys:
            # Simple case: no holes
            mesh = rg.Mesh.CreateFromClosedPolyline(exterior_poly)
            if mesh:
                v_idx = list(range(mesh.Vertices.Count))
                f_idx = list(range(mesh.Faces.Count))
                ngon = rg.MeshNgon.Create(v_idx, f_idx)
                if ngon:
                    mesh.Ngons.AddNgon(ngon)
            return mesh

        # With holes: planar Brep route
        exterior_curve = _to_polyline_curve(exterior_poly)
        all_curves = [exterior_curve] + [_to_polyline_curve(h) for h in hole_polys]
        breps = rg.Brep.CreatePlanarBreps(all_curves, 1e-6)

        if not breps or len(breps) == 0:
            return None

        mesh_params = rg.MeshingParameters.Default
        mesh_params.MaximumEdgeLength = 10.0

        meshes = rg.Mesh.CreateFromBrep(breps[0], mesh_params)
        if not meshes or len(meshes) == 0:
            return None

        final_mesh = rg.Mesh()
        for m in meshes:
            final_mesh.Append(m)

        v_idx = list(range(final_mesh.Vertices.Count))
        f_idx = list(range(final_mesh.Faces.Count))
        ngon = rg.MeshNgon.Create(v_idx, f_idx)
        if ngon:
            final_mesh.Ngons.AddNgon(ngon)

        return final_mesh

    except Exception:
        return None


def create_building_mesh_with_holes(exterior_poly, hole_polys, height):
    """Extrude a building footprint (with optional courtyard holes) to meshes.

    Produces three separate meshes:
    * **ground** — flat ngon at Z=0, holes cut out.
    * **lateral** — quad-per-edge wall mesh for exterior + each hole boundary.
    * **roof** — duplicate of ground translated up by ``height``.

    Args:
        exterior_poly: Exterior Rhino.Geometry.Polyline.
        hole_polys (list): Interior hole Polyline objects.
        height (float): Building height (must be positive).

    Returns:
        tuple: (ground_mesh, lateral_mesh, roof_mesh) or (None, None, None) on failure.
    """
    try:
        # --- Ground / Roof ---
        ground_mesh = create_ngon_mesh_with_holes(exterior_poly, hole_polys)
        if not ground_mesh:
            return None, None, None

        roof_mesh = ground_mesh.Duplicate()
        roof_mesh.Translate(rg.Vector3d(0, 0, height))

        # --- Lateral walls ---
        lateral_mesh = rg.Mesh()
        all_polys = [exterior_poly] + list(hole_polys)

        for poly in all_polys:
            pts = list(poly)
            # Ensure the ring is explicitly closed
            if pts[0].DistanceTo(pts[-1]) > 1e-6:
                pts.append(pts[0])

            unique_pts = pts[:-1]  # drop the repeated closing vertex
            n = len(unique_pts)
            base = lateral_mesh.Vertices.Count

            # Add base ring then top ring
            for pt in unique_pts:
                lateral_mesh.Vertices.Add(pt)
            for pt in unique_pts:
                lateral_mesh.Vertices.Add(rg.Point3d(pt.X, pt.Y, pt.Z + height))

            # One quad face per segment
            for i in range(n):
                ni = (i + 1) % n
                lateral_mesh.Faces.AddFace(
                    base + i,
                    base + i + n,
                    base + ni + n,
                    base + ni,
                )

        lateral_mesh.Normals.ComputeNormals()

        return ground_mesh, lateral_mesh, roof_mesh

    except Exception:
        return None, None, None
