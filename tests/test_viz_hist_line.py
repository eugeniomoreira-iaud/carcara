"""
tests/test_viz_hist_line.py
Tests for crc_modules/viz/histogram.py and crc_modules/viz/lineplot.py.

All geometry is returned as plain coordinate data (no Rhino imports).
Run with: conda run -n carcara python -m pytest tests/test_viz_hist_line.py -v
"""

import pytest
from crc_modules.viz.histogram import create_histogram
from crc_modules.viz.lineplot import create_lineplot


# ============================================================
# Fixtures
# ============================================================

CANVAS_100 = (0.0, 0.0, 100.0, 100.0)   # origin at (0,0), 100x100
CANVAS_OFF  = (10.0, 20.0, 200.0, 150.0) # non-zero origin


# ============================================================
# Histogram tests
# ============================================================

class TestHistogramBasic:

    def test_returns_dict_with_required_keys(self):
        result = create_histogram(CANVAS_100, list(range(100)), bins=10)
        for key in ("bars", "axes", "x_pts", "x_txt", "y_pts", "y_txt", "grid", "metadata"):
            assert key in result, "Missing key: {}".format(key)

    def test_bar_count_equals_bins(self):
        for b in (5, 10, 20):
            result = create_histogram(CANVAS_100, list(range(100)), bins=b)
            assert len(result["bars"]) == b, "Expected {} bars, got {}".format(b, len(result["bars"]))

    def test_axes_always_two_segments(self):
        result = create_histogram(CANVAS_100, [1, 2, 3, 4, 5], bins=5)
        assert len(result["axes"]) == 2

    def test_y_label_count_matches_ny(self):
        result = create_histogram(CANVAS_100, list(range(50)), bins=10, num_y_labels=7)
        assert len(result["y_pts"]) == 7
        assert len(result["y_txt"]) == 7

    def test_x_label_count_matches_nx(self):
        result = create_histogram(CANVAS_100, list(range(50)), bins=10, num_x_labels=5)
        assert len(result["x_pts"]) == 5
        assert len(result["x_txt"]) == 5

    def test_default_x_labels_are_all_bin_edges(self):
        # Default: num_x_labels=None → all bin_edges = bins+1
        result = create_histogram(CANVAS_100, list(range(100)), bins=10, num_x_labels=None)
        # 10 bins → 11 bin edges
        assert len(result["x_pts"]) == 11

    def test_no_grid_by_default(self):
        result = create_histogram(CANVAS_100, list(range(100)), bins=10)
        assert result["grid"] == []

    def test_grid_lines_when_gy_true(self):
        result = create_histogram(CANVAS_100, list(range(100)), bins=10,
                                   num_y_labels=5, grid_y=True)
        assert len(result["grid"]) == 5

    def test_bars_are_4_tuples(self):
        result = create_histogram(CANVAS_100, [1.0, 2.0, 3.0, 4.0, 5.0], bins=5)
        for bar in result["bars"]:
            assert len(bar) == 4, "Each bar should be (x0,y0,x1,y1)"

    def test_bar_bottom_at_canvas_origin_y(self):
        result = create_histogram(CANVAS_100, list(range(20)), bins=5)
        for x0, y0, x1, y1 in result["bars"]:
            assert abs(y0 - CANVAS_100[1]) < 1e-9

    def test_tallest_bar_reaches_canvas_height(self):
        data = [1] * 10 + [2] * 20  # bin 2 is tallest
        result = create_histogram(CANVAS_100, data, bins=2)
        heights = [y1 - y0 for x0, y0, x1, y1 in result["bars"]]
        assert abs(max(heights) - CANVAS_100[3]) < 1e-9

    def test_metadata_populated(self):
        data = list(range(50))
        result = create_histogram(CANVAS_100, data, bins=10)
        m = result["metadata"]
        assert m["num_values"] == 50
        assert m["num_bins"] == 10
        assert m["data_range"] == (0.0, 49.0)
        assert m["max_count"] > 0

    def test_x_labels_are_formatted_strings(self):
        result = create_histogram(CANVAS_100, [0.0, 1.0, 2.0], bins=2, decimals=2)
        for t in result["x_txt"]:
            assert isinstance(t, str)
            assert "." in t  # decimal point present

    def test_non_zero_canvas_origin(self):
        data = list(range(20))
        result = create_histogram(CANVAS_OFF, data, bins=5)
        ox, oy, w, h = CANVAS_OFF
        for x0, y0, x1, y1 in result["bars"]:
            assert x0 >= ox - 1e-9
            assert y0 >= oy - 1e-9
            assert x1 <= ox + w + 1e-9

    def test_extension_stretches_axes(self):
        ext = 15.0
        result_no_ext = create_histogram(CANVAS_100, list(range(10)), bins=5, extension=0)
        result_with_ext = create_histogram(CANVAS_100, list(range(10)), bins=5, extension=ext)
        # X-axis end should be further right
        x_end_no  = result_no_ext["axes"][0][1][0]
        x_end_ext = result_with_ext["axes"][0][1][0]
        assert abs(x_end_ext - x_end_no - ext) < 1e-9

    def test_label_distance_offsets_x_labels_below_origin(self):
        dist = 12.0
        result = create_histogram(CANVAS_100, list(range(10)), bins=5, label_distance=dist)
        for xp, yp in result["x_pts"]:
            assert abs(yp - (CANVAS_100[1] - dist)) < 1e-9

    def test_label_distance_offsets_y_labels_left_of_origin(self):
        dist = 8.0
        result = create_histogram(CANVAS_100, list(range(10)), bins=5, label_distance=dist)
        for xp, yp in result["y_pts"]:
            assert abs(xp - (CANVAS_100[0] - dist)) < 1e-9


