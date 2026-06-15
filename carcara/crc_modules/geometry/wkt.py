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