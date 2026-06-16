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

statement, report, out = "", "", ""

try:
    if not sql:
        raise ValueError("No SQL template provided.")
    _variables = variables if isinstance(variables, (list, tuple)) else ([variables] if variables else [])
    _values = values if isinstance(values, (list, tuple)) else ([values] if values else [])
    if len(_variables) != len(_values):
        raise ValueError(
            f"variables and values must have the same length "
            f"(got {len(_variables)} and {len(_values)})."
        )
    replacements = dict(zip([str(v) for v in _variables], [str(v) for v in _values]))
    statement = compose(sql, replacements)
    n = len(replacements)
    report = f"OK – {n} replacement{'s' if n != 1 else ''} applied"
    out = f"Replaced {n} placeholder{'s' if n != 1 else ''}: {list(replacements.keys())}"
except Exception as e:
    report = f"ERROR: {e}"
    out = f"Error: {e}"