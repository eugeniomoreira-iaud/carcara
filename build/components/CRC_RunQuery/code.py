"""CRC_RunQuery: Run a raw SQL SELECT and return results as a DataTree organised by column."""
# r: psycopg2-binary
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