class TestHistogramEdgeCases:

    def test_empty_values_raises(self):
        with pytest.raises(ValueError):
            create_histogram(CANVAS_100, [], bins=5)

    def test_none_values_raises(self):
        with pytest.raises((ValueError, TypeError)):
            create_histogram(CANVAS_100, None, bins=5)

    def test_all_same_values(self):
        # Should not raise; single-bin case
        result = create_histogram(CANVAS_100, [5.0] * 20, bins=5)
        assert "bars" in result

    def test_single_value_raises(self):
        # Only 1 unique value — bins can still compute, just all in one bin
        result = create_histogram(CANVAS_100, [42.0], bins=3)
        assert len(result["bars"]) >= 1  # should produce at least 1 bar

    def test_decimals_zero(self):
        result = create_histogram(CANVAS_100, [1.0, 2.0, 3.0], bins=3, decimals=0)
        for t in result["y_txt"]:
            assert "." not in t


# ============================================================
# LinePlot tests
# ============================================================

class TestLinePlotBasic:

    def test_returns_dict_with_required_keys(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 4.0, 9.0, 16.0, 25.0]
        result = create_lineplot(CANVAS_100, x, y)
        for key in ("lines", "axes", "x_pts", "x_txt", "y_pts", "y_txt",
                    "grid_x", "grid_y", "metadata"):
            assert key in result, "Missing key: {}".format(key)

    def test_single_series_flat_list(self):
        x = list(range(10))
        y = [v ** 2 for v in x]
        result = create_lineplot(CANVAS_100, x, y)
        assert len(result["lines"]) == 1
        assert len(result["lines"][0]) == 10

    def test_multi_series_list_of_lists(self):
        x = [[0.0, 1.0, 2.0], [0.0, 1.0, 2.0]]
        y = [[0.0, 1.0, 4.0], [0.0, 2.0, 8.0]]
        result = create_lineplot(CANVAS_100, x, y)
        assert len(result["lines"]) == 2

    def test_axes_two_segments(self):
        result = create_lineplot(CANVAS_100, [0.0, 1.0], [0.0, 1.0])
        assert len(result["axes"]) == 2

    def test_x_label_count(self):
        result = create_lineplot(CANVAS_100, list(range(20)), list(range(20)),
                                  num_x_labels=6)
        assert len(result["x_pts"]) == 6
        assert len(result["x_txt"]) == 6

    def test_y_label_count(self):
        result = create_lineplot(CANVAS_100, list(range(20)), list(range(20)),
                                  num_y_labels=4)
        assert len(result["y_pts"]) == 4
        assert len(result["y_txt"]) == 4

    def test_no_grid_by_default(self):
        result = create_lineplot(CANVAS_100, [0.0, 1.0, 2.0], [0.0, 1.0, 2.0])
        assert result["grid_x"] == []
        assert result["grid_y"] == []

    def test_grid_x_lines_when_enabled(self):
        result = create_lineplot(CANVAS_100, [0.0, 1.0, 2.0], [0.0, 1.0, 2.0],
                                  num_x_labels=4, grid_x=True)
        assert len(result["grid_x"]) == 4

    def test_grid_y_lines_when_enabled(self):
        result = create_lineplot(CANVAS_100, [0.0, 1.0, 2.0], [0.0, 1.0, 2.0],
                                  num_y_labels=3, grid_y=True)
        assert len(result["grid_y"]) == 3

    def test_line_points_within_canvas_bounds(self):
        x = [0.0, 10.0, 20.0]
        y = [0.0, 5.0, 10.0]
        ox, oy, w, h = CANVAS_100
        result = create_lineplot(CANVAS_100, x, y)
        for series in result["lines"]:
            for xp, yp in series:
                assert ox - 1e-6 <= xp <= ox + w + 1e-6
                assert oy - 1e-6 <= yp <= oy + h + 1e-6

    def test_metadata_populated(self):
        x = [0.0, 1.0, 2.0, 3.0]
        y = [0.0, 1.0, 4.0, 9.0]
        result = create_lineplot(CANVAS_100, x, y)
        m = result["metadata"]
        assert m["num_series"] == 1
        assert "x_range" in m
        assert "y_range" in m

    def test_non_zero_canvas_origin(self):
        x = [0.0, 5.0, 10.0]
        y = [0.0, 2.5, 5.0]
        ox, oy, w, h = CANVAS_OFF
        result = create_lineplot(CANVAS_OFF, x, y)
        for series in result["lines"]:
            for xp, yp in series:
                assert xp >= ox - 1e-6
                assert yp >= oy - 1e-6

    def test_extension_stretches_axes(self):
        ext = 20.0
        r1 = create_lineplot(CANVAS_100, [0.0, 1.0], [0.0, 1.0], extension=0)
        r2 = create_lineplot(CANVAS_100, [0.0, 1.0], [0.0, 1.0], extension=ext)
        x_end_1 = r1["axes"][0][1][0]
        x_end_2 = r2["axes"][0][1][0]
        assert abs(x_end_2 - x_end_1 - ext) < 1e-9

    def test_margin_x_shifts_x_min(self):
        x = [10.0, 20.0, 30.0]
        y = [1.0, 2.0, 3.0]
        r_no  = create_lineplot(CANVAS_100, x, y, margin_x=0)
        r_marg = create_lineplot(CANVAS_100, x, y, margin_x=10)
        # With margin, x_min is lower → first data point maps further right
        first_no   = r_no["lines"][0][0][0]
        first_marg = r_marg["lines"][0][0][0]
        assert first_marg > first_no

    def test_first_point_at_canvas_origin_x_no_margin(self):
        """When margin=0 and first data point is x_min, it should map to canvas left."""
        x = [0.0, 10.0, 20.0]
        y = [0.0, 5.0, 10.0]
        result = create_lineplot(CANVAS_100, x, y, margin_x=0)
        first_x = result["lines"][0][0][0]
        assert abs(first_x - CANVAS_100[0]) < 1e-9

    def test_label_texts_are_strings(self):
        result = create_lineplot(CANVAS_100, [0.0, 1.0], [0.0, 1.0], decimals=2)
        for t in result["x_txt"] + result["y_txt"]:
            assert isinstance(t, str)

    def test_label_distance_x(self):
        dist = 15.0
        result = create_lineplot(CANVAS_100, [0.0, 1.0], [0.0, 1.0], label_distance=dist)
        for xp, yp in result["x_pts"]:
            assert abs(yp - (CANVAS_100[1] - dist)) < 1e-9

    def test_label_distance_y(self):
        dist = 15.0
        result = create_lineplot(CANVAS_100, [0.0, 1.0], [0.0, 1.0], label_distance=dist)
        for xp, yp in result["y_pts"]:
            assert abs(xp - (CANVAS_100[0] - dist)) < 1e-9


