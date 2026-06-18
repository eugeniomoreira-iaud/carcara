"""CRC_RunCommand: Run a SQL DDL/DML command (non-SELECT) and return execution feedback."""
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

from crc_modules.db.query import run_command

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

# INPUT MAPPING: 0:cs(CString/item), 1:tog(CToggle/item), 2:sql(sql/item)
cs_int  = _in_item(0)
tog_int = _in_item(1)
sql_int = _in_item(2)

report = "Set 'CToggle' to True to execute"

if tog_int:
    try:
        if not cs_int:
            raise ValueError("CString is required")
        if not sql_int:
            raise ValueError("sql is required")

        affected = run_command(cs_int, sql_int)
        report = "success: true\nRows Affected: {}".format(affected)
    except Exception as e:
        report = "success: false\n{}".format(e)
