# SDK-Mode (Viewport-Preview) Components

How to build Grasshopper **SDK / advanced-mode** Python Script components in Carcara —
components that draw a custom Rhino-viewport preview (`DrawViewportWires`,
`DrawViewportMeshes`, `get_ClippingBox`) instead of (or in addition to) returning geometry
to GH params. Read this before adding a preview component or editing
`vendor/componentizer/componentize_py_sdk.py`. Companion to
[`componentizer.md`](componentizer.md).

---

## 1. Procedural vs SDK mode

A Rhino 8 Script component runs CPython one of two ways:

| | Procedural | SDK / advanced |
|---|---|---|
| `code.py` shape | flat script body; inputs are globals | a subclass of `ghpythonlib.componentbase.executingcomponent` |
| Outputs | assigned to named globals | returned as a tuple from `RunScript` |
| Viewport preview | only GH's default param preview | full override: `DrawViewportWires` / `DrawViewportMeshes` / `get_ClippingBox` |
| `metadata.json` | `ghpython.isAdvancedMode: false` | `ghpython.isAdvancedMode: true` |

Use SDK mode **only** when you need custom viewport drawing — line weights, custom colors,
shaded fills, 3-D text tags. Everything else (DB, geometry conversion, charts that only emit
geometry) stays procedural.

---

## 2. Why a separate builder

`componentize_cpy.py` emits the **old GHPython schema** (LanguageSpec Taxon `*.*.python` /
Version `3.-1`, minimal chunk set). That schema runs procedurally and **silently ignores the
SDK preview overrides** — and it ignores `isAdvancedMode` entirely. An SDK component built
with it loads but never previews.

SDK components must be built with **`vendor/componentizer/componentize_py_sdk.py`**, which
writes the **new Rhino 8 Script-component schema**:

- BaseID `c9b2d725-6f87-4b07-af90-bd9aefef68eb` (same component GUID; the schema selects the mode)
- LanguageSpec Taxon **`mcneel.pythonnet.python`**, Version **`3.9.10`**
- `ScriptComponentVersion=3`, `Marsh{Guids,Inputs,Outputs}`, `UsingScriptOutputParam`,
  `ScriptParameterVersion=2`, and a per-input `ConverterData` (CLR type) sub-chunk.

This is the same archive structure `componentize_cs.py` produces for C#, just with the Python
taxon. The reference that proved it: `legacy-0.4.0-beta.2/carcara/test-displaycurve.ghuser`.

---

## 3. Build routing

`tools/build_userobjects.py` chooses a builder per bundle, no hard-coded names:

1. bundle has **`code.cs`** → C# builder (`componentize_cs.create_curvedisplay_cs_ghuser`).
2. bundle has **`code.py`** AND `metadata.json` `ghpython.isAdvancedMode == true` →
   SDK builder (`componentize_py_sdk.create_python_sdk_ghuser`).
3. otherwise `code.py` → procedural builder (`componentize_cpy.create_ghuser_component`).

So **the only switch you flip to make a component SDK is `isAdvancedMode: true` in its
`metadata.json`** (with a `code.py`, no `code.cs`). The helper `is_advanced_mode(source)` in
`tools/build_userobjects.py` reads the flag.

Build / deploy is unchanged:

```powershell
conda run -n carcara python tools/build_userobjects.py
powershell -ExecutionPolicy Bypass -File tools\deploy.ps1
```

---

## 4. The `code.py` pattern

```python
import sys, os
# --- sys.path bootstrap so `import crc_modules` resolves (GHPython has no __file__) ---
_bases = []
_appdata = os.environ.get("APPDATA")
if _appdata:
    _bases.append(os.path.join(_appdata, "Grasshopper", "UserObjects", "carcara"))
_bases.append(os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "McNeel",
    "Rhinoceros", "8.0", "Plug-ins", "Grasshopper", "UserObjects", "carcara"))
for _b in _bases:
    if os.path.isdir(_b) and _b not in sys.path:
        sys.path.insert(0, _b)

from ghpythonlib.componentbase import executingcomponent as component
import Rhino
import System                      # REQUIRED before ANY System.* use (see gotchas)
from System.Drawing import Color
from crc_modules.rhino.preview import PreviewPayload   # shared draw helper

class MyComponent(component):
    def RunScript(self, A, B, C):          # params in metadata INPUT order
        # ... compute everything; build a preview payload ...
        pv = PreviewPayload()
        pv.add_curve(some_curve, color, width=2)
        pv.add_filled_curve(closed_curve, fill_color)
        pv.add_text("Label", point_or_plane, height, Color.Black)
        self._pv = pv
        self.Hidden = True                  # suppress default param preview; we draw our own
        return (out1, out2)                 # tuple in metadata OUTPUT order (omit if no outputs)

    def DrawViewportWires(self, args):
        if hasattr(self, "_pv"): self._pv.draw_wires(args)

    def DrawViewportMeshes(self, args):
        if hasattr(self, "_pv"): self._pv.draw_meshes(args)

    def get_ClippingBox(self):
        return self._pv.clipping_box if hasattr(self, "_pv") else Rhino.Geometry.BoundingBox.Empty
```

