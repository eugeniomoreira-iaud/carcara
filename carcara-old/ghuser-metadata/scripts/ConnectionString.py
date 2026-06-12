"""Connection String - PostgreSQL Database Connection Builder

This component creates an ODBC connection string for PostgreSQL databases with
secure password encoding. It displays a dialog to collect credentials and 
encodes the password using base64 before building the connection string.

Typical usage:
    Toggle True -> Enter Database Name -> Credentials Dialog -> Connection String

Logic:
    1. Validate toggle and database name inputs
    2. Display Eto dialog to collect IP, username, password
    3. Validate credentials format
    4. Encode password using base64
    5. Build ODBC connection string
    6. Return formatted connection string

Args (Component Inputs):
    CToggle: (Boolean) Set True to display connection dialog
        - Type: bool
        - Access: item
        - Optional: No (defaults to False)
    
    DB: (String) Database name to connect to
        - Type: str
        - Access: item
        - Optional: No

Returns (Component Outputs):
    out: (str) Processing log
        - Type: str
    
    CString: (String) ODBC connection string with encoded password
        - Type: str
        - Format: Driver={PostgreSQL Unicode(x64)};Server=...;Database=...

Version: 2.3
Date: 2025/11/13
Security Note: Base64 encoding is obfuscation, NOT encryption.
"""

################
# IMPORTS
################
import sys
import os
import importlib
import Rhino
import scriptcontext
import System
import Rhino.UI
import Eto.Drawing as drawing
import Eto.Forms as forms
import base64
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML


################
# COMPONENT METADATA
################
COMPONENT_VERSION = "2.3"
COMPONENT_DATE = "2025/11/13"
DEFAULT_PORT = 5432
POSTGRESQL_DRIVER = "PostgreSQL Unicode(x64)"

ghenv.Component.Name = "Connection String"
ghenv.Component.NickName = "CString.py"
ghenv.Component.Message = "v{} - {}".format(COMPONENT_VERSION, COMPONENT_DATE)
ghenv.Component.Category = 'carcara'
ghenv.Component.SubCategory = '03.Utilities'
ghenv.Component.Description = "Creates a connection string to the database with an encoded password."
ghenv.Component.AdditionalHelpFromDocStrings = '1'


################
# INPUT METADATA
################
ghenv.Component.Params.Input[0].Name = "CToggle"
ghenv.Component.Params.Input[0].NickName = "CToggle"
ghenv.Component.Params.Input[0].Description = "Set 'True' to connect."

ghenv.Component.Params.Input[1].Name = "DB"
ghenv.Component.Params.Input[1].NickName = "DB"
ghenv.Component.Params.Input[1].Description = "Database name."


################
# OUTPUT METADATA (starts at index 1, index 0 is default 'out')
################
ghenv.Component.Params.Output[1].Name = "CString"
ghenv.Component.Params.Output[1].NickName = "CString"
ghenv.Component.Params.Output[1].Description = "Connection string with an encoded password."


