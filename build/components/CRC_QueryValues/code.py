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

rows, columns, report, queries = [], [], "Set 'CToggle' to True to execute", ""

if CToggle:
    try:
        if not schema or not table or not column:
            raise ValueError("schema, table, and column are required")
        
        # Handle single column or multiple columns (comma-separated)
        cols = [c.strip() for c in str(column).split(",")] if column else []
        null_val = nullReplacement if nullReplacement else ""
        
        # Build SQL for multiple columns
        from crc_modules.db.query import _quote_identifier, _quote_literal
        target = "{}.{}".format(_quote_identifier(schema), _quote_identifier(table))
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
        
        _rows, columns = run_query(CString, sql)

        # Output as Grasshopper DataTree: each row is a branch, items are column values in order
        from Grasshopper import DataTree
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