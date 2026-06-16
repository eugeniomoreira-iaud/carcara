# DB Writer Phase 06 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `crc_modules/db/writer.py` (CREATE TABLE + INSERT geometries with false-origin add-back), two GH components (`CRC_CreateTable`, `CRC_CreateShapefile`), tests, build `.ghuser` files, and deploy.

**Architecture:** Core logic in `writer.py` using `psycopg2.sql` for identifier quoting. Cx/Cy kept as TEXT, embedded verbatim into SQL via `validate_offset`. Two thin GH wrappers call into the module. Tests assert SQL shape via `flatten(Composed)` helper (no live DB needed).

**Tech Stack:** Python 3.11, psycopg2, psycopg2.sql, pytest + MagicMock, componentizer (build_userobjects.py), deploy.ps1.

---

### Task 1: Write `carcara/crc_modules/db/writer.py`

**Files:**
- Create: `carcara/crc_modules/db/writer.py`

- [ ] **Step 1: Create writer.py exactly as specified**

Write the file at `C:\Users\eugenio.moreira\Documents\github\carcara\carcara\crc_modules\db\writer.py` with:
- `_get_connection(cstring)` helper (same pattern as spatial_query.py)
- `create_table(cstring, schema, table, columns, geom_column=None, geom_type=None, srid=4326, replace_table=False)` — uses `psycopg2.sql.Identifier` for all names, `psycopg2.sql.Literal(int(srid))` for SRID, optional DROP IF EXISTS, commits, returns `cur.rowcount`
- `insert_geometries(cstring, schema, table, geom_column, wkt_list, srid, cx="0", cy="0", column_names=None, values=None)` — validates cx/cy via `validate_offset`, embeds verbatim in `ST_Translate(ST_GeomFromText(%s, %s), <cx>, <cy>)`, uses `executemany`, commits, returns count

Key rule: cx/cy are NEVER float()-parsed. They are string-concatenated into the SQL slot text, NOT bound as parameters.

- [ ] **Step 2: Verify file written correctly**

Re-read the file and confirm the `insert_geometries` function builds the geom slot as:
```python
geom_slot = sql.SQL("ST_Translate(ST_GeomFromText(%s, %s), " + cx + ", " + cy + ")")
```
and that `float(cx)` and `float(cy)` do NOT appear anywhere.

---

### Task 2: Write `tests/test_writer.py`

**Files:**
- Create: `tests/test_writer.py`

- [ ] **Step 1: Write the test file**

Write `C:\Users\eugenio.moreira\Documents\github\carcara\tests\test_writer.py` with:

1. `flatten(comp)` helper that traverses `psycopg2.sql.Composed` recursively, collecting `.string` from `SQL`, `'"' + '"."'.join(x.strings) + '"'` from `Identifier`, `str(x.wrapped)` from `Literal`, joining with `" "`.

2. Mock pattern: patch `crc_modules.db.writer.psycopg2.connect` and `crc_modules.db.writer.parse_connection_string`. Make mock conn have a cursor that is a context manager. Capture `cur.execute.call_args_list` and `cur.executemany.call_args`.

3. Test cases:
   - `test_create_table_basic`: no geom column. flatten(execute arg) contains `"CREATE TABLE"`, `'"myschema"'`, `'"mytable"'`, `'"name"'`, `'"TEXT"` or `text`
   - `test_create_table_with_geometry`: geom_column="geom", geom_type="POLYGON", srid=4326. flatten has `geometry(` and `4326`
   - `test_create_table_replace_drops_first`: replace_table=True. execute called twice; first call flatten has `"DROP TABLE IF EXISTS"`, second has `"CREATE TABLE"`
   - `test_insert_geometries_cx_cy_verbatim`: cx="500000", cy="9500000". flatten(executemany first arg) has `"ST_Translate(ST_GeomFromText(%s, %s), 500000, 9500000)"`. Params row is `("POINT (1 2)", 4326)` (no cx/cy in params).
   - `test_insert_geometries_zero_offset`: cx="0", cy="0". flatten has `"ST_Translate(ST_GeomFromText(%s, %s), 0, 0)"`
   - `test_insert_with_attribute_columns`: column_names=["name"], values=[[("Alice",)]]. flatten has `'"name"'`. Params row has 3 elements: (wkt, srid, "Alice")
   - `test_insert_propagates_db_error`: connect raises `psycopg2.OperationalError("fail")`. `insert_geometries(...)` raises the same error.
   - `test_no_float_in_source`: `import inspect, crc_modules.db.writer as w; src = inspect.getsource(w); assert "float(cx)" not in src; assert "float(cy)" not in src`

- [ ] **Step 2: Run tests (expect FAIL — writer.py not yet confirmed importable)**

```
conda run -n carcara pytest tests/test_writer.py -v 2>&1 | head -60
```

Fix import errors only (e.g., missing `__init__` exposure). Do NOT implement writer.py changes here — it should already be written in Task 1.

