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

from crc_modules.db.query import run_query, _query_values_sql

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

        # Handle single column or multiple columns (comma-separated)
        cols = [c.strip() for c in str(col_int).split(",")] if col_int else []
        null_val = N_int if N_int else ""

        # Build SQL for multiple columns
        from crc_modules.db.query import _quote_identifier, _quote_literal
        target = "{}.{}".format(_quote_identifier(sch_int), _quote_identifier(tbl_int))
        col_list = ", ".join(_quote_identifier(c) for c in cols)

        if null_val != "":
            case_exprs = []
            for c in cols:
                qc = _quote_identifier(c)
                case_exprs.append("CASE WHEN {qc} IS NULL THEN {nv} ELSE {qc}::text END".format(
                    qc=qc, nv=_quote_literal(null_val)))
            select_clause = ", ".join(case_exprs)
        else:
            select_clause = col_list

        sql = "SELECT {} FROM {}".format(select_clause, target)

        _rows, columns = run_query(cs_int, sql)

        # Output as Grasshopper DataTree: each row is a branch, items are column values in order
        from Grasshopper.Kernel.Data import GH_Path
        tree = DataTree[object]()
        for i, row in enumerate(_rows):
            path = GH_Path(i)
            for val in row:
                tree.Add(str(val), path)
        rows = tree

        executed_sql = [sql]
        report = "OK – {} rows, {} columns returned".format(len(_rows), len(columns))
        queries = "\n\n".join("-- query {}\n{}".format(i + 1, s) for i, s in enumerate(executed_sql))
    except Exception as e:
        report = "ERROR: {}".format(e)
