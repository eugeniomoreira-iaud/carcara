"""
tests/test_svg.py
Tests for crc_modules/svg/export.py and crc_modules/svg/save.py.
No DB, no Rhino — plain CPython pytest.
"""

import os
import pytest

from crc_modules.svg.export import (
    polyline_to_svg,
    circle_to_svg,
    nurbs_to_svg,
    text_to_svg,
)
from crc_modules.svg.save import save_svg


# ---------------------------------------------------------------------------
# polyline_to_svg
# ---------------------------------------------------------------------------

class TestPolylineToSvg:
    def test_open_polyline_emits_polyline_tag(self):
        pts = [(0, 0), (10, 0), (10, 10)]
        result = polyline_to_svg(pts)
        assert "<polyline" in result
        assert "0,0" in result
        assert "10,0" in result

    def test_closed_polyline_emits_polygon_tag(self):
        # first == last → polygon; closing duplicate vertex dropped
        pts = [(0, 0), (10, 0), (10, 10), (0, 0)]
        result = polyline_to_svg(pts)
        assert "<polygon" in result
        # all 3 unique vertices appear in the points attr
        assert "0,0" in result
        assert "10,0" in result
        assert "10,10" in result
        # points attr should have exactly 3 vertex entries (not 4)
        import re
        points_match = re.search(r'points="([^"]+)"', result)
        assert points_match is not None
        vertex_count = len(points_match.group(1).split())
        assert vertex_count == 3

    def test_stroke_attribute_present(self):
        pts = [(0, 0), (5, 5)]
        result = polyline_to_svg(pts, stroke="red", stroke_width=2)
        assert 'stroke="red"' in result
        assert 'stroke-width="2"' in result

    def test_fill_none_default(self):
        pts = [(0, 0), (5, 5)]
        result = polyline_to_svg(pts)
        assert 'fill="none"' in result

    def test_dash_pattern_emitted(self):
        pts = [(0, 0), (20, 0)]
        result = polyline_to_svg(pts, dash="5,5")
        assert 'stroke-dasharray="5,5"' in result

    def test_empty_input_returns_empty_string(self):
        assert polyline_to_svg([]) == ""
        assert polyline_to_svg([(0, 0)]) == ""

    def test_fill_opacity_only_when_not_one(self):
        pts = [(0, 0), (5, 5)]
        result_full = polyline_to_svg(pts, fill="blue", fill_opacity=1.0)
        assert "fill-opacity" not in result_full

        result_partial = polyline_to_svg(pts, fill="blue", fill_opacity=0.5)
        assert 'fill-opacity="0.5"' in result_partial


# ---------------------------------------------------------------------------
# circle_to_svg
# ---------------------------------------------------------------------------

class TestCircleToSvg:
    def test_circle_tag_present(self):
        result = circle_to_svg(50, 50, 25)
        assert "<circle" in result
        assert 'cx="50"' in result
        assert 'cy="50"' in result
        assert 'r="25"' in result

    def test_stroke_and_fill(self):
        result = circle_to_svg(0, 0, 10, stroke="black", fill="white", stroke_width=1)
        assert 'stroke="black"' in result
        assert 'fill="white"' in result
        assert 'stroke-width="1"' in result

    def test_self_closing_tag(self):
        result = circle_to_svg(0, 0, 5)
        assert result.endswith("/>")

    def test_fractional_coords(self):
        result = circle_to_svg(12.3456789, 9.8765, 3.14159)
        assert "12.3457" in result  # rounded to 4 decimal places
        assert "9.8765" in result


# ---------------------------------------------------------------------------
# nurbs_to_svg
# ---------------------------------------------------------------------------

class TestNurbsToSvg:
    def test_path_tag_present(self):
        pts = [(0, 0), (5, 2), (10, 0), (15, 3)]
        result = nurbs_to_svg(pts)
        assert "<path" in result
        assert 'd="M' in result
        assert "L " in result

    def test_first_point_is_moveto(self):
        pts = [(3.0, 4.0), (7.0, 8.0)]
        result = nurbs_to_svg(pts)
        assert "M 3.0,4.0" in result

    def test_subsequent_points_are_lineto(self):
        pts = [(0, 0), (10, 5), (20, 0)]
        result = nurbs_to_svg(pts)
        # "L" commands for subsequent points (coords may be int-rounded)
        assert "L 10" in result and "5" in result
        assert "L 20" in result

    def test_empty_or_single_point_returns_empty(self):
        assert nurbs_to_svg([]) == ""
        assert nurbs_to_svg([(0, 0)]) == ""

    def test_style_attrs(self):
        pts = [(0, 0), (1, 1)]
        result = nurbs_to_svg(pts, stroke="blue", stroke_width=0.5, fill="none")
        assert 'stroke="blue"' in result
        assert 'stroke-width="0.5"' in result


