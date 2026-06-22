import psycopg2
import psycopg2.extras
from typing import Optional

from .connection import parse_connection_string


def _quote_literal(value: str) -> str:
    """Escape a value for safe embedding as a SQL string literal."""
    return "'" + str(value).replace("'", "''") + "'"


def _quote_identifier(name: str) -> str:
    """Escape a name for safe embedding as a SQL identifier."""
    return '"' + str(name).replace('"', '""') + '"'


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
        WHERE table_schema = {schema}
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """.format(schema=_quote_literal(schema)).strip()


def _list_columns(schema: str, table: str) -> str:
    """SQL to list all columns in a table with their types."""
    return """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = {schema}
          AND table_name = {table}
        ORDER BY ordinal_position;
    """.format(schema=_quote_literal(schema), table=_quote_literal(table)).strip()


def _query_values_sql(schema: str, table: str, column: str, null_val: str = "", limit: Optional[int] = None) -> str:
    """
    Build SELECT query for a single column with optional NULL replacement and LIMIT.
    Identifiers and literals are escaped locally — no connection needed to compose.
    """
    target = "{}.{}".format(_quote_identifier(schema), _quote_identifier(table))
    col = _quote_identifier(column)

    if null_val != "":
        # Cast to text so the NULL-replacement literal and the column share a type.
        q = "SELECT CASE WHEN {col} IS NULL THEN {nv} ELSE {col}::text END FROM {target}".format(
            col=col, nv=_quote_literal(null_val), target=target)
    else:
        q = "SELECT {col} FROM {target}".format(col=col, target=target)

    if limit is not None and limit > 0:
        q = "{} LIMIT {}".format(q, int(limit))

    return q


def query_values(cstring: str, schema: str, table: str, columns: list,
                 null_val: str = "", sql_log: Optional[list] = None) -> tuple[list, list]:
    """
    SELECT one or more columns from a table, ordered by primary key (or the
    table's first column if no PK). Optionally replace NULL with null_val.
    Returns (rows, columns). Raises psycopg2.Error on failure.
    """
    from .spatial_query import detect_primary_key, detect_first_column

    target = "{}.{}".format(_quote_identifier(schema), _quote_identifier(table))

    if null_val != "":
        parts = []
        for c in columns:
            qc = _quote_identifier(c)
            parts.append("CASE WHEN {qc} IS NULL THEN {nv} ELSE {qc}::text END".format(
                qc=qc, nv=_quote_literal(null_val)))
        select_clause = ", ".join(parts)
    else:
        select_clause = ", ".join(_quote_identifier(c) for c in columns)

    sql = "SELECT {} FROM {}".format(select_clause, target)

    order_col = detect_primary_key(cstring, schema, table, sql_log) \
        or detect_first_column(cstring, schema, table, sql_log)
    if order_col:
        sql = "{} ORDER BY {}".format(sql, _quote_identifier(order_col))

    if sql_log is not None:
        sql_log.append(sql)

    return run_query(cstring, sql)