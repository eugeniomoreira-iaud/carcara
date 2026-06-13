import sys
import os

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
    ghenv.Component.Message = "v{{version}} - {{date}}"
except Exception:
    pass

from crc_modules.utils.sql_composer import compose

stmt, report, out = "", "", ""

try:
    if not sql:
        raise ValueError("No SQL template provided.")
    _var = var if isinstance(var, (list, tuple)) else ([var] if var else [])
    _val = val if isinstance(val, (list, tuple)) else ([val] if val else [])
    if len(_var) != len(_val):
        raise ValueError(
            f"var and val must have the same length "
            f"(got {len(_var)} and {len(_val)})."
        )
    replacements = dict(zip([str(v) for v in _var], [str(v) for v in _val]))
    stmt = compose(sql, replacements)
    n = len(replacements)
    report = f"OK – {n} replacement{'s' if n != 1 else ''} applied"
    out = f"Replaced {n} placeholder{'s' if n != 1 else ''}: {list(replacements.keys())}"
except Exception as e:
    report = f"ERROR: {e}"
    out = f"Error: {e}"