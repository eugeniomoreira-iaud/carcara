from shapely import wkt as shapely_wkt
from shapely.geometry import BaseGeometry
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