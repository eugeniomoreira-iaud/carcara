"""Run ODBC Command - PostgreSQL DDL/DML Execution Component

This component executes SQL commands (DDL/DML) against PostgreSQL databases
using ODBC connections. Commands include CREATE, ALTER, DROP, INSERT, UPDATE,
DELETE, and other non-SELECT statements. Returns execution feedback.

Typical usage:
    Connection String -> Toggle True -> Enter Command -> Receive Feedback

Logic:
    1. Validate connection string, toggle, and command inputs
    2. Execute SQL command using carcara_odbc module
    3. Parse feedback to determine success or failure
    4. Return detailed execution feedback
    5. Display appropriate runtime messages

Args (Component Inputs):
    CString: (String) ODBC connection string with encoded password
        - Type: str
        - Access: item
        - Optional: No
    
    CToggle: (Boolean) Set True to execute command
        - Type: bool
        - Access: item
        - Optional: No (defaults to False)
    
    Command: (String) SQL command statement to execute
        - Type: str
        - Access: item
        - Optional: No
        - Note: Use for DDL/DML statements, not SELECT queries

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    Fb: (String) Detailed command execution feedback
        - Type: str
        - Format: Includes success status, rows affected, and error messages

Version: 1.3
Date: 2025/11/13
Requires: carcara_odbc module
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Grasshopper
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML

user_objects_folder = Grasshopper.Folders.UserObjectFolders[0]
module_path = os.path.join(user_objects_folder, "carcara", "modules")
if module_path not in sys.path:
    sys.path.append(module_path)

import carcara_odbc as odbc
importlib.reload(odbc)


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "1.3"
COMPONENT_DATE = "2025/11/13"

ghenv.Component.Name = "Run ODBC Command"
ghenv.Component.NickName = "runCommand.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '03.Utilities'
ghenv.Component.Description = "Executes an ODBC command (DDL/DML) and returns execution feedback."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "CString"
ghenv.Component.Params.Input[0].NickName = "CString"
ghenv.Component.Params.Input[0].Description = "Connection string with encoded password."

ghenv.Component.Params.Input[1].Name = "CToggle"
ghenv.Component.Params.Input[1].NickName = "CToggle"
ghenv.Component.Params.Input[1].Description = "Set True to connect."

ghenv.Component.Params.Input[2].Name = "Command"
ghenv.Component.Params.Input[2].NickName = "Command"
ghenv.Component.Params.Input[2].Description = "SQL command to execute."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "Fb"
ghenv.Component.Params.Output[1].NickName = "Fb"
ghenv.Component.Params.Output[1].Description = "Detailed command execution feedback."


################
# HELPER FUNCTIONS
################
def log(message):
    """
    Print message to default 'out' output.
    
    Args:
        message (str): Message text to log
    """
    print(message)


def report(level, message):
    """
    Send runtime message to Grasshopper component (warnings/errors only).
    
    Args:
        level (GH_RuntimeMessageLevel): Message severity level
        message (str): Message text to display
    """
    ghenv.Component.AddRuntimeMessage(level, message)
    log(message)


def validate_inputs(cstring, ctoggle, command):
    """
    Validate all input parameters before execution.
    
    Args:
        cstring (str): Connection string
        ctoggle (bool): Connection toggle
        command (str): SQL command string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not ctoggle:
        return False, "CToggle is False. No connection attempted."
    
    if not cstring or not cstring.strip():
        return False, "Empty connection string."
    
    if not command or not command.strip():
        return False, "Command cannot be empty."
    
    return True, None


def parse_feedback(feedback):
    """
    Parse command execution feedback to determine success or failure.
    
    Args:
        feedback (str): Feedback string from command execution
    
    Returns:
        tuple: (success, message_level, summary)
    """
    if not isinstance(feedback, str):
        return True, RML.Remark, "Command executed."
    
    feedback_lower = feedback.lower()
    
    if "success: true" in feedback_lower:
        rows_affected = extract_rows_affected(feedback)
        if rows_affected is not None:
            return True, RML.Remark, "Command executed successfully. {} row(s) affected.".format(rows_affected)
        return True, RML.Remark, "Command executed successfully."
    
    if "error" in feedback_lower or "success: false" in feedback_lower:
        return False, RML.Error, "Command failed. Check feedback for details."
    
    return True, RML.Remark, "Command executed."


def extract_rows_affected(feedback):
    """
    Extract number of rows affected from feedback string.
    
    Args:
        feedback (str): Feedback string
    
    Returns:
        int or None: Number of rows affected, or None if not found
    """
    try:
        if "rows affected:" in feedback.lower():
            parts = feedback.split("Rows Affected:")
            if len(parts) > 1:
                rows_str = parts[1].strip().split()[0]
                return int(rows_str)
    except:
        pass
    return None


################
# INPUT HANDLING & VALIDATION
################
CString = globals().get('CString', "")
CToggle = globals().get('CToggle', False)
Command = globals().get('Command', "")

if not isinstance(CToggle, bool):
    log("Warning: 'CToggle' must be a boolean value. Using False.")
    CToggle = False

if CString is not None and not isinstance(CString, str):
    CString = str(CString)

if Command is not None and not isinstance(Command, str):
    Command = str(Command)


################
# EXECUTION
################
Fb = None

try:
    is_valid, error_msg = validate_inputs(CString, CToggle, Command)
    
    if not is_valid:
        if not CToggle:
            log(error_msg)
        else:
            report(RML.Error, error_msg)
        Fb = error_msg
    else:
        log("Executing command...")
        log("Connection string: {}".format(CString[:50] + "..." if len(CString) > 50 else CString))
        log("Command: {}".format(Command[:100] + "..." if len(Command) > 100 else Command))
        
        Fb = odbc.run_command(CToggle, CString, Command)
        
        success, message_level, summary = parse_feedback(Fb)
        
        if success:
            log(summary)
        else:
            log("Command execution failed")
            log("Feedback: {}".format(Fb))
            report(message_level, "Command failed (see 'out' for details).")

except ImportError as e:
    error_msg = "Module import error: {}. Ensure carcara_odbc is in the modules folder.".format(e)
    report(RML.Error, "Module import error - see 'out' for details.")
    log(error_msg)
    Fb = error_msg
except AttributeError as e:
    error_msg = "Module function error: {}. Check carcara_odbc module version.".format(e)
    report(RML.Error, "Module function error - see 'out' for details.")
    log(error_msg)
    Fb = error_msg
except Exception as e:
    error_msg = "Unexpected error: {} (Type: {}).".format(e, type(e).__name__)
    report(RML.Error, "Unexpected error - see 'out' for details.")
    log(error_msg)
    Fb = error_msg
