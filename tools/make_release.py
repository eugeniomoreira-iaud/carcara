#!/usr/bin/env python3
"""Cut a Carcara release: build all .ghuser files and stamp the version.

One command to run before tagging/pushing a release:

    python tools/make_release.py

It does two things:
  1. Runs build_userobjects.py  -> release/userobjects/*.ghuser
  2. Writes release/version.txt  <- [project].version from pyproject.toml

The installer (build/installer/install_carcara.py) compares the remote
release/version.txt against the installed one to decide install/update/skip.
"""

import os
import subprocess
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(ROOT, "release", "version.txt")


def read_version():
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
        return tomllib.load(f)["project"]["version"]


def main():
    version = read_version()
    print(f"Releasing Carcara {version}")

    # 1. Build components into release/userobjects/.
    print("\n[1/2] Building components...")
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, "build_userobjects.py"),
         "--clean", "--version", version],
        cwd=ROOT,
    )
    if result.returncode != 0:
        print("Build failed. Version file not written.")
        sys.exit(result.returncode)

    # 2. Stamp version.txt inside the deployable folder.
    print("\n[2/2] Writing version.txt...")
    os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
    with open(VERSION_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(version + "\n")
    print(f"  {VERSION_FILE} -> {version}")

    print(f"\nRelease {version} ready. Commit release/ and push.")


if __name__ == "__main__":
    main()
