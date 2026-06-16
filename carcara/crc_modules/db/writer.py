"""PostGIS write layer: CREATE TABLE and INSERT geometries (with false-origin add-back).

No Rhino imports. Identifier-safe via psycopg2.sql.
"""
import re
import psycopg2
import psycopg2.sql
from typing import Any, List, Optional, Tuple

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


# ---------------------------------------------------------------------------
# Type coercion helper
# ---------------------------------------------------------------------------

_INTEGER_TYPES = {"integer", "int", "int4", "int8", "bigint", "smallint", "serial"}
_FLOAT_TYPES = {"double precision", "real", "numeric", "decimal",
                "float", "float4", "float8"}
_BOOL_TYPES = {"boolean", "bool"}


def coerce_value(raw: Any, sql_type: str) -> Any:
    """Coerce a raw GH string value to the Python type matching sql_type.

    Rules:
    - blank / None / empty-after-strip -> None (SQL NULL) for every type.
    - integer/int/int4/int8/bigint/smallint/serial -> int(raw)
    - double precision/real/numeric/decimal/float/float4/float8 -> float(raw)
    - boolean/bool -> True/False parsed from true/t/1/yes or false/f/0/no
    - everything else (text/varchar/char/uuid/date/timestamp/json/...) -> str(raw)

    sql_type is normalised (lowercased, parenthesised args stripped).
    """
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip() == "":
        return None

    # Normalise: lowercase + strip anything in parentheses (e.g. "varchar(255)" -> "varchar")
    norm = re.sub(r"\(.*\)", "", str(sql_type)).strip().lower()

    if norm in _INTEGER_TYPES:
        return int(raw)
    if norm in _FLOAT_TYPES:
        return float(raw)
    if norm in _BOOL_TYPES:
        lower = str(raw).strip().lower()
        if lower in ("true", "t", "1", "yes"):
            return True
        if lower in ("false", "f", "0", "no"):
            return False
        raise ValueError(f"Cannot coerce {raw!r} to boolean")
    # text, varchar, char, uuid, date, timestamp, json, and fallback
    return str(raw)


# ---------------------------------------------------------------------------
# Primary-key resolution helper
# ---------------------------------------------------------------------------

def _resolve_pk(columns: List[Tuple[str, str]], id_values: Optional[List]) -> dict:
    """Determine the primary-key strategy from the supplied inputs.

    Returns a dict with keys:
      pk_in_columns : bool  — True if 'id' is already among column names
      pk_col_def    : str   — SQL fragment for the id column definition
      id_type       : str   — 'integer' or 'text' (only when id_values given)
      use_identity  : bool  — True when auto-increment identity PK
      include_id_in_insert : bool — True when INSERT must supply the id value
    """
    col_names = [c[0].lower() for c in columns]
    pk_in_columns = "id" in col_names

    if id_values is not None:
        # Infer type: integer if every value is int-castable, else text
        try:
            [int(v) for v in id_values]
            id_type = "integer"
        except (TypeError, ValueError):
            id_type = "text"

        if pk_in_columns:
            # The caller already declared an 'id' column — make it PK; no extra column.
            return {
                "pk_in_columns": True,
                "pk_col_def": None,
                "id_type": id_type,
                "use_identity": False,
                "include_id_in_insert": True,
            }
        else:
            return {
                "pk_in_columns": False,
                "pk_col_def": f"id {id_type} PRIMARY KEY",
                "id_type": id_type,
                "use_identity": False,
                "include_id_in_insert": True,
            }

    else:
        # No id_values supplied
        if pk_in_columns:
            # The caller declared 'id' but gave no values.  We cannot auto-fill it
            # without identity either because the column type is unknown here.
            raise ValueError(
                "'id' is already in column_names but no id_values were supplied. "
                "Either provide id_values or omit 'id' from column_names to use "
                "auto-increment identity."
            )
        return {
            "pk_in_columns": False,
            "pk_col_def": "id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY",
            "id_type": "integer",
            "use_identity": True,
            "include_id_in_insert": False,
        }