Rules:
- Class name is irrelevant; the host finds the `executingcomponent` subclass.
- `RunScript` parameters map to inputs by name/order — they MUST match `metadata.json`
  `inputParameters` exactly (including any appended inputs).
- Outputs are the returned tuple in `outputParameters` order. DataTrees return as built
  (`from Grasshopper import DataTree`). No outputs → declare none and `return` nothing.
- **Rhino imports in `code.py` are an accepted, documented exception** to the normal
  "no Rhino in code.py" rule (CLAUDE.md): preview overrides live in the component class and
  cannot be isolated. Keep all pure logic in `crc_modules` (e.g. `geometry/dash.py`,
  `viz/*.py`, `utils/color.py`); only the drawing glue lives here.

`metadata.json`: set `ghpython.isAdvancedMode: true`, keep a stable `instanceGuid`, declare
inputs/outputs as usual (see [`componentizer.md`](componentizer.md) §4–5 for the schema and
`typeHintID` values).

---

## 5. Shared draw helper — `crc_modules/rhino/preview.py`

A `PreviewPayload` accumulator every SDK component delegates to. Rhino imports are deferred
inside its methods so the `crc_modules` package stays importable under pytest (the module is
never imported by tests). API:

| Method | Use |
|---|---|
| `add_curve(curve, color, width=1)` | a wire (any `Rhino.Geometry.Curve`) |
| `add_filled_curve(closed_curve, fill_color)` | a flat fill — builds a planar `Mesh` via `Mesh.CreateFromPlanarBoundary`, all vertices = `fill_color`. Open/non-planar curves skipped silently |
| `add_mesh(mesh)` | an already-vertex-colored mesh (e.g. a legend) |
| `add_text(text, point_or_plane, height, color, h_align=None, v_align=None)` | a `Rhino.Display.Text3d` tag. `h_align`/`v_align` are `Rhino.DocObjects.TextHorizontalAlignment` / `TextVerticalAlignment` enum values |
| `draw_wires(args)` | call from `DrawViewportWires` — draws curves + texts |
| `draw_meshes(args)` | call from `DrawViewportMeshes` — `DrawMeshFalseColors` (renders vertex colors) |
| `clipping_box` (property) | return from `get_ClippingBox`; `BoundingBox.Empty` when nothing added |

Module helper: `color_to_hex(color) -> "#RRGGBB"` — convert a `System.Drawing.Color` to a CSS
string (used by components that also emit SVG).

All `add_*` methods guard `None` and wrap drawing in try/except, so one bad item never kills
the pipeline.

---

## 6. Gotchas (each one bit us)

- **`import System`** — Rhino 8 CPython needs the top-level `import System` to register the
  `System` namespace before any `System.*` (e.g. `from System.Drawing import Color`). Omitting
  it raises `name 'System' is not defined` at runtime.
- **Auto-generated RunScript annotations must resolve at module top.** Rhino rewrites the
  `RunScript` signature with `.NET` type annotations derived from each input's Type Hint, and
  Python evaluates those annotation expressions at class-definition time. If any namespace they
  reference is not importable, the `def` raises, the class is created WITHOUT `RunScript`, and the
  host reports `object has no attribute 'RunScript'` with empty outputs. Consequences:
  - **Any `list`-access input** → annotation `System.Collections.Generic.List[...]`. `import
    System` does NOT load `System.Collections` in Rhino's pythonnet — add
    **`import System.Collections.Generic`** at module top.
  - **`color` input** → annotation `...List[System.Drawing.Color]`. Load System.Drawing via
    `from System.Drawing import Color` (NOT a bare `import System.Drawing`, which raises unless
    preceded by `clr.AddReference("System.Drawing")` — it is not auto-referenced like
    `System`/`Rhino`/`Grasshopper`).
  - **`tree` input** → `Grasshopper.DataTree[...]` (need `import Grasshopper`); a `plane`/geometry
    hint → `Rhino.Geometry.*` (need `import Rhino.Geometry`).
  Rule of thumb: import every .NET namespace your inputs' Type Hints map to, at module top.
