"""Tests for crc_modules/utils/correction.py

Covers:
- validate_offset  (pure helper)
- translate_expr   (pure helper)
- find_correction_parameters (DB function, all psycopg2 mocked)
"""
import pytest
from unittest.mock import patch, MagicMock

from crc_modules.utils.correction import (
    validate_offset,
    translate_expr,
    find_correction_parameters,
)


# ---------------------------------------------------------------------------
# validate_offset
# ---------------------------------------------------------------------------

def test_validate_offset_integer_string():
    assert validate_offset("9500000") == "9500000"


def test_validate_offset_float_string():
    assert validate_offset("500123.45") == "500123.45"


def test_validate_offset_zero():
    assert validate_offset("0") == "0"


def test_validate_offset_negative():
    assert validate_offset("-100.5") == "-100.5"


def test_validate_offset_injection_raises():
    with pytest.raises(ValueError):
        validate_offset("5e5; DROP TABLE")


def test_validate_offset_empty_raises():
    with pytest.raises(ValueError):
        validate_offset("")


def test_validate_offset_scientific_notation_raises():
    # Scientific notation must be rejected (not a safe SQL numeric literal)
    with pytest.raises(ValueError):
        validate_offset("1e6")


def test_validate_offset_returns_str_not_float():
    # Must return the string unchanged — never a float
    result = validate_offset("9500000")
    assert isinstance(result, str)
    assert result == "9500000"   # NOT "9500000.0"


# ---------------------------------------------------------------------------
# translate_expr
# ---------------------------------------------------------------------------

def test_translate_expr_to_local():
    result = translate_expr("geom", "500000", "9500000", "to_local")
    assert result == "ST_Translate(geom, -500000, -9500000)"


def test_translate_expr_to_projected():
    result = translate_expr("geom", "500000", "9500000", "to_projected")
    assert result == "ST_Translate(geom, 500000, 9500000)"


def test_translate_expr_invalid_direction():
    with pytest.raises(ValueError):
        translate_expr("geom", "0", "0", "unknown")


def test_translate_expr_cx_cy_embedded_verbatim():
    # The exact text must appear verbatim in the output — no float conversion
    result = translate_expr("g", "500123.45", "9483210.78", "to_local")
    assert "500123.45" in result
    assert "9483210.78" in result
    # Must not appear as reformatted float
    assert "500123.450" not in result


def test_translate_expr_invalid_offset_raises():
    with pytest.raises(ValueError):
        translate_expr("g", "1e6", "0", "to_local")


# ---------------------------------------------------------------------------
# Helpers for mocking psycopg2
#
# find_correction_parameters makes 2 DB calls:
#   1. detect_geometry_column (via spatial_query._get_connection) — uses fetchall
#   2. centroid SELECT                                             — uses fetchone
#
# Both go through the same psycopg2.connect so we use side_effect to sequence them.
# ---------------------------------------------------------------------------

FAKE_CSTRING = "host=localhost port=5432 dbname=testdb user=u password=cGFzcw=="


def _make_geom_col_conn(geom_col_name):
    """Mock connection for detect_geometry_column (calls cursor.fetchall)."""
    cur = MagicMock()
    cur.fetchall.return_value = [(geom_col_name,)] if geom_col_name else []
    cur.__enter__ = lambda s: cur
    cur.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


def _make_centroid_conn(cx_text, cy_text):
    """Mock connection for centroid SELECT (calls cursor.fetchone)."""
    cur = MagicMock()
    cur.fetchone.return_value = (cx_text, cy_text) if cx_text is not None else None
    cur.__enter__ = lambda s: cur
    cur.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


# ---------------------------------------------------------------------------
# find_correction_parameters — filtered case (column + value given)
# ---------------------------------------------------------------------------

@patch("psycopg2.connect")
def test_find_correction_filtered_returns_verbatim_text(mock_connect):
    """Returns verbatim text strings from DB — not floats, not reformatted."""
    geom_col_conn, _ = _make_geom_col_conn("geom")
    centroid_conn, _ = _make_centroid_conn("500123.45", "9483210.78")
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    cx, cy = find_correction_parameters(
        FAKE_CSTRING, "public", "buildings", column="id", value="42"
    )

    assert cx == "500123.45"    # verbatim text, not float
    assert cy == "9483210.78"   # verbatim text, not float
    assert isinstance(cx, str)
    assert isinstance(cy, str)


@patch("psycopg2.connect")
def test_find_correction_filtered_sql_has_params(mock_connect):
    """Filtered case: execute is called with params tuple containing the value."""
    geom_col_conn, _ = _make_geom_col_conn("geom")
    centroid_conn, centroid_cur = _make_centroid_conn("100.0", "200.0")
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    find_correction_parameters(
        FAKE_CSTRING, "public", "mytable", column="name", value="Centro"
    )

    centroid_cur.execute.assert_called_once()
    call_args = centroid_cur.execute.call_args
    # The value "Centro" should appear in the params argument
    params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params")
    assert params == ("Centro",)


