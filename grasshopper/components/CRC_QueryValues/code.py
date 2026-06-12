"""CRC_QueryValues: Run arbitrary SQL SELECT, return rows and columns."""
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

from crc_modules.db.query import run_query

rows, columns, report = [], [], "Set 'CToggle' to True to execute"

if CToggle:
    try:
        _rows, columns = run_query(CString, sql)
        rows = [str(r) for r in _rows]
        report = "OK – {} rows returned".format(len(rows))
    except Exception as e:
        report = "ERROR: {}".format(e)