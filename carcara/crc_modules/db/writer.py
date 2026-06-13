"""PostGIS write layer: CREATE TABLE and INSERT geometries (with false-origin add-back).

No Rhino imports. Identifier-safe via psycopg2.sql.
"""
import psycopg2
import psycopg2.sql
from typing import List, Optional, Tuple

from .connection import parse_connection_string
from ..utils.correction import validate_offset


def _get_connection(cstring: str):
    p = parse_connection_string(cstring)
    return psycopg2.connect(
        host=p["host"], port=p["port"], dbname=p["dbname"],
        user=p["user"], password=p["password"], connect_timeout=5,
    )


def create_table(cstring: str, schema: str, table: str,
                 columns: List[Tuple[str, str]],
                 geom_column: Optional[str] = None,
                 geom_type: Optional[str] = None,
                 srid: int = 4326,
                 replace_table: bool = False) -> int:
    """CREATE TABLE (optionally DROP IF EXISTS first; optionally a PostGIS geometry column).
    columns: list of (name, sql_type). Identifiers quoted via psycopg2.sql.Identifier.
    Returns cur.rowcount (DDL usually -1). Raises psycopg2.Error on failure."""
    sql = psycopg2.sql
    col_defs = [
        sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(typ))
        for name, typ in columns
    ]
    if geom_column and geom_type:
        col_defs.append(sql.SQL("{} geometry({}, {})").format(
            sql.Identifier(geom_column), sql.SQL(geom_type), sql.Literal(int(srid))))
    create_stmt = sql.SQL("CREATE TABLE {}.{} ({})").format(
        sql.Identifier(schema), sql.Identifier(table), sql.SQL(", ").join(col_defs))
    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            if replace_table:
                cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                    sql.Identifier(schema), sql.Identifier(table)))
            cur.execute(create_stmt)
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


def insert_geometries(cstring: str, schema: str, table: str,
                      geom_column: str,
                      wkt_list: List[str],
                      srid: int,
                      cx: str = "0",
                      cy: str = "0",
                      column_names: Optional[List[str]] = None,
                      values: Optional[list] = None) -> int:
    """INSERT WKT geometries into an existing table, adding false origin back in SQL:
        ST_Translate(ST_GeomFromText(%s, %s), <cx>, <cy>)
    cx/cy validated as numeric TEXT and embedded verbatim — NEVER bind params, NEVER float().
    wkt + srid are bound via %s. Attribute values (optional) bound via %s per column.
    Uses executemany. Returns rows inserted. Raises psycopg2.Error on failure."""
    sql = psycopg2.sql
    cx = validate_offset(cx)
    cy = validate_offset(cy)

    geom_slot = sql.SQL("ST_Translate(ST_GeomFromText(%s, %s), " + cx + ", " + cy + ")")

    cols = [sql.Identifier(geom_column)]
    value_slots = [geom_slot]
    if column_names:
        cols += [sql.Identifier(c) for c in column_names]
        value_slots += [sql.SQL("%s")] * len(column_names)

    insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema), sql.Identifier(table),
        sql.SQL(", ").join(cols), sql.SQL(", ").join(value_slots))

    params = []
    for i, wkt in enumerate(wkt_list):
        row = [wkt, int(srid)]
        if column_names and values is not None:
            row += list(values[i])
        params.append(tuple(row))

    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            cur.executemany(insert_stmt, params)
            conn.commit()
            return cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else len(params)
    finally:
        conn.close()
