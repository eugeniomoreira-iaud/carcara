"""Tests for crc_modules/utils/color.py"""
import math
import pytest
from crc_modules.utils.color import (
    rgb_to_hsv,
    hsv_to_rgb,
    interpolate_color_argb,
    interpolate_color_rgb,
    value_to_color,
    default_gradient_argb,
    map_values_to_classes,
    LegendConfig,
    parse_legend_config,
    compute_color_assignment,
    compute_statistics,
    legend_layout,
)


# ---------------------------------------------------------------------------
# rgb_to_hsv / hsv_to_rgb round-trips
# ---------------------------------------------------------------------------

def _roundtrip(r, g, b):
    h, s, v = rgb_to_hsv(r, g, b)
    r2, g2, b2 = hsv_to_rgb(h, s, v)
    return r2, g2, b2


def test_rgb_hsv_roundtrip_red():
    assert _roundtrip(255, 0, 0) == (255, 0, 0)


def test_rgb_hsv_roundtrip_green():
    assert _roundtrip(0, 255, 0) == (0, 255, 0)


def test_rgb_hsv_roundtrip_blue():
    assert _roundtrip(0, 0, 255) == (0, 0, 255)


def test_rgb_hsv_roundtrip_white():
    assert _roundtrip(255, 255, 255) == (255, 255, 255)


def test_rgb_hsv_roundtrip_black():
    assert _roundtrip(0, 0, 0) == (0, 0, 0)


def test_rgb_hsv_roundtrip_mid_gray():
    r2, g2, b2 = _roundtrip(128, 128, 128)
    assert abs(r2 - 128) <= 1
    assert abs(g2 - 128) <= 1
    assert abs(b2 - 128) <= 1


def test_rgb_hsv_roundtrip_arbitrary():
    r, g, b = 100, 150, 200
    r2, g2, b2 = _roundtrip(r, g, b)
    assert abs(r2 - r) <= 1
    assert abs(g2 - g) <= 1
    assert abs(b2 - b) <= 1


def test_rgb_to_hsv_red_hue():
    h, s, v = rgb_to_hsv(255, 0, 0)
    assert abs(h - 0.0) < 1.0
    assert abs(s - 1.0) < 0.001
    assert abs(v - 1.0) < 0.001


def test_rgb_to_hsv_green_hue():
    h, s, v = rgb_to_hsv(0, 255, 0)
    assert abs(h - 120.0) < 1.0


def test_rgb_to_hsv_blue_hue():
    h, s, v = rgb_to_hsv(0, 0, 255)
    assert abs(h - 240.0) < 1.0


def test_hsv_to_rgb_yellow():
    r, g, b = hsv_to_rgb(60.0, 1.0, 1.0)
    assert r == 255
    assert g == 255
    assert b == 0


def test_hsv_to_rgb_cyan():
    r, g, b = hsv_to_rgb(180.0, 1.0, 1.0)
    assert r == 0
    assert g == 255
    assert b == 255


# ---------------------------------------------------------------------------
# interpolate_color_argb
# ---------------------------------------------------------------------------

def test_interpolate_argb_at_zero():
    colors = [(255, 0, 0, 255), (255, 255, 0, 0)]
    result = interpolate_color_argb(colors, 0.0)
    assert result == (255, 0, 0, 255)


def test_interpolate_argb_at_one():
    colors = [(255, 0, 0, 255), (255, 255, 0, 0)]
    result = interpolate_color_argb(colors, 1.0)
    assert result == (255, 255, 0, 0)


def test_interpolate_argb_midpoint():
    colors = [(255, 0, 0, 0), (255, 0, 0, 255)]
    result = interpolate_color_argb(colors, 0.5)
    # alpha and first two channels stable; blue should be ~127-128
    assert result[0] == 255
    assert 126 <= result[3] <= 129


def test_interpolate_argb_single_color():
    colors = [(255, 100, 150, 200)]
    result = interpolate_color_argb(colors, 0.7)
    assert result == (255, 100, 150, 200)


