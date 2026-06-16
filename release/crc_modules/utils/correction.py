import re
import psycopg2
import psycopg2.sql


def validate_offset(value: str) -> str:
    """Return value unchanged if numeric literal (text). Raise ValueError otherwise. '0' = no shift."""
    if not re.match(r'^-?\d+(\.\d+)?$', value):
        raise ValueError(f"Invalid offset: {value}")
    return value


def translate_expr(geom_sql: str, cx: str, cy: str, direction: str) -> str:
    """Wrap SQL geometry expression in ST_Translate.
    direction='to_local'     -> ST_Translate(<geom_sql>, -cx, -cy)   (read)
    direction='to_projected' -> ST_Translate(<geom_sql>,  cx,  cy)   (write / filter)
    cx, cy are validated numeric text, embedded verbatim."""
    cx = validate_offset(cx)
    cy = validate_offset(cy)
    if direction == "to_local":
        return f"ST_Translate({geom_sql}, -{cx}, -{cy})"
    elif direction == "to_projected":
        return f"ST_Translate({geom_sql}, {cx}, {cy})"
    raise ValueError(f"Unknown direction: {direction}")


def find_correction_parameters(
    cstring: str,
    schema: str,
    table: str,
    column: str = None,
    value: str = None,
) -> tuple:
    """Find one row, auto-detect the geometry column, compute its centroid,
    and return (Cx, Cy) as verbatim TEXT strings from the DB — never float()-parsed.

    Row selection:
        - column AND value given -> WHERE <column> = %s  LIMIT 1
        - both omitted           -> first row of table   LIMIT 1 (no WHERE)

    Raises ValueError if no row found.
    """
    # Import here to avoid circular import at module level (spatial_query imports
    # validate_offset/translate_expr from this module at the top level).
    from ..db.spatial_query import detect_geometry_column
    from ..db.connection import parse_connection_string

    geom_col = detect_geometry_column(cstring, schema, table)
    if not geom_col:
        raise ValueError(
            f"No geometry column found for {schema}.{table}"
        )

    schema_id = psycopg2.sql.Identifier(schema)
    table_id = psycopg2.sql.Identifier(table)
    geom_id = psycopg2.sql.Identifier(geom_col)

    if column and value is not None:
        col_id = psycopg2.sql.Identifier(column)
        sql = psycopg2.sql.SQL(
            "SELECT ST_X(ST_Centroid({geom}))::text, "
            "ST_Y(ST_Centroid({geom}))::text "
            "FROM {schema}.{table} "
            "WHERE {col} = %s "
            "LIMIT 1"
        ).format(
            geom=geom_id,
            schema=schema_id,
            table=table_id,
            col=col_id,
        )
        params = (value,)
    else:
        sql = psycopg2.sql.SQL(
            "SELECT ST_X(ST_Centroid({geom}))::text, "
            "ST_Y(ST_Centroid({geom}))::text "
            "FROM {schema}.{table} "
            "LIMIT 1"
        ).format(
            geom=geom_id,
            schema=schema_id,
            table=table_id,
        )
        params = None

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
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            row = cur.fetchone()
            if row is None or row[0] is None or row[1] is None:
                raise ValueError(
                    f"No row found in {schema}.{table}"
                    + (f" where {column} = {value!r}" if column else "")
                )
            # Return verbatim text strings from the DB — never float()-parse
            return (str(row[0]), str(row[1]))
    finally:
        conn.close()