# ---------------------------------------------------------------------------
# INSERT rows (attribute data only)
# ---------------------------------------------------------------------------

def insert_rows(cstring: str, schema: str, table: str,
                column_names: List[str], rows: List[tuple]) -> int:
    """INSERT rows of attribute data into an existing table.

    Uses executemany with psycopg2.sql.Identifier for safe quoting.
    rows: list of tuples parallel to column_names.
    Returns the row count. Raises psycopg2.Error on failure.
    """
    sql = psycopg2.sql
    cols = [sql.Identifier(c) for c in column_names]
    placeholders = [sql.SQL("%s")] * len(column_names)
    insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(cols),
        sql.SQL(", ").join(placeholders),
    )
    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            cur.executemany(insert_stmt, rows)
            conn.commit()
            return cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else len(rows)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CREATE TABLE with tabular data (no geometry)
# ---------------------------------------------------------------------------

def create_table_with_data(
    cstring: str,
    schema: str,
    table: str,
    columns: List[Tuple[str, str]],
    rows: List[tuple],
    id_values: Optional[List] = None,
    replace_table: bool = False,
) -> int:
    """CREATE a table and INSERT row data.  Always adds a primary key.

    columns  : list of (name, sql_type).
    rows     : list of tuples parallel to columns (one tuple per row).
    id_values: optional list of PK values, one per row.  If absent, an
               auto-increment identity PK is used and INSERT omits the id.
    replace_table: DROP TABLE IF EXISTS before CREATE when True.

    Returns rows inserted. Raises on failure.
    """
    if rows and columns and any(len(r) != len(columns) for r in rows):
        raise ValueError("Row length does not match column count")

    pk = _resolve_pk(columns, id_values)
    sql = psycopg2.sql

    # Build column definitions
    col_defs = []
    if not pk["pk_in_columns"]:
        # Prepend the PK column definition
        col_defs.append(sql.SQL(pk["pk_col_def"]))

    for name, typ in columns:
        if pk["pk_in_columns"] and name.lower() == "id":
            # Rewrite the user-supplied 'id' column to include PRIMARY KEY
            col_defs.append(
                sql.SQL("{} {} PRIMARY KEY").format(
                    sql.Identifier(name), sql.SQL(typ)
                )
            )
        else:
            col_defs.append(
                sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(typ))
            )

    create_stmt = sql.SQL("CREATE TABLE {}.{} ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(col_defs),
    )

    # Build INSERT column list and coerced params
    if pk["include_id_in_insert"] and not pk["pk_in_columns"]:
        # Explicit id column comes first
        insert_cols = [sql.Identifier("id")] + [sql.Identifier(n) for n, _ in columns]
    else:
        insert_cols = [sql.Identifier(n) for n, _ in columns]

    placeholders = [sql.SQL("%s")] * len(insert_cols)
    insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(insert_cols),
        sql.SQL(", ").join(placeholders),
    )

    # Coerce rows
    col_types = [typ for _, typ in columns]
    coerced_rows = []
    for i, row in enumerate(rows):
        coerced = tuple(coerce_value(v, col_types[j]) for j, v in enumerate(row))
        if pk["include_id_in_insert"] and not pk["pk_in_columns"]:
            id_val = coerce_value(id_values[i], pk["id_type"])
            coerced_rows.append((id_val,) + coerced)
        else:
            coerced_rows.append(coerced)

    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            if replace_table:
                cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                    sql.Identifier(schema), sql.Identifier(table)))
            cur.execute(create_stmt)
            if coerced_rows:
                cur.executemany(insert_stmt, coerced_rows)
            conn.commit()
            count = cur.rowcount
            return count if count is not None and count >= 0 else len(coerced_rows)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CREATE TABLE with geometry column
# ---------------------------------------------------------------------------