def test_interpolate_rgb_midpoint():
    colors = [(0, 0, 0), (255, 255, 255)]
    r, g, b = interpolate_color_rgb(colors, 0.5)
    assert 126 <= r <= 129
    assert 126 <= g <= 129
    assert 126 <= b <= 129


# ---------------------------------------------------------------------------
# value_to_color
# ---------------------------------------------------------------------------

def test_value_to_color_at_min():
    colors = [(255, 0, 0, 0), (255, 0, 0, 255)]
    result = value_to_color(0.0, 0.0, 10.0, colors)
    assert result == (255, 0, 0, 0)


def test_value_to_color_at_max():
    colors = [(255, 0, 0, 0), (255, 0, 0, 255)]
    result = value_to_color(10.0, 0.0, 10.0, colors)
    assert result == (255, 0, 0, 255)


def test_value_to_color_nan():
    colors = [(255, 0, 0, 0), (255, 255, 0, 0)]
    result = value_to_color(float("nan"), 0, 10, colors)
    assert result == (255, 128, 128, 128)


def test_value_to_color_inf():
    colors = [(255, 0, 0, 0), (255, 255, 0, 0)]
    result = value_to_color(float("inf"), 0, 10, colors)
    assert result == (255, 128, 128, 128)


def test_value_to_color_rgb_tuples():
    # Should work with (R,G,B) 3-tuples too (auto-pads alpha=255)
    colors = [(0, 0, 0), (255, 255, 255)]
    a, r, g, b = value_to_color(5.0, 0.0, 10.0, colors)
    assert a == 255
    assert 126 <= r <= 129


# ---------------------------------------------------------------------------
# default_gradient_argb
# ---------------------------------------------------------------------------

def test_default_gradient_has_6_stops():
    grad = default_gradient_argb()
    assert len(grad) == 6


def test_default_gradient_starts_blue():
    grad = default_gradient_argb()
    assert grad[0] == (255, 0, 0, 255)


def test_default_gradient_ends_red():
    grad = default_gradient_argb()
    assert grad[-1] == (255, 255, 0, 0)


# ---------------------------------------------------------------------------
# map_values_to_classes
# ---------------------------------------------------------------------------

def test_map_classes_linear_basic():
    values = [0.0, 5.0, 10.0]
    classes = map_values_to_classes(values, 2, 0.0, 10.0, linear=True)
    # 0.0 -> class 0, 5.0 -> class 1, 10.0 -> class 1 (capped)
    assert classes[0] == 0
    assert classes[-1] == 1


def test_map_classes_none_maps_to_minus1():
    values = [1.0, None, 3.0]
    classes = map_values_to_classes(values, 3)
    assert classes[1] == -1


def test_map_classes_percentile():
    values = list(range(10))
    classes = map_values_to_classes(values, 2, linear=False)
    # All values should map to 0 or 1
    for c in classes:
        assert c in (0, 1)


# ---------------------------------------------------------------------------
# parse_legend_config
# ---------------------------------------------------------------------------

def test_parse_legend_config_defaults():
    cfg = parse_legend_config(None)
    assert cfg.min is None
    assert cfg.max is None
    assert cfg.segments == 11
    assert cfg.decimals == 2
    assert cfg.vertical is True
    assert cfg.seg_height == 1.0
    assert cfg.seg_width == 1.0
    assert cfg.text_height == 0.5
    assert cfg.title is None
    assert cfg.title_size == 1.5
    assert cfg.scale == 1.0
    assert cfg.title_offset == 1.0
    assert cfg.label_offset == 0.5


def test_parse_legend_config_empty_string():
    cfg = parse_legend_config("")
    assert cfg.segments == 11  # defaults intact


