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

from crc_modules.utils.sql_composer import compose

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

# INPUT MAPPING: 0:sql(sql/item), 1:var(variables/list), 2:val(values/list)
sql_int = _in_item(0)
var_int = _in_list(1)
val_int = _in_list(2)

statement, report, out = "", "", ""

try:
    if not sql_int:
        raise ValueError("No SQL template provided.")
    _variables = var_int if isinstance(var_int, (list, tuple)) else ([var_int] if var_int else [])
    _values = val_int if isinstance(val_int, (list, tuple)) else ([val_int] if val_int else [])
    if len(_variables) != len(_values):
        raise ValueError(
            f"variables and values must have the same length "
            f"(got {len(_variables)} and {len(_values)})."
        )
    replacements = dict(zip([str(v) for v in _variables], [str(v) for v in _values]))
    statement = compose(sql_int, replacements)
    n = len(replacements)
    report = f"OK – {n} replacement{'s' if n != 1 else ''} applied"
    out = f"Replaced {n} placeholder{'s' if n != 1 else ''}: {list(replacements.keys())}"
except Exception as e:
    report = f"ERROR: {e}"
    out = f"Error: {e}"
