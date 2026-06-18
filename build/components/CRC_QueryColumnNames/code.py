"""CRC_QueryColumnNames: List all columns and their types in a specified table."""
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

from crc_modules.db.query import run_query, _list_columns

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
from Grasshopper import DataTree

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

# INPUT MAPPING: 0:cs(CString/item), 1:tog(CToggle/item), 2:sch(schema/item), 3:tbl(table/item)
cs_int  = _in_item(0)
tog_int = _in_item(1)
sch_int = _in_item(2)
tbl_int = _in_item(3)

columns, types, report, queries = [], [], "Set 'CToggle' to True to execute", ""

if tog_int:
    try:
        q = _list_columns(sch_int, tbl_int)
        _rows, _ = run_query(cs_int, q)
        columns = [r[0] for r in _rows]
        types = [r[1] for r in _rows]
        executed_sql = [q]
        report = "OK – {} columns".format(len(columns))
        queries = "\n\n".join("-- query {}\n{}".format(i + 1, s) for i, s in enumerate(executed_sql))
    except Exception as e:
        report = "ERROR: {}".format(e)