################
# DIALOG CLASS
################
class SampleEtoConnectionDialog(forms.Dialog[bool]):
    """
    Eto dialog for collecting PostgreSQL connection credentials.
    
    Displays a modal dialog with fields for IP address, username, and password.
    Validates inputs before accepting.
    """
    
    def __init__(self):
        super(SampleEtoConnectionDialog, self).__init__()
        self.Title = 'Connection Credentials'
        self.Padding = drawing.Padding(10)
        self.Resizable = False
        try:
            self.Topmost = True
        except:
            pass

        self.m_label_ip = forms.Label()
        self.m_label_ip.Text = 'Enter the IP Address:'
        self.m_textbox_ip = forms.TextBox()
        try:
            self.m_textbox_ip.PlaceholderText = "e.g., 192.168.1.100 or localhost"
        except:
            pass

        self.m_label_username = forms.Label()
        self.m_label_username.Text = 'Enter the User Name:'
        self.m_textbox_username = forms.TextBox()
        try:
            self.m_textbox_username.PlaceholderText = "Database username"
        except:
            pass

        self.m_label_password = forms.Label()
        self.m_label_password.Text = 'Enter the Password:'
        self.m_password_box = forms.PasswordBox()

        self.DefaultButton = forms.Button()
        self.DefaultButton.Text = 'OK'
        self.DefaultButton.Click += self.OnOKButtonClick
        self.AbortButton = forms.Button()
        self.AbortButton.Text = 'Cancel'
        self.AbortButton.Click += self.OnCloseButtonClick

        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(5, 5)
        layout.AddRow(self.m_label_ip, self.m_textbox_ip)
        layout.AddRow(self.m_label_username, self.m_textbox_username)
        layout.AddRow(self.m_label_password, self.m_password_box)
        layout.AddRow(None)
        layout.AddRow(self.DefaultButton, self.AbortButton)
        self.Content = layout

    def GetValues(self):
        """
        Retrieve entered values from dialog fields.
        
        Returns:
            tuple: (ip, username, password) as strings
        """
        return (
            (self.m_textbox_ip.Text or "").strip(),
            (self.m_textbox_username.Text or "").strip(),
            self.m_password_box.Text or ""
        )

    def OnCloseButtonClick(self, sender, e):
        """Handle Cancel button click."""
        self.m_textbox_ip.Text = ""
        self.m_textbox_username.Text = ""
        self.m_password_box.Text = ""
        self.Close(False)

    def OnOKButtonClick(self, sender, e):
        """Handle OK button click with validation."""
        ip, username, password = self.GetValues()
        if not ip or not username or not password:
            self._warn("Some information from the dialog box is missing.")
            return
        if not self._is_valid_ip_or_hostname(ip):
            self._warn("Please enter a valid IP address or hostname.")
            return
        self.Close(True)

    def _is_valid_ip_or_hostname(self, text):
        """
        Validate IP address or hostname format.
        
        Args:
            text (str): IP address or hostname to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not text or text.isspace():
            return False
        if text.lower() == "localhost":
            return True
        parts = text.split('.')
        if len(parts) == 4:
            try:
                return all(0 <= int(p) <= 255 for p in parts)
            except:
                pass
        return len(text) > 0 and not text.isspace()

    def _warn(self, message):
        """Display warning message to user."""
        try:
            forms.MessageBox.Show(self, message, "Validation", forms.MessageBoxType.Warning)
        except:
            ghenv.Component.AddRuntimeMessage(RML.Warning, message)


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


def RequestConnectionInfo():
    """
    Display Eto dialog to collect database connection credentials.
    
    Shows a modal dialog with fields for IP address, username, and password.
    Validates inputs and encodes the password before returning.
    
    Returns:
        tuple: (ip, username, encoded_password) or ("", "", "") if cancelled
    """
    dialog = SampleEtoConnectionDialog()
    try:
        log("Opening connection credentials dialog...")
        rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
        if rc:
            ip, username, password = dialog.GetValues()
            encoded_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")
            log("Credentials received: IP={}, Username={}".format(ip, username))
            return ip, username, encoded_password
        else:
            log("Dialog cancelled by user")
            return "", "", ""
    except Exception as e:
        log("Dialog error: {}".format(e))
        report(RML.Error, "Dialog error - see 'out' for details.")
        return "", "", ""
    finally:
        try:
            dialog.Dispose()
        except:
            pass


def _make_connection_string(ip, username, encoded_password, db, port=DEFAULT_PORT):
    """
    Build PostgreSQL ODBC connection string.
    
    Args:
        ip (str): Server IP address or hostname
        username (str): Database username
        encoded_password (str): Base64-encoded password
        db (str): Database name
        port (int, optional): PostgreSQL port. Defaults to 5432.
    
    Returns:
        str: ODBC connection string
    """
    return (
        "Driver={" + POSTGRESQL_DRIVER + "};"
        "Server=" + ip + ";"
        "Port=" + str(port) + ";"
        "Database=" + db + ";"
        "Uid=" + username + ";"
        "Pwd=" + encoded_password + ";"
        "CommandTimeout=0;Timeout=0"
    )


################
# INPUT HANDLING & VALIDATION
################
CToggle = globals().get('CToggle', False)
DB = globals().get('DB', "")

if not isinstance(CToggle, bool):
    log("Warning: 'Connect?' must be a boolean value. Using False.")
    CToggle = False

if DB is not None and not isinstance(DB, str):
    DB = str(DB)


################
# EXECUTION
################
CString = ""

try:
    if not CToggle:
        log("'Connect?' input is False. No connection will be attempted.")
    elif not DB:
        report(RML.Error, "'Database' (DB) input is not connected or empty.")
    else:
        log("Security Notice: Connection string uses base64 encoding (not encryption)")
        log("Database: {}".format(DB))
        
        ip, username, encoded_password = RequestConnectionInfo()
        
        if not ip or not username or not encoded_password:
            log("Connection setup cancelled or incomplete")
        else:
            try:
                CString = _make_connection_string(ip, username, encoded_password, str(DB))
                
                ghenv.Component.Message = "v{} - {} | String Built".format(
                    COMPONENT_VERSION, 
                    COMPONENT_DATE
                )
                
                log("Connection string created successfully")
                log("String length: {} characters".format(len(CString)))
                log("Server: {}".format(ip))
                log("Database: {}".format(DB))
                log("Username: {}".format(username))
                
            except ValueError as e:
                report(RML.Error, "Invalid value error - see 'out' for details.")
                log("Invalid value error: {}".format(e))
                CString = ""
            except Exception as e:
                report(RML.Error, "Error building connection string - see 'out' for details.")
                log("Error building connection string: {}".format(e))
                CString = ""
                
except KeyError as e:
    report(RML.Error, "Missing required input - see 'out' for details.")
    log("Missing required input: {}".format(e))
    CString = ""
except Exception as e:
    report(RML.Error, "Unexpected error - see 'out' for details.")
    log("Unexpected error: {} (Type: {})".format(e, type(e).__name__))
    CString = ""
