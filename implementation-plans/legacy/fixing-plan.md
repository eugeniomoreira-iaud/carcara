# Fixing plan — round 2 (canvas-tested bug batch)

Bugs found running the built components in Grasshopper. One section per component.
Each has: cause (verified by reading the current code), fix, files. Pure-module
work is pytest-tested; component work is verified by `build_userobjects.py` + canvas.

> All causes below were re-checked against the actual source on disk. Where this
> supersedes an earlier draft: BuildingMeshes inputs are already tree-access (the
> `VolatileData` call is the bug); ColorCalculator's cause is the `clr.AddReference`
> block (NOT `marshalGuids` — CRC_Heatmap works with `marshalGuids:true`); and the
> SVG exporters' real crash is `_get` rejecting .NET `List[T]`.

---

## 1. CRC_BuildingMeshes — `'GH_Structure[IGH_Goo]' object has no attribute 'Path'`

**Cause.** `code.py` reads inputs via
`ghenv.Component.Params.Input[0].VolatileData`, which returns a **GH_Structure**.
GH_Structure has no `.Path(i)` / `.Branch(path)` methods (those are `DataTree`),
so iteration throws → 0 buildings. Both inputs (`BdgFp`, `BdgH`) are already
declared `scriptParamAccess: "tree"`, so GHPython already hands them in as
DataTrees — the VolatileData hack is unnecessary and wrong.

**Fix (code.py).** Delete the two `VolatileData` lines; use the tree variables:
```python
_fp_tree = BdgFp
_h_tree  = BdgH
```
Use the DataTree API throughout: `.PathCount`, `.Path(i)`, `.PathExists(path)`,
`.Branch(path)`. Replace the indexer `tree[path]` in `_get_h_branch` with
`tree.Branch(path)` and `tree.Path(0)` stays. Keep all height fan-out /
empty-branch / summary logic.

Files: `grasshopper/components/CRC_BuildingMeshes/code.py`.

---

## 2. CRC_PointInsidePolygon — does it compute the pole of inaccessibility?

**Answer: yes.** It calls `crc_modules/geometry/polylabel.py` `interior_point()`,
the polylabel / pole-of-inaccessibility algorithm (deepest interior point from the
boundary). No functional change required.

**Optional polish.** Fix the `pol` input typehint `ghdoc` → `curve`; clarify the
`description`/`report` to say "pole of inaccessibility (polylabel)". No logic change.

Files (optional): `grasshopper/components/CRC_PointInsidePolygon/{metadata.json, code.py}`.

---

## 3. CRC_SortByContainer — flatten inputs, descriptive names, correct typehints

**Asks:** flatten all inputs; output = point indexes grouped into branches that
map 1:1 to the container curves; descriptive names + short nicknames; fix typehints.

**Cause.** Inputs `crv`/`pt` use `typeHintID: "ghdoc"` (wrong) and `list` access.
On a tree input, list-access reruns the script per-branch and point indices reset
per branch → grouping/indices wrong.

**Fix (metadata.json).** Use per-param `nickname` + correct `typeHintID`, and
`tree` access so we can flatten deterministically:
- `crv` → name `containers`, nickname `C`, `typeHintID: "curve"`, access `tree`.
- `pt`  → name `points`,     nickname `P`, `typeHintID: "point"`, access `tree`.
- output `i` → name `indices`, nickname `i` (branch k ↔ containers[k]).

**Fix (code.py).** Rename params to `containers`/`points`. Flatten BOTH trees to
flat Python lists (iterate every branch, concatenate) before sorting, so point
indices are global and there is exactly one container list. Keep the existing
`sort_points_by_containers` call and the branch-per-container output (empty branch
preserved when a container holds no points).

Files: `grasshopper/components/CRC_SortByContainer/{code.py, metadata.json}`.

---

## 4. CRC_ColorCalculator — `object has no attribute 'RunScript'`

**Cause.** `code.py` carries a `clr.AddReference` block at module top:
```python
import clr
clr.AddReference("Grasshopper")
clr.AddReference("System.Drawing")
clr.AddReference("RhinoCommon")
```
No working SDK component does this (`specs/sdk-components.md` §4 canonical pattern
has no `clr` calls). It interferes with SDK component-class registration so the
host instantiates a ColorCalculator with no `RunScript`. (NOT a `marshalGuids`
issue — CRC_Heatmap works with `marshalGuids:true`.)

**Fix (code.py).** Remove the `import clr` + three `AddReference` lines. Keep
`import System` (required — §6 gotcha) and the existing
`from System.Drawing import Color` / `from Grasshopper import DataTree` /
`import Rhino.Geometry as rg`. Match the working SDK import block (e.g. Heatmap).
No other logic change. (color inputs already use `color` typehint — fine.)

Verify after build by decoding the `.ghuser` (sdk-components.md §8): Taxon
`mcneel.pythonnet.python`, Version `3.9.10`.

Files: `grasshopper/components/CRC_ColorCalculator/code.py`.

---

## 5. CRC_CurveDisplay — only tints the first item of the list

