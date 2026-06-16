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

affected, report = 0, "Set CToggle=True to CREATE the table and INSERT rows. This operation is destructive if replace_table=True."

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")

        # --- validate parallel column lists ---
        names = [str(c) for c in (columnNames or [])]
        types = [str(t) for t in (columnTypes or [])]
        if len(names) != len(types):
            raise ValueError(
                "columnNames and columnTypes must be parallel (same length); "
                "got {} names and {} types".format(len(names), len(types))
            )
        columns = list(zip(names, types))

        # --- read DataTree rows (branch per row) ---
        rows = []
        if values is not None and hasattr(values, "BranchCount"):
            for i in range(values.BranchCount):
                branch = [str(x) if x is not None else "" for x in values.Branch(i)]
                if names and len(branch) != len(names):
                    raise ValueError(
                        "Row {} has {} values but {} columns are declared".format(
                            i, len(branch), len(names)
                        )
                    )
                rows.append(branch)

        # --- optional idValues (DataTree: branch per row, one id per branch) ---
        ids = None
        if idValues is not None and hasattr(idValues, "BranchCount") and idValues.BranchCount > 0:
            ids = []
            for i in range(idValues.BranchCount):
                branch = idValues.Branch(i)
                ids.append(str(branch[0]) if branch and branch[0] is not None else "")
            if rows and len(ids) != len(rows):
                raise ValueError(
                    "idValues has {} branches but values tree has {} rows".format(
                        len(ids), len(rows)
                    )
                )

        # --- call module (coercion + PK resolution happen inside) ---
        n = create_table_with_data(
            CString, schema, table, columns, rows,
            id_values=ids,
            replace_table=bool(replaceTable)
        )
        affected = n if n is not None else 0
        report = "success: true\nRows Inserted: {}".format(affected)

    except Exception as e:
        report = "ERROR: {}".format(e)
