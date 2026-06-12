import psycopg2
import re
import base64


def _encode_password(password: str) -> str:
    """Encode password for CString (base64 obfuscation, not encryption)."""
    return base64.b64encode(password.encode("utf-8")).decode("ascii")


def _decode_password(encoded: str) -> str:
    """Decode password from CString."""
    try:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        return encoded


def build_connection_string(host: str, port: int, database: str,
                            user: str, password: str) -> str:
    """Returns a single CString (libpq conninfo) with the password encoded."""
    encoded_pw = _encode_password(password)
    return f"host={host} port={port} dbname={database} user={user} password={encoded_pw}"


def parse_connection_string(cstring: str) -> dict:
    """Returns a dict of psycopg2 connection kwargs (decodes the password)."""
    params = {}
    pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|(\S+))'
    for match in re.finditer(pattern, cstring):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        params[key] = value

    return {
        "host": params.get("host", "localhost"),
        "port": int(params.get("port", 5432)),
        "dbname": params.get("dbname", params.get("database", "")),
        "user": params.get("user", ""),
        "password": _decode_password(params.get("password", "")),
    }


def test_connection(cstring: str) -> tuple[bool, str]:
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