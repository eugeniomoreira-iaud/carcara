import psycopg2
import re


def build_connection_string(host: str, port: int, database: str,
                            user: str, password: str) -> str:
    """Returns a single CString (libpq conninfo) with the password as plain text."""
    return f"host={host} port={port} dbname={database} user={user} password={password}"


def parse_connection_string(cstring: str) -> dict:
    """Returns a dict of psycopg2 connection kwargs (parses the libpq conninfo)."""
    params = {}
    # Parse libpq connection string format: key=value key=value ...
    # Values can be quoted or unquoted
    pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|(\S+))'
    for match in re.finditer(pattern, cstring):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        params[key] = value

    # Map to psycopg2 connect kwargs
    return {
        "host": params.get("host", "localhost"),
        "port": int(params.get("port", 5432)),
        "dbname": params.get("dbname", params.get("database", "")),
        "user": params.get("user", ""),
        "password": params.get("password", ""),
    }


def _test_connection_cstring(cstring: str) -> tuple[bool, str]:
    """Returns (True, 'Connection successful') or (False, error_message)."""
    try:
        conn_params = parse_connection_string(cstring)
        conn = psycopg2.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            dbname=conn_params["dbname"],
            user=conn_params["user"],
            password=conn_params["password"],
            connect_timeout=5,
        )
        conn.close()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)