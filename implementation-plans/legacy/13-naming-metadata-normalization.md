# Phase 13 — Parameter Naming & Metadata Normalization

## Goal

Bring every component into line with the `CRC_ColorCalculator` reference pattern and
make the build-stamp/date metadata regular across all 32 components.

Reference pattern (`grasshopper/components/CRC_ColorCalculator`):

- Component `name` = descriptive PascalCase; component `nickname` = short UI alias. **(already uniform — no change needed)**
- Every **input** param has a descriptive **camelCase `name`** + a short **`nickname`**.
- `componentVersion` + `date` present in metadata.
- After the `_bases` sys.path block, a top-level stamp:
  ```python
  try:
      ghenv.Component.Message = "v{{component_version}}-{{date}}"
  except Exception:
      pass
  ```
- SDK/advanced components also set `self.Message = "v{{component_version}}-{{date}}"` inside `RunScript`.

## Decisions (locked)

1. **Inputs:** full camelCase `name` + a `nickname` on **every** input. snake_case → camelCase
   (`column_names` → `columnNames`), terse → descriptive (`p` → `polylines`).
2. **Outputs:** camelCase `name`, **no nickname** (rename only; drop any existing output nickname).
3. **`CString` / `CToggle`:** names kept **verbatim** (documented wire protocol) — add a nickname only.
4. **Token reality:** the componentizer substitutes `{{component_version}}` from `metadata.componentVersion`
   and `{{date}}` from the **build date** (`datetime.now()`), *not* the metadata `date` field. The
   `Component.Message` therefore always reflects build date — this is expected, not a bug.

## Hard rule when renaming an INPUT

Renaming an input `name` **requires** matching `code.py` edits — the input name is the variable
GH injects. For SDK components edit both the `RunScript(self, ...)` signature and every body
reference; for procedural components edit every reference to the injected global. Output renames:
rename the local return variable too, for readability (functionally positional).

---

## Global fixes (apply regardless of naming)

### G1 — Missing `date` metadata (add `"date": "2026-06-16"`)
Histogram, Heatmap, ScatterPlot, LinePlot, NurbsToSVG, PolylineToSVG, TextToSVG.

### G2 — Missing top-level stamp block (insert after the `_bases` for-loop)
Same 7 as G1. Insert exactly:
```python
try:
    ghenv.Component.Message = "v{{component_version}}-{{date}}"
except Exception:
    pass
```

### G3 — `self.Message` missing `-{{date}}`
Every SDK component except ColorCalculator currently sets `self.Message = "v{{component_version}}"`.
Change to `self.Message = "v{{component_version}}-{{date}}"`:
CircleToSVG, CurveDisplay, Histogram, Heatmap, ScatterPlot, LinePlot, NurbsToSVG, PolylineToSVG, TextToSVG.

### G4 — Date bugs
- `CRC_ConnectionString/metadata.json`: **duplicate `"date"` key** (two lines). Delete one.
- `CRC_CircleToSVG/metadata.json`: `"2024-06-16"` → `"2026-06-16"`.
- `CRC_CurveDisplay/metadata.json`: `"2024-06-16"` → `"2026-06-16"`.

### G5 — Component-nickname fixes
- `CRC_SQLComposer`: nickname `"SQLComp.py"` → `"SQLComp"` (drop stray `.py`).
- `CRC_SaveSVG`: nickname `"SaveSVG"` (= name) → `"Save"`.

---

## Per-component changes

Legend: `old → newName | nick` for inputs; `old → newName` for outputs.
"keep" = already conformant. Names already camelCase needing only a nickname are shown `name | nick`.

### 01.Modeling

**CRC_BuildingMeshes**
- Inputs: `buildingFootprints | fp` (fix nickname bug: was `BdgMsh`), `buildingHeights | h` (was `BdgH`)
- Outputs: `out` keep · `GrdF → groundFaces` · `LatF → lateralFaces` · `RftF → rooftopFaces`
- code.py: rename output vars.

