# Phase 09 — SVG Export (`svg/export.py`, `svg/save.py` + 5 components)

## Goal

Convert Grasshopper / Rhino geometry into SVG elements and write the
result to disk. Pure-Python via `svgwrite`; Rhino-side conversion goes
through the bridge from Phase 07.

Components delivered:

| Component             | Module             | Notes                          |
|-----------------------|--------------------|--------------------------------|
| `CRC_PolylineToSVG`   | `svg/export.py`    | Polyline → `<polyline>`        |
| `CRC_CircleToSVG`     | `svg/export.py`    | Circle → `<circle>`            |
| `CRC_NurbsToSVG`      | `svg/export.py`    | NURBS → sampled `<path>`       |
| `CRC_TextToSVG`       | `svg/export.py`    | Text → `<text>`                |
| `CRC_SaveSVG`         | `svg/save.py`      | Assemble + write SVG file      |

## Inputs you must give me

For each of the 5 legacy `.ghuser`, the standard rundown. Specifically:

- **PolylineToSVG / CircleToSVG / NurbsToSVG / TextToSVG** — what styling
  parameters does each component expose? Stroke color, stroke width,
  fill, opacity, dash array? Coordinate transform (Y-flip for screen
  coords)? Units (mm/px)?
- **NurbsToSVG** — sampling density: by curve count, by chord tolerance,
  or by angle tolerance?
- **TextToSVG** — does it embed a font name, size, anchor, baseline?
  Or does it convert text-to-curves first (so the output is paths, not
  `<text>`)? These are very different code paths.
- **SaveSVG** — how does it receive SVG elements: as a list of strings,
  as a list of dicts, or as objects? What is the page setup (viewBox,
  size, units)?

## Steps

1. **Implement `carcara/crc_modules/svg/export.py`**:
   ```python
   def polyline_to_svg(points: list[tuple[float, float]], **style) -> str
   def circle_to_svg(cx: float, cy: float, r: float, **style) -> str
   def nurbs_to_svg(sampled_points: list[tuple[float, float]], **style) -> str
   def text_to_svg(x: float, y: float, text: str, **style) -> str
   ```
   Each returns a snippet of SVG markup (string). `**style` accepts
   `stroke`, `stroke_width`, `fill`, `opacity`, etc. The function maps to
   `svgwrite` calls under the hood.

2. **Implement `carcara/crc_modules/svg/save.py`**:
   ```python
   def save_svg(elements: list[str], out_path: str,
                width: float, height: float,
                viewbox: tuple = None,
                units: str = "mm") -> str
   ```
   Assembles a valid SVG document from string elements and writes it.
   Returns the absolute path of the written file.

3. **Tests** `tests/test_svg.py`:
   - Each export function returns a string containing the expected SVG tag
     and attribute values.
   - `save_svg` writes a file at `out_path` and the file contains all the
     element strings between the `<svg>` open/close tags.
   - Use `tmp_path` fixture for the file write.

4. **GH bundles** (5 folders):
   - Each `*ToSVG` component takes Rhino geometry input → converts to
     coordinate lists via `crc_modules.rhino.convert` → calls the matching
     `crc_modules.svg.export` function → emits an `svg` string output.
   - `CRC_SaveSVG` collects a list of SVG strings + dimensions + path →
     calls `save_svg` → emits the written `path` and `report`.

5. **Build & install**.

## Tests

```powershell
pytest tests/test_svg.py -v
```

## Grasshopper checkpoint

Restart Grasshopper. Build one canvas chaining the lot:

1. Draw a polyline, a circle, a NURBS curve, and a text annotation in Rhino.
2. Feed each through its matching `*ToSVG` component.
3. Merge the 4 SVG strings into a list.
4. Feed into `CRC_SaveSVG` with `out_path = "C:\\temp\\carcara_test.svg"`,
   sensible width/height.
5. Flip `run`. Open the resulting SVG in a browser. Confirm:
   - All 4 elements appear at correct positions and scale.
   - Styling parameters (stroke, fill) match what you wired in.
   - The Y-axis convention is the one you expect (most legacy SVG exporters
     flip Y; document and stick with one).

Induce errors (read-only path, empty input lists) and confirm `report`
surfaces them.

Save the canvas as `tests/_manual/smoke_svg.gh`.

## Commit

```
feat(svg): add export + save modules with 5 GH components
```

## Done when

- [ ] `carcara/crc_modules/svg/export.py` and `carcara/crc_modules/svg/save.py` exist and are tested.
- [ ] All 5 GH bundles built and validated end-to-end through a real `.svg` file.
- [ ] Statuses flipped to ✅ Done in `CLAUDE.md`.
