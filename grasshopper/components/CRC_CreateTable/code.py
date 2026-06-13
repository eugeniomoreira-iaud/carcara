"""CRC_CreateTable: CREATE TABLE in PostGIS, optionally with a geometry column."""
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

from crc_modules.db.writer import create_table

affected, report = 0, "Set CToggle=True to CREATE the table. This operation is destructive if replace_table=True."

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not schema or not table:
            raise ValueError("schema and table are required")
        names = [str(c) for c in (column_names or [])]
        types = [str(t) for t in (column_types or [])]
        if len(names) != len(types):
            raise ValueError("column_names and column_types must be parallel (same length)")
        cols = list(zip(names, types))
        gc = geom_column if geom_column else None
        gt = geom_type if geom_type else None
        sr = int(srid) if srid else 4326
        rc = create_table(CString, schema, table, cols, geom_column=gc, geom_type=gt, srid=sr, replace_table=bool(replace_table))
        affected = 0 if rc is None or rc < 0 else rc
        report = "success: true\nRows Affected: {}".format(affected)
    except Exception as e:
        report = "ERROR: {}".format(e)
