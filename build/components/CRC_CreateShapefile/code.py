"""CRC_CreateShapefile: CREATE PostGIS table with attribute columns + auto-detected geometry column."""
# r: psycopg2-binary, shapely
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

from crc_modules.db.writer import create_table_with_geometry
from crc_modules.geometry.wkt import combine_wkts, detect_wkt_type, promote_to_multi
from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt

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
# 6:vals:tree  7:ids:tree  8:geo:tree  9:srid:item  10:cx:item  11:cy:item  12:rep:item
cs_int   = _in_item(0)
tog_int  = _in_item(1)
sch_int  = _in_item(2)
tbl_int  = _in_item(3)
cols_int = _in_list(4)
types_int = _in_list(5)
vals_int = _in_tree(6)
ids_int  = _in_tree(7)
geo_int  = _in_tree(8)
srid_int = _in_item(9)
cx_int   = _in_item(10)
cy_int   = _in_item(11)
rep_int  = _in_item(12)

affected, report = 0, "Set CToggle=True to CREATE the table and INSERT rows. This operation is destructive if replace_table=True."

if tog_int:
    try:
        if not cs_int:
            raise ValueError("CString is required")
        if not sch_int or not tbl_int:
            raise ValueError("schema and table are required")

        # --- geometry DataTree (required) ---
        if geo_int is None or not hasattr(geo_int, "BranchCount") or geo_int.BranchCount == 0:
            raise ValueError("geometry DataTree is required (branch per row)")

        num_geo_branches = geo_int.BranchCount

        # --- optional attribute columns ---
        names = [str(c) for c in (cols_int or [])]
        types = [str(t) for t in (types_int or [])]
        if len(names) != len(types):
            raise ValueError(
                "columnNames and columnTypes must be parallel (same length); "
                "got {} names and {} types".format(len(names), len(types))
            )
        columns = list(zip(names, types))

        # --- optional attribute values DataTree (branch per row) ---
        rows = []
        if vals_int is not None and hasattr(vals_int, "BranchCount") and vals_int.BranchCount > 0:
            if vals_int.BranchCount != num_geo_branches:
                raise ValueError(
                    "values tree has {} branches but geometry tree has {} branches — must be equal".format(
                        vals_int.BranchCount, num_geo_branches
                    )
                )
            for i in range(vals_int.BranchCount):
                branch = [str(x) if x is not None else "" for x in vals_int.Branch(i)]
                if names and len(branch) != len(names):
                    raise ValueError(
                        "Row {} has {} attribute values but {} columns are declared".format(
                            i, len(branch), len(names)
                        )
                    )
                rows.append(branch)
        elif names:
            # columnNames declared but no values tree — fill all rows with empty
            rows = [[""] * len(names) for _ in range(num_geo_branches)]

        # --- optional idValues (DataTree: branch per row, one id per branch) ---
        ids = None
        if ids_int is not None and hasattr(ids_int, "BranchCount") and ids_int.BranchCount > 0:
            ids = []
            for i in range(ids_int.BranchCount):
                branch = ids_int.Branch(i)
                ids.append(str(branch[0]) if branch and branch[0] is not None else "")
            if len(ids) != num_geo_branches:
                raise ValueError(
                    "idValues has {} branches but geometry tree has {} branches".format(
                        len(ids), num_geo_branches
                    )
                )

        # --- convert each geometry branch to one WKT per row ---
        row_wkts = []
        for i in range(num_geo_branches):
            branch_geoms = [g for g in geo_int.Branch(i) if g is not None]
            if not branch_geoms:
                raise ValueError("Geometry branch {} is empty".format(i))
            branch_wkts = [rh_geometry_to_wkt(g) for g in branch_geoms]
            row_wkts.append(combine_wkts(branch_wkts))

        # --- detect geometry type across all rows (strict single base type) ---
        geom_type = detect_wkt_type(row_wkts)

        # --- promote every row to MULTI when the column type is MULTI ---
        if geom_type.startswith("MULTI"):
            row_wkts = [promote_to_multi(w, geom_type) for w in row_wkts]

        # --- scalar inputs ---
        sr = int(srid_int) if srid_int else 4326
        cx = str(cx_int) if cx_int else "0"
        cy = str(cy_int) if cy_int else "0"

        # --- call module ---
        n = create_table_with_geometry(
            cs_int, sch_int, tbl_int, columns, rows,
            row_wkts, geom_type, sr, cx, cy,
            id_values=ids,
            replace_table=bool(rep_int)
        )
        affected = n if n is not None else 0
        report = "success: true\nRows Inserted: {}".format(affected)

    except Exception as e:
        report = "ERROR: {}".format(e)
