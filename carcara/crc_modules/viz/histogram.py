"""
crc_modules/viz/histogram.py
Pure-Python histogram chart math — no Rhino, no matplotlib.

Returns plain coordinate data (tuples/lists) that the GH code.py layer
converts to Rhino geometry and to SVG elements.

Public API
----------
create_histogram(canvas, values, bins, num_x_labels, num_y_labels,
                 decimals, extension, label_distance, grid_y)
    -> dict with keys:
        bars      : list of (x0, y0, x1, y1) corner tuples   [left, bottom, right, top]
        axes      : list of ((x0,y0),(x1,y1)) line segment tuples
        x_pts     : list of (x, y) label-anchor tuples
        x_txt     : list of str
        y_pts     : list of (x, y) label-anchor tuples
        y_txt     : list of str
        grid      : list of ((x0,y0),(x1,y1)) line segment tuples
        metadata  : dict (num_values, num_bins, data_range, max_count)

Canvas is passed as a plain tuple (origin_x, origin_y, width, height).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _histogram_bins(data: list, num_bins: int):
    """Return (bin_edges, counts) for data partitioned into num_bins bins."""
    if not data or num_bins <= 0:
        return [], []

    data_min = min(data)
    data_max = max(data)

    if data_min == data_max:
        return [data_min, data_max], [len(data)]

    bin_width = (data_max - data_min) / float(num_bins)
    bin_edges = [data_min + i * bin_width for i in range(num_bins + 1)]

    counts = [0] * num_bins
    for v in data:
        idx = int((v - data_min) / bin_width)
        if idx >= num_bins:
            idx = num_bins - 1
        counts[idx] += 1

    return bin_edges, counts


def _label_positions(min_val: float, max_val: float, num_labels: int) -> list:
    """Return num_labels evenly spaced values between min_val and max_val."""
    if num_labels <= 0:
        return []
    if num_labels == 1:
        return [(min_val + max_val) / 2.0]
    step = (max_val - min_val) / float(num_labels - 1)
    return [min_val + i * step for i in range(num_labels)]


def _fmt(value: float, decimals: int) -> str:
    fmt = "{{:.{}f}}".format(decimals)
    return fmt.format(value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_histogram(
    canvas: tuple,
    values: list,
    bins: int = 10,
    num_x_labels: int | None = None,
    num_y_labels: int = 5,
    decimals: int = 1,
    extension: float = 0.0,
    label_distance: float = 10.0,
    grid_y: bool = False,
) -> dict:
    """
    Build all chart geometry for a histogram.

    Args:
        canvas        : (origin_x, origin_y, width, height)
        values        : iterable of numeric values
        bins          : number of histogram bins (default 10)
        num_x_labels  : number of X-axis tick labels
                        (default: all bin edges = bins+1)
        num_y_labels  : number of Y-axis tick labels (default 5)
        decimals      : decimal places for label text (default 1)
        extension     : how much axes extend beyond the canvas (default 0)
        label_distance: distance from axis to label anchor point (default 10)
        grid_y        : draw horizontal grid lines at Y ticks (default False)

    Returns:
        dict with keys: bars, axes, x_pts, x_txt, y_pts, y_txt, grid, metadata

    Raises:
        ValueError: if values is empty or None after filtering
    """
    origin_x, origin_y, canvas_width, canvas_height = canvas

    # --- clean data --------------------------------------------------------
    data = [float(v) for v in values if v is not None]
    if not data:
        raise ValueError("Histogram requires at least one non-null value")

    # --- compute bins ------------------------------------------------------
    bin_edges, counts = _histogram_bins(data, bins)
    if not counts:
        raise ValueError("Could not compute histogram bins")

    max_count = max(counts) if counts else 1
    if max_count == 0:
        max_count = 1  # guard divide-by-zero

    bar_width = canvas_width / float(bins)

    # --- bars (x0,y0,x1,y1) -----------------------------------------------
    bars = []
    for i, count in enumerate(counts):
        bar_height = (count / float(max_count)) * canvas_height
        x0 = origin_x + i * bar_width
        y0 = origin_y
        x1 = x0 + bar_width
        y1 = origin_y + bar_height
        bars.append((x0, y0, x1, y1))

    # --- axes (two line segments) ------------------------------------------
    # X-axis: horizontal from origin to right edge (+ extension)
    x_ax_start = (origin_x, origin_y)
    x_ax_end   = (origin_x + canvas_width + extension, origin_y)
    # Y-axis: vertical from origin to top edge (+ extension)
    y_ax_start = (origin_x, origin_y)
    y_ax_end   = (origin_x, origin_y + canvas_height + extension)
    axes = [(x_ax_start, x_ax_end), (y_ax_start, y_ax_end)]

    # --- X-axis labels -------------------------------------------------------
    if num_x_labels is None or num_x_labels <= 0:
        x_label_values = bin_edges
    elif num_x_labels >= len(bin_edges):
        x_label_values = bin_edges
    else:
        step = (len(bin_edges) - 1) / float(num_x_labels - 1)
        indices = [int(round(i * step)) for i in range(num_x_labels)]
        x_label_values = [bin_edges[idx] for idx in indices if idx < len(bin_edges)]

    x_pts = []
    x_txt = []
    n_x = len(x_label_values)
    data_min = min(data)
    data_max = max(data)
    data_range = data_max - data_min if data_max != data_min else 1.0

    for i, val in enumerate(x_label_values):
        # Position along canvas width proportional to value
        t = (val - data_min) / data_range if data_range != 0 else 0.0
        x_pos = origin_x + t * canvas_width
        y_pos = origin_y - label_distance
        x_pts.append((x_pos, y_pos))
        x_txt.append(_fmt(val, decimals))

    # --- Y-axis labels -------------------------------------------------------
    y_label_values = _label_positions(0.0, float(max_count), num_y_labels)
    y_pts = []
    y_txt = []
    for val in y_label_values:
        t = val / float(max_count)
        y_pos = origin_y + t * canvas_height
        x_pos = origin_x - label_distance
        y_pts.append((x_pos, y_pos))
        y_txt.append(_fmt(val, decimals))

    # --- grid lines (horizontal) -------------------------------------------
    grid = []
    if grid_y:
        for val in y_label_values:
            t = val / float(max_count)
            y = origin_y + t * canvas_height
            grid.append(
                ((origin_x, y), (origin_x + canvas_width, y))
            )

    # --- metadata -----------------------------------------------------------
    metadata = {
        "num_values": len(data),
        "num_bins": bins,
        "data_range": (min(data), max(data)),
        "max_count": max_count,
    }

    return {
        "bars":     bars,
        "axes":     axes,
        "x_pts":    x_pts,
        "x_txt":    x_txt,
        "y_pts":    y_pts,
        "y_txt":    y_txt,
        "grid":     grid,
        "metadata": metadata,
    }
