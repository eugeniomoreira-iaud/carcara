import psycopg2
import psycopg2.extras
import psycopg2.sql
from typing import Optional, List, Tuple, Union

from .connection import parse_connection_string
from ..utils.correction import validate_offset, translate_expr


def _get_connection(cstring: str):
    """Create a psycopg2 connection from CString."""
    conn_params = parse_connection_string(cstring)
    return psycopg2.connect(
        host=conn_params["host"],
        port=conn_params["port"],
        dbname=conn_params["dbname"],
        user=conn_params["user"],
        password=conn_params["password"],
        connect_timeout=5,
    )


def detect_geometry_columns(cstring: str, schema: str, table: str,
                            sql_log: Optional[list] = None) -> list:
    """Return all geometry/geography column names for a table, ordered by ordinal position."""
    sql = psycopg2.sql.SQL("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = {schema} AND table_name = {table}
          AND udt_name IN ('geometry', 'geography')
        ORDER BY ordinal_position
    """).format(
        schema=psycopg2.sql.Literal(schema),
        table=psycopg2.sql.Literal(table),
    )
    try:
        conn = _get_connection(cstring)
        try:
            with conn.cursor() as cur:
                if sql_log is not None:
                    sql_log.append(cur.mogrify(sql).decode("utf-8", "replace"))
                cur.execute(sql)
                return [r[0] for r in cur.fetchall()]
        finally:
            conn.close()
    except Exception:
        return []


def detect_geometry_column(cstring: str, schema: str, table: str,
                           sql_log: Optional[list] = None) -> Optional[str]:
    """Return the geometry column name for a table, or None if not found."""
    cols = detect_geometry_columns(cstring, schema, table, sql_log)
    return cols[0] if cols else None


def detect_primary_key(cstring: str, schema: str, table: str,
                       sql_log: Optional[list] = None) -> Optional[str]:
    """Return the primary key column name for a table, or None if not found."""
    sql = psycopg2.sql.SQL("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = {schema}
          AND tc.table_name = {table}
        LIMIT 1
    """).format(
        schema=psycopg2.sql.Literal(schema),
        table=psycopg2.sql.Literal(table),
    )
    try:
        conn = _get_connection(cstring)
        try:
            with conn.cursor() as cur:
                if sql_log is not None:
                    sql_log.append(cur.mogrify(sql).decode("utf-8", "replace"))
                cur.execute(sql)
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
    except Exception:
        return None


def _build_geometry_expr(geom_col: str, cx: str, cy: str, srid: int) -> str:
    """Build the geometry expression with coordinate correction for read path."""
    cx = validate_offset(cx)
    cy = validate_offset(cy)
    return f"ST_AsText(ST_Translate({geom_col}, -{cx}, -{cy}))"


def _build_spatial_filter_expr(geom_col: str, filter_wkt: str, cx: str, cy: str, srid: int, func: int) -> str:
    """Build the spatial filter WHERE clause.
    func=0 -> ST_Intersects, else -> ST_Contains
    The filter geometry (already local) is pushed to projected CRS with +cx, +cy."""
    cx = validate_offset(cx)
    cy = validate_offset(cy)
    filter_geom = f"ST_Translate(ST_GeomFromText({_quote_literal(filter_wkt)}, {srid}), {cx}, {cy})"
    if func == 0:
        return f"ST_Intersects({geom_col}, {filter_geom})"
    return f"ST_Contains({filter_geom}, {geom_col})"


def _quote_literal(value: str) -> str:
    """Escape a value for safe embedding as a SQL string literal."""
    return "'" + str(value).replace("'", "''") + "'"


def get_geometries(
    cstring: str,
    schema: str,
    table: str,
    cx: str = "0",
    cy: str = "0",
    where: Optional[str] = None,
    srid: int = 4326,
    sql_log: Optional[list] = None,
) -> Tuple[List[str], List[Union[int, None]]]:
    """
    Returns (wkt_geometries, primary_keys).
    Auto-detects geometry column and primary key.
    Builds ST_AsText(ST_Translate(<geom_expr>, -Cx, -Cy)) ordered by PK.
    If no PK exists, returns NULL for pk.
    """
    geom_col = detect_geometry_column(cstring, schema, table, sql_log)
    if not geom_col:
        raise ValueError(f"No geometry column found for {schema}.{table}")

    pk_col = detect_primary_key(cstring, schema, table, sql_log)

    geom_expr = _build_geometry_expr(f'"{geom_col}"', cx, cy, srid)

    if pk_col:
        order_by = f'ORDER BY "{pk_col}"'
        select_pk = f'"{pk_col}"'
    else:
        order_by = ""
        select_pk = "NULL"

    where_clause = f"WHERE {where}" if where else ""

    sql = f"""
        SELECT {geom_expr}, {select_pk}
        FROM "{schema}"."{table}"
        {where_clause}
        {order_by}
    """.strip()

    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            if sql_log is not None:
                sql_log.append(cur.mogrify(sql).decode("utf-8", "replace"))
            cur.execute(sql)
            rows = cur.fetchall()
            wkt_list = [row[0] for row in rows]
            pk_list = [row[1] for row in rows]
            return wkt_list, pk_list
    finally:
        conn.close()