def test_parse_legend_config_basic_keys():
    text = "title: My Legend\nmin: 0.0\nmax: 100.0\nsegments: 5\ndecimals: 1"
    cfg = parse_legend_config(text)
    assert cfg.title == "My Legend"
    assert cfg.min == 0.0
    assert cfg.max == 100.0
    assert cfg.segments == 5
    assert cfg.decimals == 1


def test_parse_legend_config_vertical_false():
    cfg = parse_legend_config("vertical: false")
    assert cfg.vertical is False


def test_parse_legend_config_vertical_truthy_values():
    for val in ("true", "yes", "1", "t", "y"):
        cfg = parse_legend_config("vertical: {}".format(val))
        assert cfg.vertical is True


def test_parse_legend_config_aliases():
    text = "titlesize: 2.0\ntitleoffset: 0.5\nlabeloffset: 0.3\nseg_count: 8\ndecimal_places: 3"
    cfg = parse_legend_config(text)
    assert cfg.title_size == 2.0
    assert cfg.title_offset == 0.5
    assert cfg.label_offset == 0.3
    assert cfg.segments == 8
    assert cfg.decimals == 3


def test_parse_legend_config_segment_height_alias():
    cfg = parse_legend_config("segment_height: 2.5\nsegment_width: 1.5")
    assert cfg.seg_height == 2.5
    assert cfg.seg_width == 1.5


def test_parse_legend_config_scale():
    cfg = parse_legend_config("scale: 3.0")
    assert cfg.scale == 3.0


def test_parse_legend_config_bad_lines_ignored():
    text = "this is bad\n: no key\nmin: 5.0\nalso bad line without colon"
    cfg = parse_legend_config(text)
    assert cfg.min == 5.0  # valid line parsed
    assert cfg.segments == 11  # bad lines did not break anything


def test_parse_legend_config_clamp_min_scale():
    cfg = parse_legend_config("scale: 0.0")
    assert cfg.scale >= 0.1  # clamped


def test_parse_legend_config_segments_clamp():
    cfg = parse_legend_config("segments: 1")
    assert cfg.segments == 2  # clamped to min 2


# ---------------------------------------------------------------------------
# compute_color_assignment
# ---------------------------------------------------------------------------

GRAD = [(255, 0, 0, 255), (255, 255, 0, 0)]  # blue → red


def _make_cfg(**kwargs):
    cfg = LegendConfig()
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return cfg


def test_compute_color_assignment_continuous_length():
    values = [0.0, 5.0, 10.0]
    cfg = _make_cfg()
    argb_vals, leg_ranges, leg_colors = compute_color_assignment(
        values, GRAD, [0], True, cfg)
    assert len(argb_vals) == 3
    assert len(leg_ranges) == cfg.segments
    assert len(leg_colors) == cfg.segments


def test_compute_color_assignment_continuous_min_is_blue():
    values = [0.0, 10.0]
    cfg = _make_cfg()
    argb_vals, _, _ = compute_color_assignment(values, GRAD, [0], True, cfg)
    assert argb_vals[0] == (255, 0, 0, 255)  # t=0 → blue


def test_compute_color_assignment_continuous_max_is_red():
    values = [0.0, 10.0]
    cfg = _make_cfg()
    argb_vals, _, _ = compute_color_assignment(values, GRAD, [0], True, cfg)
    assert argb_vals[1] == (255, 255, 0, 0)  # t=1 → red


def test_compute_color_assignment_none_sentinel():
    values = [1.0, None, "bad", 5.0]
    cfg = _make_cfg()
    argb_vals, _, _ = compute_color_assignment(values, GRAD, [0], True, cfg)
    assert argb_vals[1] is None
    assert argb_vals[2] is None


def test_compute_color_assignment_cfg_min_max_updated():
    values = [2.0, 4.0, 6.0]
    cfg = _make_cfg()
    assert cfg.min is None
    compute_color_assignment(values, GRAD, [0], True, cfg)
    assert cfg.min == 2.0
    assert cfg.max == 6.0


