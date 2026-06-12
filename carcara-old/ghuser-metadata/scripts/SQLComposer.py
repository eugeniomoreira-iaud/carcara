"""SQL Composer - Parametric SQL Statement Generator

This component generates SQL statements by replacing variable placeholders
with corresponding values. Useful for creating dynamic queries with multiple
parameters in Grasshopper workflows.

Typical usage:
    SQL Template -> Variables List -> Values List -> Complete SQL Statement

Logic:
    1. Validate SQL template and variable/value lists
    2. Check that variables and values lists have matching lengths
    3. Replace each placeholder in template with corresponding value
    4. Return final SQL statement
    5. Report number of replacements made

Args (Component Inputs):
    sql: (String) SQL template with placeholders
        - Type: str
        - Access: item
        - Optional: No
        - Format: Use #placeholder# syntax (e.g., 'SELECT * FROM #table#')
    
    var: (List[String]) List of placeholder strings to replace
        - Type: list[str]
        - Access: list
        - Optional: Yes (if no replacements needed)
        - Note: Must match length of val
    
    val: (List[String]) List of replacement values
        - Type: list[str/object]
        - Access: list
        - Optional: Yes (if no replacements needed)
        - Note: Must match length of var

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    stmt: (String) Final SQL statement with all replacements applied
        - Type: str

Version: 1.2
Date: 2025/11/13
"""

################
# IMPORTS
################
import sys
import os
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "1.2"
COMPONENT_DATE = "2025/11/13"

ghenv.Component.Name = "SQL Composer"
ghenv.Component.NickName = "SQLComp.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '03.Utilities'
ghenv.Component.Description = "Generates SQL statements by replacing variable placeholders with corresponding values."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "sql"
ghenv.Component.Params.Input[0].NickName = "sql"
ghenv.Component.Params.Input[0].Description = "SQL template with placeholders (e.g., 'SELECT * FROM #table# WHERE col = #value#')."

ghenv.Component.Params.Input[1].Name = "var"
ghenv.Component.Params.Input[1].NickName = "var"
ghenv.Component.Params.Input[1].Description = "List of placeholder strings to be replaced."

ghenv.Component.Params.Input[2].Name = "val"
ghenv.Component.Params.Input[2].NickName = "val"
ghenv.Component.Params.Input[2].Description = "List of replacement values corresponding to the placeholders."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "stmt"
ghenv.Component.Params.Output[1].NickName = "stmt"
ghenv.Component.Params.Output[1].Description = "Final SQL statement after all replacements."


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


def validate_inputs(sql_template, variables, values):
    """
    Validate all input parameters before processing.
    
    Args:
        sql_template (str): SQL template string
        variables (list): List of placeholder strings
        values (list): List of replacement values
    
    Returns:
        tuple: (is_valid, error_message, skip_replacements)
    """
    if not sql_template or not sql_template.strip():
        return False, "No SQL template provided.", False
    
    if not variables and not values:
        return True, None, True
    
    if not variables or not values:
        return False, "Both Variables and Values must be provided together.", False
    
    if len(variables) != len(values):
        return False, "Variables and Values lists must have the same number of elements. Got {} variables and {} values.".format(
            len(variables), len(values)
        ), False
    
    return True, None, False


def replace_placeholders(template, variables, values):
    """
    Replace all placeholders in SQL template with corresponding values.
    
    Args:
        template (str): SQL template string
        variables (list): List of placeholder strings
        values (list): List of replacement values
    
    Returns:
        tuple: (final_statement, replacements_count)
    """
    statement = template
    replacements_made = 0
    
    for placeholder, replacement in zip(variables, values):
        placeholder_str = str(placeholder)
        replacement_str = str(replacement)
        
        if placeholder_str in statement:
            statement = statement.replace(placeholder_str, replacement_str)
            replacements_made += 1
            log("Replaced '{}' with '{}'".format(placeholder_str, replacement_str))
    
    return statement, replacements_made


################
# INPUT HANDLING & VALIDATION
################
sql = globals().get('sql', "")
var = globals().get('var', [])
val = globals().get('val', [])

if sql is not None and not isinstance(sql, str):
    sql = str(sql)

if not isinstance(var, (list, tuple)):
    if var:
        var = [var]
    else:
        var = []

if not isinstance(val, (list, tuple)):
    if val:
        val = [val]
    else:
        val = []


################
# EXECUTION
################
stmt = ""

try:
    is_valid, error_msg, skip_replacements = validate_inputs(sql, var, val)
    
    if not is_valid:
        if not sql:
            log(error_msg)
        else:
            report(RML.Error, error_msg)
    elif skip_replacements:
        stmt = sql
        log("No variables provided - returning original SQL template")
        log("Template: {}".format(sql[:200] + "..." if len(sql) > 200 else sql))
    else:
        log("Processing {} placeholder(s)...".format(len(var)))
        log("Original template: {}".format(sql[:200] + "..." if len(sql) > 200 else sql))
        
        stmt, replacements_made = replace_placeholders(sql, var, val)
        
        log("Successfully replaced {} placeholder{}.".format(
            replacements_made,
            "s" if replacements_made != 1 else ""
        ))
        
        if replacements_made < len(var):
            unmatched_count = len(var) - replacements_made
            log("Warning: {} placeholder{} not found in template.".format(
                unmatched_count,
                "s were" if unmatched_count != 1 else " was"
            ))
            report(
                RML.Warning,
                "{} placeholder{} not found (see 'out' for details).".format(
                    unmatched_count,
                    "s were" if unmatched_count != 1 else " was"
                )
            )
        
        log("Final statement: {}".format(stmt[:200] + "..." if len(stmt) > 200 else stmt))

except TypeError as e:
    report(
        RML.Error,
        "Type error during replacement - see 'out' for details."
    )
    log("Type error during replacement: {}. Check input data types.".format(e))
    stmt = ""
except Exception as e:
    report(
        RML.Error,
        "Unexpected error - see 'out' for details."
    )
    log("Unexpected error: {} (Type: {}).".format(e, type(e).__name__))
    stmt = ""
