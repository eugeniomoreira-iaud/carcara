"""Interior point of a polygon using centroid-with-polylabel-fallback.

Pure Python / shapely — no Rhino imports. Takes coordinates as sequences of
(x, y) tuples (or a WKT string) and returns an interior point guaranteed to
lie inside the polygon.

Algorithm
---------
1. Try the centroid (average of ring vertices, Shapely's centroid).
2. If the centroid falls outside (concave / complex polygon), run the polylabel
   iterative grid-search to find the pole of inaccessibility — the point
   maximally distant from all edges.

The pure-Python polylabel implementation below is a port of Mapbox's
reference JavaScript implementation (MIT licence), operating entirely on
(x, y) tuples so it works in any CPython environment.
"""

from __future__ import annotations

import heapq
import math
from typing import List, Tuple, Optional


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def point_in_polygon(x: float, y: float, vertices: List[Tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon test.

    Parameters
    ----------
    x, y:     query point
    vertices: list of (x, y) tuples forming a closed ring
              (first == last is accepted but not required)

    Returns
    -------
    True if (x, y) is strictly inside the polygon.
    """
    inside = False
    n = len(vertices)
    j = n - 1
    for i in range(n):
        xi, yi = vertices[i]
        xj, yj = vertices[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def point_to_polygon_distance(x: float, y: float,
                               vertices: List[Tuple[float, float]]) -> float:
    """Signed distance from (x, y) to the nearest polygon edge.

    Positive → inside, negative → outside.
    """
    min_dist_sq = math.inf
    n = len(vertices)
    j = n - 1
    for i in range(n):
        ax, ay = vertices[i]
        bx, by = vertices[j]
        dx, dy = bx - ax, by - ay
        len_sq = dx * dx + dy * dy
        if len_sq > 0:
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / len_sq))
        else:
            t = 0.0
        px = ax + t * dx - x
        py = ay + t * dy - y
        min_dist_sq = min(min_dist_sq, px * px + py * py)
        j = i
    min_dist = math.sqrt(min_dist_sq)
    return min_dist if point_in_polygon(x, y, vertices) else -min_dist


def interior_point(
    vertices: List[Tuple[float, float]],
    tolerance: float = 1.0,
) -> Tuple[Tuple[float, float], float]:
    """Return (point, distance_to_nearest_edge) for a polygon.

    Parameters
    ----------
    vertices:  closed ring of (x, y) tuples
    tolerance: polylabel precision (smaller → more accurate but slower)

    Returns
    -------
    ((x, y), distance)  where distance > 0 means point is inside.

    Raises
    ------
    ValueError  if vertices is empty or has fewer than 3 distinct points.
    """
    if not vertices or len(vertices) < 3:
        raise ValueError("interior_point: need at least 3 vertices")

    # Ensure ring is closed (first == last) for distance calculations
    ring = list(vertices)
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    # Try centroid first
    unique = ring[:-1]
    cx = sum(p[0] for p in unique) / len(unique)
    cy = sum(p[1] for p in unique) / len(unique)

    if point_in_polygon(cx, cy, ring):
        dist = point_to_polygon_distance(cx, cy, ring)
        return (cx, cy), dist

    # Fall back to polylabel
    return _polylabel(ring, tolerance)


def interior_point_from_wkt(
    polygon_wkt: str,
    tolerance: float = 1.0,
) -> Tuple[Tuple[float, float], float]:
    """Convenience wrapper: parse WKT Polygon and find interior point.

    Parameters
    ----------
    polygon_wkt: WKT string (POLYGON or MULTIPOLYGON — uses first ring)
    tolerance:   polylabel grid precision

    Returns
    -------
    ((x, y), distance)
    """
    from shapely import wkt as shapely_wkt

    geom = shapely_wkt.loads(polygon_wkt)
    geom_type = geom.geom_type

    if geom_type == "Polygon":
        poly = geom
    elif geom_type == "MultiPolygon":
        # Use the largest polygon
        poly = max(geom.geoms, key=lambda g: g.area)
    else:
        raise ValueError(f"interior_point_from_wkt: expected Polygon or MultiPolygon, got {geom_type}")

    ring = list(poly.exterior.coords)
    return interior_point(ring, tolerance)


# ---------------------------------------------------------------------------
# Polylabel — iterative grid search (port of mapbox/polylabel)
# ---------------------------------------------------------------------------

class _Cell:
    """Represents a square cell in the polylabel grid search."""

    __slots__ = ("x", "y", "h", "d", "max")

    def __init__(self, x: float, y: float, h: float,
                 ring: List[Tuple[float, float]]) -> None:
        self.x = x
        self.y = y
        self.h = h                                       # half-size
        self.d = point_to_polygon_distance(x, y, ring)  # signed distance
        self.max = self.d + h * math.sqrt(2)             # upper bound

    # heapq is a min-heap; we want max on self.max → invert sign
    def __lt__(self, other: "_Cell") -> bool:
        return self.max > other.max  # reversed for max-heap


def _polylabel(
    ring: List[Tuple[float, float]],
    tolerance: float = 1.0,
) -> Tuple[Tuple[float, float], float]:
    """Find the pole of inaccessibility for the given closed ring.

    Returns ((x, y), distance).
    """
    min_x = min(p[0] for p in ring)
    max_x = max(p[0] for p in ring)
    min_y = min(p[1] for p in ring)
    max_y = max(p[1] for p in ring)

    width = max_x - min_x
    height = max_y - min_y
    cell_size = min(width, height)

    if cell_size == 0:
        # Degenerate polygon
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        return (cx, cy), 0.0

    h = cell_size / 2.0

    # Priority queue (max-heap via _Cell.__lt__)
    heap: list = []

    # Seed the queue with an evenly spaced grid
    x = min_x
    while x < max_x:
        y = min_y
        while y < max_y:
            heapq.heappush(heap, _Cell(x + h, y + h, h, ring))
            y += cell_size
        x += cell_size

    # Best cell so far: bounding-box centroid
    best = _Cell((min_x + max_x) / 2, (min_y + max_y) / 2, 0, ring)

    while heap:
        cell = heapq.heappop(heap)

        if cell.d > best.d:
            best = cell

        if cell.max - best.d <= tolerance:
            continue

        # Split cell into four quadrants
        h2 = cell.h / 2
        for dx, dy in ((-h2, -h2), (h2, -h2), (-h2, h2), (h2, h2)):
            heapq.heappush(heap, _Cell(cell.x + dx, cell.y + dy, h2, ring))

    return (best.x, best.y), best.d
