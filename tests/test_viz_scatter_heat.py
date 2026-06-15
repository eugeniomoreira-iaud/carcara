"""
tests/test_viz_scatter_heat.py
Tests for crc_modules/viz/scatter.py and crc_modules/viz/heatmap.py.
No DB, no Rhino — plain CPython pytest.
"""

import pytest

from crc_modules.viz.scatter import create_scatterplot, interpolate_color as scatter_interp
from crc_modules.viz.heatmap import create_heatmap, interpolate_color as heatmap_interp


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

CANVAS = (0.0, 0.0, 100.0, 100.0)  # origin_x, origin_y, width, height
TWO_COLORS = [(0, 0, 255, 255), (255, 0, 0, 255)]   # blue → red
THREE_COLORS = [(0, 0, 255, 255), (0, 255, 0, 255), (255, 0, 0, 255)]  # blue→green→red


# ---------------------------------------------------------------------------
# interpolate_color (scatter)
# ---------------------------------------------------------------------------

class TestScatterInterpolateColor:
    def test_min_value_returns_first_color(self):
        r, g, b, a = scatter_interp(0.0, 0.0, 10.0, TWO_COLORS)
        assert (r, g, b) == (0, 0, 255)

    def test_max_value_returns_last_color(self):
        r, g, b, a = scatter_interp(10.0, 0.0, 10.0, TWO_COLORS)
        assert (r, g, b) == (255, 0, 0)

    def test_midpoint_is_interpolated(self):
        r, g, b, a = scatter_interp(5.0, 0.0, 10.0, TWO_COLORS)
        # midpoint between blue (0,0,255) and red (255,0,0) → roughly (127,0,127)
        assert 120 <= r <= 135
        assert b >= 120

    def test_three_colors_first_segment(self):
        # value at 0 = blue
        r, g, b, a = scatter_interp(0.0, 0.0, 10.0, THREE_COLORS)
        assert (r, g, b) == (0, 0, 255)

    def test_three_colors_last_segment(self):
        # value at 10 = red
        r, g, b, a = scatter_interp(10.0, 0.0, 10.0, THREE_COLORS)
        assert (r, g, b) == (255, 0, 0)

    def test_raises_with_one_color(self):
        with pytest.raises(ValueError):
            scatter_interp(5.0, 0.0, 10.0, [(255, 0, 0, 255)])

    def test_raises_with_empty_list(self):
        with pytest.raises(ValueError):
            scatter_interp(5.0, 0.0, 10.0, [])

    def test_clamp_below_min(self):
        r, g, b, a = scatter_interp(-5.0, 0.0, 10.0, TWO_COLORS)
        assert (r, g, b) == (0, 0, 255)  # clamped to first

    def test_clamp_above_max(self):
        r, g, b, a = scatter_interp(20.0, 0.0, 10.0, TWO_COLORS)
        assert (r, g, b) == (255, 0, 0)  # clamped to last


# ---------------------------------------------------------------------------
# create_scatterplot — structure
# ---------------------------------------------------------------------------

