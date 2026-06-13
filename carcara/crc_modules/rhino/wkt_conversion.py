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

    def _ring_to_curve(ring):
        coords = _extract_coords(ring)
        if len(coords) < 2:
            return None
        poly = rg.Polyline()
        for c in coords:
            poly.Add(c[0], c[1], c[2])
        if poly.Count >= 2:
            first, last = poly[0], poly[poly.Count - 1]
            if first.DistanceTo(last) > 0:
                poly.Add(first.X, first.Y, first.Z)
        return rg.PolylineCurve(poly)

    def _polygon_curves(poly_geom):
        out = []
        ext = _ring_to_curve(poly_geom.exterior)
        if ext is not None:
            out.append(ext)
        for interior in poly_geom.interiors:
            ic = _ring_to_curve(interior)
            if ic is not None:
                out.append(ic)
        return out

    if geom_type == "Point":
        return rg.Point3d(*_to_coords(shp_geom.coords[0]))
    if geom_type == "MultiPoint":
        return [rg.Point3d(*_to_coords(m.coords[0])) for m in shp_geom.geoms]

    if geom_type == "LineString":
        coords = _extract_coords(shp_geom)
        if len(coords) < 2:
            return None
        poly = rg.Polyline()
        for c in coords:
            poly.Add(c[0], c[1], c[2])
        return rg.PolylineCurve(poly)
    if geom_type == "MultiLineString":
        out = []
        for m in shp_geom.geoms:
            c = _shapely_to_rhino(m)
            if c is not None:
                out.append(c)
        return out

    if geom_type == "Polygon":
        return _polygon_curves(shp_geom)
    if geom_type == "MultiPolygon":
        out = []
        for m in shp_geom.geoms:
            out.extend(_polygon_curves(m))
        return out

    if geom_type == "GeometryCollection":
        out = []
        for m in shp_geom.geoms:
            r = _shapely_to_rhino(m)
            if isinstance(r, list):
                out.extend(r)
            elif r is not None:
                out.append(r)
        return out

    return None


def _fmt_coords(pts):
    """Return (coord_string, z_tag). z_tag=' Z' when any point has nonzero Z, else ''."""
    pts = list(pts)
    has_z = any(abs(p.Z) > 1e-9 for p in pts)
    if has_z:
        return ", ".join(f"{p.X} {p.Y} {p.Z}" for p in pts), " Z"
    return ", ".join(f"{p.X} {p.Y}" for p in pts), ""


def rh_geometry_to_wkt(geom):
    """Convert a Rhino geometry to a WKT string (3D when Z nonzero, else 2D).

    Accepts Point3d, Point, Line, LineCurve, Polyline, PolylineCurve, Curve, Brep, Mesh.
    Returns None when the input cannot be converted.
    """
    import Rhino
    import scriptcontext as sc
    rg = Rhino.Geometry

    # ghdoc-hinted inputs deliver referenced geometry as System.Guid
    if str(type(geom)).endswith("System.Guid'>"):
        rh_obj = sc.doc.Objects.Find(geom)
        geom = rh_obj.Geometry if rh_obj else None
    if geom is None:
        return None

    if isinstance(geom, rg.Point3d):
        coords, z = _fmt_coords([geom])
        return f"POINT{z} ({coords})"
    elif isinstance(geom, rg.Point):
        coords, z = _fmt_coords([geom.Location])
        return f"POINT{z} ({coords})"
    elif isinstance(geom, rg.Line):
        coords, z = _fmt_coords([geom.From, geom.To])
        return f"LINESTRING{z} ({coords})"
    elif isinstance(geom, rg.LineCurve):
        p0 = geom.PointAt(geom.Domain.Min)
        p1 = geom.PointAt(geom.Domain.Max)
        coords, z = _fmt_coords([p0, p1])
        return f"LINESTRING{z} ({coords})"
    elif isinstance(geom, rg.Polyline):
        if len(geom) == 0:
            return None
        coords, z = _fmt_coords(geom)
        return f"POLYGON{z} (({coords}))" if geom.IsClosed else f"LINESTRING{z} ({coords})"
    elif isinstance(geom, rg.PolylineCurve):
        ok, poly = geom.TryGetPolyline()
        if not ok or len(poly) == 0:
            return None
        coords, z = _fmt_coords(poly)
        return f"POLYGON{z} (({coords}))" if poly.IsClosed else f"LINESTRING{z} ({coords})"
    elif isinstance(geom, rg.Curve):
        # Try polyline extraction first (fastest path for polylines/arcs etc.)
        ok, poly = geom.TryGetPolyline()
        if ok and len(poly) > 0:
            coords, z = _fmt_coords(poly)
            return f"POLYGON{z} (({coords}))" if poly.IsClosed else f"LINESTRING{z} ({coords})"
        # Fallback: approximate with many sample points
        params = geom.DivideByLength(1.0, True)
        if params:
            pts = [geom.PointAt(t) for t in params]
            if geom.IsClosed:
                pts.append(pts[0])
            coords, z = _fmt_coords(pts)
            if geom.IsClosed:
                return f"POLYGON{z} (({coords}))"
            return f"LINESTRING{z} ({coords})"
    elif isinstance(geom, rg.Brep):
        for face in geom.Faces:
            loop = face.OuterLoop
            if loop:
                crv = loop.To3dCurve()
                if crv:
                    ok, poly_out = crv.TryGetPolyline()
                    if ok and len(poly_out) > 0:
                        coords, z = _fmt_coords(poly_out)
                        return f"POLYGON{z} (({coords}))"
        # Edge fallback
        edges = geom.GetEdges()
        if edges:
            pts_list = []
            for e in edges:
                pts_list.append(e.PointAtStart)
            pts_list.append(e.PointAtEnd)
            if len(pts_list) >= 4:
                coords, z = _fmt_coords(pts_list)
                return f"POLYGON{z} (({coords}))"
    elif isinstance(geom, rg.Mesh):
        outlines = rg.Mesh.GetOutlines(geom)
        if outlines and len(outlines) > 0:
            for crv in outlines:
                ok, poly_out = crv.TryGetPolyline()
                if ok and len(poly_out) > 0:
                    coords, z = _fmt_coords(poly_out)
                    return f"POLYGON{z} (({coords}))"

    return None