class TestLinePlotEdgeCases:

    def test_empty_x_raises(self):
        with pytest.raises(ValueError):
            create_lineplot(CANVAS_100, [], [1.0, 2.0])

    def test_empty_y_raises(self):
        with pytest.raises(ValueError):
            create_lineplot(CANVAS_100, [1.0, 2.0], [])

    def test_mismatched_series_count_raises(self):
        x = [[0.0, 1.0], [0.0, 1.0]]
        y = [[0.0, 1.0]]
        with pytest.raises(ValueError):
            create_lineplot(CANVAS_100, x, y)

    def test_series_too_short_skipped(self):
        # A series with only 1 point is invalid (need >= 2)
        x = [[0.0], [0.0, 1.0, 2.0]]
        y = [[0.0], [0.0, 1.0, 4.0]]
        result = create_lineplot(CANVAS_100, x, y)
        # Only the valid series should appear
        assert len(result["lines"]) == 1

    def test_all_series_too_short_raises(self):
        x = [[0.0]]
        y = [[0.0]]
        with pytest.raises(ValueError):
            create_lineplot(CANVAS_100, x, y)

    def test_none_x_raises(self):
        with pytest.raises(ValueError):
            create_lineplot(CANVAS_100, None, [1.0, 2.0])

    def test_identical_x_values_no_crash(self):
        # All same X → x_range handled via jitter in _range_with_margin
        result = create_lineplot(CANVAS_100, [5.0, 5.0], [1.0, 2.0])
        assert len(result["lines"]) == 1
