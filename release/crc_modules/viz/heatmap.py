"""
crc_modules/viz/heatmap.py
Pure-Python heatmap math — NO Rhino imports, NO matplotlib.

Returns plain coordinate tuples and RGB color tuples so the GH component
can build Rhino geometry from them.

Canvas is expressed as (origin_x, origin_y, width, height) — all floats.
Colors are expressed as (r, g, b, a) integer tuples 0-255.
"""

from __future__ import annotations


###############################################################################
# HELPERS (local copies — no cross-module import from scatter to keep clean)
###############################################################################

def _generate_label_positions(min_val: float, max_val: float, num_labels: int) -> list:
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
    Interpolate across color_list (list of (r,g,b[,a]) tuples) for value.
    Returns (r, g, b, a) integers 0-255.
    Raises ValueError if color_list has < 2 entries.
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

def create_heatmap(
    canvas: tuple,              # (origin_x, origin_y, width, height)
    data_matrix: list,          # list of rows; each row is a list of floats
    color_list: list,           # list of (r,g,b[,a]) tuples — min 2 REQUIRED
    row_labels=None,            # list of str or None
    col_labels=None,            # list of str or None
    show_values: bool = False,
    decimals: int = 1,
    num_legend_steps: int = 5,
    label_distance: float = 10.0,
    legend_width=None,
    legend_label_distance: float = 5.0,
    legend_orientation: str = "vertical",
    legend_distance: float = 20.0,
    show_legend: bool = True,
) -> dict:
    """
    Create a complete heatmap from plain Python coordinates.

    canvas: (origin_x, origin_y, width, height)
    color_list: list of (r, g, b[, a]) tuples — at least 2, NO System.Drawing

    Returns a dict with keys:
        cells         : list of (x, y, w, h) rect coords (lower-left corner)
        colors        : list of (r,g,b,a) — one per cell, row-major order
        row_pts       : list of (x, y) label anchors
        row_txt       : list of str
        col_pts       : list of (x, y) label anchors
        col_txt       : list of str
        value_pts     : list of (x, y) cell-centre anchors (if show_values)
        value_txt     : list of str
        legend_cells  : list of (x, y, w, h)
        legend_colors : list of (r,g,b,a)
        legend_pts    : list of (x, y)
        legend_txt    : list of str
        metadata      : dict
    """
    # Validate color list early — raise so caller can surface the error
    if not color_list or len(color_list) < 2:
        raise ValueError("color_list must have at least 2 colors for heatmap gradient")

    result = {
        "cells": [],
        "colors": [],
        "row_pts": [],
        "row_txt": [],
        "col_pts": [],
        "col_txt": [],
        "value_pts": [],
        "value_txt": [],
        "legend_cells": [],
        "legend_colors": [],
        "legend_pts": [],
        "legend_txt": [],
        "metadata": {},
    }

    if not data_matrix or not data_matrix[0]:
        return result

    # Convert to float matrix
    try:
        numeric_matrix = []
        for row in data_matrix:
            numeric_row = [float(v) if v is not None else 0.0 for v in row]
            numeric_matrix.append(numeric_row)
    except Exception as exc:
        raise ValueError("Invalid data_matrix: {}".format(exc))

    num_rows = len(numeric_matrix)
    num_cols = len(numeric_matrix[0])
    if not all(len(r) == num_cols for r in numeric_matrix):
        raise ValueError("All rows in data_matrix must have the same length")

    # Normalise color_list to (r,g,b,a)
    norm_colors = []
    for c in color_list:
        if len(c) >= 4:
            norm_colors.append((int(c[0]), int(c[1]), int(c[2]), int(c[3])))
        else:
            norm_colors.append((int(c[0]), int(c[1]), int(c[2]), 255))

    origin_x, origin_y, full_w, full_h = (
        float(canvas[0]), float(canvas[1]),
        float(canvas[2]), float(canvas[3]),
    )

    # Reserve legend space
    if show_legend:
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

    cell_w = chart_w / float(num_cols)
    cell_h = chart_h / float(num_rows)

    all_values = [v for row in numeric_matrix for v in row]
    min_val = min(all_values)
    max_val = max(all_values)

    # Cells — row 0 is top (legacy mirrors rows)
    for i, row in enumerate(numeric_matrix):
        row_idx = num_rows - 1 - i   # flip so row 0 renders at top
        for j, value in enumerate(row):
            x = origin_x + j * cell_w
            y = origin_y + row_idx * cell_h
            result["cells"].append((x, y, cell_w, cell_h))
            result["colors"].append(
                interpolate_color(value, min_val, max_val, norm_colors)
            )
            if show_values:
                cx_pt = x + cell_w / 2.0
                cy_pt = y + cell_h / 2.0
                result["value_pts"].append((cx_pt, cy_pt))
                result["value_txt"].append(_format_number(value, decimals))

    # Row labels (left of chart, centred vertically per row)
    if row_labels and len(row_labels) == num_rows:
        for i, label in enumerate(row_labels):
            row_idx = num_rows - 1 - i
            y_ctr = origin_y + (row_idx + 0.5) * cell_h
            result["row_pts"].append((origin_x - label_distance, y_ctr))
            result["row_txt"].append(str(label))

    # Column labels (below chart, centred horizontally per column)
    if col_labels and len(col_labels) == num_cols:
        for j, label in enumerate(col_labels):
            x_ctr = origin_x + (j + 0.5) * cell_w
            result["col_pts"].append((x_ctr, origin_y - label_distance))
            result["col_txt"].append(str(label))

    # Legend
    if show_legend:
        leg_vals = _generate_label_positions(min_val, max_val, num_legend_steps)
        if legend_orientation == "vertical":
            leg_x = origin_x + chart_w + legend_distance
            step_h = chart_h / float(num_legend_steps)
            for i, v in enumerate(leg_vals):
                ly = origin_y + i * step_h
                result["legend_cells"].append((leg_x, ly, legend_width, step_h))
                result["legend_colors"].append(
                    interpolate_color(v, min_val, max_val, norm_colors)
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
                    interpolate_color(v, min_val, max_val, norm_colors)
                )
                result["legend_pts"].append(
                    (lx + step_w / 2.0, leg_y + legend_width + legend_label_distance)
                )
                result["legend_txt"].append(_format_number(v, decimals))

    result["metadata"] = {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "value_range": (min_val, max_val),
        "num_colors": len(norm_colors),
        "legend_orientation": legend_orientation,
        "chart_area": (chart_w, chart_h),
        "canvas_area": (full_w, full_h),
        "has_legend": show_legend,
    }
    return result
