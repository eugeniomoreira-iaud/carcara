# ╔═══════════════════════════════════════════════════════════════╗
# ║  CHANGE THIS LINE TO POINT THE INSTALLER AT A DIFFERENT REPO   ║
# ╚═══════════════════════════════════════════════════════════════╝
GITHUB_REPO = "eugeniomoreira-iaud/carcara"
GITHUB_BRANCH = "master"

"""Carcara installer #2 - download & install the components.

Downloads the repo zip from GitHub, then copies the `carcara/` folder (package
+ built .ghuser files + version.txt) into Grasshopper's UserObjects. Run the
Python-library installer FIRST.

Self-contained: imports nothing from crc_modules (it does not exist yet on a
fresh machine). May import Rhino for confirm dialogs.

Inputs  : run (bool)   - toggle True to install / update
Outputs : report (str) - what happened
"""
import os
import io
import shutil
import tempfile
import zipfile
import datetime
import urllib.request

ZIP_URL = "https://github.com/{}/archive/refs/heads/{}.zip".format(GITHUB_REPO, GITHUB_BRANCH)
# Raw version.txt inside the deployable folder, for a cheap remote version check.
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/{}/{}/carcara/version.txt".format(
    GITHUB_REPO, GITHUB_BRANCH)


def _user_objects():
    """Return the Grasshopper UserObjects folder for this OS."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, "Grasshopper", "UserObjects")
    return os.path.join(
        os.path.expanduser("~"), "Library", "Application Support", "McNeel",
        "Rhinoceros", "8.0", "Plug-ins", "Grasshopper", "UserObjects")


def _read_version(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def _fetch_remote_version():
    try:
        with urllib.request.urlopen(REMOTE_VERSION_URL, timeout=15) as r:
            return r.read().decode("utf-8").strip()
    except Exception:
        return None


def _vtuple(v):
    parts = []
    for p in (v or "0").split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _confirm(message):
    """Ask the user yes/no. Returns True if confirmed (or no UI available)."""
    try:
        import Rhino
        rc = Rhino.UI.Dialogs.ShowMessage(
            message, "Carcara installer",
            Rhino.UI.ShowMessageButton.YesNo,
            Rhino.UI.ShowMessageIcon.Question)
        return rc == Rhino.UI.ShowMessageResult.Yes
    except Exception:
        return True  # headless: proceed


def _download_and_extract(dest_parent):
    """Download the repo zip and return the path to its inner carcara/ folder."""
    with urllib.request.urlopen(ZIP_URL, timeout=120) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(dest_parent)
    # Zip top folder is "<repo>-<branch>"; the deployable is inside it as carcara/.
    for name in os.listdir(dest_parent):
        cand = os.path.join(dest_parent, name, "carcara")
        if os.path.isdir(cand):
            return cand
    raise RuntimeError("carcara/ folder not found inside the downloaded zip")


report = "Set 'run' to True to install Carcara"

if run:
    try:
        user_objects = _user_objects()
        target = os.path.join(user_objects, "carcara")
        installed_version = _read_version(os.path.join(target, "version.txt"))
        remote_version = _fetch_remote_version()

        # Decide the action and confirm.
        if installed_version is None:
            action = "First install of Carcara {}.".format(remote_version or "?")
        else:
            cmp_i, cmp_r = _vtuple(installed_version), _vtuple(remote_version)
            if remote_version is None:
                action = "Reinstall (remote version unknown). Installed: {}.".format(installed_version)
            elif cmp_r > cmp_i:
                action = "Update {} -> {}.".format(installed_version, remote_version)
            elif cmp_r == cmp_i:
                action = "Reinstall {} (same version).".format(installed_version)
            else:
                action = "DOWNGRADE {} -> {}.".format(installed_version, remote_version)

        if not _confirm(action + "\n\nProceed?"):
            report = "Cancelled by user.\n" + action
        else:
            os.makedirs(user_objects, exist_ok=True)
            backup = None
            tmp = tempfile.mkdtemp(prefix="carcara_dl_")
            try:
                src = _download_and_extract(tmp)

                # Timestamped backup of any existing install (rollback safety).
                if os.path.isdir(target):
                    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup = target + ".bak_" + stamp
                    shutil.move(target, backup)

                try:
                    shutil.copytree(src, target)
                except Exception:
                    # Rollback: restore the backup we just moved aside.
                    if os.path.isdir(target):
                        shutil.rmtree(target, ignore_errors=True)
                    if backup and os.path.isdir(backup):
                        shutil.move(backup, target)
                        backup = None
                    raise

                new_version = _read_version(os.path.join(target, "version.txt"))
                ghuser_dir = os.path.join(target, "userobjects")
                n = len([f for f in os.listdir(ghuser_dir)
                         if f.endswith(".ghuser")]) if os.path.isdir(ghuser_dir) else 0
                msg = ["Carcara {} installed.".format(new_version or "?"),
                       "  -> {}".format(target),
                       "  {} component(s).".format(n)]
                if backup:
                    msg.append("  Previous install backed up at:")
                    msg.append("  {}".format(backup))
                msg.append("")
                msg.append("Restart Grasshopper to load the components.")
                report = "\n".join(msg)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        report = "ERROR: {}".format(e)
