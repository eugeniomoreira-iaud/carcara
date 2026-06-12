# Phase 11 — Utilities (`utils/*` + utility components)

## Goal

Ship the remaining cross-cutting helpers. `CRC_SQLComposer` (03.Utilities) was
already shipped as the Phase 02 smoke test — it is not rebuilt here. This phase
covers **two components** that sit in **different GH subcategories** (per the
authoritative subcategory list):

- `CRC_ColorCalculator` → **01.Modeling**
- `CRC_FindCorrectionParameters` → **03.Utilities** (the coordinate false-origin tool)

Set the `subcategory` field in each `metadata.json` accordingly.

Components delivered:

| Component                       | Module                | Subcategory    |
|---------------------------------|-----------------------|----------------|
| `CRC_ColorCalculator`           | `utils/color.py`      | 01.Modeling    |
| `CRC_FindCorrectionParameters`  | `utils/correction.py` | 03.Utilities   |

> `utils/correction.py` (the false-origin SQL helpers used by the geometry DB
> components in Phases 05/06) also lives here — implement it now if it was not
> already created in Phase 05.

## Inputs you must give me

- `carcara_ColorCalculator_r00.ghuser` — what color spaces does it support
  (RGB, HSV, LAB, sRGB curves)? Input/output conventions (0-1 floats vs
  0-255 ints)?

The decoded interface for `CRC_FindCorrectionParameters` is already confirmed at
`carcara-old/ghuser-metadata/scripts/FindCorrectionParameters_interface.txt` and
documented in `carcara-old/ghuser-metadata/03.Utilities.md`. No user action
needed for that component — proceed from the spec below.

## Steps

1. **Implement `carcara/crc_modules/utils/color.py`** with color-space
   conversion functions based on the legacy `ColorCalculator` behavior you
   confirm above. Typical shape (adjust to real legacy inputs/outputs):

   ```python
   def rgb_to_hsv(r, g, b) -> tuple[float, float, float]
   def hsv_to_rgb(h, s, v) -> tuple[float, float, float]
   ```

   Plus whatever extra functions the legacy `ColorCalculator` requires. No
   Rhino imports. Pure numeric logic.

2. **Implement `carcara/crc_modules/utils/correction.py`** (if not already
   done in Phase 05). This module has two layers:

   **2a. Pure SQL helpers** (no DB, no Rhino — fully pytest-testable):

   ```python
   def validate_offset(value: str) -> str:
       """Return value unchanged if it is a numeric literal (kept as TEXT,
       never float()). Raise ValueError otherwise. Keeps Cx/Cy injection-safe.
       '0' = no shift."""

   def translate_expr(geom_sql: str, cx: str, cy: str, direction: str) -> str:
       """Wrap a SQL geometry expression in ST_Translate.
       direction='to_local'     -> ST_Translate(<geom_sql>, -cx, -cy)  (read)
       direction='to_projected' -> ST_Translate(<geom_sql>,  cx,  cy)  (write / filter)
       cx, cy are numeric-validated text, embedded verbatim — never parsed to float."""
   ```

   **2b. DB function for `CRC_FindCorrectionParameters`**:

   ```python
   def find_correction_parameters(cstring: str, schema: str, table: str,
                                  column: str = None,
                                  value: str = None) -> tuple[str, str]:
       """
       Find one row, auto-detect the geometry column via the PostGIS
       geometry_columns view, compute its centroid, and return (Cx, Cy)
       as TEXT strings — never float()-parsed.

       Row selection:
         - column AND value given -> WHERE <column> = <value>  LIMIT 1
         - both omitted           -> first row of the table    LIMIT 1 (no WHERE)

       SQL shape (filtered case):
           SELECT ST_X(ST_Centroid(<geom>))::text,
                  ST_Y(ST_Centroid(<geom>))::text
           FROM <schema>.<table>
           WHERE <column> = %s
           LIMIT 1
       Fallback case: same SELECT without the WHERE clause.

       Geometry column auto-detected via detect_geometry_column(cstring, schema, table)
       from db/spatial_query.py — same shared helper reused by Phase 05 spatial reads.
       Returns (cx_text, cy_text). Raises ValueError if no row found
       (no match, or table empty in the fallback case).
       """
   ```

   Inputs match the confirmed legacy hook params: `CString`, `CToggle`,
   `Schema`, `Table`, `Column`, `Value` — with `Column` and `Value`
   **optional**: when both are left unwired, the component returns the
   centroid of the table's **first row**. The component does **not** take
   `x_col` / `y_col` inputs — geometry column auto-detection is internal.
   Cx/Cy are returned as TEXT, consistent with the coordinate-correction
   contract: they feed the `Cx`/`Cy` text inputs of Phase 05 geometry
   components and must never be coerced to float.

