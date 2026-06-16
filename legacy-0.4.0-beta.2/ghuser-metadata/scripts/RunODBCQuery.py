"""Run ODBC Query - PostgreSQL Query Execution Component

This component executes SQL queries against PostgreSQL databases using ODBC
connections. Results are returned as Grasshopper DataTrees with separate
trees for data and column headers.

Typical usage:
    Connection String -> Toggle True -> Enter Query -> Receive Results

Logic:
    1. Validate connection string, toggle, and query inputs
    2. Execute SQL query using carcara_odbc module
    3. Return results as DataTree (columns as branches)
    4. Return headers as DataTree (column names)
    5. Handle errors and display runtime messages

Args (Component Inputs):
    CString: (String) ODBC connection string with encoded password
        - Type: str
        - Access: item
        - Optional: No
    
    CToggle: (Boolean) Set True to execute query
        - Type: bool
        - Access: item
        - Optional: No (defaults to False)
    
    Query: (String) SQL query statement to execute
        - Type: str
        - Access: item
        - Optional: No

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    QResult: (DataTree[object]) Query results with columns as branches
        - Type: Grasshopper.DataTree[object]
        - Structure: Each branch contains one column of data
    
    QHeaders: (DataTree[str]) Column names matching result structure
        - Type: Grasshopper.DataTree[str]
        - Structure: Mirrors QResult tree structure

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
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
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

ghenv.Component.Name = "Run ODBC Query"
ghenv.Component.NickName = "runQueryTree.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '03.Utilities'
ghenv.Component.Description = "Executes an ODBC query and returns results as DataTrees (results & headers)."
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

ghenv.Component.Params.Input[2].Name = "Query"
ghenv.Component.Params.Input[2].NickName = "Query"
ghenv.Component.Params.Input[2].Description = "SQL query to execute."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "QResult"
ghenv.Component.Params.Output[1].NickName = "QResult"
ghenv.Component.Params.Output[1].Description = "Query results as a DataTree (each branch is a column)."

ghenv.Component.Params.Output[2].Name = "QHeaders"
ghenv.Component.Params.Output[2].NickName = "QHeaders"
ghenv.Component.Params.Output[2].Description = "Column names as a DataTree mirroring the data structure."


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


def validate_inputs(cstring, ctoggle, query):
    """
    Validate all input parameters before execution.
    
    Args:
        cstring (str): Connection string
        ctoggle (bool): Connection toggle
        query (str): SQL query string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not ctoggle:
        return False, "CToggle is False. No connection attempted."
    
    if not cstring or not cstring.strip():
        return False, "Empty connection string."
    
    if not query or not query.strip():
        return False, "Query cannot be empty."
    
    return True, None


def detect_error_result(result_tree):
    """
    Check if query result contains an error message.
    
    Args:
        result_tree (DataTree): Query result tree
    
    Returns:
        tuple: (has_error, error_message)
    """
    if result_tree.BranchCount == 1 and len(result_tree.Branch(0)) == 1:
        first_item = str(result_tree.Branch(0)[0])
        if first_item.startswith("Error:"):
            return True, first_item
    return False, None


################
# INPUT HANDLING & VALIDATION
################
CString = globals().get('CString', "")
CToggle = globals().get('CToggle', False)
Query = globals().get('Query', "")

if not isinstance(CToggle, bool):
    log("Warning: 'CToggle' must be a boolean value. Using False.")
    CToggle = False

if CString is not None and not isinstance(CString, str):
    CString = str(CString)

if Query is not None and not isinstance(Query, str):
    Query = str(Query)


################
# EXECUTION
################
QResult = DataTree[object]()
QHeaders = DataTree[str]()

try:
    is_valid, error_msg = validate_inputs(CString, CToggle, Query)
    
    if not is_valid:
        if not CToggle:
            log(error_msg)
        else:
            report(RML.Error, error_msg)
    else:
        log("Executing query...")
        log("Connection string: {}".format(CString[:50] + "..." if len(CString) > 50 else CString))
        log("Query: {}".format(Query[:100] + "..." if len(Query) > 100 else Query))
        
        QResult = odbc.run_query_to_tree(CToggle, CString, Query)
        QHeaders = odbc.get_query_headers(CToggle, CString, Query)
        
        has_error, error_msg = detect_error_result(QResult)
        
        if has_error:
            report(RML.Error, error_msg)
        else:
            row_count = sum(len(QResult.Branch(i)) for i in range(QResult.BranchCount)) if QResult.BranchCount > 0 else 0
            col_count = QResult.BranchCount
            
            log("Query executed successfully")
            log("Results: {} rows, {} columns".format(row_count, col_count))

except ImportError as e:
    report(
        RML.Error,
        "Module import error - see 'out' for details."
    )
    log("Module import error: {}. Ensure carcara_odbc is in the modules folder.".format(e))
except AttributeError as e:
    report(
        RML.Error,
        "Module function error - see 'out' for details."
    )
    log("Module function error: {}. Check carcara_odbc module version.".format(e))
except Exception as e:
    report(
        RML.Error,
        "Unexpected error - see 'out' for details."
    )
    log("Unexpected error: {} (Type: {})".format(e, type(e).__name__))
