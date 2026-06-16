from unittest.mock import patch, MagicMock
import pytest
import psycopg2
from psycopg2 import sql as _sql


# ---------------------------------------------------------------------------
# Helper: flatten a psycopg2.sql Composed/SQL/Identifier/Literal into a string
# ---------------------------------------------------------------------------

def flatten(comp) -> str:
    """Recursively traverse a psycopg2.sql object and return all parts joined."""
    parts = []
    _flatten_into(comp, parts)
    return " ".join(parts)


def _flatten_into(x, parts):
    if isinstance(x, _sql.Composed):
        for child in x.seq:
            _flatten_into(child, parts)
    elif isinstance(x, _sql.SQL):
        parts.append(x.string)
    elif isinstance(x, _sql.Identifier):
        parts.append('"' + '"."'.join(x.strings) + '"')
    elif isinstance(x, _sql.Literal):
        parts.append(str(x.wrapped))
    else:
        parts.append(str(x))


# ---------------------------------------------------------------------------
# Helper: build a mock connection + cursor pair
# ---------------------------------------------------------------------------

def _make_mock_conn():
    cur = MagicMock()
    cur.__enter__ = lambda s: cur
    cur.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_create_table_basic():
    """No geom column. SQL has CREATE TABLE, quoted schema/table/column names."""
    conn, cur = _make_mock_conn()
    cur.rowcount = -1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table
        result = create_table("fake_cs", "myschema", "mytable", [("name", "TEXT"), ("area", "double precision")])
    # Only one execute call (no replace_table)
    assert cur.execute.call_count == 1
    composed = cur.execute.call_args[0][0]
    text = flatten(composed)
    assert "CREATE TABLE" in text
    assert '"myschema"' in text
    assert '"mytable"' in text
    assert '"name"' in text
    assert "TEXT" in text


def test_create_table_with_geometry():
    """With geom_column/geom_type/srid: SQL includes geometry( and srid."""
    conn, cur = _make_mock_conn()
    cur.rowcount = -1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table
        create_table("fake_cs", "myschema", "mytable", [("name", "TEXT")],
                     geom_column="geom", geom_type="POLYGON", srid=4326)
    composed = cur.execute.call_args[0][0]
    text = flatten(composed)
    assert "geometry(" in text
    assert "POLYGON" in text
    assert "4326" in text


def test_create_table_replace_drops_first():
    """replace_table=True: execute called twice; first is DROP, second is CREATE."""
    conn, cur = _make_mock_conn()
    cur.rowcount = -1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table
        create_table("fake_cs", "myschema", "mytable", [("name", "TEXT")], replace_table=True)
    assert cur.execute.call_count == 2
    first_text = flatten(cur.execute.call_args_list[0][0][0])
    second_text = flatten(cur.execute.call_args_list[1][0][0])
    assert "DROP TABLE IF EXISTS" in first_text
    assert "CREATE TABLE" in second_text


def test_insert_geometries_cx_cy_verbatim():
    """cx/cy appear verbatim in SQL, NOT in bound params."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import insert_geometries
        insert_geometries("fake_cs", "myschema", "mytable", "geom",
                         ["POINT (1 2)"], 4326, cx="500000", cy="9500000")
    composed, params = cur.executemany.call_args[0]
    text = flatten(composed)
    assert "ST_Translate(ST_GeomFromText(%s, %s), 500000, 9500000)" in text
    # cx/cy must NOT be in bound params
    assert len(params) == 1
    assert params[0] == ("POINT (1 2)", 4326)


def test_insert_geometries_zero_offset():
    """cx='0', cy='0': SQL has ST_Translate(ST_GeomFromText(%s, %s), 0, 0)."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import insert_geometries
        insert_geometries("fake_cs", "myschema", "mytable", "geom",
                         ["POINT (0 0)"], 4326, cx="0", cy="0")
    composed, params = cur.executemany.call_args[0]
    text = flatten(composed)
    assert "ST_Translate(ST_GeomFromText(%s, %s), 0, 0)" in text


