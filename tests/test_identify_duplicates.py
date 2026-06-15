"""Tests for crc_modules.geometry.duplicates (pure Python, no Rhino)."""
import pytest

from crc_modules.geometry.duplicates import (
    identify_duplicates,
    identify_duplicates_flat,
)


# ---------------------------------------------------------------------------
# Fixtures: coordinate rings
# ---------------------------------------------------------------------------

SQUARE_0 = [(0, 0), (4, 0), (4, 4), (0, 4)]           # open ring
SQUARE_0_CLOSED = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]   # closed ring

# Rotated start-point (same vertices, different start)
SQUARE_ROT = [(4, 0), (4, 4), (0, 4), (0, 0)]

# Reversed direction
SQUARE_REV = [(0, 4), (4, 4), (4, 0), (0, 0)]

# Different polygon
TRIANGLE = [(0, 0), (5, 0), (2.5, 4)]

# Another distinct polygon
RECT = [(0, 0), (8, 0), (8, 2), (0, 2)]


class TestIdentifyDuplicates:
    # --- basic non-duplicate case ---

    def test_no_duplicates(self):
        result = identify_duplicates([SQUARE_0, TRIANGLE, RECT])
        assert result == []

    def test_empty_list(self):
        assert identify_duplicates([]) == []

    def test_single_polyline_no_duplicates(self):
        assert identify_duplicates([SQUARE_0]) == []

    # --- exact duplicates ---

    def test_exact_duplicate_detected(self):
        polys = [SQUARE_0, TRIANGLE, SQUARE_0]
        groups = identify_duplicates(polys)
        # One group: index 2 duplicates index 0
        assert len(groups) == 1
        assert 2 in groups[0]
        assert 0 not in groups[0]   # first occurrence excluded

    def test_multiple_exact_duplicates_in_one_group(self):
        polys = [SQUARE_0, SQUARE_0, SQUARE_0]
        groups = identify_duplicates(polys)
        assert len(groups) == 1
        # Duplicates: indexes 1 and 2
        assert set(groups[0]) == {1, 2}

    # --- rotation-invariance ---

    def test_rotated_start_detected_as_duplicate(self):
        polys = [SQUARE_0, SQUARE_ROT]
        groups = identify_duplicates(polys)
        assert len(groups) == 1
        assert 1 in groups[0]

    # --- direction-invariance ---

    def test_reversed_direction_detected_as_duplicate(self):
        polys = [SQUARE_0, SQUARE_REV]
        groups = identify_duplicates(polys)
        assert len(groups) == 1
        assert 1 in groups[0]

    def test_rotated_and_reversed_detected_as_duplicate(self):
        # A rotation of the reversed sequence
        # SQUARE_REV = [(0,4),(4,4),(4,0),(0,0)] rotated by 1
        rotated_rev = [(4, 4), (4, 0), (0, 0), (0, 4)]
        polys = [SQUARE_0, rotated_rev]
        groups = identify_duplicates(polys)
        assert len(groups) == 1
        assert 1 in groups[0]

    # --- closed-ring handling ---

    def test_closed_and_open_ring_are_same(self):
        # SQUARE_0_CLOSED has the closing duplicate vertex; should match SQUARE_0
        polys = [SQUARE_0, SQUARE_0_CLOSED]
        groups = identify_duplicates(polys)
        assert len(groups) == 1
        assert 1 in groups[0]

    # --- multiple groups ---

    def test_two_independent_duplicate_groups(self):
        polys = [
            SQUARE_0,    # 0 — first SQUARE
            TRIANGLE,    # 1 — first TRIANGLE
            SQUARE_ROT,  # 2 — dup of SQUARE
            TRIANGLE,    # 3 — dup of TRIANGLE
        ]
        groups = identify_duplicates(polys)
        assert len(groups) == 2
        # groups may be in any order, so use flat check
        flat = [idx for g in groups for idx in g]
        assert 2 in flat
        assert 3 in flat
        assert 0 not in flat
        assert 1 not in flat

    # --- None entries ---

    def test_none_entry_skipped(self):
        polys = [SQUARE_0, None, SQUARE_ROT]
        # None is skipped gracefully; index 2 is still a dup of index 0
        groups = identify_duplicates(polys)
        assert len(groups) == 1
        assert 2 in groups[0]

    # --- degenerate polylines ---

    def test_single_point_skipped(self):
        polys = [[(0, 0)], SQUARE_0]
        # One-point "polyline" has no valid signature; no group formed
        groups = identify_duplicates(polys)
        assert groups == []

    def test_two_point_polylines_matched(self):
        line = [(0, 0), (1, 1)]
        line_rev = [(1, 1), (0, 0)]
        polys = [line, line_rev]
        groups = identify_duplicates(polys)
        assert len(groups) == 1
        assert 1 in groups[0]

    # --- tolerance sensitivity ---

    def test_near_duplicate_within_tolerance(self):
        # Slightly shifted SQUARE_0 (< default tolerance 1e-6)
        shifted = [(0 + 1e-8, 0), (4, 0), (4, 4), (0, 4)]
        polys = [SQUARE_0, shifted]
        groups = identify_duplicates(polys, tolerance=1e-6)
        assert len(groups) == 1   # treated as identical

    def test_near_duplicate_outside_tolerance(self):
        # Shifted by 0.1 — clearly different at default tolerance
        shifted = [(0.1, 0), (4, 0), (4, 4), (0, 4)]
        polys = [SQUARE_0, shifted]
        groups = identify_duplicates(polys, tolerance=1e-6)
        assert groups == []   # not duplicates


class TestIdentifyDuplicatesFlat:
    def test_flat_returns_sorted_list(self):
        polys = [SQUARE_0, TRIANGLE, SQUARE_ROT, TRIANGLE]
        flat = identify_duplicates_flat(polys)
        assert isinstance(flat, list)
        # Duplicates: index 2 (SQUARE dup), index 3 (TRIANGLE dup)
        assert 2 in flat
        assert 3 in flat
        assert flat == sorted(flat)

    def test_no_duplicates_returns_empty(self):
        assert identify_duplicates_flat([SQUARE_0, TRIANGLE]) == []
