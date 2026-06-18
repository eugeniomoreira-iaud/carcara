"""CRC_CreateTable: CREATE TABLE in PostGIS and INSERT row data with mandatory primary key."""
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

from crc_modules.db.writer import create_table_with_data

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

# INPUT MAPPING
# 0:cs:item  1:tog:item  2:sch:item  3:tbl:item  4:cols:list  5:types:list
# 6:vals:tree  7:ids:tree  8:rep:item
cs_int    = _in_item(0)
tog_int   = _in_item(1)
sch_int   = _in_item(2)
tbl_int   = _in_item(3)
cols_int  = _in_list(4)
types_int = _in_list(5)
vals_int  = _in_tree(6)
ids_int   = _in_tree(7)
rep_int   = _in_item(8)

affected, report = 0, "Set CToggle=True to CREATE the table and INSERT rows. This operation is destructive if replace_table=True."

if tog_int:
    try:
        if not cs_int:
            raise ValueError("CString is required")
        if not sch_int or not tbl_int:
            raise ValueError("schema and table are required")

        # --- validate parallel column lists ---
        names = [str(c) for c in (cols_int or [])]
        types = [str(t) for t in (types_int or [])]
        if len(names) != len(types):
            raise ValueError(
                "columnNames and columnTypes must be parallel (same length); "
                "got {} names and {} types".format(len(names), len(types))
            )
        columns = list(zip(names, types))

        # --- read DataTree rows (branch per row) ---
        rows = []
        if vals_int is not None and hasattr(vals_int, "BranchCount"):
            for i in range(vals_int.BranchCount):
                branch = [str(x) if x is not None else "" for x in vals_int.Branch(i)]
                if names and len(branch) != len(names):
                    raise ValueError(
                        "Row {} has {} values but {} columns are declared".format(
                            i, len(branch), len(names)
                        )
                    )
                rows.append(branch)

        # --- optional idValues (DataTree: branch per row, one id per branch) ---
        ids = None
        if ids_int is not None and hasattr(ids_int, "BranchCount") and ids_int.BranchCount > 0:
            ids = []
            for i in range(ids_int.BranchCount):
                branch = ids_int.Branch(i)
                ids.append(str(branch[0]) if branch and branch[0] is not None else "")
            if rows and len(ids) != len(rows):
                raise ValueError(
                    "idValues has {} branches but values tree has {} rows".format(
                        len(ids), len(rows)
                    )
                )

        # --- call module (coercion + PK resolution happen inside) ---
        n = create_table_with_data(
            cs_int, sch_int, tbl_int, columns, rows,
            id_values=ids,
            replace_table=bool(rep_int)
        )
        affected = n if n is not None else 0
        report = "success: true\nRows Inserted: {}".format(affected)

    except Exception as e:
        report = "ERROR: {}".format(e)
