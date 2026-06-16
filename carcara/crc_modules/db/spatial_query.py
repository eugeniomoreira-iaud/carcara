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


def _build_spatial_filter_expr(geom_col: str, filter_wkts: List[str], cx: str, cy: str, srid: int, func: int) -> str:
    """Build the spatial filter WHERE clause from a list of filter WKTs.
    All WKTs are unioned into a single mask via ST_Union(ARRAY[...]).
    func=0 -> ST_Intersects(geom_col, combined), else -> ST_Contains(combined, geom_col).
    The combined filter geometry (already local) is pushed to projected CRS with +cx, +cy."""
    cx = validate_offset(cx)
    cy = validate_offset(cy)
    geom_parts = ", ".join(
        f"ST_GeomFromText({_quote_literal(w)}, {srid})" for w in filter_wkts
    )
    combined = f"ST_Translate(ST_Union(ARRAY[{geom_parts}]), {cx}, {cy})"
    if func == 0:
        return f"ST_Intersects({geom_col}, {combined})"
    return f"ST_Contains({combined}, {geom_col})"


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
    filter_wkts: List[str],
    cx: str = "0",
    cy: str = "0",
    srid: int = 4326,
    func: int = 0,
    sql_log: Optional[list] = None,
) -> Tuple[List[str], List[Union[int, None]]]:
    """
    SELECT geometries translated to local (-Cx, -Cy), filtered by one or more
    GH-drawn boundary WKTs that are unioned into a single mask and translated to
    the projected CRS (+Cx, +Cy) inside the WHERE:
        ST_Intersects(<db_geom>, ST_Translate(ST_Union(ARRAY[...]), Cx, Cy))
    Auto-detects geometry column and PK. Returns (wkt_list, pk_list).
    ORDER BY pk when pk is present.
    """
    geom_col = detect_geometry_column(cstring, schema, table, sql_log)
    if not geom_col:
        raise ValueError(f"No geometry column found for {schema}.{table}")

    pk_col = detect_primary_key(cstring, schema, table, sql_log)

    geom_expr = _build_geometry_expr(f'"{geom_col}"', cx, cy, srid)
    spatial_pred = _build_spatial_filter_expr(f'"{geom_col}"', filter_wkts, cx, cy, srid, func)

    if pk_col:
        order_by = f'ORDER BY "{pk_col}"'
        select_pk = f'"{pk_col}"'
    else:
        order_by = ""
        select_pk = "NULL"

    where_clause = f"WHERE {spatial_pred}"

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
    column: str,
    filter_wkts: List[str],
    cx: str = "0",
    cy: str = "0",
    srid: int = 4326,
    func: int = 0,
    sql_log: Optional[list] = None,
) -> Tuple[List, List]:
    """
    SELECT a single attribute column for rows matching spatial filter.
    Same spatial filter logic as get_geometries_with_spatial_filter (ST_Union mask).
    Also selects the primary key for row correlation.
    Returns (values_list, pk_list) — both in pk ORDER BY order.
    If no PK, pk_list contains None per row.
    """
    geom_col = detect_geometry_column(cstring, schema, table, sql_log)
    if not geom_col:
        raise ValueError(f"No geometry column found for {schema}.{table}")

    pk_col = detect_primary_key(cstring, schema, table, sql_log)

    spatial_pred = _build_spatial_filter_expr(f'"{geom_col}"', filter_wkts, cx, cy, srid, func)

    if pk_col:
        order_by = f'ORDER BY "{pk_col}"'
        select_pk = f'"{pk_col}"'
    else:
        order_by = ""
        select_pk = "NULL"

    where_clause = f"WHERE {spatial_pred}"

    sql = f"""
        SELECT "{column}", {select_pk}
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
            values_list = [row[0] for row in rows]
            pk_list = [row[1] for row in rows]
            return values_list, pk_list
    finally:
        conn.close()