def get_geometries_with_spatial_filter(
    cstring: str,
    schema: str,
    table: str,
    filter_wkt: str,
    cx: str = "0",
    cy: str = "0",
    srid: int = 4326,
    sql_filter: Optional[str] = None,
    func: int = 0,
    sql_log: Optional[list] = None,
) -> Tuple[List[str], List[Union[int, None]]]:
    """
    SELECT geometries translated to local (-Cx, -Cy), filtered by a GH-drawn
    boundary that is itself translated to the projected CRS (+Cx, +Cy) inside
    the WHERE:
        ST_Intersects(<db_geom>, ST_Translate(ST_GeomFromText(filter_wkt, srid), Cx, Cy))
        AND (sql_filter)
    Auto-detects geometry column and PK. Returns (wkt_list, pk_list).
    """
    geom_col = detect_geometry_column(cstring, schema, table, sql_log)
    if not geom_col:
        raise ValueError(f"No geometry column found for {schema}.{table}")

    pk_col = detect_primary_key(cstring, schema, table, sql_log)

    geom_expr = _build_geometry_expr(f'"{geom_col}"', cx, cy, srid)
    spatial_filter = _build_spatial_filter_expr(f'"{geom_col}"', filter_wkt, cx, cy, srid, func)

    if pk_col:
        order_by = f'ORDER BY "{pk_col}"'
        select_pk = f'"{pk_col}"'
    else:
        order_by = ""
        select_pk = "NULL"

    where_parts = [spatial_filter]
    if sql_filter:
        where_parts.append(f"({sql_filter})")
    where_clause = "WHERE " + " AND ".join(where_parts)

    sql = f"""
        SELECT {geom_expr}, {select_pk}
        FROM "{schema}"."{table}"
        {where_clause}
        {order_by}
    """.strip()

    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            if sql_log is not None:
                sql_log.append(cur.mogrify(sql).decode("utf-8", "replace"))
            cur.execute(sql)
            rows = cur.fetchall()
            wkt_list = [row[0] for row in rows]
            pk_list = [row[1] for row in rows]
            return wkt_list, pk_list
    finally:
        conn.close()


def get_values_with_spatial_filter(
    cstring: str,
    schema: str,
    table: str,
    columns: List[str],
    filter_wkt: str,
    cx: str = "0",
    cy: str = "0",
    srid: int = 4326,
    sql_filter: Optional[str] = None,
    func: int = 0,
    sql_log: Optional[list] = None,
) -> Tuple[List[Tuple], List[str]]:
    """
    SELECT attribute columns for rows matching spatial filter.
    Same spatial filter logic as get_geometries_with_spatial_filter.
    Returns (rows, column_names).
    """
    geom_col = detect_geometry_column(cstring, schema, table, sql_log)
    if not geom_col:
        raise ValueError(f"No geometry column found for {schema}.{table}")

    pk_col = detect_primary_key(cstring, schema, table, sql_log)

    col_list = ", ".join(f'"{c}"' for c in columns)
    spatial_filter = _build_spatial_filter_expr(f'"{geom_col}"', filter_wkt, cx, cy, srid, func)

    if pk_col:
        order_by = f'ORDER BY "{pk_col}"'
    else:
        order_by = ""

    where_parts = [spatial_filter]
    if sql_filter:
        where_parts.append(f"({sql_filter})")
    where_clause = "WHERE " + " AND ".join(where_parts)

    sql = f"""
        SELECT {col_list}
        FROM "{schema}"."{table}"
        {where_clause}
        {order_by}
    """.strip()

    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            if sql_log is not None:
                sql_log.append(cur.mogrify(sql).decode("utf-8", "replace"))
            cur.execute(sql)
            col_names = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return rows, col_names
    finally:
        conn.close()