#!/usr/bin/env python3
"""Build Carcara .ghuser components from grasshopper/components/* bundles."""

import argparse
import os
import shutil
import sys
import tomllib

ROOT = os.path.dirname(os.path.abspath(__file__))
COMPONENTS_DIR = os.path.join(ROOT, "grasshopper", "components")
# Built .ghuser files land inside the deployable folder so `carcara/` is the
# single thing users download (committed to git; installer copies it as-is).
DIST_DIR = os.path.join(ROOT, "carcara", "userobjects")
VENDOR_COMPONENTIZER = os.path.join(ROOT, "vendor", "componentizer")
VENDOR_GHIO = os.path.join(ROOT, "vendor", "ghio")

RHINO_SEARCH_PATHS = [
    r"C:\Program Files\Rhino 8\Plug-ins\Grasshopper",
    r"C:\Program Files\Rhino 8 WIP\Plug-ins\Grasshopper",
    os.path.expandvars(r"%APPDATA%\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper"),
]


def find_ghio_dll(explicit=None):
    candidates = ([explicit] if explicit else []) + [VENDOR_GHIO] + RHINO_SEARCH_PATHS
    for path in candidates:
        if not path:
            continue
        if os.path.isfile(path) and path.lower().endswith(".dll"):
            return path
        dll = os.path.join(path, "GH_IO.dll")
        if os.path.isfile(dll):
            return dll
    return None


def read_version():
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
        return tomllib.load(f)["project"]["version"]


def main():
    parser = argparse.ArgumentParser(description="Build Carcara .ghuser files")
    parser.add_argument("--ghio", help="Path to folder or file containing GH_IO.dll")
    parser.add_argument("--version", help="Version string (default: from pyproject.toml)")
    parser.add_argument("--clean", action="store_true", help="Remove carcara/userobjects before build")
    args = parser.parse_args()

    try:
        import clr  # noqa: F401
    except ImportError:
        print("ERROR: pythonnet not installed. Run: pip install 'pythonnet>=3.0'")
        sys.exit(1)

    ghio_path = find_ghio_dll(args.ghio)
    if not ghio_path:
        print("ERROR: GH_IO.dll not found.")
        print("  Copy from Rhino 8 to vendor/ghio/GH_IO.dll, or pass --ghio <path>")
        sys.exit(1)

    import clr as _clr
    _clr.AddReference(os.path.splitext(ghio_path)[0])

    if VENDOR_COMPONENTIZER not in sys.path:
        sys.path.insert(0, VENDOR_COMPONENTIZER)
    try:
        from componentize_cpy import create_ghuser_component
    except ImportError as exc:
        print(f"ERROR: Cannot import componentizer: {exc}")
        print(f"  Expected at: {VENDOR_COMPONENTIZER}/componentize_cpy.py")
        sys.exit(1)

    version = args.version or read_version()

    if args.clean and os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)

    bundles = sorted(
        d for d in os.listdir(COMPONENTS_DIR)
        if os.path.isdir(os.path.join(COMPONENTS_DIR, d))
        and d not in ("__pycache__", ".git")
    )

    if not bundles:
        print(f"No component bundles found in {COMPONENTS_DIR}")
        sys.exit(0)

    print(f"Building {len(bundles)} component(s) — version {version}")
    print(f"  GH_IO : {ghio_path}")
    print()

    results = []
    for name in bundles:
        source = os.path.join(COMPONENTS_DIR, name)
        target = os.path.join(DIST_DIR, name + ".ghuser")
        try:
            create_ghuser_component(source, target, version)
            results.append(("OK", name, target))
        except Exception as exc:
            results.append(("FAIL", name, str(exc)))

    ok = [r for r in results if r[0] == "OK"]
    fail = [r for r in results if r[0] == "FAIL"]

    for status, name, detail in results:
        tag = "[OK]  " if status == "OK" else "[FAIL]"
        info = os.path.basename(detail) if status == "OK" else detail
        print(f"  {tag} {name:<42} {info}")

    print()
    print(f"Done: {len(ok)} built, {len(fail)} failed.")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
