"""Carcara Library Installer - Grasshopper Component

This component automates the download and installation of the Carcara library
from GitHub. Includes backup, version checking, and user confirmation for
reinstallation when already up-to-date.

Important: This component modifies Grasshopper UserObjects folder.
A backup is automatically created before any changes.

Args (Component Inputs):
    install (bool): Trigger installation/update
        - Type: bool
        - Access: item
        - Optional: No
        - Note: Uses edge detection (only runs on False->True transition)

Returns (Component Outputs):
    out (str): Installation status and messages
    installed_version (str): Currently installed version
    available_version (str): Latest version from GitHub

Version: 1.2.3
Date: 2026/06/16
Requires: urllib, zipfile, shutil, Rhino, Grasshopper
"""

import os
import shutil
import zipfile
import urllib.request
from datetime import datetime

import Rhino
import Grasshopper
from Grasshopper.Kernel import GH_RuntimeMessageLevel as RML


#################
# CONFIGURATION #
#################

GITHUB_REPO = "eugeniomoreira-iaud/carcara"
GITHUB_BRANCH = "master"

GITHUB_ZIP_URL = "https://github.com/{}/archive/refs/heads/{}.zip".format(GITHUB_REPO, GITHUB_BRANCH)
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/{}/{}/carcara/version.txt".format(GITHUB_REPO, GITHUB_BRANCH)

# CROSS-PLATFORM FIX: Use Grasshopper's native API to find the UserObjects folder instead of Windows APPDATA
USER_OBJECTS_FOLDER = Grasshopper.Folders.DefaultUserObjectFolder
TARGET_FOLDER = os.path.join(USER_OBJECTS_FOLDER, "carcara")
DOWNLOADS_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")
VERSION_FILE = "version.txt"


#####################################
# PERSISTENT STATE (EDGE DETECTION) #
#####################################

try:
    prev_install
except NameError:
    prev_install = False


####################
# HELPER FUNCTIONS #
####################

def report(level, message):
    """Send runtime message to Grasshopper component."""
    ghenv.Component.AddRuntimeMessage(level, message)
    print(message)


def get_installed_version():
    """Get currently installed Carcara version."""
    version_path = os.path.join(TARGET_FOLDER, VERSION_FILE)
    if os.path.exists(version_path):
        try:
            with open(version_path, 'r') as f:
                version = f.read().strip()
                return version
        except Exception as e:
            report(RML.Warning, "Could not read version file: {}".format(e))
    return None


def get_available_version():
    """Get latest Carcara version from GitHub."""
    try:
        response = urllib.request.urlopen(GITHUB_VERSION_URL, timeout=10)
        version = response.read().decode('utf-8').strip()
        return version
    except urllib.error.HTTPError as e:
        if e.code == 404:
            report(RML.Remark, "version.txt not found in repository")
            return "Unknown"
        else:
            report(RML.Warning, "HTTP error fetching version: {}".format(e))
            return None
    except Exception as e:
        report(RML.Warning, "Could not fetch remote version: {}".format(e))
        return None


def compare_versions(current, available):
    """Compare version strings."""
    if current is None:
        return -1
    if available is None or available == "Unknown":
        return None
    
    try:
        if current < available:
            return -1
        elif current > available:
            return 1
        else:
            return 0
    except:
        return None


def ask_user_confirmation(message, title="Confirm Installation"):
    """
    Show confirmation dialog to user using cross-platform Rhino UI.
    """
    response = Rhino.UI.Dialogs.ShowMessage(
        message,
        title,
        Rhino.UI.ShowMessageButton.YesNo,
        Rhino.UI.ShowMessageIcon.Question
    )
    return response == Rhino.UI.ShowMessageResult.Yes


def check_if_should_proceed(installed_version, available_version):
    """
    Determine if installation should proceed based on versions.
    Shows appropriate dialogs for different scenarios.
    """
    comparison = compare_versions(installed_version, available_version)
    
    if installed_version is None:
        return True, "Installing Carcara for the first time"
    
    if comparison is None:
        message = (
            "Cannot verify remote version.\n\n"
            "Current version: {}\n\n"
            "Proceed with installation anyway?"
        ).format(installed_version)
        
        if ask_user_confirmation(message, "Version Check Failed"):
            return True, "User chose to proceed despite version check failure"
        else:
            return False, "User cancelled installation"
    
    if comparison == -1:
        message = (
            "An update is available!\n\n"
            "Installed version: {}\n"
            "Available version: {}\n\n"
            "Update now?"
        ).format(installed_version, available_version)
        
        if ask_user_confirmation(message, "Update Available"):
            return True, "Updating from {} to {}".format(installed_version, available_version)
        else:
            return False, "User cancelled update"
    
    elif comparison == 0:
        message = (
            "Carcara {} is already up to date.\n\n"
            "Do you want to reinstall anyway?\n\n"
            "(This can help repair corrupted installations)"
        ).format(installed_version)
        
        if ask_user_confirmation(message, "Already Up-to-Date"):
            return True, "Reinstalling version {} (user confirmed)".format(installed_version)
        else:
            return False, "Installation skipped - already up to date"
    
    elif comparison == 1:
        message = (
            "Your installed version is NEWER than available!\n\n"
            "Installed version: {}\n"
            "Available version: {}\n\n"
            "Do you want to DOWNGRADE?"
        ).format(installed_version, available_version)
        
        if ask_user_confirmation(message, "Downgrade Warning"):
            return True, "Downgrading from {} to {} (user confirmed)".format(installed_version, available_version)
        else:
            return False, "User cancelled downgrade"
    
    return False, "Unknown version comparison result"


