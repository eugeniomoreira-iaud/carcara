"""CRC_CreateShapefile: CREATE PostGIS table with attribute columns + auto-detected geometry column."""
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
    ghenv.Component.Message = "v{{component_version}}"
except Exception:
    pass

from crc_modules.db.writer import create_table_with_geometry
from crc_modules.geometry.wkt import combine_wkts, detect_wkt_type, promote_to_multi
from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt

affected, report = 0, "Set CToggle=True to CREATE the table and INSERT rows. This operation is destructive if replace_table=True."

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")

        # --- geometry DataTree (required) ---
        if geometry is None or not hasattr(geometry, "BranchCount") or geometry.BranchCount == 0:
            raise ValueError("geometry DataTree is required (branch per row)")

        num_geo_branches = geometry.BranchCount

        # --- optional attribute columns ---
        names = [str(c) for c in (column_names or [])]
        types = [str(t) for t in (column_types or [])]
        if len(names) != len(types):
            raise ValueError(
                "column_names and column_types must be parallel (same length); "
                "got {} names and {} types".format(len(names), len(types))
            )
        columns = list(zip(names, types))

        # --- optional attribute values DataTree (branch per row) ---
        rows = []
        if values is not None and hasattr(values, "BranchCount") and values.BranchCount > 0:
            if values.BranchCount != num_geo_branches:
                raise ValueError(
                    "values tree has {} branches but geometry tree has {} branches — must be equal".format(
                        values.BranchCount, num_geo_branches
                    )
                )
            for i in range(values.BranchCount):
                branch = [str(x) if x is not None else "" for x in values.Branch(i)]
                if names and len(branch) != len(names):
                    raise ValueError(
                        "Row {} has {} attribute values but {} columns are declared".format(
                            i, len(branch), len(names)
                        )
                    )
                rows.append(branch)
        elif names:
            # column_names declared but no values tree — fill all rows with empty
            rows = [[""] * len(names) for _ in range(num_geo_branches)]

        # --- optional id_values (DataTree: branch per row, one id per branch) ---
        ids = None
        if id_values is not None and hasattr(id_values, "BranchCount") and id_values.BranchCount > 0:
            ids = []
            for i in range(id_values.BranchCount):
                branch = id_values.Branch(i)
                ids.append(str(branch[0]) if branch and branch[0] is not None else "")
            if len(ids) != num_geo_branches:
                raise ValueError(
                    "id_values has {} branches but geometry tree has {} branches".format(
                        len(ids), num_geo_branches
                    )
                )

        # --- convert each geometry branch to one WKT per row ---
        row_wkts = []
        for i in range(num_geo_branches):
            branch_geoms = [g for g in geometry.Branch(i) if g is not None]
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
        sr = int(srid) if srid else 4326
        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"

        # --- call module ---
        n = create_table_with_geometry(
            CString, schema, table, columns, rows,
            row_wkts, geom_type, sr, cx, cy,
            id_values=ids,
            replace_table=bool(replace_table)
        )
        affected = n if n is not None else 0
        report = "success: true\nRows Inserted: {}".format(affected)

    except Exception as e:
        report = "ERROR: {}".format(e)
