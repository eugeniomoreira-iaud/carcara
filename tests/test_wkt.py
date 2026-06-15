"""Tests for crc_modules.geometry.wkt (pure shapely, no Rhino)."""
import pytest

from crc_modules.geometry.wkt import (
    wkt_to_shapely,
    shapely_to_wkt,
    wkt_list_to_points,
    split_multipart_wkt,
    is_multipart_wkt,
    classify_wkt,
    combine_to_multipart,
)


CANONICAL = [
    "POINT (1 2)",
    "LINESTRING (0 0, 1 1, 2 0)",
    "POLYGON ((0 0, 4 0, 4 4, 0 4, 0 0))",
    "MULTIPOINT ((0 0), (1 1))",
    "MULTILINESTRING ((0 0, 1 1), (2 2, 3 3))",
    "MULTIPOLYGON (((0 0, 1 0, 1 1, 0 1, 0 0)), ((2 2, 3 2, 3 3, 2 3, 2 2)))",
]


@pytest.mark.parametrize("s", CANONICAL)
def test_round_trip_geometric_equality(s):
    geom = wkt_to_shapely(s)
    back = wkt_to_shapely(shapely_to_wkt(geom))
    assert back.equals(geom)


@pytest.mark.parametrize("s,expected", [
    ("POINT (1 2)", "POINT"),
    ("LINESTRING (0 0, 1 1)", "LINESTRING"),
    ("POLYGON ((0 0, 4 0, 4 4, 0 0))", "POLYGON"),
    ("MULTIPOINT ((0 0), (1 1))", "MULTIPOINT"),
    ("MULTILINESTRING ((0 0, 1 1), (2 2, 3 3))", "MULTILINESTRING"),
    ("MULTIPOLYGON (((0 0, 1 0, 1 1, 0 0)))", "MULTIPOLYGON"),
    ("GEOMETRYCOLLECTION (POINT (1 2))", "GEOMETRYCOLLECTION"),
])
def test_classify_wkt(s, expected):
    assert classify_wkt(s) == expected


def test_wkt_list_to_points():
    pts = wkt_list_to_points(["POINT (1 2)", "POINT (3 4)", "LINESTRING (0 0, 1 1)"])
    assert pts == [(1.0, 2.0), (3.0, 4.0)]


def test_is_multipart_wkt():
    assert is_multipart_wkt("MULTIPOINT ((0 0))")
    assert not is_multipart_wkt("POINT (0 0)")


def test_split_multipart_wkt():
    parts = split_multipart_wkt("MULTIPOINT ((0 0), (1 1))")
    assert len(parts) == 2
    assert all(classify_wkt(p) == "POINT" for p in parts)


def test_split_multipart_single_passthrough():
    parts = split_multipart_wkt("POINT (0 0)")
    assert parts == ["POINT (0 0)"]


def test_combine_to_multipart_points():
    out = combine_to_multipart(["POINT (0 0)", "POINT (1 1)"])
    assert classify_wkt(out) == "MULTIPOINT"
    assert wkt_to_shapely(out).equals(wkt_to_shapely("MULTIPOINT ((0 0), (1 1))"))


def test_combine_to_multipart_lines():
    out = combine_to_multipart(["LINESTRING (0 0, 1 1)", "LINESTRING (2 2, 3 3)"])
    assert classify_wkt(out) == "MULTILINESTRING"


def test_combine_to_multipart_polygons():
    out = combine_to_multipart([
        "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
        "POLYGON ((2 2, 3 2, 3 3, 2 3, 2 2))",
    ])
    assert classify_wkt(out) == "MULTIPOLYGON"


def test_combine_to_multipart_mixed_raises():
    with pytest.raises(ValueError):
        combine_to_multipart(["POINT (0 0)", "LINESTRING (0 0, 1 1)"])


def test_combine_to_multipart_empty_raises():
    with pytest.raises(ValueError):
        combine_to_multipart([])
