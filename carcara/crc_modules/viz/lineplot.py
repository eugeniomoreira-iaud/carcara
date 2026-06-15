"""
crc_modules/viz/lineplot.py
Pure-Python line chart math — no Rhino, no matplotlib.

Returns plain coordinate data (tuples/lists) that the GH code.py layer
converts to Rhino geometry and to SVG elements.

Public API
----------
create_lineplot(canvas, x_series, y_series, num_x_labels, num_y_labels,
                decimals, extension, label_distance, margin_x, margin_y,
                grid_x, grid_y)
    -> dict with keys:
        lines   : list of series; each series is a list of (x, y) canvas-space tuples
        axes    : list of ((x0,y0),(x1,y1)) line segment tuples
        x_pts   : list of (x, y) label-anchor tuples
        x_txt   : list of str
        y_pts   : list of (x, y) label-anchor tuples
        y_txt   : list of str
        grid_x  : list of ((x0,y0),(x1,y1)) vertical grid line tuples
        grid_y  : list of ((x0,y0),(x1,y1)) horizontal grid line tuples
        metadata: dict (num_series, x_range, y_range)

Canvas is passed as a plain tuple (origin_x, origin_y, width, height).

x_series / y_series: each is either
    - a flat list of numbers        -> treated as a single series
    - a list of lists of numbers    -> each sub-list is one series
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_series(data) -> list:
    """
    Return a list-of-lists from either a flat list or a list-of-lists.
    Empty input returns [].
    """
    if data is None:
        return []
    # Already a list-of-lists?
    try:
        first = next(iter(data), None)
    except TypeError:
        return []

    if first is None:
        return []

    if hasattr(first, "__iter__") and not isinstance(first, (str, bytes)):
        # List of lists
        result = []
        for sub in data:
            try:
                cleaned = [float(v) for v in sub if v is not None]
                if cleaned:
                    result.append(cleaned)
            except (TypeError, ValueError):
                pass
        return result
    else:
        # Flat list -> single series
        try:
            cleaned = [float(v) for v in data if v is not None]
            return [cleaned] if cleaned else []
        except (TypeError, ValueError):
            return []


def _label_positions(min_val: float, max_val: float, num_labels: int) -> list:
    if num_labels <= 0:
        return []
    if num_labels == 1:
        return [(min_val + max_val) / 2.0]
    step = (max_val - min_val) / float(num_labels - 1)
    return [min_val + i * step for i in range(num_labels)]


def _range_with_margin(data: list, margin_percent: float = 0.0):
    """Return (min_display, max_display, range_display) with optional margin."""
    d_min = min(data)
    d_max = max(data)
    if d_min == d_max:
        d_min -= 0.5
        d_max += 0.5
    d_range = d_max - d_min
    margin_val = margin_percent * d_range / 100.0
    min_disp = d_min - margin_val
    max_disp = d_max
    rng = max_disp - min_disp
    return min_disp, max_disp, rng


def _fmt(value: float, decimals: int) -> str:
    fmt = "{{:.{}f}}".format(decimals)
    return fmt.format(value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_lineplot(
    canvas: tuple,
    x_series,
    y_series,
    num_x_labels: int = 5,
    num_y_labels: int = 5,
    decimals: int = 1,
    extension: float = 0.0,
    label_distance: float = 10.0,
    margin_x: float = 0.0,
    margin_y: float = 0.0,
    grid_x: bool = False,
    grid_y: bool = False,
) -> dict:
    """
    Build all chart geometry for a line plot.

    Args:
        canvas        : (origin_x, origin_y, width, height)
        x_series      : flat list (single series) or list-of-lists (multi-series)
        y_series      : same shape as x_series
        num_x_labels  : number of X-axis tick labels (default 5)
        num_y_labels  : number of Y-axis tick labels (default 5)
        decimals      : decimal places for label text (default 1)
        extension     : how much axes extend beyond the canvas (default 0)
        label_distance: distance from axis to label anchor point (default 10)
        margin_x      : left margin as % of X data range (default 0)
        margin_y      : bottom margin as % of Y data range (default 0)
        grid_x        : draw vertical grid lines at X ticks (default False)
        grid_y        : draw horizontal grid lines at Y ticks (default False)

    Returns:
        dict with keys: lines, axes, x_pts, x_txt, y_pts, y_txt,
                        grid_x, grid_y, metadata

    Raises:
        ValueError: if no valid series pairs exist
    """
    origin_x, origin_y, canvas_width, canvas_height = canvas

    # --- parse inputs ------------------------------------------------------
    x_data_series = _parse_series(x_series)
    y_data_series = _parse_series(y_series)

    if not x_data_series or not y_data_series:
        raise ValueError("LinePlot requires non-empty X and Y data")

    if len(x_data_series) != len(y_data_series):
        raise ValueError(
            "X and Y must have the same number of series "
            "(got {} vs {})".format(len(x_data_series), len(y_data_series))
        )

    # Filter to series with matching lengths and >= 2 points
    valid_pairs = [
        (xs, ys)
        for xs, ys in zip(x_data_series, y_data_series)
        if len(xs) == len(ys) and len(xs) >= 2
    ]
    if not valid_pairs:
        raise ValueError("No valid series pairs found (each series needs >= 2 points and equal length)")

    # --- global data range (for axis labels) --------------------------------
    all_x = [v for xs, _ in valid_pairs for v in xs]
    all_y = [v for _, ys in valid_pairs for v in ys]

    x_min, x_max, x_range = _range_with_margin(all_x, margin_x)
    y_min, y_max, y_range = _range_with_margin(all_y, margin_y)

    # --- coordinate mapping helpers ----------------------------------------
    def map_x(v):
        return origin_x + ((v - x_min) / x_range) * canvas_width

    def map_y(v):
        return origin_y + ((v - y_min) / y_range) * canvas_height

    # --- build line series (canvas-space point lists) ----------------------
    lines = []
    for xs, ys in valid_pairs:
        pts = [(map_x(xv), map_y(yv)) for xv, yv in zip(xs, ys)]
        lines.append(pts)

    # --- axes ---------------------------------------------------------------
    x_ax = ((origin_x, origin_y), (origin_x + canvas_width + extension, origin_y))
    y_ax = ((origin_x, origin_y), (origin_x, origin_y + canvas_height + extension))
    axes = [x_ax, y_ax]

    # --- X-axis labels ------------------------------------------------------
    x_label_values = _label_positions(x_min, x_max, num_x_labels)
    x_pts = []
    x_txt = []
    for val in x_label_values:
        xp = map_x(val)
        yp = origin_y - label_distance
        x_pts.append((xp, yp))
        x_txt.append(_fmt(val, decimals))

    # --- Y-axis labels ------------------------------------------------------
    y_label_values = _label_positions(y_min, y_max, num_y_labels)
    y_pts = []
    y_txt = []
    for val in y_label_values:
        xp = origin_x - label_distance
        yp = map_y(val)
        y_pts.append((xp, yp))
        y_txt.append(_fmt(val, decimals))

    # --- grid lines ---------------------------------------------------------
    grid_x_segs = []
    if grid_x:
        for val in x_label_values:
            xp = map_x(val)
            grid_x_segs.append(
                ((xp, origin_y), (xp, origin_y + canvas_height))
            )

    grid_y_segs = []
    if grid_y:
        for val in y_label_values:
            yp = map_y(val)
            grid_y_segs.append(
                ((origin_x, yp), (origin_x + canvas_width, yp))
            )

    # --- metadata -----------------------------------------------------------
    metadata = {
        "num_series": len(valid_pairs),
        "x_range": (x_min, x_max),
        "y_range": (y_min, y_max),
    }

    return {
        "lines":    lines,
        "axes":     axes,
        "x_pts":    x_pts,
        "x_txt":    x_txt,
        "y_pts":    y_pts,
        "y_txt":    y_txt,
        "grid_x":   grid_x_segs,
        "grid_y":   grid_y_segs,
        "metadata": metadata,
    }
