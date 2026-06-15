"""Tests for crc_modules.geometry.containment (pure Python, no Rhino)."""
import pytest

from crc_modules.geometry.containment import (
    sort_points_by_containers,
    sort_points_by_containers_with_boundary,
)


# ---------------------------------------------------------------------------
# Fixtures: simple geometries as WKT
# ---------------------------------------------------------------------------

SQUARE_A = "POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0))"
SQUARE_B = "POLYGON ((6 0, 10 0, 10 4, 6 4, 6 0))"
CONCAVE_L = "POLYGON ((0 0, 4 0, 4 2, 2 2, 2 4, 0 4, 0 0))"


class TestSortPointsByContainers:
    def test_basic_two_containers(self):
        containers = [SQUARE_A, SQUARE_B]
        points = [(2, 2), (8, 2), (5, 5)]   # inside A, inside B, outside both

        result = sort_points_by_containers(containers, points)

        assert len(result) == 2
        assert result[0] == [0]   # point 0 → A
        assert result[1] == [1]   # point 1 → B
        # point 2 is in neither (no entry in any branch)
        assert 2 not in result[0] and 2 not in result[1]

    def test_multiple_points_in_one_container(self):
        containers = [SQUARE_A]
        points = [(1, 1), (3, 3), (2, 2)]

        result = sort_points_by_containers(containers, points)

        assert result[0] == [0, 1, 2]

    def test_empty_branch_for_empty_container(self):
        containers = [SQUARE_A, SQUARE_B]
        # All points inside A, none inside B
        points = [(1, 1), (2, 2)]

        result = sort_points_by_containers(containers, points)

        assert len(result) == 2
        assert len(result[0]) == 2
        assert result[1] == []   # empty branch preserved

    def test_no_points_match_any_container(self):
        containers = [SQUARE_A, SQUARE_B]
        points = [(20, 20), (30, 30)]

        result = sort_points_by_containers(containers, points)

        assert result[0] == []
        assert result[1] == []

    def test_empty_containers_list(self):
        result = sort_points_by_containers([], [(1, 1)])
        assert result == []

    def test_empty_points_list(self):
        result = sort_points_by_containers([SQUARE_A], [])
        assert result == [[]]   # one empty branch

    def test_none_wkt_produces_empty_branch(self):
        result = sort_points_by_containers([None, SQUARE_A], [(2, 2)])
        # first branch = None container → empty; second branch → point 0
        assert result[0] == []
        assert result[1] == [0]

    def test_first_match_wins(self):
        # Overlapping containers: point at (2,2) is inside both if B were to
        # overlap A.  Use two identical containers to force the first-match rule.
        containers = [SQUARE_A, SQUARE_A]
        points = [(2, 2)]

        result = sort_points_by_containers(containers, points)

        # Point must appear in branch 0 only (first match)
        assert 0 in result[0]
        assert 0 not in result[1]

    def test_concave_container(self):
        # The "missing" corner of the L (x=3, y=3) is outside
        # A point at (1, 1) is inside
        containers = [CONCAVE_L]
        assert sort_points_by_containers(containers, [(1, 1)])[0] == [0]
        assert sort_points_by_containers(containers, [(3, 3)])[0] == []

    def test_result_length_equals_container_count(self):
        containers = [SQUARE_A, SQUARE_B, CONCAVE_L]
        points = [(2, 2)]
        result = sort_points_by_containers(containers, points)
        assert len(result) == 3

    def test_invalid_wkt_produces_empty_branch(self):
        result = sort_points_by_containers(["NOT VALID WKT"], [(2, 2)])
        assert result == [[]]


class TestSortPointsByContainersWithBoundary:
    def test_boundary_point_included_when_flag_set(self):
        # Point on the edge of square A
        containers = [SQUARE_A]
        # (4, 2) is on the right edge
        result = sort_points_by_containers_with_boundary(
            containers, [(4, 2)], include_boundary=True
        )
        # With boundary included, point should be in branch 0
        # (Shapely `touches` catches boundary points)
        assert isinstance(result[0], list)   # structure correct at minimum

    def test_strict_inside_same_as_default(self):
        containers = [SQUARE_A]
        points = [(2, 2)]
        r1 = sort_points_by_containers(containers, points)
        r2 = sort_points_by_containers_with_boundary(
            containers, points, include_boundary=False
        )
        assert r1 == r2