**CRC_IdentifyDuplicatePolylines**
- Inputs: `p → polylines | pl`
- Outputs: `i → duplicateIndices` · `report` keep
- code.py: rename `p` and `i`.

**CRC_OffsetPython**
- Inputs: `Crv → curves | crv`, `Dist → distances | dist`, `CStyle → cornerStyle | cs`
- Outputs: `out` keep · `OffCrv → offsetCurves`
- code.py: rename all four.

**CRC_PointInsidePolygon**
- Inputs: `pol → polygon | pol`
- Outputs: `pt → interiorPoint` · `report` keep
- code.py: rename `pol`, `pt`.

**CRC_SortByContainer** (inputs already conformant)
- Inputs: `containers | C` keep, `points | P` keep
- Outputs: `indices` keep name, **drop nickname `i`** · `report` keep

**CRC_ColorCalculator** (reference — inputs already done; normalize outputs to Decision 2)
- Inputs: no change.
- Outputs: `out` keep · `col → colors` · `leg_geo → legendGeo` · `txt_loc → textLocations` ·
  `txt_con → textContents` · `txt_siz → textSizes` · `stats` keep · `report` keep
- code.py: rename the return-tuple vars (`col_out`, `leg_geo`, `txt_loc`, `txt_con`, `txt_siz`).

### 02.Queries (every comp: `CString | cs`, `CToggle | tog`)

Shared input nicknames: `schema | sch`, `table | tbl`, `column | col`, `Cx | cx`, `Cy | cy`,
`SRID → srid | srid`, `spatial_filter → spatialFilter | flt`, `function → sqlFilter | fn`,
`N → nullReplacement | N`, `column_names → columnNames | cols`, `column_types → columnTypes | types`,
`values | vals`, `id_values → idValues | ids`, `replace_table → replaceTable | rep`,
`geometry | geo`, `srid | srid`.

**CRC_QuerySchemaNames** — Inputs: CString, CToggle. Outputs: `schemas`, `report`, `queries` keep.

**CRC_QueryTableNames** — Inputs: CString, CToggle, `schema`. Outputs keep (`tables`, `report`, `queries`).

**CRC_QueryColumnNames** — Inputs: CString, CToggle, `schema`, `table`. Outputs keep (`columns`, `types`, `report`, `queries`).

**CRC_QueryValues** — Inputs: CString, CToggle, `schema`, `table`, `column`, `N → nullReplacement | N`.
Outputs keep (`rows`, `columns`, `report`, `queries`).

**CRC_GeometryEntities** — Inputs: CString, CToggle, `schema`, `table`, `Cx`, `Cy`.
Outputs: `geometry` keep · `pk → primaryKeys` · `report`, `queries` keep.

**CRC_GeometriesWithSpatialFilter** — Inputs: CString, CToggle, `schema`, `table`,
`spatial_filter → spatialFilter`, `SRID → srid`, `function → sqlFilter`, `Cx`, `Cy`.
Outputs: `geometry` keep · `pk → primaryKeys` · `report`, `queries` keep.

**CRC_ValuesWithSpatialFilter** — Inputs: CString, CToggle, `schema`, `table`, `column`,
`N → nullReplacement`, `spatial_filter → spatialFilter`, `SRID → srid`, `function → sqlFilter`, `Cx`, `Cy`.
Outputs: `values` keep · `pk → primaryKeys` · `report`, `queries` keep.

**CRC_CreateTable** — Inputs: CString, CToggle, `schema`, `table`, `column_names → columnNames`,
`column_types → columnTypes`, `values`, `id_values → idValues`, `replace_table → replaceTable`.
Outputs: `affected` keep · `report` keep.

**CRC_CreateShapefile** — Inputs: CString, CToggle, `schema`, `table`, `column_names → columnNames`,
`column_types → columnTypes`, `values`, `id_values → idValues`, `geometry`, `srid`, `Cx`, `Cy`,
`replace_table → replaceTable`.
Outputs: `affected` keep · `report` keep.

