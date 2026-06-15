"""Tests for crc_modules.geometry.polylabel (pure Python, no Rhino)."""
import math
import pytest

from crc_modules.geometry.polylabel import (
    point_in_polygon,
    point_to_polygon_distance,
    interior_point,
    interior_point_from_wkt,
)


# ---------------------------------------------------------------------------
# Fixtures: simple geometries
# ---------------------------------------------------------------------------

SQUARE = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]          # closed
TRIANGLE = [(0, 0), (6, 0), (3, 5), (0, 0)]                 # closed

# L-shaped (concave) polygon — centroid falls outside the L
L_SHAPE = [
    (0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4), (0, 0)
]

# Thin C / horseshoe polygon — centroid clearly outside
HORSESHOE = [
    (0, 0), (6, 0), (6, 1), (1, 1), (1, 4), (6, 4), (6, 5),
    (0, 5), (0, 0)
]


# ---------------------------------------------------------------------------
# point_in_polygon
# ---------------------------------------------------------------------------

class TestPointInPolygon:
    def test_center_of_square_inside(self):
        assert point_in_polygon(2, 2, SQUARE) is True

    def test_outside_square(self):
        assert point_in_polygon(5, 5, SQUARE) is False

    def test_center_of_triangle_inside(self):
        # centroid of triangle = (3, 5/3) ≈ (3, 1.67)
        assert point_in_polygon(3, 1.6, TRIANGLE) is True

    def test_far_outside_triangle(self):
        assert point_in_polygon(10, 10, TRIANGLE) is False

    def test_concave_polygon_inside_arm(self):
        # A point inside one arm of the L
        assert point_in_polygon(1, 1, L_SHAPE) is True

    def test_concave_polygon_in_hole(self):
        # The "missing" corner of the L (3, 3) is outside
        assert point_in_polygon(3, 3, L_SHAPE) is False


# ---------------------------------------------------------------------------
# point_to_polygon_distance
# ---------------------------------------------------------------------------

class TestPointToPolygonDistance:
    def test_center_square_positive(self):
        d = point_to_polygon_distance(2, 2, SQUARE)
        assert d > 0, "centroid should be inside (positive distance)"
        # Nearest edge is 2 units away for a 4×4 square centred at (2,2)
        assert abs(d - 2.0) < 1e-9

    def test_outside_negative(self):
        d = point_to_polygon_distance(5, 5, SQUARE)
        assert d < 0, "outside point should give negative distance"

    def test_near_boundary(self):
        # Point very close to but strictly inside
        d = point_to_polygon_distance(0.01, 0.01, SQUARE)
        # closest edge ≈ 0.01
        assert 0 < d < 0.02


# ---------------------------------------------------------------------------
# interior_point
# ---------------------------------------------------------------------------

class TestInteriorPoint:
    def test_convex_polygon_returns_inside(self):
        pt, dist = interior_point(SQUARE)
        x, y = pt
        assert point_in_polygon(x, y, SQUARE), "returned point must be inside"
        assert dist > 0

    def test_triangle_returns_inside(self):
        ring = list(TRIANGLE)
        pt, dist = interior_point(ring)
        x, y = pt
        assert point_in_polygon(x, y, TRIANGLE), "must be inside triangle"
        assert dist > 0

    def test_concave_l_shape_returns_inside(self):
        # centroid of L-shape is at (1.14, 2.29) approximately — let's check
        # it falls outside the L: centroid_x = avg(0+4+4+2+2+0)/6 ≈ 2.0
        # That IS actually inside this L shape, so we just verify the result
        pt, dist = interior_point(L_SHAPE)
        x, y = pt
        assert point_in_polygon(x, y, L_SHAPE), "must be inside L-shape"
        assert dist > 0

    def test_horseshoe_concave_returns_inside(self):
        # Horseshoe: centroid likely falls in the middle opening — polylabel
        # must rescue this case
        pt, dist = interior_point(HORSESHOE, tolerance=0.1)
        x, y = pt
        assert point_in_polygon(x, y, HORSESHOE), "must be inside horseshoe"
        assert dist > 0

    def test_too_few_vertices_raises(self):
        with pytest.raises(ValueError):
            interior_point([(0, 0), (1, 1)])  # only 2 points

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            interior_point([])


# ---------------------------------------------------------------------------
# interior_point_from_wkt
# ---------------------------------------------------------------------------

class TestInteriorPointFromWkt:
    def test_simple_square_wkt(self):
        wkt = "POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0))"
        pt, dist = interior_point_from_wkt(wkt)
        x, y = pt
        assert 0 < x < 4 and 0 < y < 4
        assert dist > 0

    def test_concave_polygon_wkt(self):
        # C / horseshoe as WKT
        wkt = (
            "POLYGON ((0 0, 6 0, 6 1, 1 1, 1 4, 6 4, 6 5, 0 5, 0 0))"
        )
        pt, dist = interior_point_from_wkt(wkt, tolerance=0.05)
        x, y = pt
        # Load ring manually for containment test
        from shapely import wkt as swkt
        geom = swkt.loads(wkt)
        ring = list(geom.exterior.coords)
        assert point_in_polygon(x, y, ring), "WKT interior point must be inside"
        assert dist > 0

    def test_multipolygon_uses_largest(self):
        # Two polygons — interior point should come from the larger one
        wkt = (
            "MULTIPOLYGON (((0 0, 2 0, 2 2, 0 2, 0 0)), "
            "((10 10, 20 10, 20 20, 10 20, 10 10)))"
        )
        pt, dist = interior_point_from_wkt(wkt)
        x, y = pt
        # Larger polygon spans 10–20
        assert 10 <= x <= 20 and 10 <= y <= 20

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            interior_point_from_wkt("POINT (1 1)")
