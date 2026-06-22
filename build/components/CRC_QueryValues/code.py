"""CRC_QueryValues: Query column(s) from a table with NULL replacement, output as tree."""
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

from crc_modules.db.query import query_values

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

# INPUT MAPPING: 0:cs(CString/item), 1:tog(CToggle/item), 2:sch(schema/item),
#                3:tbl(table/item), 4:col(column/item), 5:N(nullReplacement/item)
cs_int  = _in_item(0)
tog_int = _in_item(1)
sch_int = _in_item(2)
tbl_int = _in_item(3)
col_int = _in_item(4)
N_int   = _in_item(5)

rows, columns, report, queries = [], [], "Set 'CToggle' to True to execute", ""

if tog_int:
    try:
        if not sch_int or not tbl_int or not col_int:
            raise ValueError("schema, table, and column are required")

        cols = [c.strip() for c in str(col_int).split(",")] if col_int else []
        null_val = N_int if N_int else ""

        executed_sql = []
        _rows, columns = query_values(cs_int, sch_int, tbl_int, cols, null_val, sql_log=executed_sql)

        # Output as Grasshopper DataTree: each row is a branch, items are column values in order
        from Grasshopper.Kernel.Data import GH_Path
        tree = DataTree[object]()
        for i, row in enumerate(_rows):
            path = GH_Path(i)
            for val in row:
                tree.Add(str(val), path)
        rows = tree

        report = "OK – {} rows, {} columns returned".format(len(_rows), len(columns))
        queries = "\n\n".join("-- query {}\n{}".format(i + 1, s) for i, s in enumerate(executed_sql))
    except Exception as e:
        report = "ERROR: {}".format(e)
