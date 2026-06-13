"""CRC_ValuesWithSpatialFilter: Query attribute values with spatial filter and coordinate correction."""
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

import Grasshopper
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

from crc_modules.db.spatial_query import get_values_with_spatial_filter
from crc_modules.rhino.wkt_conversion import rh_geometry_to_wkt

values, report = DataTree[object](), "Set 'CToggle' to True to execute"

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")
        if columns is None:
            raise ValueError("columns list is required")
        if spatial_filter is None:
            raise ValueError("spatial_filter geometry is required")

        # Handle columns input (can be list or comma-separated string)
        if isinstance(columns, (list, tuple)):
            col_list = [str(c).strip() for c in columns]
        else:
            col_list = [c.strip() for c in str(columns).split(",")]

        null_val = str(N) if N else ""

        srid = int(SRID) if SRID else 4326
        func = int(function) if function else 0
        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"
        sql_filter = sql_filter if sql_filter else None

        # Convert GH geometry to WKT for spatial filter
        filter_wkt = rh_geometry_to_wkt(spatial_filter)
        if not filter_wkt:
            raise ValueError("Failed to convert spatial filter geometry to WKT")

        rows, col_names = get_values_with_spatial_filter(
            CString, schema, table, col_list, filter_wkt,
            cx=cx, cy=cy, srid=srid, sql_filter=sql_filter, func=func
        )

        # Apply NULL replacement if specified
        if null_val != "":
            rows = [[null_val if v is None else v for v in row] for row in rows]

        # Output as Grasshopper DataTree: each column is a branch
        for col_idx, col_name in enumerate(col_names):
            path = GH_Path(col_idx)
            for row_idx, row in enumerate(rows):
                if col_idx < len(row):
                    val = row[col_idx]
                    values.Add(str(val) if val is not None else "", path)

        report = f"OK – {len(rows)} rows, {len(col_names)} columns returned"
    except Exception as e:
        report = f"ERROR: {e}"
