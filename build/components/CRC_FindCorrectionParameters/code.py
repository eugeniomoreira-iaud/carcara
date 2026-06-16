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

from crc_modules.utils.correction import find_correction_parameters

Cx, Cy, report = None, None, "Set 'CToggle' to True to execute"

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")

        # Unwired column/value arrive as None → first-row fallback in find_correction_parameters
        col_arg = str(column) if column else None
        val_arg = str(value) if value else None

        Cx, Cy = find_correction_parameters(CString, schema, table, col_arg, val_arg)
        report = "OK — Cx={}, Cy={}".format(Cx, Cy)

    except Exception as e:
        report = "ERROR: {}".format(e)
        Cx, Cy = None, None
