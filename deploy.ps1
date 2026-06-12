# Deploy Carcara to the Grasshopper UserObjects folder (Windows dev convenience).
#
# Mirrors the whole deployable folder:
#   <repo>\carcara\  ->  %APPDATA%\Grasshopper\UserObjects\carcara\
# That folder holds the crc_modules package, the built userobjects\*.ghuser, and
# version.txt - exactly what the GitHub installer copies for end users.
#
# Run from the repo root after `python build_userobjects.py` (or make_release.py):
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$userObjects = Join-Path $env:APPDATA "Grasshopper\UserObjects"
$src = Join-Path $root "carcara"
$dst = Join-Path $userObjects "carcara"

New-Item -ItemType Directory -Force -Path $userObjects | Out-Null

# Remove the stale pre-restructure container if present.
$stale = Join-Path $userObjects "carcara-modules"
if (Test-Path $stale) {
    Remove-Item -Recurse -Force $stale
    Write-Host "Removed stale carcara-modules\"
}

# Mirror carcara\ -> UserObjects\carcara\ (excludes __pycache__).
robocopy $src $dst /MIR /XD __pycache__ /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed copying carcara\ (exit $LASTEXITCODE)" }

Write-Host "Deployed to $dst"
Write-Host "  package : $dst\crc_modules"
Write-Host "  ghuser  : $dst\userobjects\*.ghuser"
Write-Host "Restart Grasshopper to load the components."