class TestCreateScatterplot:
    def _xy(self, n=5):
        x = [float(i) for i in range(n)]
        y = [float(i * i) for i in range(n)]
        return x, y

    def test_returns_correct_dot_count(self):
        x, y = self._xy(7)
        res = create_scatterplot(CANVAS, x, y)
        assert len(res["dots"]) == 7

    def test_dot_format_is_cx_cy_r(self):
        x, y = self._xy(3)
        res = create_scatterplot(CANVAS, x, y, radii=4.0)
        for dot in res["dots"]:
            assert len(dot) == 3
            cx, cy, r = dot
            assert r == pytest.approx(4.0)

    def test_variable_radii(self):
        x, y = self._xy(3)
        radii = [1.0, 2.0, 3.0]
        res = create_scatterplot(CANVAS, x, y, radii=radii)
        assert res["dots"][0][2] == pytest.approx(1.0)
        assert res["dots"][1][2] == pytest.approx(2.0)
        assert res["dots"][2][2] == pytest.approx(3.0)

    def test_dots_within_canvas_bounds(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y)
        ox, oy, w, h = CANVAS
        for cx, cy, r in res["dots"]:
            assert ox <= cx <= ox + w
            assert oy <= cy <= oy + h

    def test_no_colors_without_color_list(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y)
        assert res["colors"] == []

    def test_colors_generated_with_color_list(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y, color_list=TWO_COLORS)
        assert len(res["colors"]) == 5
        for c in res["colors"]:
            assert len(c) == 4
            assert all(0 <= v <= 255 for v in c)

    def test_color_endpoints_match_gradient(self):
        x = [0.0, 10.0]
        y = [0.0, 10.0]
        res = create_scatterplot(CANVAS, x, y, color_list=TWO_COLORS)
        # first dot color ≈ first gradient color (blue)
        assert res["colors"][0][2] > res["colors"][0][0]   # more blue than red
        # last dot color ≈ last gradient color (red)
        assert res["colors"][-1][0] > res["colors"][-1][2]  # more red than blue

    def test_axes_two_lines(self):
        x, y = self._xy(3)
        res = create_scatterplot(CANVAS, x, y)
        assert len(res["axes"]) == 2

    def test_x_labels_count(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y, num_x_labels=4)
        assert len(res["x_pts"]) == 4
        assert len(res["x_txt"]) == 4

    def test_y_labels_count(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y, num_y_labels=3)
        assert len(res["y_pts"]) == 3
        assert len(res["y_txt"]) == 3

    def test_grid_x_lines_count_matches_labels(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y, num_x_labels=5, grid_x=True)
        assert len(res["grid_x_lines"]) == 5

    def test_grid_y_lines_count_matches_labels(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y, num_y_labels=4, grid_y=True)
        assert len(res["grid_y_lines"]) == 4

    def test_no_grid_lines_when_disabled(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y, grid_x=False, grid_y=False)
        assert res["grid_x_lines"] == []
        assert res["grid_y_lines"] == []

    def test_legend_steps_honored(self):
        x, y = self._xy(5)
        res = create_scatterplot(
            CANVAS, x, y,
            color_list=TWO_COLORS,
            show_legend=True,
            num_legend_steps=7,
        )
        assert len(res["legend_cells"]) == 7
        assert len(res["legend_colors"]) == 7
        assert len(res["legend_pts"]) == 7
        assert len(res["legend_txt"]) == 7

    def test_no_legend_when_show_legend_false(self):
        x, y = self._xy(5)
        res = create_scatterplot(
            CANVAS, x, y,
            color_list=TWO_COLORS,
            show_legend=False,
        )
        assert res["legend_cells"] == []

    def test_no_legend_without_color_list(self):
        x, y = self._xy(5)
        res = create_scatterplot(CANVAS, x, y, show_legend=True)
        assert res["legend_cells"] == []

    def test_legend_cell_format_is_xywh(self):
        x, y = self._xy(5)
        res = create_scatterplot(
            CANVAS, x, y,
            color_list=TWO_COLORS,
            show_legend=True,
            num_legend_steps=3,
        )
        for cell in res["legend_cells"]:
            assert len(cell) == 4

    def test_empty_data_returns_empty_result(self):
        res = create_scatterplot(CANVAS, [], [])
        assert res["dots"] == []
        assert res["axes"] == []

    def test_mismatched_xy_returns_empty(self):
        res = create_scatterplot(CANVAS, [1, 2, 3], [1, 2])
        assert res["dots"] == []

    def test_metadata_num_points(self):
        x, y = self._xy(8)
        res = create_scatterplot(CANVAS, x, y)
        assert res["metadata"]["num_points"] == 8

    def test_label_texts_are_formatted_numbers(self):
        x, y = self._xy(3)
        res = create_scatterplot(CANVAS, x, y, decimals=2)
        for t in res["x_txt"] + res["y_txt"]:
            # should end with exactly 2 decimal digits
            assert "." in t
            assert len(t.split(".")[-1]) == 2

    def test_col_vals_used_for_coloring(self):
        x = [0.0, 5.0, 10.0]
        y = [1.0, 1.0, 1.0]   # y is flat → if y used for color, all same
        col_vals = [0.0, 5.0, 10.0]
        res = create_scatterplot(
            CANVAS, x, y,
            color_list=TWO_COLORS,
            color_values=col_vals,
        )
        # first point should be blue-ish, last red-ish
        assert res["colors"][0][2] > res["colors"][0][0]
        assert res["colors"][-1][0] > res["colors"][-1][2]

    def test_horizontal_legend(self):
        x, y = self._xy(5)
        res = create_scatterplot(
            CANVAS, x, y,
            color_list=TWO_COLORS,
            show_legend=True,
            num_legend_steps=4,
            legend_orientation="horizontal",
        )
        assert len(res["legend_cells"]) == 4


