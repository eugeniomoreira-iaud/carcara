"""Tests for crc_modules.geometry.dash.parse_dash_pattern."""
import pytest
from crc_modules.geometry.dash import parse_dash_pattern


def test_two_values():
    assert parse_dash_pattern("5 2") == [5.0, 2.0]


def test_single_value():
    assert parse_dash_pattern("3") == [3.0]


def test_empty_string_returns_none():
    assert parse_dash_pattern("") is None


def test_whitespace_only_returns_none():
    assert parse_dash_pattern("   ") is None


def test_none_returns_none():
    assert parse_dash_pattern(None) is None


def test_non_numeric_raises():
    with pytest.raises(ValueError, match="abc is not a valid number"):
        parse_dash_pattern("abc 1")


def test_negative_raises():
    with pytest.raises(ValueError, match="strictly positive"):
        parse_dash_pattern("-1 2")


def test_zero_raises():
    with pytest.raises(ValueError, match="strictly positive"):
        parse_dash_pattern("0 1")