3. **Tests** `tests/test_color.py`, `tests/test_correction.py`:

   - **Color**: round-trip RGB→HSV→RGB within rounding error.
   - **Correction — pure helpers**:
     - `validate_offset("9500000")` passes and returns the string `"9500000"`
       unchanged (assert `result == "9500000"`, not `"9500000.0"`).
     - `validate_offset("5e5; DROP TABLE")` raises `ValueError`.
     - `translate_expr(..., 'to_local')` emits `-cx,-cy` embedded verbatim
       as text.
     - `translate_expr(..., 'to_projected')` emits `+cx,+cy` embedded
       verbatim as text.
   - **Correction — DB function** (mock psycopg2):
     - Assert that `find_correction_parameters` issues a geometry-column
       auto-detect query (the `geometry_columns` view query from
       `detect_geometry_column`) before the centroid query.
     - Assert that the returned values are verbatim text strings from the DB
       row — never reformatted (e.g. if the DB returns `"500123.45"` the
       function returns `"500123.45"`, not `500123.45` or `"500123.45000"`).
     - Assert the fallback: with `column=None, value=None` the issued SQL has
       **no WHERE clause** (first row of the table, `LIMIT 1`).
     - Assert that `ValueError` is raised when the query returns no rows
       (both the filtered and the fallback case).

   > `test_sql_composer.py` was delivered in Phase 02 — do not duplicate it here.

4. **GH bundles** (2 folders):

   **`CRC_ColorCalculator`** (`grasshopper/components/CRC_ColorCalculator/`):
   - Pure Python in `code.py` (no Rhino, no DB).
   - Inputs/outputs from the legacy `.ghuser` you confirm above.
   - `subcategory`: `"01.Modeling"`.

   **`CRC_FindCorrectionParameters`**
   (`grasshopper/components/CRC_FindCorrectionParameters/`):
   - Inputs (from confirmed legacy hook params): `CString` (str), `CToggle`
     (bool), `Schema` (str), `Table` (str), `Column` (str, **optional**),
     `Value` (str, **optional**).
   - Outputs: `Cx` (str, "Correction X"), `Cy` (str, "Correction Y"),
     `report` (str, legacy label "Exceptions").
   - `code.py` guards on `CToggle`, calls
     `find_correction_parameters(CString, Schema, Table, Column, Value)`,
     surfaces `Cx` and `Cy` as text, errors to `report`. Unwired `Column`/
     `Value` pass through as `None` → first-row fallback.
   - `subcategory`: `"03.Utilities"`.

5. **Build & install**.

## Tests

```powershell
pytest tests/test_color.py tests/test_correction.py -v
```

## Grasshopper checkpoint

Restart Grasshopper.

**CRC_ColorCalculator** — wire numeric panels for the legacy color inputs.
Expect the requested color-space conversion in the output panels. Confirm
the output convention (0-1 floats vs 0-255 ints) matches the legacy behavior
you recorded in "Inputs you must give me".

**CRC_FindCorrectionParameters** — wire `CString` (from a live
`CRC_ConnectionString`), `CToggle = True`, and text panels for `Schema`,
`Table`, `Column`, `Value` pointing to a known row in your test DB. Expect:
- `Cx` and `Cy` output panels show text coordinate strings (e.g.
  `"500123.45"`, `"9483210.78"`), **not** floats.
- `report` shows no error.

Then disconnect `Column` and `Value` and re-run: the component must return
the centroid of the table's **first row** instead of erroring.

Feed those `Cx`/`Cy` text outputs directly into a Phase 05 geometry
component (`CRC_GeometryEntities`) as its `Cx`/`Cy` inputs. Confirm that
the geometry returned by that component lands near the Rhino world origin
(local coordinates, not full-magnitude projected values).

Save canvases as `tests/_manual/smoke_utils_*.gh` (gitignored).

## Commit

```
feat(utils): add color calculator, correction params + 2 components
```

## Done when

- [ ] `carcara/crc_modules/utils/color.py` exists and tested.
- [ ] `carcara/crc_modules/utils/correction.py` exists with
      `validate_offset`, `translate_expr`, and `find_correction_parameters`,
      all tested.
- [ ] Both GH bundles built and validated on the canvas.
- [ ] `CRC_ColorCalculator` and `CRC_FindCorrectionParameters` statuses
      flipped to ✅ Done in `CLAUDE.md`.
- [ ] At this point all `03.Utilities` components are ✅ Done (SQLComposer
      was Phase 02; ConnectionString, RunQuery, RunCommand, WKTtoGH, GHtoWKT
      are their own phases).
