from unittest.mock import patch, MagicMock, call
import pytest
import psycopg2
from crc_modules.db.query import run_query, run_command, _list_schemas, _list_tables, _list_columns, query_values


def _mock_conn(rows, col_names):
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = rows
    mock_cur.description = [(c,) + (None,) * 6 for c in col_names]
    mock_cur.__enter__ = lambda s: mock_cur
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


def test_run_query_returns_rows_and_columns():
    rows = [(1, "Alice"), (2, "Bob")]
    cols = ["id", "name"]
    mock_conn, _ = _mock_conn(rows, cols)
    cstring = "host=localhost port=5432 dbname=db user=user password=pw"
    with patch("crc_modules.db.query.psycopg2.connect", return_value=mock_conn):
        r, c = run_query(cstring, "SELECT id, name FROM t")
        assert r == rows
        assert c == cols


def test_run_query_closes_connection_on_success():
    mock_conn, _ = _mock_conn([(1,)], ["x"])
    cstring = "host=localhost port=5432 dbname=db user=user password=pw"
    with patch("crc_modules.db.query.psycopg2.connect", return_value=mock_conn):
        run_query(cstring, "SELECT 1")
        mock_conn.close.assert_called_once()


def test_run_query_closes_connection_on_error():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.__enter__ = lambda s: mock_cur
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.execute.side_effect = psycopg2.OperationalError("boom")
    mock_conn.cursor.return_value = mock_cur
    cstring = "host=localhost port=5432 dbname=db user=user password=pw"
    with patch("crc_modules.db.query.psycopg2.connect", return_value=mock_conn):
        with pytest.raises(psycopg2.OperationalError):
            run_query(cstring, "SELECT 1")
        mock_conn.close.assert_called_once()


def test_run_query_propagates_connect_error():
    cstring = "host=localhost port=5432 dbname=db user=user password=pw"
    with patch("crc_modules.db.query.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = psycopg2.OperationalError("refused")
        with pytest.raises(psycopg2.OperationalError):
            run_query(cstring, "SELECT 1")


def test_run_command_returns_rowcount():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.rowcount = 3
    mock_cur.__enter__ = lambda s: mock_cur
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cur
    cstring = "host=localhost port=5432 dbname=db user=user password=pw"
    with patch("crc_modules.db.query.psycopg2.connect", return_value=mock_conn):
        count = run_command(cstring, "UPDATE t SET x=1")
        assert count == 3
        mock_conn.commit.assert_called_once()


def test_run_command_closes_connection():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.rowcount = 0
    mock_cur.__enter__ = lambda s: mock_cur
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cur
    cstring = "host=localhost port=5432 dbname=db user=user password=pw"
    with patch("crc_modules.db.query.psycopg2.connect", return_value=mock_conn):
        run_command(cstring, "DELETE FROM t")
        mock_conn.close.assert_called_once()


def test_list_schemas_sql():
    sql = _list_schemas()
    assert "schema_name" in sql
    assert "information_schema.schemata" in sql
    assert "pg_catalog" in sql
    assert "information_schema" in sql
    assert "pg_%" in sql


def test_list_tables_sql():
    sql = _list_tables("public")
    assert "table_name" in sql
    assert "information_schema.tables" in sql
    assert "table_schema = 'public'" in sql
    assert "table_type = 'BASE TABLE'" in sql


def test_list_columns_sql():
    sql = _list_columns("public", "mytable")
    assert "column_name" in sql
    assert "data_type" in sql
    assert "information_schema.columns" in sql
    assert "table_schema = 'public'" in sql
    assert "table_name = 'mytable'" in sql


# ── query_values ───────────────────────────────────────────────────────────

def test_query_values_orders_by_pk():
    from crc_modules.db import query as q
    sql_log = []
    with patch("crc_modules.db.spatial_query.detect_primary_key", return_value="id"), \
         patch("crc_modules.db.spatial_query.detect_first_column", return_value="other"), \
         patch("crc_modules.db.query.run_query", return_value=([(1,)], ["a"])) as rq:
        q.query_values("cs", "public", "t", ["a", "b"], sql_log=sql_log)
        sent = rq.call_args[0][1]
        assert 'ORDER BY "id"' in sent
        assert 'SELECT "a", "b"' in sent


def test_query_values_orders_by_first_column_when_no_pk():
    from crc_modules.db import query as q
    with patch("crc_modules.db.spatial_query.detect_primary_key", return_value=None), \
         patch("crc_modules.db.spatial_query.detect_first_column", return_value="gid"), \
         patch("crc_modules.db.query.run_query", return_value=([], [])) as rq:
        q.query_values("cs", "public", "t", ["a"])
        sent = rq.call_args[0][1]
        assert 'ORDER BY "gid"' in sent


def test_query_values_null_replacement_case():
    from crc_modules.db import query as q
    with patch("crc_modules.db.spatial_query.detect_primary_key", return_value="id"), \
         patch("crc_modules.db.spatial_query.detect_first_column", return_value=None), \
         patch("crc_modules.db.query.run_query", return_value=([], [])) as rq:
        q.query_values("cs", "public", "t", ["a"], null_val="N/A")
        sent = rq.call_args[0][1]
        assert "CASE WHEN" in sent
        assert "'N/A'" in sent