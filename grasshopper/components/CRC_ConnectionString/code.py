"""CRC_ConnectionString: Eto dialog for credentials, builds CString (libpq format)."""
import sys
import os

# Make the crc_modules package importable. GHPython runs from an in-memory
# string, so __file__ is undefined; the installer copies the whole `carcara`
# folder into UserObjects, with the package at .../UserObjects/carcara/crc_modules.
# Put the PARENT (.../UserObjects/carcara) on sys.path so `import crc_modules` works.
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
    ghenv.Component.Message = "v{{component_version}}"
except Exception:
    pass

import Rhino
import Rhino.UI
import scriptcontext
import Eto.Drawing as drawing
import Eto.Forms as forms

from crc_modules.db.connection import build_connection_string, test_connection

CString, ok, report = "", False, "Set 'CToggle' to True to connect"

if CToggle:
    try:
        port = int(port) if port else 5432
        if not database:
            report = "ERROR: 'database' is required"
        else:
            # Show Eto dialog to collect host, user, password
            dialog = _CredentialsDialog(database)
            try:
                accepted = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
                if not accepted:
                    report = "Cancelled - no credentials entered"
                else:
                    host, user, password = dialog.values()
                    if not host or not user or not password:
                        report = "ERROR: All fields (host, user, password) are required"
                    else:
                        CString = build_connection_string(host, port, database, user, password)
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