def test_compute_color_assignment_cfg_min_max_override():
    values = [2.0, 4.0, 6.0]
    cfg = _make_cfg(min=0.0, max=10.0)
    compute_color_assignment(values, GRAD, [0], True, cfg)
    assert cfg.min == 0.0
    assert cfg.max == 10.0


def test_compute_color_assignment_fixed_class_linear():
    values = list(range(10))
    cfg = _make_cfg()
    argb_vals, leg_ranges, leg_colors = compute_color_assignment(
        values, GRAD, [5], True, cfg)
    assert len(leg_ranges) == 5
    assert len(leg_colors) == 5
    # All values should map to a color (not None) since all are in [0, 9]
    assert all(v is not None for v in argb_vals)


def test_compute_color_assignment_fixed_class_percentile():
    values = list(range(20))
    cfg = _make_cfg()
    argb_vals, leg_ranges, leg_colors = compute_color_assignment(
        values, GRAD, [4], False, cfg)
    assert len(leg_ranges) == 4
    assert len(leg_colors) == 4


def test_compute_color_assignment_fixed_class_out_of_range_is_none():
    # cfg.min/max override: value 15 is > max=10, should be None
    values = [0.0, 5.0, 15.0]
    cfg = _make_cfg(min=0.0, max=10.0)
    argb_vals, _, _ = compute_color_assignment(values, GRAD, [3], True, cfg)
    assert argb_vals[2] is None


def test_compute_color_assignment_custom_bins():
    values = [1.0, 5.0, 9.0]
    cfg = _make_cfg()
    argb_vals, leg_ranges, leg_colors = compute_color_assignment(
        values, GRAD, [0.0, 4.0, 8.0, 12.0], True, cfg)
    assert len(leg_ranges) <= 3  # 3 bins from 4 breakpoints
    assert argb_vals[0] is not None  # 1.0 in [0, 4)
    assert argb_vals[1] is not None  # 5.0 in [4, 8)
    assert argb_vals[2] is not None  # 9.0 in [8, 12]


def test_compute_color_assignment_custom_bins_out_of_range_is_none():
    values = [-1.0, 5.0]
    cfg = _make_cfg()
    argb_vals, _, _ = compute_color_assignment(
        values, GRAD, [0.0, 10.0], True, cfg)
    assert argb_vals[0] is None  # -1 < 0.0 → not in any bin


def test_compute_color_assignment_no_valid_raises():
    with pytest.raises(ValueError):
        cfg = _make_cfg()
        compute_color_assignment([None, "abc"], GRAD, [0], True, cfg)


def test_compute_color_assignment_nan_inf_fixed_class_are_none():
    # In fixed-class mode the original code explicitly checks nan/inf → None/Gray.
    values = [float('nan'), float('inf'), 5.0]
    cfg = _make_cfg()
    argb_vals, _, _ = compute_color_assignment(values, GRAD, [3], True, cfg)
    assert argb_vals[0] is None
    assert argb_vals[1] is None
    assert argb_vals[2] is not None


def test_compute_color_assignment_leg_ranges_count_continuous():
    cfg = _make_cfg(segments=7)
    argb_vals, leg_ranges, leg_colors = compute_color_assignment(
        [1.0, 5.0], GRAD, [0], True, cfg)
    assert len(leg_ranges) == 7
    assert len(leg_colors) == 7


def test_compute_color_assignment_leg_last_max_equals_data_max():
    values = [0.0, 3.0, 7.0, 10.0]
    cfg = _make_cfg(segments=4)
    _, leg_ranges, _ = compute_color_assignment(values, GRAD, [0], True, cfg)
    assert leg_ranges[-1]['max'] == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# compute_statistics
# ---------------------------------------------------------------------------

def test_compute_statistics_format():
    result = compute_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
    lines = result.split('\n')
    assert len(lines) == 5
    assert lines[0].startswith("Min:")
    assert lines[1].startswith("Max:")
    assert lines[2].startswith("Mean:")
    assert lines[3].startswith("Median:")
    assert lines[4].startswith("Valid:")


