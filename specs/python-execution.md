# Python Execution Environment (Windows PowerShell)

This document records the verified shell setup for running Python commands in this repository on Windows.

## The Problem

On this machine, `python` alone resolves to the Windows Store stub ("Python was not found") unless the **conda `carcara` environment is activated**. The real interpreter lives at:

```
C:\ProgramData\anaconda3\envs\carcara\python.exe
```

The primary shell auto-activates conda via profile, so bare `python` works there. Secondary shells (e.g., fresh terminals, CI, some agent contexts) do not.

## The Fix — Command Pattern

Replace every `python ...` call with one of these. **Never chain with `&&`** (PowerShell parse error).

| Pattern | Example |
|---------|---------|
| **Preferred** — robust, no activation needed | `conda run -n carcara python -m pytest tests/ -v` |
| **Full path** | `& "C:\ProgramData\anaconda3\envs\carcara\python.exe" -m pytest tests/ -v` |
| **Activate once per shell**, then bare python | `conda activate carcara` (separate command), then `python -m pytest tests/ -v` |

## Shell Rules

- Never use `&&` — use `;` or separate tool calls.
- Never prefix with `cd` / `Set-Location` — the working directory is already the repo root.

## Verification

In a fresh shell (conda NOT pre-activated), confirm each works:

```powershell
conda run -n carcara python --version
conda run -n carcara python -m pytest tests/ -v          # expect 20+ passed
conda run -n carcara python build_userobjects.py         # expect 6+ built, 0 failed
```

If a targeted test file (e.g., `tests/test_sql_composer.py`) does not exist yet, that is expected — it is created in the relevant phase, not a shell error.

## Reference in Main Spec

See [`CLAUDE.md`](CLAUDE.md) → **Build Pipeline** and **Testing** sections for the authoritative invocation pattern.