**Cause.** `RunScript(self, Curve, Width, Colour, Dash)` takes `Curve` as a single
item (`rs.coercecurve(Curve)`), so only one curve is drawn.

**Fix (metadata.json).** `Curve` → `list` access (keep typehint `curve`).
`Colour` (`color`), `Width` (`float`), `Dash` (`str`) → `list` access (per-curve,
fallback to last/global). Keep descriptive names + short nicknames.

**Fix (code.py).** Iterate the curve list. For each curve i, resolve per-curve
color/width/dash via the robust `_get` helper (see §6 — must handle .NET `List[T]`),
compute its dash segments, accumulate `(segments, color, width)`. Store the list on
`self`; `DrawViewportWires` loops all accumulated entries drawing each with its own
color/width. Union all curve bboxes for `get_ClippingBox`.

Files: `grasshopper/components/CRC_CurveDisplay/{code.py, metadata.json}`.

---

## 6. CRC_PolylineToSVG / CircleToSVG / NurbsToSVG / TextToSVG — `float() argument ... not 'List[Double]'`, 0 generated

**Cause (all four).** These SDK components receive list inputs as **.NET
`List[T]`** (e.g. `List[Double]`, `List[Color]`), not Python lists. The `_get`
helper guards with `isinstance(seq, (list, tuple))` — **False** for a .NET list —
so it falls through to `return lst` and hands back the WHOLE list. Then
`float(_get(sw, i, 0))` → `float(List[Double])` → crash → every item "failed" →
empty `svgCode`. Same break for `_get(sc/f/j/pt, ...)`. This is the real cause of
"0 element(s) generated, 1 failed (first: float() ... not 'List[Double]')".

**Fix.** Replace `_get` in all four exporters (and reuse in CurveDisplay §5) with a
version that detects sequences via `len()` (works on `List[T]`) instead of
`isinstance`:
```python
def _get(seq, i, default):
    if seq is None:
        return default
    if isinstance(seq, str):
        return seq
    try:
        n = len(seq)          # works for Python list AND .NET List[T]
    except TypeError:
        return seq            # scalar: Color, number, single geometry
    if n == 0:
        return default
    return seq[i] if i < n else seq[n - 1]
```
This makes per-item stroke/width/fill/justification/point resolution work; the
Part-2 color + no-color paths then function as intended.

Files: `code.py` of CRC_PolylineToSVG, CRC_CircleToSVG, CRC_NurbsToSVG,
CRC_TextToSVG.

---

## 7. CRC_ScatterPlot — `Replacement index 5 out of range for positional args tuple`

**Cause.** The success `report` format string (code.py ~lines 300–311) has **6**
placeholders — `points {}`, `has colors {}`, `has legend {}`,
`chart area {:.1f} x {:.1f}` (2), plus a trailing `SVG: {}` — but `.format(...)`
supplies only **5** args. The `SVG: {}` placeholder has no argument.

**Fix (code.py).** Remove the `"  SVG: {}"` line from the format string (it added
nothing). Result: 5 placeholders, 5 args.

Files: `grasshopper/components/CRC_ScatterPlot/code.py`.

---

## 8. CRC_CreateTable + CRC_CreateShapefile — `id_values` must be a DataTree

**Ask.** `geometry` and `values` are DataTrees (branch per row); `id_values` is
currently a flat `list`. Make it a DataTree too, for consistency.

**Fix (metadata.json, both).** `id_values` → `scriptParamAccess: "tree"`;
description "Optional DataTree of primary-key values — branch per row (one id per
branch); omit for auto-increment id".

**Fix (code.py, both).** Read `id_values` as a DataTree: build `ids` by iterating
branches in path order, taking the single value per branch (one id per row).
`ids = None` when empty/absent. Validate `len(ids) == row count` when provided.
Pass to `create_table_with_data` / `create_table_with_geometry` unchanged (the
module already coerces id to the inferred PK type). No module change.

Files: `grasshopper/components/CRC_CreateTable/{code.py, metadata.json}`,
`grasshopper/components/CRC_CreateShapefile/{code.py, metadata.json}`.

---

## Execution order & verification
- All fixes are component-side; the `crc_modules` API is stable, so `pytest tests/
  -q` should stay green (run it as a guard).
- Components are independent → can be done in parallel by component group:
  - Group A: BuildingMeshes + SortByContainer
  - Group B: ColorCalculator + CurveDisplay
  - Group C: 4 SVG exporters (`_get` fix) + ScatterPlot
  - Group D: CreateTable + CreateShapefile (id_values tree)
  - (PointInsidePolygon §2 optional doc/typehint tweak — fold into Group A)
- After edits: `conda run -n carcara python build_userobjects.py` (expect 32 OK).
- Canvas checks: BuildingMeshes makes meshes; SVG exporters emit colored elements;
  ScatterPlot reports OK; ColorCalculator runs; CurveDisplay tints every curve;
  SortByContainer groups indices per container; CreateTable/Shapefile accept
  id_values as a tree.
- Windows python: `C:\ProgramData\anaconda3\envs\carcara\python.exe` (conda not on
  bash PATH) or `conda run -n carcara python ...` via PowerShell.
