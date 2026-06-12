# Phase 11 — Utilities (`utils/*` + utility components)

## Goal

Ship the remaining cross-cutting helpers. `CRC_SRID` (03.Utilities) was already
shipped as the Phase 02 smoke test. This phase covers three components that the
build groups together by module even though they sit in **different GH
subcategories** (per the authoritative subcategory list):

- `CRC_ColorCalculator` → **01.Modeling**
- `CRC_FindCorrectionParameters` → **03.Utilities** (the coordinate false-origin tool)
- `CRC_SQLComposer` → **02.Queries**

Set the `subcategory` field in each `metadata.json` accordingly — do not assume
all three share one subcategory.

Components delivered:

| Component                       | Module                    |
|---------------------------------|---------------------------|
| `CRC_ColorCalculator`           | `utils/color.py`          |
| `CRC_FindCorrectionParameters`  | `utils/correction.py`     |
| `CRC_SQLComposer`               | `utils/sql_composer.py`   |

> `utils/correction.py` (the false-origin SQL helpers used by the geometry DB components in
> Phases 05/06) also lives here — implement it now if it was not already created in Phase 05.
> **`CRC_FindCorrectionParameters` is the coordinate false-origin tool** (confirmed): it computes
> the `(Cx, Cy)` for a study area and returns it as **text**. Module `utils/correction.py`, not
> `utils/color.py`.

## Inputs you must give me

For each of the 3 legacy `.ghuser`:

- `carcara_ColorCalculator_r00.ghuser` — what color spaces does it support
  (RGB, HSV, LAB, sRGB curves)? Input/output conventions (0-1 floats vs
  0-255 ints)?
- `carcara_FindCorrectionParameters_r03.ghuser` — **the coordinate false-origin
  tool** (confirmed). It takes a study-area point / known control point(s) and returns
  the `(Cx, Cy)` correction as **text** to feed the geometry DB components. Module
  `utils/correction.py`. Give me its exact inputs/outputs and how it derives Cx/Cy.
- `carcara_SQLComposer_rev02.ghuser` — how does it compose SQL? Field
  selector + WHERE builder + ORDER BY? Does it sanitize? Does it accept a
  table name and a list of `(column, op, value)` triples?

## Steps

1. **Implement `carcara/crc_modules/utils/color.py`** with:
   ```python
   def rgb_to_hsv(r, g, b) -> tuple[float, float, float]
   def hsv_to_rgb(h, s, v) -> tuple[float, float, float]
   def find_correction_parameters(measured: list[tuple],
                                  target:   list[tuple]) -> tuple[float, float, float]
   ```
   Plus whatever extra functions the legacy `ColorCalculator` requires.

1b. **Implement `carcara/crc_modules/utils/correction.py`** (if not already done in Phase 05):
   ```python
   def validate_offset(value: str) -> str
       # return value if numeric literal (kept as TEXT, never float()); else raise ValueError
   def translate_expr(geom_sql: str, cx: str, cy: str, direction: str) -> str
       # 'to_local' -> ST_Translate(<geom_sql>, -cx, -cy);  'to_projected' -> +cx, +cy
   ```
   Pure string/SQL — no DB, no Rhino. If `CRC_FindCorrectionParameters` is the coordinate
   tool, its core logic (compute `(Cx, Cy)` for a study area, return as text) goes here too.

2. **Implement `carcara/crc_modules/utils/sql_composer.py`**:
   ```python
   def compose_select(table: str,
                      columns: list[str] | None = None,
                      where:   list[tuple[str, str, object]] | None = None,
                      order_by: str | None = None,
                      limit: int | None = None) -> tuple[str, tuple]
   ```
   Returns `(sql_with_placeholders, params)` so it can be passed straight
   to `psycopg2.cursor.execute(sql, params)`. **Identifiers must be quoted
   via `psycopg2.sql.Identifier`** — never f-string interpolated.

3. **Tests** `tests/test_color.py`, `tests/test_sql_composer.py`, `tests/test_correction.py`:
   - Color: round-trip RGB→HSV→RGB within rounding error.
   - Correction: `validate_offset("9500000")` passes and returns the string unchanged
     (assert it is **not** reformatted to a float like `9500000.0`); `validate_offset`
     rejects `"5e5; DROP TABLE"`. `translate_expr(..., 'to_local')` emits `-cx,-cy`;
     `'to_projected'` emits `+cx,+cy`; the values appear verbatim as text.
   - SQL composer: builds correct SQL for each combination of
     args; identifier-injection attempts are quoted, not interpolated;
     positional args end up in the `params` tuple.

4. **GH bundles** (3 folders). All pure-Python in `code.py` (no Rhino, no
   DB — `SQLComposer` only **emits** SQL, it doesn't execute it; downstream
   components like `CRC_QueryValues` do).

5. **Build & install**.

## Tests

```powershell
pytest tests/test_color.py tests/test_sql_composer.py -v
```

## Grasshopper checkpoint

Restart Grasshopper.

**CRC_ColorCalculator** — wire numeric panels for RGB. Expect the requested
color space conversion in the output. If the legacy supports interactive
color preview, confirm it renders the right swatch.

**CRC_FindCorrectionParameters** — feed two parallel lists of colors
(measured + target). Expect a parameter triple. Sanity-check by applying
the parameters back to the measured colors and confirming they land near
the target.

**CRC_SQLComposer** — wire `table = "buildings"`, `columns = ["id","name","height"]`,
`where = [("height",">",10)]`. Expect SQL output like
`SELECT "id","name","height" FROM "buildings" WHERE "height" > %s` and
`params = (10,)`. Pipe the SQL into `CRC_QueryValues` to verify the
emitted SQL is valid against your DB.

Save canvases as `tests/_manual/smoke_utils_*.gh`.

## Commit

```
feat(utils): add color calculator, correction params, SQL composer + 3 components
```

## Done when

- [ ] `carcara/crc_modules/utils/color.py` + `carcara/crc_modules/utils/sql_composer.py` exist and tested.
- [ ] All 3 GH bundles built and validated.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
- [ ] At this point the `Utilities` subcategory and the `SQLComposer`
      row of the `Database` table are both fully ✅.
