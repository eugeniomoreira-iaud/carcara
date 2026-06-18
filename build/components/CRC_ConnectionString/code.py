"""CRC_ConnectionString: Eto dialog for credentials, builds CString (libpq format)."""
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

import Rhino
import Rhino.UI
import scriptcontext
import Eto.Drawing as drawing
import Eto.Forms as forms

from crc_modules.db.connection import build_connection_string, test_connection

# ===== POSITIONAL INPUT HELPERS (index-based; independent of name/nickname display) =====
from Grasshopper import DataTree

def _unwrap(g):
    return g.Value if hasattr(g, "Value") else g

def _in_item(i):
    for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True):
        return _unwrap(g)
    return None

def _in_list(i):
    return [_unwrap(g) for g in ghenv.Component.Params.Input[i].VolatileData.AllData(True)]

def _in_tree(i):
    src = ghenv.Component.Params.Input[i].VolatileData
    t = DataTree[object]()
    for p in src.Paths:
        for g in src[p]:
            t.Add(_unwrap(g), p)
    return t
# ========================================================================================

# INPUT MAPPING  0:db:item  1:port:item  2:tog:item
db_int   = _in_item(0)
port_int = _in_item(1)
tog_int  = _in_item(2)

CString, ok, report = "", False, "Set 'CToggle' to True to connect"

if tog_int:
    try:
        port_int = int(port_int) if port_int else 5432
        if not db_int:
            report = "ERROR: 'database' is required"
        else:
            # Show Eto dialog to collect host, user, password
            dialog = _CredentialsDialog(db_int)
            try:
                accepted = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
                if not accepted:
                    report = "Cancelled - no credentials entered"
                else:
                    host, user, password = dialog.values()
                    if not host or not user or not password:
                        report = "ERROR: All fields (host, user, password) are required"
                    else:
                        CString = build_connection_string(host, port_int, db_int, user, password)
                        ok, msg = test_connection(CString)
                        report = msg if ok else "ERROR: {}".format(msg)
            finally:
                try:
                    dialog.Dispose()
                except Exception:
                    pass
    except Exception as e:
        report = "ERROR: {}".format(e)


class _CredentialsDialog(forms.Dialog[bool]):
    """Modal Eto dialog collecting host / user / password."""

    def __init__(self, database):
        super().__init__()
        self.Title = "Carcara - credentials for '{}'".format(database)
        self.Padding = drawing.Padding(10)
        self.Resizable = False
        try:
            self.Topmost = True
        except Exception:
            pass

        lbl_host = forms.Label()
        lbl_host.Text = "Host / IP:"
        self.host_box = forms.TextBox()
        try:
            self.host_box.PlaceholderText = "e.g. 192.168.1.100 or localhost"
        except Exception:
            pass

        lbl_user = forms.Label()
        lbl_user.Text = "User:"
        self.user_box = forms.TextBox()
        try:
            self.user_box.PlaceholderText = "Database username"
        except Exception:
            pass

        lbl_pw = forms.Label()
        lbl_pw.Text = "Password:"
        self.pw_box = forms.PasswordBox()

        self.DefaultButton = forms.Button()
        self.DefaultButton.Text = "OK"
        self.DefaultButton.Click += self._on_ok
        self.AbortButton = forms.Button()
        self.AbortButton.Text = "Cancel"
        self.AbortButton.Click += self._on_cancel

        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(5, 5)
        layout.AddRow(lbl_host, self.host_box)
        layout.AddRow(lbl_user, self.user_box)
        layout.AddRow(lbl_pw, self.pw_box)
        layout.AddRow(None)
        layout.AddRow(self.DefaultButton, self.AbortButton)
        self.Content = layout

    def values(self):
        return (
            (self.host_box.Text or "").strip(),
            (self.user_box.Text or "").strip(),
            self.pw_box.Text or "",
        )

    def _on_cancel(self, sender, e):
        self.host_box.Text = ""
        self.user_box.Text = ""
        self.pw_box.Text = ""
        self.Close(False)

    def _on_ok(self, sender, e):
        host, user, password = self.values()
        if not host or not user or not password:
            self._warn("All fields are required.")
            return
        self.Close(True)

    def _warn(self, message):
        try:
            forms.MessageBox.Show(self, message, "Validation", forms.MessageBoxType.Warning)
        except Exception:
            pass