# ---------------------------------------------------------------------------
# text_to_svg
# ---------------------------------------------------------------------------

class TestTextToSvg:
    def test_text_tag_present(self):
        result = text_to_svg(10, 20, "Hello")
        assert "<text" in result
        assert "</text>" in result
        assert "Hello" in result

    def test_position_attributes(self):
        result = text_to_svg(5.0, 15.0, "Test")
        assert 'x="5.0"' in result
        assert 'y="15.0"' in result

    def test_font_family_and_size(self):
        result = text_to_svg(0, 0, "X", font_family="Helvetica", font_size=24)
        assert 'font-family="Helvetica"' in result
        assert 'font-size="24"' in result

    def test_text_anchor(self):
        result = text_to_svg(0, 0, "A", text_anchor="middle")
        assert 'text-anchor="middle"' in result

    def test_dominant_baseline(self):
        result = text_to_svg(0, 0, "A", dominant_baseline="hanging")
        assert 'dominant-baseline="hanging"' in result

    def test_rotation_transform(self):
        result = text_to_svg(10, 10, "R", rotation=45)
        assert 'transform="rotate(' in result
        assert "45" in result

    def test_no_rotation_transform_when_zero(self):
        result = text_to_svg(0, 0, "Z", rotation=0)
        assert "transform" not in result

    def test_html_escape(self):
        result = text_to_svg(0, 0, "<b>&me</b>")
        assert "&lt;" in result
        assert "&amp;" in result
        assert "<b>" not in result

    def test_default_fill_black(self):
        result = text_to_svg(0, 0, "Hi")
        assert 'fill="black"' in result

    def test_fill_opacity_applied_when_not_one(self):
        result = text_to_svg(0, 0, "X", fill_opacity=0.75)
        assert 'fill-opacity="0.75"' in result

    def test_no_fill_opacity_when_one(self):
        result = text_to_svg(0, 0, "X", fill_opacity=1.0)
        assert "fill-opacity" not in result


# ---------------------------------------------------------------------------
# save_svg
# ---------------------------------------------------------------------------

class TestSaveSvg:
    def test_writes_file(self, tmp_path):
        out = tmp_path / "test.svg"
        path = save_svg(["<circle/>"], str(out), 200, 100)
        assert os.path.isfile(path)

    def test_returns_absolute_path(self, tmp_path):
        out = tmp_path / "out.svg"
        returned = save_svg(["<rect/>"], str(out), 100, 100)
        assert os.path.isabs(returned)

    def test_file_contains_elements(self, tmp_path):
        elem1 = '<circle cx="5" cy="5" r="3"/>'
        elem2 = '<rect x="0" y="0" width="10" height="10"/>'
        out = tmp_path / "elems.svg"
        save_svg([elem1, elem2], str(out), 100, 100)
        content = out.read_text(encoding="utf-8")
        assert elem1 in content
        assert elem2 in content

    def test_svg_open_and_close_tags(self, tmp_path):
        out = tmp_path / "doc.svg"
        save_svg(["<line/>"], str(out), 50, 50)
        content = out.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "</svg>" in content

    def test_viewbox_default(self, tmp_path):
        out = tmp_path / "vb.svg"
        save_svg(["<g/>"], str(out), 300, 200)
        content = out.read_text(encoding="utf-8")
        assert 'viewBox="0 0 300 200"' in content

    def test_custom_viewbox(self, tmp_path):
        out = tmp_path / "vbc.svg"
        save_svg(["<g/>"], str(out), 300, 200, viewbox=(10, 20, 280, 180))
        content = out.read_text(encoding="utf-8")
        assert 'viewBox="10 20 280 180"' in content

    def test_units_in_width_height(self, tmp_path):
        out = tmp_path / "units.svg"
        save_svg(["<g/>"], str(out), 210, 297, units="mm")
        content = out.read_text(encoding="utf-8")
        assert 'width="210mm"' in content
        assert 'height="297mm"' in content

    def test_empty_elements_skipped(self, tmp_path):
        out = tmp_path / "empty.svg"
        save_svg(["", "<circle/>", ""], str(out), 100, 100)
        content = out.read_text(encoding="utf-8")
        assert "<circle/>" in content

    def test_empty_out_path_raises(self, tmp_path):
        with pytest.raises(ValueError):
            save_svg(["<g/>"], "", 100, 100)

    def test_creates_parent_directories(self, tmp_path):
        out = tmp_path / "nested" / "deep" / "file.svg"
        save_svg(["<g/>"], str(out), 100, 100)
        assert out.is_file()
