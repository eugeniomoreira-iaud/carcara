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

# INPUT MAPPING  0:cs:item  1:tog:item  2:sch:item  3:tbl:item  4:col:item  5:val:item
cs_int  = _in_item(0)
tog_int = _in_item(1)
sch_int = _in_item(2)
tbl_int = _in_item(3)
col_int = _in_item(4)
val_int = _in_item(5)

Cx, Cy, report = None, None, "Set 'CToggle' to True to execute"

if tog_int:
    try:
        if not cs_int:
            raise ValueError("CString is required")
        if not sch_int or not tbl_int:
            raise ValueError("schema and table are required")

        # Unwired column/value arrive as None → first-row fallback in find_correction_parameters
        col_arg = str(col_int) if col_int else None
        val_arg = str(val_int) if val_int else None

        Cx, Cy = find_correction_parameters(cs_int, sch_int, tbl_int, col_arg, val_arg)
        report = "OK — Cx={}, Cy={}".format(Cx, Cy)

    except Exception as e:
        report = "ERROR: {}".format(e)
        Cx, Cy = None, None