def test_compute_statistics_exact_format():
    result = compute_statistics([2.0, 4.0])
    assert result == "Min: 2.00\nMax: 4.00\nMean: 3.00\nMedian: 4.00\nValid: 2"


def test_compute_statistics_single_value():
    result = compute_statistics([7.5])
    assert "Min: 7.50" in result
    assert "Max: 7.50" in result
    assert "Valid: 1" in result


def test_compute_statistics_valid_count():
    result = compute_statistics([1.0, 2.0, 3.0])
    assert "Valid: 3" in result


# ---------------------------------------------------------------------------
# legend_layout
# ---------------------------------------------------------------------------

def _make_leg(n=3):
    leg_ranges = [{'min': float(i), 'max': float(i + 1)} for i in range(n)]
    leg_colors = [(255, 0, 0, 255)] * n
    return leg_ranges, leg_colors


def test_legend_layout_vertical_segment_count():
    cfg = _make_cfg()
    lr, lc = _make_leg(4)
    layout = legend_layout(cfg, lr, lc)
    assert len(layout['segment_quads']) == 4
    assert len(layout['segment_argb']) == 4


def test_legend_layout_horizontal_segment_count():
    cfg = _make_cfg(vertical=False)
    lr, lc = _make_leg(3)
    layout = legend_layout(cfg, lr, lc)
    assert len(layout['segment_quads']) == 3


def test_legend_layout_vertical_differs_from_horizontal():
    lr, lc = _make_leg(3)
    layout_v = legend_layout(_make_cfg(vertical=True), lr, lc)
    layout_h = legend_layout(_make_cfg(vertical=False), lr, lc)
    assert layout_v['segment_quads'] != layout_h['segment_quads']


def test_legend_layout_no_title_label_count():
    cfg = _make_cfg()  # title=None
    lr, lc = _make_leg(3)
    layout = legend_layout(cfg, lr, lc)
    # No title → labels count == number of segments
    assert len(layout['labels']) == 3


def test_legend_layout_with_title_label_count():
    cfg = _make_cfg(title="MyTitle")
    lr, lc = _make_leg(3)
    layout = legend_layout(cfg, lr, lc)
    # Title first, then 3 segment labels
    assert len(layout['labels']) == 4
    assert layout['labels'][0][2] == "MyTitle"


def test_legend_layout_vertical_label_format():
    cfg = _make_cfg(decimals=2)
    lr = [{'min': 0.0, 'max': 5.0}]
    lc = [(255, 0, 0, 255)]
    layout = legend_layout(cfg, lr, lc)
    label_text = layout['labels'][0][2]
    assert label_text == "0.00 - 5.00"


def test_legend_layout_horizontal_label_format():
    cfg = _make_cfg(vertical=False, decimals=2)
    lr = [{'min': 0.0, 'max': 5.0}]
    lc = [(255, 0, 0, 255)]
    layout = legend_layout(cfg, lr, lc)
    label_text = layout['labels'][0][2]
    assert label_text == "0.00-5.00"


def test_legend_layout_segment_quad_has_4_corners():
    cfg = _make_cfg()
    lr, lc = _make_leg(2)
    layout = legend_layout(cfg, lr, lc)
    for quad in layout['segment_quads']:
        assert len(quad) == 4
        for corner in quad:
            assert len(corner) == 2  # (x, y)


def test_legend_layout_scale_affects_coords():
    lr, lc = _make_leg(2)
    layout1 = legend_layout(_make_cfg(scale=1.0), lr, lc)
    layout2 = legend_layout(_make_cfg(scale=2.0), lr, lc)
    # Second segment top y should be doubled
    y1 = layout1['segment_quads'][1][2][1]
    y2 = layout2['segment_quads'][1][2][1]
    assert abs(y2 - 2 * y1) < 1e-9