> All 02.Queries code.py: rename the snake_case input vars (`column_names`, `column_types`,
> `id_values`, `replace_table`, `spatial_filter`, `function`) and `N`/`SRID` references in the body.

### 03.Utilities

**CRC_ConnectionString** — Inputs: `database | db`, `port | port`, `CToggle | tog`.
Outputs keep (`CString`, `ok`, `report`). **+ G4: delete duplicate `date` key.**

**CRC_FindCorrectionParameters** — Inputs: CString, CToggle, `Schema → schema | sch`,
`Table → table | tbl`, `Column → column | col`, `Value → value | val`.
Outputs keep (`Cx`, `Cy`, `report`). code.py: rename `Schema/Table/Column/Value`.

**CRC_SQLComposer** — Inputs: `sql | sql`, `var → variables | var`, `val → values | val`.
Outputs: `out` keep · `stmt → statement` · `report` keep. **+ G5 nickname.** code.py: rename `var`, `val`, `stmt`.

**CRC_RunQuery** — Inputs: CString, CToggle, `sql | sql`. Outputs keep (`rows`, `columns`, `report`).

**CRC_RunCommand** — Inputs: CString, CToggle, `sql | sql`. Outputs: `report` (verify whether an
`affected` output exists; if so keep). 

**CRC_GrasshopperGeometryToWKT** — Inputs: `geom → geometry | geo`.
Outputs: `WKT` keep (acronym) · `report` keep. code.py: rename `geom`.

**CRC_WKTtoGrasshopperGeometry** — Inputs: `WKT_geom → wktGeometry | wkt`.
Outputs: `geom → geometry` · `report` keep. code.py: rename `WKT_geom`, `geom`.

### 04.Dataviz

**CRC_CurveDisplay** — Inputs: `Curve → curves | crv`, `Colour → colours | col`,
`Width → widths | w`, `Dash → dashes | dash`. No outputs. **+ G3** (self.Message). **+ G4** (date 2024→2026).
code.py: rename all four in RunScript signature + body.

**CRC_PolylineToSVG** — Inputs: `p → polylines | pl`, `sc → strokeColor | sc`, `sw → strokeWidth | sw`,
`f → fillColor | f`, `canvas | canvas`, `dash → dashPattern | dash`.
Outputs keep (`svgCode`, `report`). **+ G1, G2, G3.** code.py: rename inputs in RunScript.

**CRC_CircleToSVG** (inputs already conformant) — no input/output rename. **+ G3, G4 (date 2024→2026).**

**CRC_NurbsToSVG** — Inputs: `n → nurbsCurves | n`, `s → sampleCount | s`, `sc → strokeColor | sc`,
`sw → strokeWidth | sw`, `f → fillColor | f`, `canvas | canvas`.
Outputs keep. **+ G1, G2, G3.** code.py: rename inputs.

**CRC_TextToSVG** — Inputs: `t → texts | t`, `pt → points | pt`, `ff → fontFamily | ff`,
`fs → fontSize | fs`, `fC → fillColor | fc`, `canvas | canvas`, `j → justification | j`.
Outputs keep. **+ G1, G2, G3.** code.py: rename inputs.

**CRC_Histogram** (inputs already camelCase — add nicknames only, no code change) **+ G1, G2, G3.**
Nicknames: `canvasRect|cnv`, `dataValues|val`, `numBins|bins`, `numXLabels|nxL`, `numYLabels|nyL`,
`decimals|dec`, `axisExtension|axE`, `labelDist|lblD`, `drawGridY|gY`, `barOutlineWidth|barW`,
`axisLineWidth|axW`, `gridLineWidth|grdW`. Outputs keep (`svgCode`, `report`).

