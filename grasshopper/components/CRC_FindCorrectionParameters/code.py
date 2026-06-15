"""CRC_FindCorrectionParameters: Find coordinate correction parameters (false origin) from a PostGIS table.

Queries one row from the table, auto-detects the geometry column, computes
the centroid, and returns (Cx, Cy) as verbatim text strings for use as
false-origin correction values in Phase 05 geometry query components.

Row selection:
  - Column AND Value given → WHERE Column = Value  LIMIT 1
  - Both omitted           → first row of the table LIMIT 1

Cx/Cy are returned as TEXT and must never be float()-parsed — they are fed
directly into the Cx/Cy inputs of CRC_GeometryEntities and related components.
"""
# r: psycopg2
import sys
import os

# Make the crc_modules package importable from a Grasshopper Python 3 component.
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

from crc_modules.utils.correction import find_correction_parameters

Cx, Cy, report = None, None, "Set 'CToggle' to True to execute"

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not Schema or not Table:
            raise ValueError("Schema and Table are required")

        # Unwired Column/Value arrive as None → first-row fallback in find_correction_parameters
        col_arg = str(Column) if Column else None
        val_arg = str(Value) if Value else None

        Cx, Cy = find_correction_parameters(CString, Schema, Table, col_arg, val_arg)
        report = "OK — Cx={}, Cy={}".format(Cx, Cy)

    except Exception as e:
        report = "ERROR: {}".format(e)
        Cx, Cy = None, None
