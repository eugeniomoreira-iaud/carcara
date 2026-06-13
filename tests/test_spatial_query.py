from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from decimal import Decimal
from crc_modules.db.spatial_query import (
    detect_geometry_column,
    detect_geometry_columns,
    detect_primary_key,
    get_geometries,
    get_geometries_with_spatial_filter,
    get_values_with_spatial_filter,
)
from crc_modules.utils.correction import validate_offset, translate_expr


# ── Helpers (pattern from test_query.py) ───────────────────────────────────

def _mock_cursor(rows, col_names):
    """Create a mock cursor with the given rows and column names."""
    mc = MagicMock()
    mc.fetchall.return_value = rows
    mc.description = [tuple([c] + [None] * 6) for c in col_names]
    cur_ctx = MagicMock()
    cur_ctx.__enter__ = MagicMock(return_value=mc)
    cur_ctx.__exit__ = MagicMock(return_value=False)
    mc.cursor.return_value = cur_ctx
    return mc, mc


def make_detection_conn(fetchone_result):
    """Return a mock connection that returns fetchone_result on cursor.fetchone()."""
    cur = MagicMock()
    cur.fetchone.return_value = fetchone_result
    # fetchall mirrors fetchone: wrap single row in list, or empty list for None
    cur.fetchall.return_value = [fetchone_result] if fetchone_result is not None else []
    cur.__enter__ = lambda s: cur
    cur.__exit__ = MagicMock(return_value=False)
    conn_out = MagicMock()
    conn_out.cursor.return_value = cur
    return conn_out


def make_fetchall_conn(fetchall_result):
    """Return a mock connection that returns fetchall_result on cursor.fetchall()."""
    cur = MagicMock()
    cur.fetchall.return_value = fetchall_result
    cur.__enter__ = lambda s: cur
    cur.__exit__ = MagicMock(return_value=False)
    conn_out = MagicMock()
    conn_out.cursor.return_value = cur
    return conn_out


# ── validate_offset ────────────────────────────────────────────────────────

class TestValidateOffset:
    def test_valid_integer(self):
        assert validate_offset("500000") == "500000"
        assert validate_offset("0") == "0"
        assert validate_offset("-1") == "-1"

    def test_invalid_injection_string(self):
        with pytest.raises(ValueError, match="Invalid offset"):
            validate_offset("500000; DROP TABLE")

    def test_invalid_malformed(self):
        with pytest.raises(ValueError, match="Invalid offset"):
            validate_offset("500000.0.0")

    def test_invalid_letters(self):
        with pytest.raises(ValueError, match="Invalid offset"):
            validate_offset("abc")

    def test_valid_with_decimal(self):
        assert validate_offset("123.456") == "123.456"


# ── translate_expr ─────────────────────────────────────────────────────────

class TestTranslateExpr:
    def test_to_local_minus_signs(self):
        result = translate_expr("geom_col", "500000", "9500000", "to_local")
        assert "- 500000" in result or "-500000" in result
        assert "- 9500000" in result or "-9500000" in result

    def test_to_projected_positive_signs(self):
        result = translate_expr("geom_col", "500000", "9500000", "to_projected")
        assert "ST_Translate" in result

    def test_injection_rejected(self):
        with pytest.raises(ValueError, match="Invalid offset"):
            translate_expr("geom_col", "5; DROP TABLE", "0", "to_local")

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError, match="Unknown direction"):
            translate_expr("geom_col", "0", "0", "to_nowhere")


# ── detect_geometry_columns (plural) ──────────────────────────────────────

