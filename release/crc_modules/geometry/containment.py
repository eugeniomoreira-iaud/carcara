"""Point-in-polygon containment sorting.

Pure Python / shapely — no Rhino imports.

Groups a flat list of (x, y) points by which container polygon (from a list
of polygon geometries expressed as coordinate rings or WKT strings) contains
them.  Returns one list of integer indexes per container, with an empty list
for containers that hold no points — matching the legacy SortByContainer
DataTree structure exactly.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple, Union

from shapely.geometry import Point, Polygon
from shapely import wkt as shapely_wkt


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sort_points_by_containers(
    container_wkts: Sequence[str],
    point_coords: Sequence[Tuple[float, float]],
) -> List[List[int]]:
    """Group point indexes by the first container polygon that contains them.

    Parameters
    ----------
    container_wkts:
        Ordered sequence of WKT strings (POLYGON or MULTIPOLYGON).
    point_coords:
        Flat list of (x, y) tuples — same order as the points the caller
        feeds to the GH component.

    Returns
    -------
    A list of length ``len(container_wkts)``.  Each element is a (possibly
    empty) list of integer indexes into ``point_coords`` for points contained
    by that container.

    Notes
    -----
    * Containment is tested with Shapely's ``Polygon.contains(Point(…))``,
      which treats the boundary as outside (``inside`` only).
    * A point is assigned to the **first** container that contains it; it will
      not appear in multiple branches.
    * None / invalid WKTs produce empty branches without raising.
    """
    # Parse container polygons (None for invalid entries)
    containers: List[Optional[Polygon]] = []
    for wkt_str in container_wkts:
        if not wkt_str:
            containers.append(None)
            continue
        try:
            geom = shapely_wkt.loads(wkt_str)
            if geom.geom_type == "MultiPolygon":
                # Treat as union so containment works across parts
                from shapely.ops import unary_union
                geom = unary_union(list(geom.geoms))
            containers.append(geom if not geom.is_empty else None)
        except Exception:
            containers.append(None)

    # Initialise output: one empty list per container
    result: List[List[int]] = [[] for _ in containers]

    for pt_idx, (px, py) in enumerate(point_coords):
        pt = Point(px, py)
        for c_idx, container in enumerate(containers):
            if container is None:
                continue
            if container.contains(pt):
                result[c_idx].append(pt_idx)
                break  # first-match only — matches legacy behaviour

    return result


def sort_points_by_containers_with_boundary(
    container_wkts: Sequence[str],
    point_coords: Sequence[Tuple[float, float]],
    include_boundary: bool = False,
) -> List[List[int]]:
    """Same as :func:`sort_points_by_containers` but optionally count
    boundary-points as contained.

    This variant exists so callers can tune boundary behaviour without
    changing the default API.

    Parameters
    ----------
    container_wkts:   see :func:`sort_points_by_containers`
    point_coords:     see :func:`sort_points_by_containers`
    include_boundary: if True, ``within`` (inside ∪ boundary) is used
                      instead of ``contains`` (strictly inside).
    """
    from shapely.ops import unary_union

    containers: List[Optional[Polygon]] = []
    for wkt_str in container_wkts:
        if not wkt_str:
            containers.append(None)
            continue
        try:
            geom = shapely_wkt.loads(wkt_str)
            if geom.geom_type == "MultiPolygon":
                geom = unary_union(list(geom.geoms))
            containers.append(geom if not geom.is_empty else None)
        except Exception:
            containers.append(None)

    result: List[List[int]] = [[] for _ in containers]

    for pt_idx, (px, py) in enumerate(point_coords):
        pt = Point(px, py)
        for c_idx, container in enumerate(containers):
            if container is None:
                continue
            hit = container.within(pt.buffer(0)) if include_boundary else container.contains(pt)
            # Use the simpler shapely predicate:
            if include_boundary:
                hit = pt.within(container) or container.touches(pt)
            else:
                hit = container.contains(pt)
            if hit:
                result[c_idx].append(pt_idx)
                break

    return result
