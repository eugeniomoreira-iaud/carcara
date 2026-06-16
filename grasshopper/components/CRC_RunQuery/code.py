"""CRC_RunQuery: Run a raw SQL SELECT and return results as a DataTree organised by column."""
# r: psycopg2
import sys
import os

# Make the crc_modules package importable from a Grasshopper Python 3 component.
# GHPython runs this code from an in-memory string, so __file__ is undefined.
# The installer copies the whole deployable folder to:
#   %APPDATA%\Grasshopper\UserObjects\carcara\   (Windows)
# with the package at .../carcara/crc_modules. Put the PARENT (.../carcara) on
# sys.path so `import crc_modules` resolves.
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
    ghenv.Component.Message = "v{{component_version}}"
except Exception:
    pass

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.db.query import run_query

rows = DataTree[object]()
columns = DataTree[object]()
report = "Set 'CToggle' to True to execute"

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not sql:
            raise ValueError("sql is required")

        _rows, _col_names = run_query(CString, sql)

        nrows = len(_rows)
        ncols = len(_col_names)

        # Transpose row-major result to column-major DataTree.
        # Branch i (GH_Path(i)) = all values for column i across every row.
        # columns mirrors the same structure: branch i = single column name string.
        for col_idx, col_name in enumerate(_col_names):
            path = GH_Path(col_idx)
            columns.Add(str(col_name), path)
            for row in _rows:
                val = row[col_idx] if col_idx < len(row) else None
                rows.Add(str(val) if val is not None else "", path)

        report = "OK – {} rows, {} columns".format(nrows, ncols)
    except Exception as e:
        report = "ERROR: {}".format(e)