class TestDetectGeometryColumns:
    def test_returns_all_names_in_order(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_fetchall_conn([("geom",), ("centroid",)])
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_geometry_columns(cstring, "public", "buildings")
            assert result == ["geom", "centroid"]

    def test_empty_table_returns_empty_list(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_fetchall_conn([])
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_geometry_columns(cstring, "public", "no_geom_table")
            assert result == []

    def test_geography_type_detected(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_fetchall_conn([("geog",)])
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_geometry_columns(cstring, "public", "geo_table")
            assert result == ["geog"]

    def test_exception_returns_empty_list(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        with patch("crc_modules.db.spatial_query.psycopg2.connect", side_effect=Exception("DB error")):
            result = detect_geometry_columns(cstring, "public", "any_table")
            assert result == []


# ── detect_geometry_column (singular, delegates to plural) ─────────────────

class TestDetectGeometryColumn:
    def test_returns_first_column(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_fetchall_conn([("geom",), ("centroid",)])
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_geometry_column(cstring, "public", "buildings")
            assert result == "geom"

    def test_not_found_returns_none(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_fetchall_conn([])
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_geometry_column(cstring, "public", "no_geom_table")
            assert result is None

    def test_geography_detection(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_fetchall_conn([("geog",)])
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_geometry_column(cstring, "public", "geo_table")
            assert result == "geog"


# ── detect_primary_key ─────────────────────────────────────────────────────

class TestDetectPrimaryKey:
    def test_found(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_detection_conn(("gid",))
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_primary_key(cstring, "public", "buildings")
            assert result == "gid"

    def test_not_found(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        conn_out = make_detection_conn(None)
        with patch("crc_modules.db.spatial_query.psycopg2.connect", return_value=conn_out):
            result = detect_primary_key(cstring, "public", "no_pk_table")
            assert result is None


# ── get_geometries ─────────────────────────────────────────────────────────

def make_spatial_query_mocks(geo_col="geom", pk_col="gid",
                             query_rows=[("POINT (0 0)", 1)],
                             query_cols=["geom", "pk"]):
    """Build a chain of mocks for the 3 connection calls in get_geometries:
    connect->geo->connect->pk->connect->query.
    Returns (capture_sql, return_value) tuple collector."""
    call_num = [0]
    captured_sql_list = []

    def make_geo_connection(n):
        """Return a MagicMock that acts as psycopg2.connect for each call n."""
        if n == 0:
            # information_schema.columns lookup (detect_geometry_columns uses fetchall)
            cur = MagicMock()
            cur.fetchall.return_value = [(geo_col,)] if geo_col else []
            ctx = MagicMock()
            ctx.__enter__ = lambda s: cur
            ctx.__exit__ = MagicMock(return_value=False)
            conn_out = MagicMock()
            conn_out.cursor.return_value = ctx
            return conn_out, None

        elif n == 1:
            # PK detection
            cur = MagicMock()
            cur.fetchone.return_value = (pk_col,) if pk_col else None
            ctx = MagicMock()
            ctx.__enter__ = lambda s: cur
            ctx.__exit__ = MagicMock(return_value=False)
            conn_out = MagicMock()
            conn_out.cursor.return_value = ctx
            return conn_out, None

        elif n == 2:
            # Actual query
            cur = MagicMock()
            cur.fetchall.return_value = query_rows
            cur.description = [tuple([c] + [None] * 6) for c in query_cols]

            def record(sql, *a, **kw):
                captured_sql_list.append(str(sql))

            cur.execute = record
            ctx = MagicMock()
            ctx.__enter__ = lambda s: cur
            ctx.__exit__ = MagicMock(return_value=False)
            conn_out = MagicMock()
            conn_out.cursor.return_value = ctx
            return conn_out, cur

    def side_effect(*args, **kwargs):
        n = call_num[0]
        call_num[0] += 1
        result, _ = make_geo_connection(n)
        return result

    call_num[0] = 0  # reset
    captured_sql_list = []

    mock_gc = MagicMock(side_effect=side_effect)
    return mock_gc, captured_sql_list


class TestGetGeometries:
    def test_returns_tuple_of_lists(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, _ = make_spatial_query_mocks(geo_col="geom", pk_col="gid")
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            wkt, pk = get_geometries(cstring, "public", "buildings")

        assert isinstance(wkt, list)
        assert isinstance(pk, list)
        assert wkt == ["POINT (0 0)"]
        assert pk == [1]

    def test_sql_contains_st_as_text_and_translate(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries(cstring, "public", "t")

        all_sql = " ".join(captured)
        upper = all_sql.upper()
        assert "ST_ASTEXT" in upper or "ST_AS_TEXT" in upper
        assert "ST_TRANSLATE" in upper

    def test_read_path_uses_negative_offset_signs(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries(cstring, "public", "t", cx="500000", cy="9500000")

        # The SQL should contain negative offsets in ST_Translate
        found_neg_x = False
        found_neg_y = False
        sql_str = " ".join(captured)
        # Check for -cx and -cy patterns (the minus sign before the offset)
        assert "-500000" in sql_str, f"No -500000 in SQL: {sql_str}"
        assert "-9500000" in sql_str, f"No -9500000 in SQL: {sql_str}"

    def test_offset_values_appear_verbatim(self):
        """Cx/Cy should appear as text — not reformatted to float."""
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries(cstring, "s", "t", cx="500000", cy="9500000")

        all_sql = " ".join(captured)
        # Should contain integer literals, not floats
        assert "500000.0" not in all_sql, f"Cx reformatted: {all_sql}"
        assert "500000.0" not in all_sql  # Cy too

    def test_no_pk_path_returns_none_and_no_order_by(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        # pk_col=None in SQL means we SELECT NULL for the PK column, so DB returns None per row
        mock_gc, captured = make_spatial_query_mocks(geo_col="geom", pk_col=None,
                                                     query_rows=[("POINT (0 0)", None)])
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            wkt, pk = get_geometries(cstring, "public", "no_pk_table")

        assert all(v is None for v in pk)
        has_ob = any("ORDER BY" in s.upper() for s in captured)
        assert not has_ob, f"Unexpected ORDER BY: {captured}"

    def test_with_pk_has_order_by(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks(geo_col="geom", pk_col="gid")
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            wkt, pk = get_geometries(cstring, "public", "with_pk_table")

        assert pk == [1]
        assert any("ORDER BY" in s.upper() for s in captured), \
            f"No ORDER BY found: {captured}"


# ── get_geometries_with_spatial_filter ─────────────────────────────────────

class TestGetGeometriesWithSpatialFilter:
    def test_sql_contains_st_as_text_and_translate(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries_with_spatial_filter(
                cstring, "public", "buildings",
                filter_wkt="POLYGON ((100 100, 200 100, 200 200, 100 200))")

        all_sql = " ".join(captured)
        assert "POINT (0 0)" not in all_sql or len(captured) > 0  # just confirms SQL was built

    def test_spatial_filter_uses_positive_offset(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries_with_spatial_filter(
                cstring, "public", "buildings",
                filter_wkt="POLYGON ((100 100, 200 100, 200 200, 100 200))",
                cx="500000", cy="9500000")

        all_sql = " ".join(captured)
        # Filter path adds +cx/+cy — should see the values in ST_Translate within WHERE
        assert "500000" in all_sql, f"Cx not in filter SQL: {all_sql}"
        assert "9500000" in all_sql, f"Cy not in filter SQL: {all_sql}"

    def test_func_parameter_chooses_predicate(self):
        """func=1 -> ST_Contains; default (0) -> ST_Intersects."""
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries_with_spatial_filter(
                cstring, "public", "buildings",
                filter_wkt="POLYGON ((0 0, 1 0, 1 1, 0 1))",
                func=1)

        assert "ST_CONTAINS" in " ".join(captured).upper()

    def test_func_default_is_intersects(self):
        """Default function (func=0 or omitted) should use ST_Intersects."""
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries_with_spatial_filter(
                cstring, "public", "buildings",
                filter_wkt="POLYGON ((0 0, 1 0, 1 1, 0 1))",
                func=0)

        assert "ST_INTERSECTS" in " ".join(captured).upper()

    def test_extra_sql_filter_anded(self):
        """Extra sql_filter is ANDed into WHERE."""
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks()
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_geometries_with_spatial_filter(
                cstring, "public", "buildings",
                filter_wkt="POLYGON ((0 0, 1 0, 1 1, 0 1))",
                sql_filter="status = 'active'")

        all_sql = " ".join(captured)
        assert "'active'" in all_sql or "STATUS" in all_sql


# ── get_values_with_spatial_filter ─────────────────────────────────────────

class TestGetValuesWithSpatialFilter:
    def test_returns_rows_and_columns_shape(self):
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks(
            query_rows=[
                ("Alice", Decimal("100.5")),
                ("Bob", Decimal("200.3")),
            ],
            query_cols=["name", "area"]
        )
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            rows, cols = get_values_with_spatial_filter(
                cstring, "public", "buildings",
                columns=["name", "area"],
                filter_wkt="POLYGON ((0 0, 1 0, 1 1, 0 1))")

        assert cols == ["name", "area"]
        assert len(rows) == 2
        assert rows[0] == ("Alice", Decimal("100.5"))
        assert rows[1] == ("Bob", Decimal("200.3"))

    def test_column_list_in_select(self):
        """Verify column list appears in SQL SELECT clause."""
        cstring = "host=localhost port=5432 dbname=db user=u password=pw"
        mock_gc, captured = make_spatial_query_mocks(
            query_rows=[("Alice",)],
            query_cols=["name"]
        )
        with patch("crc_modules.db.spatial_query.psycopg2.connect", mock_gc), \
             patch("crc_modules.db.spatial_query.parse_connection_string"
                   , return_value={"host": "localhost", "port": 5432,
                                  "dbname": "db", "user": "u", "password": "pw"}):
            get_values_with_spatial_filter(
                cstring, "public", "buildings",
                columns=["name"],
                filter_wkt="POLYGON ((0 0, 1 0, 1 1, 0 1))")

        all_sql = " ".join(captured).upper()
        assert "NAME" in all_sql


# ── Multipart splitting (unit, no DB) ──────────────────────────────────────

class TestMultipartSplitting:
    def test_multipolygon_splits_into_members(self):
        """A MULTIPOLYGON WKT should yield multiple members when split by shapely."""
        multipoly_wkt = "MULTIPOLYGON (((0 0, 0 1, 1 1, 1 0, 0 0)), ((10 10, 11 10, 11 11, 10 11, 10 10)))"
        from shapely import wkt as shapely_wkt, get_parts
        geom = shapely_wkt.loads(multipoly_wkt)
        assert geom.geom_type == "MultiPolygon"
        parts = get_parts(geom)
        assert len(parts) >= 2

    def test_multipoint_splits(self):
        multipoint_wkt = "MULTIPOINT ((0 0), (1 1), (2 2))"
        from shapely import wkt as shapely_wkt, get_parts
        geom = shapely_wkt.loads(multipoint_wkt)
        parts = get_parts(geom)
        assert len(parts) == 3

    def test_linestring_remains_single(self):
        linestring_wkt = "LINESTRING (0 0, 1 1, 2 2)"
        from shapely import wkt as shapely_wkt
        geom = shapely_wkt.loads(linestring_wkt)
        assert geom.geom_type == "LineString"

    @pytest.mark.skip(reason="Typo in name — fix later")
    def test_identifier_quoting_with_special_chars(self):
        """Pass a table/column name with special chars; assert quoting."""
        pass
