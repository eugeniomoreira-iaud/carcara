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
        names = [str(c) for c in (columnNames or [])]
        types = [str(t) for t in (columnTypes or [])]
        if len(names) != len(types):
            raise ValueError(
                "columnNames and columnTypes must be parallel (same length); "
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
            # columnNames declared but no values tree — fill all rows with empty
            rows = [[""] * len(names) for _ in range(num_geo_branches)]

        # --- optional idValues (DataTree: branch per row, one id per branch) ---
        ids = None
        if idValues is not None and hasattr(idValues, "BranchCount") and idValues.BranchCount > 0:
            ids = []
            for i in range(idValues.BranchCount):
                branch = idValues.Branch(i)
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
            replace_table=bool(replaceTable)
        )
        affected = n if n is not None else 0
        report = "success: true\nRows Inserted: {}".format(affected)

    except Exception as e:
        report = "ERROR: {}".format(e)