def test_insert_with_attribute_columns():
    """With column_names+values: extra identifiers in SQL; params row has 3 elements."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import insert_geometries
        insert_geometries("fake_cs", "myschema", "mytable", "geom",
                         ["POINT (1 2)"], 4326,
                         column_names=["name"], values=[["Alice"]])
    composed, params = cur.executemany.call_args[0]
    text = flatten(composed)
    assert '"name"' in text
    assert len(params) == 1
    assert len(params[0]) == 3  # wkt, srid, "Alice"
    assert params[0][2] == "Alice"


def test_insert_propagates_db_error():
    """When connect raises OperationalError, insert_geometries raises it."""
    import psycopg2 as pg2
    with patch("crc_modules.db.writer.psycopg2.connect",
               side_effect=pg2.OperationalError("fail")), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import insert_geometries
        with pytest.raises(pg2.OperationalError, match="fail"):
            insert_geometries("fake_cs", "s", "t", "geom", ["POINT (0 0)"], 4326)


def test_no_float_in_source():
    """Source must not contain float(cx) or float(cy)."""
    import inspect
    import crc_modules.db.writer as w
    src = inspect.getsource(w)
    assert "float(cx)" not in src
    assert "float(cy)" not in src


# ---------------------------------------------------------------------------
# coerce_value tests
# ---------------------------------------------------------------------------

def test_coerce_value_integer_types():
    from crc_modules.db.writer import coerce_value
    assert coerce_value("42", "integer") == 42
    assert isinstance(coerce_value("42", "integer"), int)
    assert coerce_value("7", "int4") == 7
    assert coerce_value("100", "bigint") == 100
    assert coerce_value("1", "serial") == 1
    assert coerce_value("0", "smallint") == 0


def test_coerce_value_float_types():
    from crc_modules.db.writer import coerce_value
    assert coerce_value("3.14", "double precision") == pytest.approx(3.14)
    assert isinstance(coerce_value("2.5", "float"), float)
    assert coerce_value("1.0", "numeric") == pytest.approx(1.0)
    assert coerce_value("9.9", "real") == pytest.approx(9.9)


def test_coerce_value_bool_types():
    from crc_modules.db.writer import coerce_value
    assert coerce_value("true", "boolean") is True
    assert coerce_value("True", "bool") is True
    assert coerce_value("t", "boolean") is True
    assert coerce_value("1", "boolean") is True
    assert coerce_value("yes", "boolean") is True
    assert coerce_value("false", "bool") is False
    assert coerce_value("f", "boolean") is False
    assert coerce_value("0", "bool") is False
    assert coerce_value("no", "boolean") is False


def test_coerce_value_text_types():
    from crc_modules.db.writer import coerce_value
    assert coerce_value("hello", "text") == "hello"
    assert coerce_value("abc", "varchar(50)") == "abc"
    assert coerce_value("2024-01-01", "date") == "2024-01-01"
    assert coerce_value("{}", "json") == "{}"


def test_coerce_value_blank_to_none():
    from crc_modules.db.writer import coerce_value
    assert coerce_value(None, "integer") is None
    assert coerce_value("", "text") is None
    assert coerce_value("   ", "double precision") is None
    assert coerce_value("", "boolean") is None
    assert coerce_value(None, "boolean") is None


def test_coerce_value_strips_parens_in_type():
    from crc_modules.db.writer import coerce_value
    # varchar(255) should be treated as 'text' (str fallback)
    assert coerce_value("hello", "varchar(255)") == "hello"
    # numeric(10,2) -> numeric -> float
    assert coerce_value("1.5", "numeric(10,2)") == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# insert_rows tests
# ---------------------------------------------------------------------------

def test_insert_rows_executemany_called():
    conn, cur = _make_mock_conn()
    cur.rowcount = 2
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import insert_rows
        result = insert_rows("fake_cs", "myschema", "mytable",
                             ["name", "area"],
                             [("Alice", 100), ("Bob", 200)])
    assert cur.executemany.call_count == 1
    stmt, params = cur.executemany.call_args[0]
    text = flatten(stmt)
    assert '"name"' in text
    assert '"area"' in text
    assert '"myschema"' in text
    assert '"mytable"' in text
    assert params == [("Alice", 100), ("Bob", 200)]


def test_insert_rows_identifiers_quoted():
    conn, cur = _make_mock_conn()
    cur.rowcount = 1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import insert_rows
        insert_rows("fake_cs", "s", "t", ["my col"], [("val",)])
    stmt, _ = cur.executemany.call_args[0]
    text = flatten(stmt)
    # Identifier quoting: column name with space must be double-quoted
    assert '"my col"' in text


# ---------------------------------------------------------------------------
# create_table_with_data tests
# ---------------------------------------------------------------------------

def _conn_with_parse():
    """Return conn+cur mocks and the patch context for writer module."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 2
    return conn, cur


