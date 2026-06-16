"""Smoke test: CRC_RunQuery and CRC_RunCommand code.py files reference only the public API.

Asserts:
  (a) each code.py references run_query / run_command (the public API functions).
  (b) neither contains a direct `import psycopg2` statement or raw `.connect(` logic.
      The `# r: psycopg2` directive comment is allowed — only bare import statements
      and explicit psycopg2 connect calls are forbidden (they belong in crc_modules).
"""
import re
from pathlib import Path

COMPONENTS_DIR = Path(__file__).parent.parent / "build" / "components"

RQ_CODE = (COMPONENTS_DIR / "CRC_RunQuery" / "code.py").read_text(encoding="utf-8")
RC_CODE = (COMPONENTS_DIR / "CRC_RunCommand" / "code.py").read_text(encoding="utf-8")


class TestRunQueryCodePy:
    def test_references_run_query(self):
        assert "run_query" in RQ_CODE, "CRC_RunQuery/code.py must call run_query"

    def test_no_direct_psycopg2_import(self):
        # Allow `# r: psycopg2` directive but forbid actual import statements
        bare_imports = [
            line.strip()
            for line in RQ_CODE.splitlines()
            if re.match(r"^\s*import\s+psycopg2", line)
        ]
        assert bare_imports == [], (
            "CRC_RunQuery/code.py must not contain `import psycopg2` — "
            "delegate to crc_modules. Found: {}".format(bare_imports)
        )

    def test_no_direct_connect_call(self):
        assert ".connect(" not in RQ_CODE, (
            "CRC_RunQuery/code.py must not open DB connections directly. "
            "Use run_query from crc_modules."
        )


class TestRunCommandCodePy:
    def test_references_run_command(self):
        assert "run_command" in RC_CODE, "CRC_RunCommand/code.py must call run_command"

    def test_no_direct_psycopg2_import(self):
        bare_imports = [
            line.strip()
            for line in RC_CODE.splitlines()
            if re.match(r"^\s*import\s+psycopg2", line)
        ]
        assert bare_imports == [], (
            "CRC_RunCommand/code.py must not contain `import psycopg2` — "
            "delegate to crc_modules. Found: {}".format(bare_imports)
        )

    def test_no_direct_connect_call(self):
        assert ".connect(" not in RC_CODE, (
            "CRC_RunCommand/code.py must not open DB connections directly. "
            "Use run_command from crc_modules."
        )
