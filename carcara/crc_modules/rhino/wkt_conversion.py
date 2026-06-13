"""Rhino geometry ↔ WKT conversion helpers.

These depend on Rhino/Common/Grasshopper and must never be imported from unit tests or plain CPython.
"""


def wkt_to_rhino(wkt_str: str):
    """Convert a single WKT string to Rhino.Geometry objects.

    Handles Z coordinates (defaults Z=0 if absent).
    Returns None → Point3d, LineString/Polygon/Multi* → PolylineCurve (multi-part members returned as list).
    """
    from shapely import wkt as shapely_wkt

    try:
        geom = shapely_wkt.loads(wkt_str)
    except Exception:
        return None

    if geom.is_empty:
        return None

    return _shapely_to_rhino(geom)


def _to_coords(pt):
    """Return (x, y, z) tuple from a shapely coord or Point."""
    if isinstance(pt, (tuple, list)):
        x, y = pt[0], pt[1]
        z = pt[2] if len(pt) > 2 else 0.0
    elif hasattr(pt, "x") and not isinstance(pt, bool):
        x = pt.x
        y = pt.y
        z = pt.z if hasattr(pt, "z") and pt.z is not None else 0.0
    else:
        x = float(pt[0])
        y = float(pt[1])
        z = float(pt[2]) if len(pt) > 2 else 0.0
    return (x, y, z)


def _extract_coords(geom):
    """Return list of coordinate tuples from various shapely types."""
    if hasattr(geom, "coords"):
        return [list(_to_coords(pt)) for pt in geom.coords]
    return []


def _shapely_to_rhino(shp_geom):
    from Rhino import Geometry as rg

    geom_type = shp_geom.geom_type

    # ---- POINT -----------------------------------------------------------
    if geom_type == "Point":
        return rg.Point3d(*_to_coords(shp_geom.coords[0]))

    if geom_type in ("MultiPoint",):
        pts = []
        for member in shp_geom.geoms:  # noqa: F821
            c = _to_coords(member.coords[0])
            p = rg.Point3d(*c)
            if p is not None:
                pts.append(p)
        return pts

    # ---- LINE STRING -----------------------------------------------------
    if geom_type == "LineString":
        coords = _extract_coords(shp_geom)
        if len(coords) >= 2:
            pts = [rg.Point3d(*c) for c in coords]
            pline = rg.Polyline(pts)
            curve = rg.PolylineCurve(pline)
            if curve and curve.IsValid:
                return curve
            return None

    if geom_type == "MultiLineString":
        return [_shapely_to_rhino(member) for member in shp_geom.geoms]  # noqa: F821

    # ---- POLYGON ---------------------------------------------------------
    if geom_type == "Polygon":
        coords = _extract_coords(shp_geom.exterior)
        if len(coords) >= 4:
            pts = [rg.Point3d(*c) for c in coords]
            pline = rg.Polyline(pts)
            curve = rg.PolylineCurve(pline)
            if curve and curve.IsValid:
                return curve
            return None

    if geom_type == "MultiPolygon":
        return [_shapely_to_rhino(member) for member in shp_geom.geoms]  # noqa: F821

    if geom_type == "GeometryCollection":
        return [_shapely_to_rhino(member) for member in shp_geom.geoms if _shapely_to_rhino(member)]

    return None


def rh_geometry_to_wkt(geom):
    """Convert a Rhino geometry to a WKT string (2D — Y omitted from WKT coords).

    Accepts Point3d, Point, Line, LineCurve, Polyline, PolylineCurve, Curve, Brep, Mesh.
    Returns None when the input cannot be converted.
    """
    import Rhino
    rg = Rhino.Geometry

    if isinstance(geom, rg.Point3d):
        return f"POINT ({geom.X} {geom.Y})"
    elif isinstance(geom, rg.Point):
        return f"POINT ({geom.Location.X} {geom.Location.Y})"
    elif isinstance(geom, rg.Line):
        return f"LINESTRING ({geom.From.X} {geom.From.Y}, {geom.To.X} {geom.To.Y})"
    elif isinstance(geom, rg.LineCurve):
        t0 = geom.Domain.Min
        t1 = geom.Domain.Max
        p0 = geom.PointAt(t0)
        p1 = geom.PointAt(t1)
        return f"LINESTRING ({p0.X} {p0.Y}, {p1.X} {p1.Y})"
    elif isinstance(geom, rg.Polyline):
        if len(geom) == 0:
            return None
        coords = ", ".join(f"{p.X} {p.Y}" for p in geom)
        return f"POLYGON (({coords}))" if geom.IsClosed else f"LINESTRING ({coords})"
    elif isinstance(geom, rg.PolylineCurve):
        poly = rg.Polyline()
        geom.TryGetPolyline(poly)
        if len(poly) == 0:
            return None
        coords = ", ".join(f"{p.X} {p.Y}" for p in poly)
        return f"POLYGON (({coords}))" if poly.IsClosed else f"LINESTRING ({coords})"
    elif isinstance(geom, rg.Curve):
        # Try polyline extraction first (fastest path for polylines/arcs etc.)
        poly = rg.Polyline()
        if geom.TryGetPolyline(poly) and len(poly) > 0:
            coords = ", ".join(f"{p.X} {p.Y}" for p in poly)
            return f"POLYGON (({coords}))" if poly.IsClosed else f"LINESTRING ({coords})"
        # Fallback: approximate with many sample points
        pts = geom.DivideByLength(1.0, True)
        if pts:
            coords = ", ".join(f"{pt.X} {pt.Y}" for pt in pts)
            return f"LINESTRING ({coords})"
    elif isinstance(geom, rg.Brep):
        for face in geom.Faces:
            loop = face.OuterLoop
            if loop:
                crv = loop.To3dCurve()
                if crv:
                    poly_out = rg.Polyline()
                    if crv.TryGetPolyline(poly_out) and len(poly_out) > 0:
                        coords = ", ".join(f"{p.X} {p.Y}" for p in poly_out)
                        return f"POLYGON (({coords}))"
        # Edge fallback
        edges = geom.GetEdges()
        if edges:
            pts_coords = []
            for e in edges:
                pts_coords.append(f"{e.PointAtStart.X} {e.PointAtStart.Y}")
            pts_coords.append(f"{e.PointAtEnd.X} {e.PointAtEnd.Y}")
            if len(pts_coords) >= 4:
                return f"POLYGON (({', '.join(pts_coords)}))"
    elif isinstance(geom, rg.Mesh):
        outlines = rg.Mesh.GetOutlines(geom)
        if outlines and len(outlines) > 0:
            for crv in outlines:
                poly_out = rg.Polyline()
                if crv.TryGetPolyline(poly_out) and len(poly_out) > 0:
                    coords = ", ".join(f"{p.X} {p.Y}" for p in poly_out)
                    return f"POLYGON (({coords}))"

    return None
