<p align="center">
  <img src="img/_logo_carcará.png" width="300" alt="Carcará logo">
</p>

<h1 align="center">Carcará</h1>

<p align="center">
A Python-based Grasshopper plugin for <b>Rhino 8</b> that bridges PostGIS spatial databases with parametric design workflows — query, visualize, and export geospatial data directly from the Grasshopper canvas.
</p>

***

## Background

City Information Modeling is not simply BIM applied at a larger scale — the shift from building to city changes the complexity of the system, the nature of the relationships between elements, and therefore the representation model it requires. Following Beirão (2012) and Duarte et al. (2012), we adopt the approach of an **integrative environment** in which a spatial Relational Database Management System (RDBMS) acts as the interoperability hub between design, analysis, and visualization platforms — GIS tools, statistical modelers, web applications, and parametric modelers — without requiring file-format conversions at each step. Rhino 8 / Grasshopper is one of those platforms, and it has no native access to relational databases. Carcará is the bridge.

> This framework was formally developed and published as a peer-reviewed paper awarded the **SIGraDi Research Innovation Award 2022**:
> Moreira, E. *The Use of Visual Programming Interface for Structuring a Generic Digital Framework in a City Information Modeling Workflow*. In: *Proceedings of SIGraDi 2022*. Blucher, 2022.
> [→ Read the full paper](https://www.proceedings.blucher.com.br/article-details/the-use-of-visual-programming-interface-for-structuring-a-generic-digital-framework-in-a-city-information-modeling-workflow-38530)

***

## What Carcará Does

Carcará adds a **Carcará** ribbon to Grasshopper with **32 components** across four subcategories. All domain logic lives in a pure-Python package (`crc_modules`) that is importable and testable outside Rhino; the Grasshopper components are thin wrappers.

| Subcategory | Count | Components |
|---|---|---|
| **01.Modeling** | 6 | BuildingMeshes, OffsetPython, PointInsidePolygon, SortByContainer, IdentifyDuplicatePolylines, ColorCalculator |
| **02.Queries** | 9 | QuerySchemaNames, QueryTableNames, QueryColumnNames, QueryValues, GeometryEntities, GeometriesWithSpatialFilter, ValuesWithSpatialFilter, CreateTable, CreateGeometryTable |
| **03.Utilities** | 7 | ConnectionString, FindCorrectionParameters, SQLComposer, RunQuery, RunCommand, GrasshopperGeometryToWKT, WKTtoGrasshopperGeometry |
| **04.Dataviz** | 10 | CurveDisplay, PolylineToSVG, CircleToSVG, NurbsToSVG, TextToSVG, Histogram, ScatterPlot, LinePlot, Heatmap, SaveSVG |

Three design decisions cut across all subcategories:

- **Connection model** — `CRC_ConnectionString` builds a single `CString` (libpq conninfo) that travels on a canvas wire into every DB component, alongside a `CToggle` trigger. One wire, one credential, no repetition.
- **Coordinate correction** — projected coordinates (UTM / SIRGAS) are shifted by a false origin `(Cx, Cy)` **inside SQL** (`ST_Translate`) so full-magnitude values never reach Rhino and lose floating-point precision. `Cx`/`Cy` are passed as numeric text, never parsed to float.
- **Dataviz** — charts are built as real Rhino geometry (visible in the viewport) **and** exported as fully-configured SVG via the `CRC_SaveSVG` component.

→ [Full component reference](COMPONENTS.md)

***

## Install

> **Prerequisites:** Rhino 8 (Windows 10/11 primary, macOS secondary) and an active internet connection during installation. No git, no pip, no manual file copying.

**1. Download the installer**
[**`carcara_setup_rev00.gh`**](https://github.com/eugeniomoreira-iaud/carcara/raw/master/build/installer/carcara_setup_rev00.gh) — a small Grasshopper definition that bootstraps the whole plugin.

**2. Run it**
Drag `carcara_setup_rev00.gh` onto the Grasshopper canvas. Set the `install` Boolean Toggle to **True**. The installer downloads the latest release, copies `release/` → `UserObjects/carcara/`, version-checks against the installed `version.txt`, keeps a timestamped backup, and rolls back automatically on failure. Third-party Python dependencies (`psycopg2`, `shapely`) install automatically on first use via Rhino 8's `# r:` package directive.

**3. Restart Grasshopper**
The **Carcará** ribbon appears with all 32 components ready to use.

***

## Quick Start

A minimal end-to-end workflow:

1. Drop `CRC_ConnectionString` on the canvas. Set `database`, `port`, then toggle `CToggle` to **True** to open the credentials dialog. The output `CString` wire carries the connection to every downstream component.
2. Drop `CRC_GeometryEntities`. Wire `CString` in. Set `schema` and `table`, optionally use `CRC_FindCorrectionParameters` to get `Cx`/`Cy` from a reference feature. Toggle to **True**.
3. Geometry draws in the Rhino viewport. Wire `primaryKeys` into `CRC_QueryValues` (same connection string) to pull attribute columns in parallel.

> For spatial filtering, replace step 2 with `CRC_GeometriesWithSpatialFilter` and draw a boundary polygon on the canvas to use as the filter geometry.

***

## Architecture

```
<repo>/                                 ← git repo root
├── release/                            ← THE deployable folder (copied as-is to UserObjects)
│   ├── crc_modules/                    ← pure-Python package = the code (no Rhino imports)
│   │   ├── db/                         ← connection, query, spatial_query, writer
│   │   ├── geometry/                   ← wkt, polylabel, containment, duplicates, dash
│   │   ├── rhino/                      ← Rhino-only modules (excluded from pytest)
│   │   ├── svg/                        ← export, save
│   │   ├── utils/                      ← color, sql_composer, correction
│   │   └── viz/                        ← histogram, scatter, lineplot, heatmap
│   ├── userobjects/                    ← all built .ghuser files (committed; shipped to users)
│   └── version.txt                     ← generated by make_release.py; installer reads this
│
├── build/
│   ├── components/                     ← component source bundles (metadata.json, code.py, icon.png)
│   ├── icons/                          ← source artwork
│   └── installer/                      ← bootstrap installers (delivered as .gh)
│
├── tests/                              ← pytest (DB mocked; no live database needed)
├── tools/                              ← dev utilities (build_userobjects.py, make_release.py, deploy.ps1)
├── vendor/                             ← componentizer + GH_IO.dll (build toolchain)
├── legacy-0.4.0-beta.2/                ← read-only reference of the original plugin
├── pyproject.toml  requirements.txt
└── CLAUDE.md  README.md  COMPONENTS.md
```

The source package lives *inside* the deployable folder (`release/crc_modules/`). The committed `release/` folder **is** what users download. Components import `from crc_modules.db.connection import ...`; the unique package name avoids clashing with a generic `import modules` in the Rhino session.

***

## Development

Full spec, component inventory, API contracts, and contribution rules: [`CLAUDE.md`](CLAUDE.md).
Per-phase implementation plans: [`implementation-plans/`](implementation-plans/).

```powershell
# install dev deps
pip install -r requirements.txt

# run tests (DB mocked; no live database needed)
conda run -n carcara python -m pytest tests/ -q

# build .ghuser files and deploy to local UserObjects
conda run -n carcara python tools/build_userobjects.py
powershell -ExecutionPolicy Bypass -File tools\deploy.ps1
```

> On Windows PowerShell, prefix Python commands with `conda run -n carcara` — the bare `python` may resolve to the Windows Store stub unless the environment is activated.

`.ghuser` files are binary `GH_Archive` artifacts produced by the componentizer (`vendor/componentizer/`); never hand-edit them. Restart Grasshopper after deploying.

***

## Requirements

| | |
|---|---|
| Rhino | 8 |
| Python | CPython 3.11+ (Rhino 8 ScriptEditor) |
| Database | PostgreSQL 14+ with PostGIS 3+ |
| DB driver | `psycopg2` (no ODBC) |
| Runtime deps | `psycopg2`, `shapely`, `svgwrite`, `matplotlib` |
| Build/dev deps | `pythonnet`, `pytest`, `python-dotenv`, `requests` |
| OS | Windows 10/11 (primary), macOS (secondary) |

***

## Acknowledgements

Carcará's build pipeline draws on patterns from two upstream open-source projects. The `.ghuser` build step uses the `metadata.json` + `code.py` + `icon.png` bundle layout pioneered by **COMPAS** in [`compas-actions.ghpython_components`](https://github.com/compas-dev/compas-actions.ghpython_components); those componentizer scripts are vendored under [`vendor/componentizer/`](vendor/componentizer/). The SDK-mode viewport-preview pattern used by the Dataviz components was inspired by [**Ladybug Tools**](https://github.com/ladybug-tools) (structural conventions adopted, not code).

***

## License & Citation

Carcará is free software under the **GNU General Public License v3.0 or later** ([GPL-3.0-or-later](LICENSE)). Copyright © 2026 Eugenio Moreira. If you distribute Carcará or any derivative work, you must release it under the same GPLv3 terms and make the complete source available.

If you use Carcará in academic work, please cite the original paper:

```bibtex
@article{Alexandrino20144,
    title="The use of visual programming interface for structuring a generic digital framework in a city information modeling workflow",
    journal="Blucher Design Proceedings",
    volume="11",
    number="2",
    pages="675 - 686",
    year="2023",
    note="",
    issn="23186968",
    doi="http://dx.doi.org/10.5151/sigradi2022-sigradi2022_200",
    url="www.proceedings.blucher.com.br/article-details/the-use-of-visual-programming-interface-for-structuring-a-generic-digital-framework-in-a-city-information-modeling-workflow-38530",
    author="João Victor Mota Alexandrino", "Vinícius Fernandes Muniz", "Daniel Cardoso", "Eugênio Moreira",
    keywords="None",
}

```