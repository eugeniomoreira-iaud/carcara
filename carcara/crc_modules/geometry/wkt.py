from shapely import wkt as shapely_wkt
from shapely.geometry import MultiPoint, MultiLineString, MultiPolygon
from shapely.geometry.base import BaseGeometry
from typing import List, Tuple, Union


def wkt_to_shapely(wkt_str: str) -> BaseGeometry:
    """Parse WKT string to shapely geometry object."""
    return shapely_wkt.loads(wkt_str)


def shapely_to_wkt(geom: BaseGeometry) -> str:
    """Convert shapely geometry to WKT string."""
    return shapely_wkt.dumps(geom)


def wkt_list_to_points(wkt_list: List[str]) -> List[Tuple[float, float]]:
    """Returns list of (x, y) tuples from a list of WKT Point strings."""
    points = []
    for wkt_str in wkt_list:
        geom = wkt_to_shapely(wkt_str)
        if geom.geom_type == "Point":
            points.append((geom.x, geom.y))
    return points


def split_multipart_wkt(wkt_str: str) -> List[str]:
    """Split a MULTI* WKT into individual geometry WKTs.
    Returns list of WKT strings (single parts)."""
    geom = wkt_to_shapely(wkt_str)
    if geom.geom_type.startswith("Multi"):
        parts = list(geom.geoms)
        return [shapely_to_wkt(p) for p in parts]
    return [wkt_str]


def is_multipart_wkt(wkt_str: str) -> bool:
    """Check if WKT is a MULTI* type."""
    return wkt_str.strip().upper().startswith("MULTI")


def classify_wkt(wkt_str: str) -> str:
    """Return the WKT geometry type token in uppercase.

    e.g. 'POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT',
    'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION'.
    """
    return wkt_to_shapely(wkt_str).geom_type.upper()


def _base_type(wkt_str: str) -> str:
    """Return the singular base type for a WKT (strips MULTI prefix).
    e.g. 'MULTIPOLYGON' -> 'POLYGON', 'POLYGON' -> 'POLYGON'.
    """
    t = wkt_to_shapely(wkt_str).geom_type.upper()
    if t.startswith("MULTI"):
        return t[5:]  # strip 'MULTI'
    return t


def combine_wkts(wkts: List[str]) -> str:
    """Combine a list of WKT geometries into a single WKT.

    - 1 item -> returned as-is.
    - >1 items -> MULTI<base> built from all parts (same base type required).
    - Mixed base types across the list -> ValueError.
    """
    if not wkts:
        raise ValueError("combine_wkts: empty input")
    if len(wkts) == 1:
        return wkts[0]

    # Verify all have the same base type
    base_types = {_base_type(w) for w in wkts}
    if len(base_types) != 1:
        raise ValueError(f"combine_wkts: mixed geometry base types: {base_types}")

    # Parse all parts; each may already be MULTI — flatten to single members
    all_geoms = []
    for w in wkts:
        g = wkt_to_shapely(w)
        if g.geom_type.startswith("Multi"):
            all_geoms.extend(list(g.geoms))
        else:
            all_geoms.append(g)

    base = base_types.pop()
    if base == "POINT":
        multi = MultiPoint(all_geoms)
    elif base == "LINESTRING":
        multi = MultiLineString(all_geoms)
    elif base == "POLYGON":
        multi = MultiPolygon(all_geoms)
    else:
        raise ValueError(f"combine_wkts: unsupported base type '{base}'")
    return shapely_to_wkt(multi)


def detect_wkt_type(wkts: List[str]) -> str:
    """Return the PostGIS geometry type token for a list of WKTs.

    Strict: raises ValueError if base types differ across the list.
    Returns MULTI<base> if ANY item is multipart, else the singular token
    (POINT / LINESTRING / POLYGON).
    """
    if not wkts:
        raise ValueError("detect_wkt_type: empty input")

    base_types = {_base_type(w) for w in wkts}
    if len(base_types) != 1:
        raise ValueError(f"detect_wkt_type: mixed geometry base types: {base_types}")

    base = next(iter(base_types))
    # Return MULTI if any WKT is already multipart
    any_multi = any(wkt_to_shapely(w).geom_type.upper().startswith("MULTI") for w in wkts)
    return f"MULTI{base}" if any_multi else base


def promote_to_multi(wkt: str, target_type: str) -> str:
    """Promote a single-part WKT to a MULTI* WKT if target_type is a MULTI* type.

    If wkt is already a MULTI, it is returned as-is.
    If target_type is NOT a MULTI, the wkt is returned unchanged.
    """
    upper_target = target_type.strip().upper()
    if not upper_target.startswith("MULTI"):
        return wkt

    geom = wkt_to_shapely(wkt)
    if geom.geom_type.upper().startswith("MULTI"):
        return wkt  # already multi

    # Wrap the single geometry in a multi-geometry with one member
    base = geom.geom_type
    if base == "Point":
        multi = MultiPoint([geom])
    elif base == "LineString":
        multi = MultiLineString([geom])
    elif base == "Polygon":
        multi = MultiPolygon([geom])
    else:
        raise ValueError(f"promote_to_multi: unsupported geometry type '{base}'")
    return shapely_to_wkt(multi)


def combine_to_multipart(wkt_list: List[str]) -> str:
    """Merge a list of uniform single-part WKTs into one MULTI* WKT.

    All inputs must be the same base type (all Point, all LineString,
    or all Polygon). Raises ValueError on mixed or unsupported types.
    """
    if not wkt_list:
        raise ValueError("combine_to_multipart: empty input")

    geoms = [wkt_to_shapely(w) for w in wkt_list]
    types = {g.geom_type for g in geoms}
    if len(types) != 1:
        raise ValueError("combine_to_multipart: mixed geometry types: %s" % types)

    base = types.pop()
    if base == "Point":
        multi = MultiPoint(geoms)
    elif base == "LineString":
        multi = MultiLineString(geoms)
    elif base == "Polygon":
        multi = MultiPolygon(geoms)
    else:
        raise ValueError("combine_to_multipart: cannot multipart type '%s'" % base)
    return shapely_to_wkt(multi)