def test_create_table_with_data_id_values_given():
    """id_values -> 'id <type> PRIMARY KEY' in CREATE, id values bound in INSERT."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 2
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table_with_data
        create_table_with_data(
            "fake_cs", "myschema", "mytable",
            columns=[("name", "text"), ("area", "double precision")],
            rows=[("Alice", "100.5"), ("Bob", "200.3")],
            id_values=[1, 2],
        )

    # Two execute calls: CREATE + executemany (INSERT)
    assert cur.execute.call_count >= 1
    create_text = flatten(cur.execute.call_args_list[0][0][0])
    assert "CREATE TABLE" in create_text
    assert "PRIMARY KEY" in create_text
    # executemany is called for INSERT
    assert cur.executemany.call_count == 1
    _, params = cur.executemany.call_args[0]
    # First row: id=1, name="Alice", area=100.5
    assert params[0][0] == 1
    assert params[0][1] == "Alice"
    assert params[0][2] == pytest.approx(100.5)


def test_create_table_with_data_no_id_values_identity():
    """No id_values -> identity PK in CREATE; INSERT omits id column."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table_with_data
        create_table_with_data(
            "fake_cs", "myschema", "mytable",
            columns=[("name", "text")],
            rows=[("Alice",)],
        )

    create_text = flatten(cur.execute.call_args_list[0][0][0])
    assert "GENERATED ALWAYS AS IDENTITY" in create_text
    assert "PRIMARY KEY" in create_text
    # INSERT params must NOT include an id value — just "Alice"
    _, params = cur.executemany.call_args[0]
    assert len(params[0]) == 1
    assert params[0][0] == "Alice"


def test_create_table_with_data_replace_table_drops_first():
    """replace_table=True: DROP issued before CREATE."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 0
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table_with_data
        create_table_with_data(
            "fake_cs", "s", "t",
            columns=[("v", "text")],
            rows=[],
            replace_table=True,
        )

    assert cur.execute.call_count >= 2
    drop_text = flatten(cur.execute.call_args_list[0][0][0])
    create_text = flatten(cur.execute.call_args_list[1][0][0])
    assert "DROP TABLE IF EXISTS" in drop_text
    assert "CREATE TABLE" in create_text


def test_create_table_with_data_row_length_mismatch_raises():
    """Row length != column count -> ValueError (raised before DB call)."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 0
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table_with_data
        with pytest.raises(ValueError):
            create_table_with_data(
                "fake_cs", "s", "t",
                columns=[("a", "text"), ("b", "integer")],
                rows=[("only_one_value",)],  # should be 2 values
            )


# ---------------------------------------------------------------------------
# create_table_with_geometry tests
# ---------------------------------------------------------------------------

def test_create_table_with_geometry_creates_geom_column():
    """CREATE has geom geometry(TYPE, srid) + id PK."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table_with_geometry
        create_table_with_geometry(
            "fake_cs", "myschema", "mytable",
            columns=[("name", "text")],
            rows=[("Alice",)],
            geom_wkts=["POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))"],
            geom_type="POLYGON",
            srid=4326,
            cx="0",
            cy="0",
        )

    create_text = flatten(cur.execute.call_args_list[0][0][0])
    assert "geometry(" in create_text or "GEOMETRY(" in create_text.upper()
    assert "POLYGON" in create_text
    assert "4326" in create_text
    assert "PRIMARY KEY" in create_text


def test_create_table_with_geometry_insert_uses_st_translate():
    """INSERT uses ST_Translate(ST_GeomFromText(%s, %s), cx, cy) with cx/cy verbatim."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 1
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table_with_geometry
        create_table_with_geometry(
            "fake_cs", "s", "t",
            columns=[],
            rows=[],
            geom_wkts=["POINT (0 0)"],
            geom_type="POINT",
            srid=31983,
            cx="500000",
            cy="9500000",
        )

    insert_stmt, params = cur.executemany.call_args[0]
    text = flatten(insert_stmt)
    assert "ST_Translate(ST_GeomFromText(%s, %s), 500000, 9500000)" in text
    # cx/cy must NOT appear in bound params
    flat_params = [str(v) for row in params for v in row]
    assert "500000" not in flat_params or all(str(v) != "500000" for v in flat_params[:-2])
    # wkt and srid are the last two params in each row
    assert params[0][-2] == "POINT (0 0)"
    assert params[0][-1] == 31983


def test_create_table_with_geometry_values_coerced():
    """Attribute values are coerced before binding (integer, float, blank=None)."""
    conn, cur = _make_mock_conn()
    cur.rowcount = 2
    with patch("crc_modules.db.writer.psycopg2.connect", return_value=conn), \
         patch("crc_modules.db.writer.parse_connection_string",
               return_value={"host": "h", "port": 5432, "dbname": "db", "user": "u", "password": "pw"}):
        from crc_modules.db.writer import create_table_with_geometry
        create_table_with_geometry(
            "fake_cs", "s", "t",
            columns=[("count", "integer"), ("area", "double precision")],
            rows=[("5", "123.4"), ("", "")],  # strings from GH
            geom_wkts=["POINT (0 0)", "POINT (1 1)"],
            geom_type="POINT",
            srid=4326,
            cx="0",
            cy="0",
        )

    _, params = cur.executemany.call_args[0]
    # Row 0: count=5 (int), area=123.4 (float)
    assert params[0][0] == 5
    assert params[0][1] == pytest.approx(123.4)
    # Row 1: blank -> None
    assert params[1][0] is None
    assert params[1][1] is None
