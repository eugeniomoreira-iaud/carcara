# C# Migration — Phase 07: csharp_shared/Utils.cs — Color, SQL Composer, Correction

## Goal

Port `carcara/crc_modules/utils/` into `grasshopper/csharp_shared/Utils.cs`. These are
shared helpers used by `Db.cs`, `Geometry.cs`, and GH component scripts. All are pure
(no DB, no Rhino) and carry no NuGet dependencies — fully available in Rhino's C#
script runtime.

## Depends on

- Phase 01 (toolchain).
- Phases 02–06 may have written local stubs for `ValidateOffset` / `TranslateExpr` —
  those stubs are replaced here.

## Python behavioral specs

| C# location in Utils.cs | Python spec |
|---|---|
| `Correction` static class | `carcara/crc_modules/utils/correction.py` |
| `SqlComposer` static class | `carcara/crc_modules/utils/sql_composer.py` |
| `ColorUtils` static class | `carcara/crc_modules/utils/color.py` |

Read each Python file before writing C#.

---

## Scope

`Utils.cs` declares no `#r "nuget:"` directives.

### `Correction` class

This is the most critical utility — it enforces the coordinate correction rule.

```csharp
static class Correction
{
    // Return value unchanged if it is a numeric literal (integer or decimal).
    // Throw ArgumentException otherwise.
    // Keeps Cx/Cy injection-safe. "0" = no shift.
    // Regex: ^-?\d+(\.\d+)?$  — match Python correction.py exactly.
    public static string ValidateOffset(string value);

    // Wrap a SQL geometry expression in ST_Translate.
    // direction = "to_local"      → ST_Translate(<geomSql>, -cx, -cy)  (read)
    // direction = "to_projected"  → ST_Translate(<geomSql>,  cx,  cy)  (write/filter)
    // cx and cy are numeric-validated text — embedded verbatim, never parsed to double.
    public static string TranslateExpr(string geomSql, string cx, string cy,
                                       string direction);
}
```

**Hard rule**: `ValidateOffset` and `TranslateExpr` are the only place in the entire
codebase where `cx`/`cy` are processed. `Db.cs` and component `code.cs` files call
`Correction.ValidateOffset(cx)` before any SQL construction. Never `double.Parse(cx)`.

### `SqlComposer` class

Port `utils/sql_composer.py`. `CRC_SQLComposer` does free-form placeholder substitution —
takes a SQL template and `(placeholder, value)` pairs, replaces each in order.

```csharp
static class SqlComposer
{
    // Replace each key in substitutions with its value in the SQL template.
    // Port substitution order and escaping rules verbatim from sql_composer.py.
    public static string Compose(string sqlTemplate,
                                 IReadOnlyDictionary<string, string> substitutions);
}
```
Read `sql_composer.py` carefully — substitution order and escaping must match Python
exactly (advanced users write their own SQL templates against this component).

### `ColorUtils` class

Port `utils/color.py`. `CRC_ColorCalculator` maps numeric values to colors on a ramp.

```csharp
static class ColorUtils
{
    // Map a normalized value [0.0, 1.0] to an RGB color on the named ramp.
    public static (byte r, byte g, byte b) MapToColor(double normalizedValue,
                                                       string colormap = "viridis");

    // Map a list of raw values to colors, normalizing across the range.
    public static List<(byte r, byte g, byte b)> MapValuesToColors(
        IEnumerable<double> values, string colormap = "viridis");
}
```
If `color.py` uses matplotlib colormaps, port the lookup table verbatim (viridis etc.
are fixed 256-entry RGB tables — copy the table, not the matplotlib dependency).
At minimum port viridis; add additional colormaps as needed by the chart components.

---

## Steps

1. Implement `Correction.ValidateOffset`: regex `^-?\d+(\.\d+)?$`; match Python edge
   cases (`"0"`, `"500000"`, `"9500000.5"`, `"-100"`, `"abc"` → throws).
2. Implement `Correction.TranslateExpr` for both directions. Verify SQL output format
   against Python `correction.py` tests.
3. Implement `SqlComposer.Compose`: read `sql_composer.py` for substitution logic.
4. Read `color.py`: port the colormap table(s). Add `MapToColor` and `MapValuesToColors`.
5. Replace any stubs of `ValidateOffset` / `TranslateExpr` written in `Db.cs` (Phase 02)
   with calls to `Correction.*` (the concat step now includes `Utils.cs` for those components).
6. Build a temporary test component; verify `ValidateOffset`, `TranslateExpr`,
   `SqlComposer`, and `ColorUtils` against expected outputs.

---

## Validation

**Python oracle** — run existing Python tests:
```powershell
conda run -n carcara pytest tests/ -v -k "correction or sql or color"
```
Port assertions to manual canvas checks.

**Canvas smoke test** — a temporary component:
- `Correction.ValidateOffset("500000")` → `"500000"` (no throw).
- `Correction.ValidateOffset("abc")` → exception caught → report error.
- `Correction.TranslateExpr("geom", "500000", "9000000", "to_local")` →
  output contains `ST_Translate` and `-500000`.
- `SqlComposer.Compose("SELECT {col} FROM {schema}.{tbl}", ...)` → correct SQL.
- `ColorUtils.MapToColor(0.0, "viridis")` vs `(1.0, "viridis")` → different colors.

---

## Done when

- [ ] `grasshopper/csharp_shared/Utils.cs` written with `Correction`, `SqlComposer`,
      `ColorUtils`.
- [ ] No `#r "nuget:"` directives needed.
- [ ] `ValidateOffset` regex matches Python exactly (same accepts/rejects).
- [ ] `TranslateExpr` produces correct `ST_Translate` SQL for both directions.
- [ ] `Correction` called by `Db.cs` — stubs replaced with real calls.
- [ ] `SqlComposer.Compose` substitution matches Python `sql_composer.py` behavior.
- [ ] Viridis colormap table ported; `MapToColor` produces expected RGB at endpoints.
- [ ] Python pytest suite still passes.
- [ ] Canvas smoke test passes for all four functions.