# ---------------------------------------------------------------------------
# interpolate_color (heatmap)
# ---------------------------------------------------------------------------

class TestHeatmapInterpolateColor:
    def test_min_value_returns_first_color(self):
        r, g, b, a = heatmap_interp(0.0, 0.0, 10.0, TWO_COLORS)
        assert (r, g, b) == (0, 0, 255)

    def test_max_value_returns_last_color(self):
        r, g, b, a = heatmap_interp(10.0, 0.0, 10.0, TWO_COLORS)
        assert (r, g, b) == (255, 0, 0)

    def test_raises_with_one_color(self):
        with pytest.raises(ValueError):
            heatmap_interp(5.0, 0.0, 10.0, [(0, 0, 0, 255)])

    def test_raises_with_empty(self):
        with pytest.raises(ValueError):
            heatmap_interp(5.0, 0.0, 10.0, [])


# ---------------------------------------------------------------------------
# create_heatmap — validation
# ---------------------------------------------------------------------------

class TestCreateHeatmapValidation:
    def test_raises_with_one_color(self):
        with pytest.raises(ValueError, match="at least 2"):
            create_heatmap(CANVAS, [[1, 2], [3, 4]], [(0, 0, 0, 255)])

    def test_raises_with_empty_color_list(self):
        with pytest.raises(ValueError):
            create_heatmap(CANVAS, [[1, 2]], [])

    def test_empty_data_returns_empty(self):
        res = create_heatmap(CANVAS, [], TWO_COLORS)
        assert res["cells"] == []

    def test_jagged_matrix_raises(self):
        with pytest.raises(ValueError):
            create_heatmap(CANVAS, [[1, 2, 3], [4, 5]], TWO_COLORS)


# ---------------------------------------------------------------------------
# create_heatmap — structure
# ---------------------------------------------------------------------------

