"""CRC_QueryColumnNames: List all columns and their types in a specified table."""
import sys
import os

# Make the crc_modules package importable. GHPython runs from an in-memory
# string, so __file__ is undefined; the installer copies the whole `carcara`
# folder into UserObjects, with the package at .../UserObjects/carcara/crc_modules.
# Put the PARENT (.../UserObjects/carcara) on sys.path so `import crc_modules` works.
_bases = []
_appdata = os.environ.get("APPDATA")
if _appdata:
    _bases.append(os.path.join(_appdata, "Grasshopper", "UserObjects", "carcara"))
_bases.append(os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "McNeel",
    "Rhinoceros", "8.0", "Plug-ins", "Grasshopper", "UserObjects", "carcara"))
for _b in _bases:
    if os.path.isdir(_b) and _b not in sys.path:
        sys.path.insert(0, _b)

try:
    ghenv.Component.Message = "v{{version}} - {{date}}"
except Exception:
    pass

from crc_modules.db.query import run_query, _list_columns

columns, types, report, queries = [], [], "Set 'CToggle' to True to execute", ""

if CToggle:
    try:
        q = _list_columns(schema, table)
        _rows, _ = run_query(CString, q)
        columns = [r[0] for r in _rows]
        types = [r[1] for r in _rows]
        executed_sql = [q]
        report = "OK – {} columns".format(len(columns))
        queries = "\n\n".join("-- query {}\n{}".format(i + 1, s) for i, s in enumerate(executed_sql))
    except Exception as e:
        report = "ERROR: {}".format(e)