- [ ] **Step 3: Run tests (expect PASS)**

```
conda run -n carcara pytest tests/test_writer.py -v
```

Expected: all 8 tests PASS.

---

### Task 3: Create `grasshopper/components/CRC_CreateTable/`

**Files:**
- Create: `grasshopper/components/CRC_CreateTable/metadata.json`
- Create: `grasshopper/components/CRC_CreateTable/code.py`
- Create: `grasshopper/components/CRC_CreateTable/icon.png` (copy from CRC_QueryValues)

- [ ] **Step 1: Write metadata.json**

Write `C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_CreateTable\metadata.json` exactly as specified in the spec (10 inputs: CString, CToggle, schema, table, column_names(list), column_types(list), geom_column, geom_type, srid(int), replace_table(bool); 2 outputs: affected, report).

- [ ] **Step 2: Write code.py**

Write `C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_CreateTable\code.py` with:
- sys.path bootstrap block (copy verbatim from CRC_QueryValues/code.py lines 5-14)
- ghenv.Component.Message block (try/except)
- `from crc_modules.db.writer import create_table`
- Default values: `affected, report = 0, "Set CToggle=True to CREATE the table. This operation is destructive if replace_table=True."`
- Guard: `if CToggle:`
- Validation: CString required, schema+table required, len(names)==len(types)
- Call: `create_table(CString, schema, table, cols, geom_column=gc, geom_type=gt, srid=sr, replace_table=bool(replace_table))`
- `affected = 0 if rc is None or rc < 0 else rc`
- `report = "success: true\nRows Affected: {}".format(affected)`
- except: `report = "ERROR: {}".format(e)`

- [ ] **Step 3: Copy icon.png**

```
cp "C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_QueryValues\icon.png" "C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_CreateTable\icon.png"
```

---

### Task 4: Create `grasshopper/components/CRC_CreateShapefile/`

**Files:**
- Create: `grasshopper/components/CRC_CreateShapefile/metadata.json`
- Create: `grasshopper/components/CRC_CreateShapefile/code.py`
- Create: `grasshopper/components/CRC_CreateShapefile/icon.png` (copy from CRC_QueryValues)

- [ ] **Step 1: Write metadata.json**

Write `C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_CreateShapefile\metadata.json` exactly as specified (12 inputs: CString, CToggle, schema, table, geom_column, geometry(list), srid(int), Cx(str), Cy(str), column_names(list), values(tree), replace_table(bool); 1 output: report).

- [ ] **Step 2: Write code.py**

Write `C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_CreateShapefile\code.py` with:
- sys.path bootstrap block (copy verbatim)
- ghenv.Component.Message block
- `from crc_modules.db.writer import insert_geometries`
- Default: `report = "Set CToggle=True to INSERT geometries. This operation writes to the database."`
- Guard: `if CToggle:`
- Validation: CString, schema, table, geom_column required; wkts non-empty
- `sr = int(srid) if srid else 4326`
- `cx = str(Cx) if Cx else "0"` / `cy = str(Cy) if Cy else "0"`
- names from column_names; vals from values DataTree (`.BranchCount`, `.Branch(i)`)
- Call: `insert_geometries(CString, schema, table, geom_column, wkts, sr, cx=cx, cy=cy, column_names=names, values=vals)`
- `report = "success: true\nRows Affected: {}".format(rc)`
- except: `report = "ERROR: {}".format(e)`

- [ ] **Step 3: Copy icon.png**

```
cp "C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_QueryValues\icon.png" "C:\Users\eugenio.moreira\Documents\github\carcara\grasshopper\components\CRC_CreateShapefile\icon.png"
```

---

### Task 5: Flip CLAUDE.md inventory

**Files:**
- Modify: `CLAUDE.md` (two cells only)

- [ ] **Step 1: Update inventory rows 14 and 15**

In the `## Component Inventory` section, `#### 02.Queries (9)` table:
- Row `| 14 | CRC_CreateTable | ... | ⬜ Todo |` → `✅ Done`
- Row `| 15 | CRC_CreateShapefile | ... | ⬜ Todo |` → `✅ Done`

Only these two cells. No other changes.

---

### Task 6: Run full test suite

- [ ] **Step 1: Run test_writer.py only**

```
conda run -n carcara pytest tests/test_writer.py -v
```

Expected: 8 PASSED, 0 FAILED.

- [ ] **Step 2: Run full suite**

```
conda run -n carcara pytest tests/ -v
```

Report total counts (pass/fail/skip). Fix only failures introduced by writer.py — do not touch pre-existing test failures.

---

### Task 7: Build .ghuser files

- [ ] **Step 1: Run build**

```
conda run -n carcara python build_userobjects.py
```

Expected: 11 components built (9 existing + CRC_CreateTable + CRC_CreateShapefile). Report built/failed/skipped counts and any verbatim errors.

---

### Task 8: Deploy

- [ ] **Step 1: Deploy if build OK**

```
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

Report: success or verbatim error.