def create_table_with_geometry(
    cstring: str,
    schema: str,
    table: str,
    columns: List[Tuple[str, str]],
    rows: List[tuple],
    geom_wkts: List[str],
    geom_type: str,
    srid: int,
    cx: str,
    cy: str,
    id_values: Optional[List] = None,
    replace_table: bool = False,
) -> int:
    """CREATE a table with attribute columns + a 'geom' geometry column, and INSERT rows.

    columns   : list of (name, sql_type) for attribute data.  May be empty.
    rows      : list of tuples parallel to columns.  May be empty list.
    geom_wkts : list of WKT strings, one per row (aligned with rows / id_values).
    geom_type : PostGIS geometry type token (e.g. 'POLYGON', 'MULTIPOLYGON').
    srid      : SRID integer.
    cx, cy    : false-origin offsets as numeric TEXT.  Validated via validate_offset
                and embedded VERBATIM in SQL — never float()-parsed.
    id_values : optional PK values (one per row).
    replace_table : DROP first when True.

    Geometry column is always named 'geom'.
    Returns rows inserted. Raises on failure.
    """
    cx = validate_offset(cx)
    cy = validate_offset(cy)

    if rows and columns and any(len(r) != len(columns) for r in rows):
        raise ValueError("Row length does not match column count")

    pk = _resolve_pk(columns, id_values)
    sql = psycopg2.sql

    # Build column definitions: id PK + data columns + geom
    col_defs = []
    if not pk["pk_in_columns"]:
        col_defs.append(sql.SQL(pk["pk_col_def"]))

    for name, typ in columns:
        if pk["pk_in_columns"] and name.lower() == "id":
            col_defs.append(
                sql.SQL("{} {} PRIMARY KEY").format(
                    sql.Identifier(name), sql.SQL(typ)
                )
            )
        else:
            col_defs.append(
                sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(typ))
            )

    # geom column: embed type and srid as safe literals
    geom_col_def = sql.SQL("geom geometry({geom_type}, {srid})").format(
        geom_type=sql.SQL(str(geom_type)),
        srid=sql.Literal(int(srid)),
    )
    col_defs.append(geom_col_def)

    create_stmt = sql.SQL("CREATE TABLE {}.{} ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(col_defs),
    )

    # Build INSERT: id? + data cols + geom slot (ST_Translate verbatim)
    if pk["include_id_in_insert"] and not pk["pk_in_columns"]:
        insert_cols = [sql.Identifier("id")] + [sql.Identifier(n) for n, _ in columns]
    else:
        insert_cols = [sql.Identifier(n) for n, _ in columns]

    # geom slot — cx/cy embedded VERBATIM, wkt+srid bound via %s
    geom_slot = sql.SQL(
        "ST_Translate(ST_GeomFromText(%s, %s), " + cx + ", " + cy + ")"
    )
    insert_cols_with_geom = insert_cols + [sql.Identifier("geom")]
    placeholders = [sql.SQL("%s")] * len(insert_cols) + [geom_slot]

    insert_stmt = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(insert_cols_with_geom),
        sql.SQL(", ").join(placeholders),
    )

    # Coerce data values and build param tuples
    col_types = [typ for _, typ in columns]
    coerced_rows = []
    for i, wkt in enumerate(geom_wkts):
        row = rows[i] if rows else ()
        coerced = tuple(coerce_value(v, col_types[j]) for j, v in enumerate(row))
        if pk["include_id_in_insert"] and not pk["pk_in_columns"]:
            id_val = coerce_value(id_values[i], pk["id_type"])
            data_part = (id_val,) + coerced
        else:
            data_part = coerced
        # geom params: wkt + srid (cx/cy are verbatim in SQL, not bound)
        coerced_rows.append(data_part + (wkt, int(srid)))

    conn = _get_connection(cstring)
    try:
        with conn.cursor() as cur:
            if replace_table:
                cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
                    sql.Identifier(schema), sql.Identifier(table)))
            cur.execute(create_stmt)
            if coerced_rows:
                cur.executemany(insert_stmt, coerced_rows)
            conn.commit()
            count = cur.rowcount
            return count if count is not None and count >= 0 else len(coerced_rows)
    finally:
        conn.close()