- **Empty clipping box → culling.** If `get_ClippingBox` returns
  `BoundingBox.Empty`, Rhino assumes no geometry and culls your draw calls the moment the world
  origin leaves the screen. Always union the bbox of everything you draw (the payload does this;
  text-only components especially — `Text3d.BoundingBox` is a *property*, not a method).
- **`self.Hidden = True`** hides only the default attribute preview; the override draws persist.
- **`colour` inputs are optional → arrive as `None`** when unconnected. Treat `None` as
  "no stroke / no fill"; guard before drawing.
- **Fills need closed, planar curves.** `add_filled_curve` skips anything else silently
  (no mesh, no error) — verify the input curve `.IsClosed` and is planar.
- **Don't leak Rhino into pytest.** `preview.py` (and any `crc_modules/rhino/*`) must defer
  Rhino imports inside functions/methods and must never be imported by a test or by a
  pytest-imported module.
- **Stable `instanceGuid`.** Never regenerate it after a component ships. When adding inputs to
  an existing component, append them at the END of `inputParameters` to minimize index shift
  for saved definitions.

---

## 7. SDK-mode component inventory

Every SDK-mode component uses the same `PreviewPayload` pattern to draw geometry in the
Rhino viewport. The nine components currently are:

| Component | Subcategory | What it draws in the viewport | Also exports to SVG? |
|---|---|---|---|
| CRC_CurveDisplay | 04.Dataviz | Curves with lineweight, color, dash | No (display-only) |
| CRC_ColorCalculator | 01.Modeling | Colored mesh geometry (legend + vertices) | No |
| CRC_PolylineToSVG | 04.Dataviz | Polylines/polygons with stroke/fill | Yes |
| CRC_CircleToSVG | 04.Dataviz | Circles | Yes |
| CRC_NurbsToSVG | 04.Dataviz | NURBS curves approximated as lines | Yes |
| CRC_TextToSVG | 04.Dataviz | Text annotations (Text3d) | Yes |
| CRC_Histogram | 04.Dataviz | Bar rects, axes, labels, grid | Yes |
| CRC_ScatterPlot | 04.Dataviz | Dot circles, axes, labels, grid, legend | Yes |
| CRC_LinePlot | 04.Dataviz | Line segments, axes, labels, grid | Yes |
| CRC_Heatmap | 04.Dataviz | Colored cell mesh, legend, labels | Yes |

> **Note:** SVG-exporting components (5–10 above) draw a preview **and** produce SVG via
> matplotlib — `PreviewPayload` shows the geometry in Rhino's viewport while `svgwrite` emits
> the file. The display-only component (#1) is the original CurveDisplay ported from C#.

All SDK component source bundles live at `build/components/CRC_<Name>/`. Each has
`isAdvancedMode: true` in `metadata.json`, a `code.py` using the executingcomponent pattern,
and an `icon.png`.

---

## 8. Add a new SDK component (checklist)

1. Put pure algorithm logic in `crc_modules/` (pytest-tested). Rhino-only helpers go in
   `crc_modules/rhino/` with deferred imports.
2. Create `build/components/CRC_<Name>/` with `metadata.json` (`isAdvancedMode: true`,
   stable `instanceGuid`), `code.py` (the §4 pattern, using `PreviewPayload`), `icon.png`.
3. `conda run -n carcara python tools/build_userobjects.py` — confirm the bundle reports `[OK]` and
   routed through the SDK builder.
4. `conda run -n carcara python -m pytest tests/ -q` — pure modules stay green; no Rhino leak.
5. `tools/deploy.ps1`, restart Grasshopper, confirm the viewport preview renders and the clip box
   frames the camera.

## 8. Verifying the built schema

Decode the built `.ghuser` (raw-deflate inflate + string scan, per
[`ghuser-decoding.md`](ghuser-decoding.md)) and confirm: Taxon `mcneel.pythonnet.python`,
Version `3.9.10`, `ScriptComponentVersion=3`, `Marsh*` keys present. If you instead see Taxon
`*.*.python` / `3.-1`, the bundle was built by the procedural builder — check
`isAdvancedMode` and that there is no stray `code.cs`.

---

## 9. References

- Builder: `vendor/componentizer/componentize_py_sdk.py`
- Routing: `tools/build_userobjects.py` (`is_advanced_mode`)
- Draw helper: `release/crc_modules/rhino/preview.py`
- Reference components: the SVG / chart / `CRC_ColorCalculator` bundles (full: outputs + preview), `CRC_CurveDisplay` (display-only)
- Working hand-made reference archive: `legacy-0.4.0-beta.2/carcara/test-displaycurve.ghuser`
- Build pipeline: [`componentizer.md`](componentizer.md) · decoding: [`ghuser-decoding.md`](ghuser-decoding.md)
