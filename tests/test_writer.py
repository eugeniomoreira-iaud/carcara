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
