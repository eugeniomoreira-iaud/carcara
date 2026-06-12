from unittest.mock import patch, MagicMock
import pytest
from crc_modules.db.connection import (
    build_connection_string,
    parse_connection_string,
    test_connection as check_connection,
)


def test_build_connection_string():
    cstring = build_connection_string("localhost", 5432, "mydb", "user", "pw")
    # Password is encoded (obfuscated), never plain text on the wire.
    assert cstring.startswith("host=localhost port=5432 dbname=mydb user=user password=")
    assert "password=pw" not in cstring
    assert parse_connection_string(cstring)["password"] == "pw"


def test_build_connection_string_with_special_chars():
    cstring = build_connection_string("my.host", 5433, "my db", "my user", "p@ss w:rd")
    assert cstring.startswith("host=my.host port=5433 dbname=my db user=my user password=")
    assert "p@ss w:rd" not in cstring
    assert parse_connection_string(cstring)["password"] == "p@ss w:rd"


def test_parse_connection_string():
    cstring = "host=localhost port=5432 dbname=mydb user=user password=pw"
    params = parse_connection_string(cstring)
    assert params["host"] == "localhost"
    assert params["port"] == 5432
    assert params["dbname"] == "mydb"
    assert params["user"] == "user"
    assert params["password"] == "pw"


def test_parse_connection_string_with_quoted_values():
    cstring = 'host="my host" port=5432 dbname="my db" user="my user" password="p@ss w:rd"'
    params = parse_connection_string(cstring)
    assert params["host"] == "my host"
    assert params["port"] == 5432
    assert params["dbname"] == "my db"
    assert params["user"] == "my user"
    assert params["password"] == "p@ss w:rd"


def test_round_trip():
    original = build_connection_string("localhost", 5432, "mydb", "user", "pw")
    params = parse_connection_string(original)
    assert params["host"] == "localhost"
    assert params["port"] == 5432
    assert params["dbname"] == "mydb"
    assert params["user"] == "user"
    assert params["password"] == "pw"


def test_test_connection_success():
    with patch("crc_modules.db.connection.psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        cstring = build_connection_string("localhost", 5432, "db", "user", "pw")
        ok, msg = check_connection(cstring)
        assert ok is True
        assert msg == "Connection successful"
        mock_connect.assert_called_once_with(
            host="localhost", port=5432, dbname="db", user="user", password="pw", connect_timeout=5
        )


def test_test_connection_failure():
    with patch("crc_modules.db.connection.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = Exception("Connection refused")
        cstring = build_connection_string("localhost", 5432, "db", "user", "pw")
        ok, msg = check_connection(cstring)
        assert ok is False
        assert "Connection refused" in msg


@pytest.mark.parametrize("exc_msg", [
    "FATAL: password authentication failed for user",
    "could not connect to server: Connection refused",
    'could not translate host name "badhost" to address: Name or service not known',
])
def test_connection_failure_messages(exc_msg):
    with patch("crc_modules.db.connection.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = Exception(exc_msg)
        cstring = build_connection_string("localhost", 5432, "db", "user", "pw")
        ok, msg = check_connection(cstring)
        assert ok is False
        assert exc_msg in msg


def test_parse_connection_string_defaults():
    cstring = "host=localhost dbname=test"
    params = parse_connection_string(cstring)
    assert params["host"] == "localhost"
    assert params["port"] == 5432
    assert params["dbname"] == "test"
    assert params["user"] == ""
    assert params["password"] == ""