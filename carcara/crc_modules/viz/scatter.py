"""
crc_modules/viz/scatter.py
Pure-Python scatter plot math — NO Rhino imports, NO matplotlib.

Returns plain coordinate tuples and RGB color tuples so the GH component
can build Rhino geometry from them.

Canvas is expressed as (origin_x, origin_y, width, height) — all floats.
Colors are expressed as (r, g, b, a) integer tuples 0-255.
"""

from __future__ import annotations


###############################################################################
# DATA HELPERS
###############################################################################

def _calculate_range_with_margin(data: list, margin_percent: float = 0):
    """Return (min_display, max_display, range_display) with optional margin."""
    if not data:
        return 0.0, 1.0, 1.0
    data_min = min(data)
    data_max = max(data)
    if data_min == data_max:
        data_min -= 0.5
        data_max += 0.5
    data_range = data_max - data_min
    margin_value = margin_percent * data_range / 100.0
    min_display = data_min - margin_value
    max_display = data_max
    range_display = max_display - min_display
    return min_display, max_display, range_display


def _generate_label_positions(min_val: float, max_val: float, num_labels: int) -> list:
    """Return evenly-spaced label values between min and max (num_labels total)."""
    if num_labels <= 0:
        return []
    if num_labels == 1:
        return [(min_val + max_val) / 2.0]
    step = (max_val - min_val) / float(num_labels - 1)
    return [min_val + i * step for i in range(num_labels)]


def _format_number(value: float, decimals: int) -> str:
    fmt = "{{:.{}f}}".format(decimals)
    return fmt.format(value)


###############################################################################
# COLOR GRADIENT
###############################################################################

def interpolate_color(value: float, min_val: float, max_val: float,
                      color_list: list) -> tuple:
    """
    Interpolate across color_list (list of (r,g,b,a) tuples) for value.
    Returns (r, g, b, a) integers 0-255.
    color_list must have >= 2 entries.
    """
    if not color_list or len(color_list) < 2:
        raise ValueError("color_list must have at least 2 colors")
    if max_val == min_val:
        t = 0.5
    else:
        t = (value - min_val) / (max_val - min_val)
    t = max(0.0, min(1.0, t))
    num_segments = len(color_list) - 1
    segment = t * num_segments
    segment_index = int(segment)
    if segment_index >= num_segments:
        segment_index = num_segments - 1
        local_t = 1.0
    else:
        local_t = segment - segment_index
    c1 = color_list[segment_index]
    c2 = color_list[segment_index + 1]
    r = int(c1[0] + (c2[0] - c1[0]) * local_t)
    g = int(c1[1] + (c2[1] - c1[1]) * local_t)
    b = int(c1[2] + (c2[2] - c1[2]) * local_t)
    a = int(c1[3] + (c2[3] - c1[3]) * local_t) if len(c1) > 3 else 255
    return (r, g, b, a)


###############################################################################
# MAIN FUNCTION
###############################################################################