class TestCreateHeatmap:
    def _mat(self, rows, cols):
        return [[float(i * cols + j) for j in range(cols)] for i in range(rows)]

    def test_cell_count_equals_rows_times_cols(self):
        mat = self._mat(3, 4)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        assert len(res["cells"]) == 12
        assert len(res["colors"]) == 12

    def test_cell_format_is_xywh(self):
        mat = self._mat(2, 2)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        for cell in res["cells"]:
            assert len(cell) == 4

    def test_colors_are_rgba_tuples(self):
        mat = self._mat(2, 3)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        for c in res["colors"]:
            assert len(c) == 4
            assert all(0 <= v <= 255 for v in c)

    def test_first_last_cell_colors_match_gradient_endpoints(self):
        # 1x2 matrix: first cell=min, last cell=max
        mat = [[0.0, 10.0]]
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        # min value → blue (first color)
        assert res["colors"][0][2] > res["colors"][0][0]
        # max value → red (last color)
        assert res["colors"][1][0] > res["colors"][1][2]

    def test_row_labels_count(self):
        mat = self._mat(3, 2)
        res = create_heatmap(
            CANVAS, mat, TWO_COLORS,
            row_labels=["A", "B", "C"],
            show_legend=False,
        )
        assert len(res["row_pts"]) == 3
        assert res["row_txt"] == ["A", "B", "C"]

    def test_col_labels_count(self):
        mat = self._mat(2, 4)
        res = create_heatmap(
            CANVAS, mat, TWO_COLORS,
            col_labels=["W", "X", "Y", "Z"],
            show_legend=False,
        )
        assert len(res["col_pts"]) == 4
        assert res["col_txt"] == ["W", "X", "Y", "Z"]

    def test_row_label_mismatch_ignored(self):
        mat = self._mat(3, 2)
        res = create_heatmap(
            CANVAS, mat, TWO_COLORS,
            row_labels=["A", "B"],   # only 2 for 3-row matrix → ignored
            show_legend=False,
        )
        assert res["row_pts"] == []

    def test_value_pts_generated_when_show_values(self):
        mat = self._mat(2, 3)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_values=True, show_legend=False)
        assert len(res["value_pts"]) == 6
        assert len(res["value_txt"]) == 6

    def test_no_value_pts_when_show_values_false(self):
        mat = self._mat(2, 3)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_values=False, show_legend=False)
        assert res["value_pts"] == []
        assert res["value_txt"] == []

    def test_legend_steps_honored(self):
        mat = self._mat(3, 3)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, num_legend_steps=6, show_legend=True)
        assert len(res["legend_cells"]) == 6
        assert len(res["legend_colors"]) == 6
        assert len(res["legend_pts"]) == 6
        assert len(res["legend_txt"]) == 6

    def test_no_legend_when_show_legend_false(self):
        mat = self._mat(2, 2)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        assert res["legend_cells"] == []

    def test_horizontal_legend(self):
        mat = self._mat(2, 2)
        res = create_heatmap(
            CANVAS, mat, TWO_COLORS,
            num_legend_steps=4,
            legend_orientation="horizontal",
            show_legend=True,
        )
        assert len(res["legend_cells"]) == 4

    def test_three_color_gradient(self):
        mat = self._mat(2, 3)
        res = create_heatmap(CANVAS, mat, THREE_COLORS, show_legend=False)
        assert len(res["colors"]) == 6

    def test_cells_cover_chart_area(self):
        mat = self._mat(4, 5)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        ox, oy, cw, ch = CANVAS
        total_cell_area = sum(w * h for _, _, w, h in res["cells"])
        assert total_cell_area == pytest.approx(cw * ch, rel=1e-9)

    def test_metadata_rows_cols(self):
        mat = self._mat(3, 5)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        assert res["metadata"]["num_rows"] == 3
        assert res["metadata"]["num_cols"] == 5

    def test_value_range_metadata(self):
        mat = [[1.0, 5.0], [3.0, 9.0]]
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        assert res["metadata"]["value_range"] == (1.0, 9.0)

    def test_value_text_formatted_correctly(self):
        mat = [[3.14159, 2.71828], [1.41421, 0.57721]]
        res = create_heatmap(
            CANVAS, mat, TWO_COLORS,
            show_values=True, decimals=2, show_legend=False,
        )
        for t in res["value_txt"]:
            assert "." in t
            assert len(t.split(".")[-1]) == 2

    def test_row_first_maps_to_top(self):
        # row 0 should render at a higher y than row 1 (legacy top-to-bottom)
        mat = self._mat(3, 2)
        res = create_heatmap(CANVAS, mat, TWO_COLORS, show_legend=False)
        # cells are in row-major, column-minor order
        # cell[0] = row0,col0; cell[2] = row1,col0; cell[4] = row2,col0
        y_row0 = res["cells"][0][1]   # y of row0,col0
        y_row1 = res["cells"][2][1]   # y of row1,col0
        y_row2 = res["cells"][4][1]   # y of row2,col0
        # row 0 top → highest y, row 2 bottom → lowest y
        assert y_row0 > y_row1 > y_row2
