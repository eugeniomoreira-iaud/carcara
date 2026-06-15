"""Rhino-dependent helpers for CRC_CurveDisplay.

WARNING: This module imports RhinoCommon (Rhino.Geometry). It must NEVER be
imported from unit tests or plain CPython environments. All pytest-importable
logic lives in ``crc_modules.geometry.dash``.
"""

from __future__ import annotations


def apply_dash_pattern(curve, pattern) -> list:
    """Apply a dash-gap pattern to a RhinoCommon Curve.

    Mirrors C# ``ApplyDashPattern`` exactly:

    - ``pattern`` is ``None`` or empty → return ``[curve]``
    - Walk the curve by arc length, cycling through pattern entries (dash, gap,
      dash, gap, …). ``index`` increments once per entry consumed, wrapping with
      ``if index >= len(pattern): index = 0``, matching the C# ``index++`` +
      bounds-wrap pattern.
    - ``offset1`` is clamped to ``curveLength`` before trimming.
    - Non-``None`` Trim results are appended; ``None`` trims are silently dropped.
    - Loop breaks when ``offset0 >= curveLength`` after advancing past the gap.

    Parameters
    ----------
    curve:
        A ``Rhino.Geometry.Curve`` instance.
    pattern:
        ``list[float]`` from ``crc_modules.geometry.dash.parse_dash_pattern``,
        or ``None`` / ``[]`` for a solid line.

    Returns
    -------
    list of ``Rhino.Geometry.Curve``
        Dash segments. Empty only if the curve is zero-length.
    """
    if not pattern:
        return [curve]

    import Rhino.Geometry as rg  # noqa: PLC0415 — deferred Rhino import

    curve_length = curve.GetLength()
    dashes: list = []

    offset0 = 0.0
    index = 0

    while True:
        # consume dash
        dash_length = pattern[index]
        index += 1
        if index >= len(pattern):
            index = 0

        offset1 = offset0 + dash_length
        if offset1 > curve_length:
            offset1 = curve_length

        ok0, t0 = curve.LengthParameter(offset0)
        ok1, t1 = curve.LengthParameter(offset1)

        segment = curve.Trim(t0, t1)
        if segment is not None:
            dashes.append(segment)

        # consume gap
        gap_length = pattern[index]
        index += 1
        if index >= len(pattern):
            index = 0

        offset0 = offset1 + gap_length

        if offset0 >= curve_length:
            break

    return dashes