def create_scatterplot(
    canvas: tuple,          # (origin_x, origin_y, width, height)
    x_values: list,
    y_values: list,
    radii=2.0,              # float or list
    num_x_labels: int = 5,
    num_y_labels: int = 5,
    decimals: int = 1,
    extension: float = 0.0,
    label_distance: float = 10.0,
    margin_x: float = 0.0,
    margin_y: float = 0.0,
    grid_x: bool = False,
    grid_y: bool = False,
    show_legend: bool = False,
    color_values=None,      # list or None → use y_values
    color_list=None,        # list of (r,g,b,a) tuples; required if show_legend or colors wanted
    num_legend_steps: int = 5,
    legend_width=None,
    legend_distance: float = 20.0,
    legend_label_distance: float = 5.0,
    legend_orientation: str = "vertical",
) -> dict:
    """
    Create a complete scatter plot from plain Python coordinates.

    canvas: (origin_x, origin_y, width, height)
    color_list: list of (r, g, b[, a]) tuples — pure Python, no System.Drawing

    Returns a dict with keys:
        dots          : list of (cx, cy, radius) — circle centers + radius
        colors        : list of (r,g,b,a) per dot  (empty if no color_list)
        axes          : list of ((x0,y0),(x1,y1)) line segments
        x_pts         : list of (x, y) label anchor coords
        x_txt         : list of str
        y_pts         : list of (x, y) label anchor coords
        y_txt         : list of str
        grid_x_lines  : list of ((x0,y0),(x1,y1))
        grid_y_lines  : list of ((x0,y0),(x1,y1))
        legend_cells  : list of (x, y, w, h) rect coords
        legend_colors : list of (r,g,b,a)
        legend_pts    : list of (x, y)
        legend_txt    : list of str
        metadata      : dict
    """
    result = {
        "dots": [],
        "colors": [],
        "axes": [],
        "x_pts": [],
        "x_txt": [],
        "y_pts": [],
        "y_txt": [],
        "grid_x_lines": [],
        "grid_y_lines": [],
        "legend_cells": [],
        "legend_colors": [],
        "legend_pts": [],
        "legend_txt": [],
        "metadata": {},
    }

    if not x_values or not y_values:
        return result

    x_data = [float(v) for v in x_values if v is not None]
    y_data = [float(v) for v in y_values if v is not None]

    if not x_data or not y_data or len(x_data) != len(y_data):
        return result

    origin_x, origin_y, full_w, full_h = (
        float(canvas[0]), float(canvas[1]),
        float(canvas[2]), float(canvas[3]),
    )

    # Validate + normalise color_list entries to (r,g,b,a)
    generate_colors = False
    norm_colors = []
    if color_list and len(color_list) >= 2:
        generate_colors = True
        for c in color_list:
            if len(c) >= 4:
                norm_colors.append((int(c[0]), int(c[1]), int(c[2]), int(c[3])))
            else:
                norm_colors.append((int(c[0]), int(c[1]), int(c[2]), 255))

    show_legend_validated = show_legend and generate_colors

    # Color data
    if generate_colors:
        if color_values is not None:
            c_data = [float(v) for v in color_values if v is not None]
            if len(c_data) != len(x_data):
                generate_colors = False
                show_legend_validated = False
                c_data = y_data
            c_min, c_max = min(c_data), max(c_data)
        else:
            c_data = y_data
            c_min, c_max = min(y_data), max(y_data)
        if c_min == c_max:
            c_min -= 0.5
            c_max += 0.5
    else:
        c_data = y_data
        c_min, c_max = min(y_data), max(y_data)

    # Reserve legend space
    if show_legend_validated:
        if legend_width is None:
            legend_width = full_w * 0.05 if legend_orientation == "vertical" else full_h * 0.05
        if legend_orientation == "vertical":
            legend_space = legend_distance + legend_width + legend_label_distance + 50
            chart_w = full_w - legend_space
            chart_h = full_h
        else:
            legend_space = legend_distance + legend_width + legend_label_distance + 20
            chart_w = full_w
            chart_h = full_h - legend_space
    else:
        chart_w = full_w
        chart_h = full_h

    # Data ranges with margins
    x_min, x_max, x_range = _calculate_range_with_margin(x_data, margin_x)
    y_min, y_max, y_range = _calculate_range_with_margin(y_data, margin_y)

    def map_x(v):
        return origin_x + ((v - x_min) / x_range) * chart_w

    def map_y(v):
        return origin_y + ((v - y_min) / y_range) * chart_h

    # Dots
    r_is_list = hasattr(radii, "__iter__") and not isinstance(radii, str)
    for i, (xv, yv) in enumerate(zip(x_data, y_data)):
        cx = map_x(xv)
        cy = map_y(yv)
        if r_is_list:
            idx = min(i, len(radii) - 1)
            r = float(radii[idx])
        else:
            r = float(radii) if radii is not None else 2.0
        result["dots"].append((cx, cy, r))

        if generate_colors:
            result["colors"].append(
                interpolate_color(c_data[i], c_min, c_max, norm_colors)
            )

    # Axes  — ((x0,y0),(x1,y1))
    x_axis = ((origin_x, origin_y), (origin_x + chart_w + extension, origin_y))
    y_axis = ((origin_x, origin_y), (origin_x, origin_y + chart_h + extension))
    result["axes"] = [x_axis, y_axis]

    # X labels + optional grid
    x_label_vals = _generate_label_positions(x_min, x_max, num_x_labels)
    for v in x_label_vals:
        px = map_x(v)
        result["x_pts"].append((px, origin_y - label_distance))
        result["x_txt"].append(_format_number(v, decimals))
    if grid_x and x_range > 0:
        for v in x_label_vals:
            px = map_x(v)
            result["grid_x_lines"].append(
                ((px, origin_y), (px, origin_y + chart_h))
            )

    # Y labels + optional grid
    y_label_vals = _generate_label_positions(y_min, y_max, num_y_labels)
    for v in y_label_vals:
        py = map_y(v)
        result["y_pts"].append((origin_x - label_distance, py))
        result["y_txt"].append(_format_number(v, decimals))
    if grid_y and y_range > 0:
        for v in y_label_vals:
            py = map_y(v)
            result["grid_y_lines"].append(
                ((origin_x, py), (origin_x + chart_w, py))
            )

    # Legend
    if show_legend_validated:
        leg_vals = _generate_label_positions(c_min, c_max, num_legend_steps)
        if legend_orientation == "vertical":
            leg_x = origin_x + chart_w + legend_distance
            step_h = chart_h / float(num_legend_steps)
            for i, v in enumerate(leg_vals):
                ly = origin_y + i * step_h
                result["legend_cells"].append((leg_x, ly, legend_width, step_h))
                result["legend_colors"].append(
                    interpolate_color(v, c_min, c_max, norm_colors)
                )
                result["legend_pts"].append(
                    (leg_x + legend_width + legend_label_distance, ly + step_h / 2.0)
                )
                result["legend_txt"].append(_format_number(v, decimals))
        else:
            leg_y = origin_y + chart_h + legend_distance
            step_w = chart_w / float(num_legend_steps)
            for i, v in enumerate(leg_vals):
                lx = origin_x + i * step_w
                result["legend_cells"].append((lx, leg_y, step_w, legend_width))
                result["legend_colors"].append(
                    interpolate_color(v, c_min, c_max, norm_colors)
                )
                result["legend_pts"].append(
                    (lx + step_w / 2.0, leg_y + legend_width + legend_label_distance)
                )
                result["legend_txt"].append(_format_number(v, decimals))

    result["metadata"] = {
        "num_points": len(x_data),
        "x_range": (x_min, x_max),
        "y_range": (y_min, y_max),
        "has_legend": show_legend_validated,
        "has_colors": generate_colors,
        "color_range": (c_min, c_max) if generate_colors else None,
        "chart_area": (chart_w, chart_h),
        "canvas_area": (full_w, full_h),
    }
    return result