**CRC_ScatterPlot** (add nicknames only) **+ G1, G2, G3.**
Nicknames: `canvasRect|cnv`, `xValues|x`, `yValues|y`, `dotRadius|r`, `numXLabels|nxL`, `numYLabels|nyL`,
`decimals|dec`, `axisExtension|axE`, `labelDist|lblD`, `marginLeft|mL`, `marginBottom|mB`,
`drawGridX|gX`, `drawGridY|gY`, `showLegend|leg`, `colorValues|cVal`, `gradientColors|grad`,
`numLegendSteps|legN`, `legendBarWidth|legW`, `legendDist|legD`, `legendLabelDist|legLD`,
`legendOrientation|legO`, `dotOutlineWidth|dotW`, `axisLineWidth|axW`, `gridLineWidth|grdW`.
Outputs keep.

**CRC_LinePlot** (add nicknames only) **+ G1, G2, G3.**
Nicknames: `canvasRect|cnv`, `xValues|x`, `yValues|y`, `numXLabels|nxL`, `numYLabels|nyL`,
`decimals|dec`, `axisExtension|axE`, `labelDist|lblD`, `marginLeft|mL`, `marginBottom|mB`,
`drawGridX|gX`, `drawGridY|gY`, `lineWidth|lnW`, `axisLineWidth|axW`, `gridLineWidth|grdW`.
Outputs keep.

**CRC_Heatmap** (add nicknames only) **+ G1, G2, G3.**
Nicknames: `canvasRect|cnv`, `dataMatrix|mtx`, `gradientColors|grad`, `rowLabels|rLbl`, `colLabels|cLbl`,
`showCellValues|cVal`, `decimals|dec`, `legendSteps|legN`, `labelDist|lblD`, `legendBarW|legW`,
`legendDist|legD`, `legendLabelDist|legLD`, `legendOrientation|legO`, `showLegend|leg`,
`cellOutlineWidth|cellW`, `legendCellOutlineWidth|lcW`. Outputs keep.

**CRC_SaveSVG** — Inputs: `svg_code → svgCode | svg`, `canvas | canvas`, `file_path → filePath | path`,
`save_flag → saveFlag | save`. Outputs: `path` keep · `svg_doc → svgDoc` · `report` keep.
**+ G5 nickname (`SaveSVG → Save`).** code.py: rename `svg_code`, `file_path`, `save_flag`, `svg_doc`.

---

## Execution strategy (delegate to sonnet caveman-ultra subagents)

Batch by subcategory so each subagent owns an isolated set of folders (no shared files):

1. **Agent A — 01.Modeling** (6 comps): BuildingMeshes, IdentifyDuplicatePolylines, OffsetPython,
   PointInsidePolygon, SortByContainer, ColorCalculator(outputs only).
2. **Agent B — 02.Queries** (9 comps): all DB comps. Highest code churn (snake_case input renames).
3. **Agent C — 03.Utilities** (7 comps): ConnectionString, FindCorrectionParameters, SQLComposer,
   RunQuery, RunCommand, GrasshopperGeometryToWKT, WKTtoGrasshopperGeometry.
4. **Agent D — 04.Dataviz** (10 comps): the 7 SDK fixes (G1/G2/G3) + nickname tables + SVG input renames + SaveSVG.

Each agent edits only `metadata.json` + `code.py` per the tables above. No `.ghuser` hand-editing.

## Verify

1. `conda run -n carcara pytest tests/ -v` — crc_modules unaffected; must stay green.
2. JSON validity: each `metadata.json` parses (no trailing/duplicate keys — esp. ConnectionString).
3. Grep audit:
   - every input has a `nickname`;
   - no output has a `nickname`;
   - all 32 metadata have `date`;
   - all 32 code.py have the top-level `ghenv.Component.Message = "v{{component_version}}-{{date}}"` block;
   - all SDK `self.Message` end in `-{{date}}`.
4. `conda run -n carcara python build_userobjects.py` — all 32 `.ghuser` rebuild without per-component failure.
5. Spot-check one rebuilt component in Rhino 8 (input nicknames + `Component.Message` stamp render).

## Risks

- Renaming any param breaks wires in previously-saved `.gh` files. Acceptable pre-release (0.5);
  `.gh` not committed.
- 02.Queries has the most code churn (snake_case → camelCase across all DB wrappers). Review that diff hardest.