# ---------------------------------------------------------------------------
# find_correction_parameters — fallback case (no column / value)
# ---------------------------------------------------------------------------

@patch("psycopg2.connect")
def test_find_correction_fallback_returns_text(mock_connect):
    """Fallback: column=None, value=None → returns verbatim text from DB."""
    geom_col_conn, _ = _make_geom_col_conn("the_geom")
    centroid_conn, _ = _make_centroid_conn("300.5", "400.5")
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    cx, cy = find_correction_parameters(FAKE_CSTRING, "public", "mytable")

    assert cx == "300.5"
    assert cy == "400.5"
    assert isinstance(cx, str)
    assert isinstance(cy, str)


@patch("psycopg2.connect")
def test_find_correction_fallback_no_params(mock_connect):
    """Fallback path: execute is called with only SQL (no params tuple)."""
    geom_col_conn, _ = _make_geom_col_conn("geom")
    centroid_conn, centroid_cur = _make_centroid_conn("1.0", "2.0")
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    find_correction_parameters(FAKE_CSTRING, "public", "mytable")

    centroid_cur.execute.assert_called_once()
    call_args = centroid_cur.execute.call_args
    # Fallback: execute called with only 1 positional arg (the SQL), no params
    assert len(call_args[0]) == 1


@patch("psycopg2.connect")
def test_find_correction_fallback_sql_no_where(mock_connect):
    """Verify the composed SQL object does not contain WHERE for the fallback case."""
    geom_col_conn, _ = _make_geom_col_conn("geom")
    centroid_conn, centroid_cur = _make_centroid_conn("1.0", "2.0")
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    find_correction_parameters(FAKE_CSTRING, "public", "mytable")

    centroid_cur.execute.assert_called_once()
    call_args = centroid_cur.execute.call_args
    # SQL is a psycopg2.sql.Composed object — inspect its string representation
    executed_sql_arg = call_args[0][0]
    # Use the object's __repr__ or string form to check for WHERE / LIMIT
    # psycopg2.sql.SQL.string property on the fragments is more reliable in tests
    import psycopg2.sql as _sql
    assert isinstance(executed_sql_arg, _sql.Composed)
    # Reconstruct the raw template text from the Composed fragments
    # psycopg2.sql.SQL items store their text in _wrapped
    template_parts = []
    for item in executed_sql_arg._wrapped:
        if isinstance(item, _sql.SQL):
            template_parts.append(item._wrapped)
    full_template = "".join(template_parts)
    assert "WHERE" not in full_template.upper()
    assert "LIMIT 1" in full_template.upper()


# ---------------------------------------------------------------------------
# find_correction_parameters — ValueError on no rows
# ---------------------------------------------------------------------------

@patch("psycopg2.connect")
def test_find_correction_raises_on_empty_result_filtered(mock_connect):
    """Raises ValueError when query returns no rows (filtered case)."""
    geom_col_conn, _ = _make_geom_col_conn("geom")
    centroid_conn, _ = _make_centroid_conn(None, None)   # no rows
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    with pytest.raises(ValueError):
        find_correction_parameters(
            FAKE_CSTRING, "public", "mytable", column="id", value="999"
        )


@patch("psycopg2.connect")
def test_find_correction_raises_on_empty_result_fallback(mock_connect):
    """Raises ValueError when query returns no rows (fallback / empty table)."""
    geom_col_conn, _ = _make_geom_col_conn("geom")
    centroid_conn, _ = _make_centroid_conn(None, None)   # empty table
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    with pytest.raises(ValueError):
        find_correction_parameters(FAKE_CSTRING, "public", "emptytable")


# ---------------------------------------------------------------------------
# find_correction_parameters — geometry column auto-detect invoked first
# ---------------------------------------------------------------------------

@patch("psycopg2.connect")
def test_find_correction_detects_geometry_column_first(mock_connect):
    """connect is called twice: once for geometry detection, once for centroid."""
    geom_col_conn, _ = _make_geom_col_conn("the_geom")
    centroid_conn, _ = _make_centroid_conn("50.0", "60.0")
    mock_connect.side_effect = [geom_col_conn, centroid_conn]

    cx, cy = find_correction_parameters(FAKE_CSTRING, "public", "buildings")

    # Two connections must have been opened: geometry detection + centroid query
    assert mock_connect.call_count == 2
    assert cx == "50.0"
    assert cy == "60.0"


@patch("psycopg2.connect")
def test_find_correction_raises_when_no_geometry_column(mock_connect):
    """Raises ValueError when detect_geometry_column returns None (no geom column)."""
    geom_col_conn, _ = _make_geom_col_conn(None)   # fetchall returns []
    mock_connect.side_effect = [geom_col_conn]

    with pytest.raises(ValueError, match="No geometry column"):
        find_correction_parameters(FAKE_CSTRING, "public", "notageotable")

    # Only one connect call — centroid query must NOT be issued
    assert mock_connect.call_count == 1