def download_file(url, output_path):
    """Download file with progress indication."""
    try:
        report(RML.Remark, "Downloading from: {}".format(url))
        urllib.request.urlretrieve(url, output_path)
        
        file_size = os.path.getsize(output_path)
        return True, "Downloaded successfully ({:.2f} MB)".format(file_size / (1024 * 1024))
    except Exception as e:
        return False, "Download error: {}".format(e)


def extract_zip(zip_path, extraction_folder):
    """Extract ZIP file."""
    try:
        os.makedirs(extraction_folder, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extraction_folder)
        return True, "Extracted successfully"
    except Exception as e:
        return False, "Extraction error: {}".format(e)


def backup_folder_as_zip(target_folder):
    """Create timestamped ZIP backup of folder."""
    try:
        parent = os.path.dirname(target_folder)
        folder_name = os.path.basename(target_folder.rstrip("\\/"))
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_name = os.path.join(parent, "{}-{}".format(folder_name, timestamp))
        
        archive_path = shutil.make_archive(
            base_name=base_name,
            format='zip',
            root_dir=parent,
            base_dir=folder_name
        )
        return True, archive_path, "Backup created: {}".format(archive_path)
    except Exception as e:
        return False, None, "Backup error: {}".format(e)


def rollback_from_backup(backup_path, target_folder):
    """Restore folder from backup ZIP."""
    try:
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)
        
        parent = os.path.dirname(target_folder)
        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            zip_ref.extractall(parent)
        
        report(RML.Warning, "Rollback successful from: {}".format(backup_path))
        return True
    except Exception as e:
        report(RML.Error, "Rollback failed: {}".format(e))
        return False


def replace_folder(source_folder, target_folder, backup_path=None):
    """Replace target folder with source, with rollback on failure."""
    try:
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)
        
        shutil.move(source_folder, target_folder)
        return True, "Installation successful"
    except Exception as e:
        error_msg = "Installation error: {}".format(e)
        
        if backup_path and os.path.exists(backup_path):
            report(RML.Warning, "Attempting rollback...")
            if rollback_from_backup(backup_path, target_folder):
                error_msg += " (Rollback successful)"
            else:
                error_msg += " (Rollback FAILED - manual intervention needed!)"
        
        return False, error_msg


def cleanup_files(*paths):
    """Remove temporary files and folders."""
    for path in paths:
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
        except Exception as e:
            report(RML.Warning, "Cleanup warning for {}: {}".format(path, e))


def install_carcara():
    """Main installation function."""
    zip_filename = "carcara_{}.zip".format(GITHUB_BRANCH)
    zip_path = os.path.join(DOWNLOADS_FOLDER, zip_filename)
    temp_extract_folder = os.path.join(DOWNLOADS_FOLDER, "temp_carcara_extract")
    backup_path = None
    
    try:
        success, message = download_file(GITHUB_ZIP_URL, zip_path)
        if not success:
            return message
        report(RML.Remark, message)
        
        success, message = extract_zip(zip_path, temp_extract_folder)
        if not success:
            cleanup_files(zip_path)
            return message
        report(RML.Remark, message)
        
        extracted_repo_folder = os.path.join(temp_extract_folder, "{}-{}".format(GITHUB_REPO.split('/')[1], GITHUB_BRANCH))
        source_folder = os.path.join(extracted_repo_folder, "carcara")
        
        if not os.path.exists(source_folder):
            cleanup_files(zip_path, temp_extract_folder)
            return "Error: 'carcara' folder not found in repository. Expected path: {}".format(source_folder)
        
        if os.path.exists(TARGET_FOLDER):
            success, backup_path, message = backup_folder_as_zip(TARGET_FOLDER)
            if not success:
                cleanup_files(zip_path, temp_extract_folder)
                return message
            report(RML.Remark, message)
        
        success, message = replace_folder(source_folder, TARGET_FOLDER, backup_path)
        if not success:
            cleanup_files(zip_path, temp_extract_folder)
            return message
        
        cleanup_files(zip_path, temp_extract_folder)
        
        new_version = get_installed_version()
        if new_version:
            return "Carcara {} installed successfully".format(new_version)
        else:
            return "Carcara installed successfully"
    
    except Exception as e:
        return "Unexpected error: {}".format(e)


####################
# INPUT VALIDATION #
####################

install = globals().get('install', False)

if not isinstance(install, bool):
    install = False


##################
# MAIN EXECUTION #
##################

out = ""
installed_version = get_installed_version()
available_version = get_available_version()

if install and not prev_install:
    should_proceed, reason = check_if_should_proceed(installed_version, available_version)
    
    report(RML.Remark, reason)
    
    if should_proceed:
        out = install_carcara()
        installed_version = get_installed_version()
    else:
        out = reason
else:
    out = "Set 'install' to True to download and install Carcara library.\n\n"
    
    if installed_version:
        out += "Installed version: {}\n".format(installed_version)
    else:
        out += "Status: Not installed\n"
    
    if available_version and available_version != "Unknown":
        out += "Available version: {}\n".format(available_version)
    
    out += "\nSource: {}".format(GITHUB_REPO)
    
    report(RML.Remark, out)

prev_install = install


##########
# OUTPUT #
##########

ghenv.Component.Message = "v1.2.3"