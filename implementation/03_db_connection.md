# Phase 03 — DB Connection (`db/connection.py` + `CRC_ConnectionString`)

> **⚠️ REWORK REQUIRED.** An earlier build of this phase shipped a **sticky/DSN**
> credential model (Eto dialog + `scriptcontext.sticky` + non-secret DSN wire). The
> project has since **reverted to the legacy `CString` connection-string model** (see
> `CLAUDE.md` → "Connection model" and "Credential handling"). The shipped
> `CRC_ConnectionString` and any `crc_modules/rhino/credentials.py` must be reworked to
> match the steps below; delete the sticky/DSN code. Treat `CRC_ConnectionString` as
> **not done** until it emits a `CString`.

## Goal

Establish a real, tested PostgreSQL/PostGIS connection from Grasshopper. This phase
produces the **`CString`** that every downstream DB component consumes: a single
connection string (libpq conninfo) carrying the encoded password, built from the five
connection parameters.

## Inputs you must give me

1. **A reachable PostGIS DB** — host, port, database, user, password.
   A local Docker `postgis/postgis:15-3.4` container is fine. Read-only this phase
   (`SELECT version();`).
2. **Legacy reference**: open `carcara-old/carcara/carcara_ConnectionString_r03.ghuser`:
   - Exact input parameter names (`host` or `server`? `database` or `db`? `user` or
     `username`?) and nicknames.
   - Output: the exact `CString` format it emits, and **how the password is encoded**
     (base64? obfuscation scheme?). We replicate it for continuity.
   - Does it test the connection, or just build the string?

## Steps

1. **Implement `carcara/crc_modules/db/connection.py`** to the `CLAUDE.md` contract:
   ```python
   def build_connection_string(host, port, database, user, password) -> str
       # single CString (libpq conninfo) with the password encoded
   def parse_connection_string(cstring) -> dict
       # psycopg2 connect kwargs (decodes the password)
   def test_connection(cstring) -> tuple[bool, str]
       # (True, "Connection successful") or (False, str(exc))
   ```
   - `build_connection_string` encodes the password (match the legacy scheme) and
     concatenates the conninfo. `parse_connection_string` is its exact inverse.
   - `test_connection` opens a connection via `parse_connection_string`, closes,
     returns the tuple. **No side effects on import.**
   - All pure (no Rhino) → pytest-testable. There is **no** `crc_modules/rhino/`
     credential module in this model.

2. **Update `tests/test_connection.py`** with `psycopg2.connect` mocked (no live DB):
   - `build_connection_string` → `parse_connection_string` round-trips (incl. password
     decode).
   - `test_connection` success + failure paths (pattern in `CLAUDE.md`).

3. **Finalize the `CRC_ConnectionString` bundle** (subcategory **02.Queries**):
   - `metadata.json` — inputs `host` (str), `port` (int), `database` (str), `user`
     (str), `password` (str), `CToggle` (bool). Outputs `CString`, `ok`, `report`.
   - `code.py` (sys.path bootstrap puts `…/UserObjects/carcara` on path):
     ```python
     from crc_modules.db.connection import build_connection_string, test_connection

     CString, ok, report = "", False, "Set 'CToggle' to True to connect"
     if CToggle:
         try:
             port = int(port) if port else 5432
             CString = build_connection_string(host, port, database, user, password)
             ok, msg = test_connection(CString)
             report = msg if ok else "ERROR: {}".format(msg)
         except Exception as e:
             report = "ERROR: {}".format(e)
     ```
   > Security: the encoded password lives in `CString`, which can appear on the canvas
   > and serialize into a saved `.gh`. Encoding is obfuscation, not encryption. Never
   > commit a `.gh` with a live `CString` (`.gitignore` excludes `*.gh`). To keep the
   > password off a visible panel, wire it from a panel set to "hidden" / a value-list,
   > or collect it however the legacy component did — but it still ends up inside
   > `CString` by design.

4. **Build and install** (deploy the whole folder so `crc_modules` is importable):
   ```powershell
   python build_userobjects.py
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```

## Tests

```powershell
pytest tests/test_connection.py -v
```

Must cover: round-trip string build/parse, success path, refused connection, invalid
credentials, DNS failure. All mocked.

## Grasshopper checkpoint

1. Restart Grasshopper.
2. Drop **Carcara → 02.Queries → CRC_ConnectionString** on a canvas.
3. Wire panels for `host`, `port`, `database`, `user`, `password`; boolean `CToggle`.
4. Flip `CToggle = True`. Verify:
   - `ok = True`, `report = "Connection successful"`.
   - `CString` panel shows the conninfo with the **encoded** (not plaintext) password.
5. Re-run with a garbage password. Verify `ok = False`, `report` starts with `ERROR:`
   and quotes the psycopg2 message; no red-bubble crash (yellow at worst).
6. Save the canvas as `tests/_manual/smoke_connection.gh` (gitignored — it contains a
   live `CString`).

## Commit

```
fix(db): rework connection.py + CRC_ConnectionString to the CString model
```

## Done when

- [ ] `carcara/crc_modules/db/connection.py` matches the spec contract
      (`build_connection_string` / `parse_connection_string` / `test_connection(cstring)`).
- [ ] Old sticky/DSN code and `crc_modules/rhino/credentials.py` removed.
- [ ] `tests/test_connection.py` passes with full mock coverage.
- [ ] `CRC_ConnectionString` builds, installs, emits a `CString`, connects to a real DB,
      and surfaces errors cleanly.
- [ ] Status of `CRC_ConnectionString` flipped to ✅ Done in `CLAUDE.md`.
