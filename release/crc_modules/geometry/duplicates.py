"""Duplicate polyline detection using normalised geometric signatures.

Pure Python — no Rhino imports.  Works on sequences of (x, y [, z]) tuples
and is fully pytest-importable in a plain CPython 3.11+ environment.

Algorithm
---------
For each polyline (list of coordinate tuples):

1. Remove the closing duplicate point if the ring is closed (first == last).
2. Round all coordinate values to the given tolerance.
3. Rotate the sequence so it starts at the lexicographically smallest vertex.
4. Take the minimum of the rotated sequence and its reverse — this canonical
   form is invariant to start-point choice AND traversal direction.
5. Group polylines by identical canonical signature.
6. Within each group, the first occurrence is kept; all subsequent indexes
   are duplicates.

Returns a list of groups (each group = list of integer duplicate indexes,
*excluding* the first occurrence in that group).
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

Coord = Tuple[float, ...]       # (x, y) or (x, y, z)
Ring = Sequence[Coord]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _round_coord(coord: Coord, factor: float) -> Coord:
    """Round all coordinate values by rounding to 1/tolerance precision."""
    return tuple(round(v * factor) / factor for v in coord)


def _min_rotation(pts: List[Coord]) -> List[Coord]:
    """Return the rotation of pts starting at the lexicographically smallest
    element (ties broken by the full rotated sequence)."""
    n = len(pts)
    # Find all indexes that equal the minimum value, then pick the one whose
    # rotated sequence is lexicographically smallest.
    min_val = min(pts)
    candidates = [i for i, p in enumerate(pts) if p == min_val]
    best = None
    for idx in candidates:
        rot = pts[idx:] + pts[:idx]
        if best is None or rot < best:
            best = rot
    return best  # type: ignore[return-value]


def _normalize_ring(ring: List[Coord], tolerance: float) -> Optional[tuple]:
    """Return the canonical (hashable) signature for a polyline ring.

    The canonical form is invariant to:
    * Starting point (rotation)
    * Traversal direction (reversal)

    Returns None if the ring has fewer than 2 distinct points after
    deduplication and rounding.
    """
    if not ring or len(ring) < 2:
        return None

    factor = 1.0 / tolerance

    # Remove closing duplicate
    pts = list(ring)
    if len(pts) > 1:
        r0 = _round_coord(pts[0], factor)
        r_last = _round_coord(pts[-1], factor)
        if r0 == r_last:
            pts = pts[:-1]

    if len(pts) < 2:
        return None

    # Round all coordinates
    rounded = [_round_coord(p, factor) for p in pts]

    # Canonical rotation of the forward sequence
    fwd = _min_rotation(rounded)

    # Canonical rotation of the reversed sequence
    rev = _min_rotation(list(reversed(rounded)))

    # Choose lexicographically smallest between the two → direction invariant
    canonical = tuple(min(fwd, rev))
    return canonical


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def identify_duplicates(
    polylines: Sequence[Ring],
    tolerance: float = 1e-6,
) -> List[List[int]]:
    """Find groups of duplicate polylines.

    Parameters
    ----------
    polylines:
        Sequence of polylines, where each polyline is a sequence of
        coordinate tuples ``(x, y)`` or ``(x, y, z)``.
    tolerance:
        Coordinates are rounded to this precision before comparison.
        Defaults to 1e-6 (same as Rhino's default model tolerance).

    Returns
    -------
    A list of duplicate groups.  Each group is a list of **integer indexes**
    into ``polylines`` for all duplicates *except* the first occurrence in
    the group.  Groups are ordered by the index of the first occurrence.

    Examples
    --------
    >>> groups = identify_duplicates([A, B, A_rotated, C, B_reversed])
    >>> groups
    [[2], [4]]   # index 2 duplicates A (first at 0); index 4 duplicates B (first at 1)
    """
    if not polylines:
        return []

    signature_to_first: dict = {}   # signature → index of first occurrence
    duplicates_by_first: dict = {}  # first_index → [duplicate indexes]

    for idx, ring in enumerate(polylines):
        if ring is None:
            continue
        sig = _normalize_ring(list(ring), tolerance)
        if sig is None:
            continue

        if sig not in signature_to_first:
            signature_to_first[sig] = idx
            duplicates_by_first[idx] = []
        else:
            first = signature_to_first[sig]
            duplicates_by_first[first].append(idx)

    # Return only groups that actually have duplicates, in order of first index
    result = []
    for first_idx in sorted(duplicates_by_first.keys()):
        group = duplicates_by_first[first_idx]
        if group:
            result.append(group)

    return result


def identify_duplicates_flat(
    polylines: Sequence[Ring],
    tolerance: float = 1e-6,
) -> List[int]:
    """Flat list of all duplicate indexes (all groups merged).

    Convenience wrapper when the caller doesn't need the group structure.
    """
    groups = identify_duplicates(polylines, tolerance)
    flat: List[int] = []
    for group in groups:
        flat.extend(group)
    return sorted(flat)
