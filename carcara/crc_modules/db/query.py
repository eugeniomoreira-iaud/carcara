import psycopg2
import psycopg2.extras

from .connection import parse_connection_string


def run_query(cstring: str, sql: str) -> tuple[list, list]:
    """
    Execute a SELECT statement.
    Returns (rows, columns) where:
      rows    : list of tuples
      columns : list of column name strings
    Raises psycopg2.Error on failure.
    """
    conn_params = parse_connection_string(cstring)
    conn = psycopg2.connect(
        host=conn_params["host"],
        port=conn_params["port"],
        dbname=conn_params["dbname"],
        user=conn_params["user"],
        password=conn_params["password"],
        connect_timeout=5,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return rows, columns
    finally:
        conn.close()


def run_command(cstring: str, sql: str) -> int:
    """
    Execute a non-SELECT statement (INSERT, UPDATE, CREATE, etc.).
    Returns number of affected rows.
    Raises psycopg2.Error on failure.
    """
    conn_params = parse_connection_string(cstring)
    conn = psycopg2.connect(
        host=conn_params["host"],
        port=conn_params["port"],
        dbname=conn_params["dbname"],
        user=conn_params["user"],
        password=conn_params["password"],
        connect_timeout=5,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


# Private SQL helpers for the query components

def _list_schemas() -> str:
    """SQL to list all non-system schemas."""
    return """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
          AND schema_name NOT LIKE 'pg_%'
        ORDER BY schema_name;
    """.strip()


def _list_tables(schema: str) -> str:
    """SQL to list all tables in a schema."""
    return """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{}'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """.format(schema).strip()


def _list_columns(schema: str, table: str) -> str:
    """SQL to list all columns in a table with their types."""
    return """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = '{}'
          AND table_name = '{}'
        ORDER BY ordinal_position;
    """.format(schema, table).strip()