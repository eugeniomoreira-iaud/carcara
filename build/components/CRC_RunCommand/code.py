"""CRC_RunCommand: Run a SQL DDL/DML command (non-SELECT) and return execution feedback."""
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

from crc_modules.db.query import run_command

report = "Set 'CToggle' to True to execute"

if CToggle:
    try:
        if not CString:
            raise ValueError("CString is required")
        if not sql:
            raise ValueError("sql is required")

        affected = run_command(CString, sql)
        report = "success: true\nRows Affected: {}".format(affected)
    except Exception as e:
        report = "success: false\n{}".format(e)
