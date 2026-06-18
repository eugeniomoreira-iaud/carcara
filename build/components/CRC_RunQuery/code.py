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

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
def _unwrap(g):
    return g.Value if hasattr(g, "Value") else g

def _in_item(i):
    for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True):
        return _unwrap(g)
    return None

def _in_list(i):
    return [_unwrap(g) for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True)]

def _in_tree(i):
    src = ghenv.Component.Params.Input[i].VolatileData
    t = DataTree[object]()
    for p in src.Paths:
        for g in src[p]:
            t.Add(_unwrap(g), p)
    return t
# ========================================================================================

# INPUT MAPPING: 0:cs(CString/item), 1:tog(CToggle/item), 2:sql(sql/item)
cs_int  = _in_item(0)
tog_int = _in_item(1)
sql_int = _in_item(2)

rows = DataTree[object]()
columns = DataTree[object]()
report = "Set 'CToggle' to True to execute"

if tog_int:
    try:
        if not cs_int:
            raise ValueError("CString is required")
        if not sql_int:
            raise ValueError("sql is required")

        _rows, _col_names = run_query(cs_int, sql_int)

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
