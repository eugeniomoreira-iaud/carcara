"""CRC_CreateShapefile: INSERT WKT geometries into PostGIS, adding false-origin correction in SQL."""
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

from crc_modules.db.writer import insert_geometries

report = "Set CToggle=True to INSERT geometries. This operation writes to the database."

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")
        if not geom_column:
            raise ValueError("geom_column is required")
        wkts = [str(w) for w in (geometry or []) if w is not None and str(w).strip()]
        if not wkts:
            raise ValueError("geometry (WKT list) is required")
        sr = int(srid) if srid else 4326
        cx = str(Cx) if Cx else "0"
        cy = str(Cy) if Cy else "0"
        names = [str(c) for c in column_names] if column_names else None
        vals = None
        if names and values is not None and hasattr(values, "BranchCount"):
            vals = []
            for i in range(values.BranchCount):
                vals.append([str(x) for x in values.Branch(i)])
        rc = insert_geometries(CString, schema, table, geom_column, wkts, sr,
                               cx=cx, cy=cy, column_names=names, values=vals)
        report = "success: true\nRows Affected: {}".format(rc)
    except Exception as e:
        report = "ERROR: {}".format(e)
