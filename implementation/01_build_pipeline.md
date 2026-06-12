# Phase 01 — Build Pipeline (`.py → .ghuser`)

## Goal

Make `python build_userobjects.py` reliably produce binary `GH_Archive`
`.ghuser` files in `carcara/userobjects/`, using the upstream
`compas-actions.ghpython_components` componentizer and Rhino 8's `GH_IO.dll`.

This phase is the most boring and the most important: every later phase
depends on it. We don't ship a useful component yet — Phase 02 does that.

## Inputs you must give me

- **Rhino 8 install path on this machine.** Run in PowerShell:
  ```powershell
  Get-ChildItem "C:\Program Files\Rhino 8\Plug-ins\Grasshopper" -Filter GH_IO.dll -ErrorAction SilentlyContinue
  Get-ChildItem "C:\Program Files\Rhino 8\System"               -Filter GH_IO.dll -ErrorAction SilentlyContinue
  ```
  Paste back whichever path actually contains the DLL. If neither does,
  we fetch it from NuGet (step 2 below).

- **Confirmation of Python environment**: which interpreter `python` resolves
  to (`(Get-Command python).Source`) — must be CPython 3.11+ (not Rhino's
  embedded one). The build is run from the conda `carcara` env or any
  CPython 3.11+ that can pip-install `pythonnet`.

## Steps

1. **Install dev deps**:
   ```powershell
   pip install pythonnet>=3.0 requests
   ```

2. **Vendor `GH_IO.dll`**:
   - If found in a local Rhino install, copy to `vendor/ghio/GH_IO.dll`.
   - Otherwise fetch from NuGet:
     ```powershell
     Invoke-WebRequest `
       "https://www.nuget.org/api/v2/package/Grasshopper/8.0.23304.15001" `
       -OutFile vendor\ghio\grasshopper.nupkg
     # unzip and extract lib/net48/GH_IO.dll
     ```
   - Either way, the final path is `vendor/ghio/GH_IO.dll`.

3. **Vendor the componentizer**:
   ```
   vendor/componentizer/componentize_cpy.py
   ```
   Source: `compas-dev/compas-actions.ghpython_components`. Pull the file
   verbatim — do not patch it. Note the upstream commit SHA in a
   `vendor/componentizer/VERSION.txt` so we can reproduce builds.

4. **Refactor `build_userobjects.py`** to be a thin wrapper. It must:
   1. Probe for `pythonnet` and exit with an install hint if missing.
   2. Resolve `vendor/ghio/GH_IO.dll` (absolute path).
   3. Resolve `vendor/componentizer/componentize_cpy.py`.
   4. Read `version` from `pyproject.toml`.
   5. Invoke the componentizer with:
      - `source = grasshopper/components`
      - `target = carcara/userobjects`
      - `--ghio <abs path>`
      - `--version <version>`
   6. Loop over `grasshopper/components/CRC_*/`, calling the componentizer
      per-folder, catching errors per-component so one failure does not
      abort the whole build. Print a summary table at the end.

5. **Add a no-op smoke component** so the build has something to chew on:
   create `grasshopper/components/CRC_Ping/` with:
   - `metadata.json` — name `Ping`, nickname `PING`, category `Carcara`,
     subcategory `Debug`, inputs `[run:bool]`, outputs `[report]`.
   - `code.py`:
     ```python
     report = "carcara alive" if run else "set run=True"
     ```
   - `icon.png` — any placeholder.

   This component is just to validate the pipeline. It is deleted (or moved
   to `Debug`-only) at the end of Phase 02 once we have the real smoke test.

6. **Run the build**:
   ```powershell
   python build_userobjects.py
   ```
   Expected output:
   ```
   [OK] CRC_Ping            → carcara/userobjects/CRC_Ping.ghuser
   [OK] CRC_ConnectionString → carcara/userobjects/CRC_ConnectionString.ghuser
   ```
   `CRC_ConnectionString` may still emit a warning (its `code.py` isn't
   finalized yet); that's fine — we only need the binary to exist.

7. **Inspect the artifact** to confirm it's a `GH_Archive` and not garbage:
   ```powershell
   # Windows PowerShell 5.1: Format-Hex has no -Count; read raw bytes instead.
   Get-Content carcara\userobjects\CRC_Ping.ghuser -Encoding Byte -TotalCount 16
   ```
   First bytes should look like a `GH_Archive` header (not a zip
   `PK\x03\x04` = `80 75 3 4`). If it's a zip, the componentizer is misconfigured.

## Tests

```powershell
pytest tests/ -v          # still green from Phase 00
python build_userobjects.py
Test-Path carcara\userobjects\CRC_Ping.ghuser
```

No new pytest tests in this phase — the build script itself is the test.

## Grasshopper checkpoint

We **don't** install `.ghuser` files in Rhino yet — Phase 02 does the first
full canvas test. If you're impatient and want to peek:

1. Run `deploy.ps1` (copies the whole `carcara/` folder, so `CRC_Ping` plus the
   `crc_modules` package land together). `CRC_Ping` has no imports so a bare
   `.ghuser` copy also works, but use `deploy.ps1` to stay consistent.
2. Restart Grasshopper. Look under tab **Carcara → Debug** for **PING**.
3. Drop it, attach a `Boolean Toggle` set to `True`, attach a `Panel` to
   `report`. The panel should read `carcara alive`.

If that works, the pipeline is healthy. If it doesn't, do **not** start
Phase 02 — debug the build first.

## Commit

```
build: wire up componentizer + GH_IO.dll, add CRC_Ping smoke target
```

## Done when

- [ ] `vendor/ghio/GH_IO.dll` and `vendor/componentizer/componentize_cpy.py`
      present (gitignored if licensing requires, otherwise committed).
- [ ] `python build_userobjects.py` produces `carcara/userobjects/CRC_Ping.ghuser`
      with no errors.
- [ ] (Optional but recommended) `CRC_Ping` loads in Grasshopper and lights
      up the `report` output.
