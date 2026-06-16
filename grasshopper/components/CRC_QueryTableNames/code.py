"""CRC_QueryTableNames: List all tables in a specified schema."""
import sys
import os
import Grasshopper

# Dynamically route to the user objects folder via the Grasshopper API
_carcara_path = os.path.join(Grasshopper.Folders.DefaultUserObjectFolder, "carcara")

if os.path.isdir(_carcara_path) and _carcara_path not in sys.path:
    sys.path.insert(0, _carcara_path)

try:
    ghenv.Component.Message = "v{{component_version}}-{{date}}"
except Exception:
    pass

from crc_modules.db.query import run_query, _list_tables

tables, report, queries = [], "Set 'CToggle' to True to execute", ""

if CToggle:
    try:
        q = _list_tables(schema)
        _rows, _ = run_query(CString, q)
        tables = [r[0] for r in _rows]
        executed_sql = [q]
        report = "OK – {} tables".format(len(tables))
        queries = "\n\n".join("-- query {}\n{}".format(i + 1, s) for i, s in enumerate(executed_sql))
    except Exception as e:
        report = "ERROR: {}".format(e)