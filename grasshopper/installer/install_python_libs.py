"""Carcara installer #1 - Python library bootstrap.

Installs the third-party packages the Carcara components need into Rhino 8's
CPython environment. Run this ONCE per machine (toggle `run` to True in the
delivered .gh), then run install_carcara.py.

Self-contained on purpose: it must work BEFORE the crc_modules package exists,
so it imports nothing from Carcara. It may touch Rhino/subprocess because it is
an installer, not library code.

Inputs  : run (bool)   - toggle True to install
Outputs : report (str) - per-library status summary
"""
import os
import sys
import glob
import subprocess

# Packages required by the Carcara components. ODBC (pyodbc) is gone - the new
# stack is psycopg2. numpy arrives transitively via matplotlib/shapely.
LIBRARIES = ["psycopg2", "shapely", "svgwrite", "matplotlib"]

# Import names differ from pip names for the check below.
IMPORT_NAMES = {
    "psycopg2": "psycopg2",
    "shapely": "shapely",
    "svgwrite": "svgwrite",
    "matplotlib": "matplotlib",
}

CREATE_NO_WINDOW = 0x08000000  # hide the console window on Windows


def _find_python():
    """Return the path to Rhino 8's CPython interpreter.

    Prefer sys.executable (inside a Rhino 8 Python 3 component this already IS
    Rhino's CPython). Fall back to scanning the .rhinocode runtime folder.
    """
    exe = sys.executable or ""
    if exe.lower().endswith(".exe") and "python" in os.path.basename(exe).lower():
        return exe
    home = os.path.expanduser("~")
    patterns = [
        os.path.join(home, ".rhinocode", "py*-rh8", "python.exe"),
        os.path.join(home, ".rhinocode", "py*-rh8", "python3*"),
    ]
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return exe  # last resort


def _is_installed(import_name, python_exe):
    try:
        out = subprocess.run(
            [python_exe, "-c", "import {}".format(import_name)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return out.returncode == 0
    except Exception:
        return False


def _pip_install(pip_name, python_exe):
    try:
        out = subprocess.run(
            [python_exe, "-m", "pip", "install", "--user", pip_name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if out.returncode == 0:
            return True, "installed"
        return False, (out.stderr or b"").decode("utf-8", "replace").strip()[-200:]
    except Exception as e:
        return False, str(e)


report = "Set 'run' to True to install Python libraries"

if run:
    python_exe = _find_python()
    lines = ["Python: {}".format(python_exe), ""]
    for pip_name in LIBRARIES:
        import_name = IMPORT_NAMES.get(pip_name, pip_name)
        if _is_installed(import_name, python_exe):
            lines.append("[OK]   {} already present".format(pip_name))
            continue
        ok, detail = _pip_install(pip_name, python_exe)
        tag = "[OK]  " if ok else "[FAIL]"
        lines.append("{} {} - {}".format(tag, pip_name, detail))
    lines.append("")
    lines.append("Restart Rhino, then run install_carcara.")
    report = "\n".join(lines)
