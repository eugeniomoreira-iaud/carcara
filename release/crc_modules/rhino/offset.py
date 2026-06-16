"""Rhino-dependent curve offset helpers for CRC_OffsetPython.

This module runs ONLY inside Rhino 8's Grasshopper Python 3 environment.
It is excluded from pytest. Do not import from plain CPython.
"""

import Rhino.Geometry as rg

# Corner style mapping: int → CurveOffsetCornerStyle enum
CORNER_STYLE_MAP = {
    0: rg.CurveOffsetCornerStyle(0),    # None
    1: rg.CurveOffsetCornerStyle.Sharp,
    2: rg.CurveOffsetCornerStyle.Round,
    3: rg.CurveOffsetCornerStyle.Smooth,
    4: rg.CurveOffsetCornerStyle.Chamfer,
}

DEFAULT_TOLERANCE = 1e-6


def get_corner_style(style_int):
    """Map int to CurveOffsetCornerStyle enum, defaulting to Sharp (1).

    Args:
        style_int (int): 0=None, 1=Sharp, 2=Round, 3=Smooth, 4=Chamfer

    Returns:
        rg.CurveOffsetCornerStyle: Corresponding enum value.
    """
    return CORNER_STYLE_MAP.get(int(style_int) if style_int is not None else 1,
                                rg.CurveOffsetCornerStyle.Sharp)


def offset_curve(curve, distance, corner_style, tolerance=DEFAULT_TOLERANCE):
    """Offset a single planar Rhino curve.

    Checks planarity via ``curve.TryGetPlane`` before calling
    ``curve.Offset(plane, distance, tolerance, corner_style)``.
    Returns the first element of the result list when successful.

    Args:
        curve: Rhino.Geometry.Curve to offset. May be None.
        distance (float): Offset distance (negative shrinks inward).
        corner_style: rg.CurveOffsetCornerStyle enum value.
        tolerance (float): Geometric tolerance. Defaults to DEFAULT_TOLERANCE.

    Returns:
        tuple: (offset_curve_or_None, error_message_or_None)
    """
    if curve is None:
        return None, "Input curve is None"

    try:
        ok, plane = curve.TryGetPlane(tolerance)
        if not ok:
            return None, "Curve is non-planar"

        offsets = curve.Offset(plane, distance, tolerance, corner_style)
        if offsets and len(offsets) > 0:
            return offsets[0], None
        else:
            return None, "Offset operation returned no results"

    except Exception as e:
        return None, "Offset error: {}".format(e)
