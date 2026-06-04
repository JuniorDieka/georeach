# Role
You are a senior GIS data engineer and geospatial software developer. Build a complete,
production-grade, portfolio-quality open-source project from scratch. The repository must
demonstrate real geospatial *engineering*: a spatial database, a reproducible raster+vector
ETL pipeline, spatial SQL, cloud-native geospatial outputs, and an interactive tiled web map
— not a Jupyter notebook run by hand. It will be evaluated by technical hiring managers in
2026, so prioritize reproducibility, correct CRS handling, clean architecture, tests, and a
polished README. It must run end-to-end on a small bundled subset with ONE command.

# Project
**Name:** GeoReach — Flood-Exposure & Service-Accessibility Geospatial Platform
**Context:** A fictional-but-realistic analysis for one province/territory of the Democratic
Republic of the Congo (use a real admin area for realism, e.g. a territory in South Kivu).
**Question it answers:** Which populated areas are both most exposed to flood hazard AND least
able to reach a health facility — i.e. where should interventions be prioritized?

# Core capabilities (the geospatial substance — this is what must be done well)
1. **Reproducible data ingestion** — scripted download + clip of open data for the study area:
   - Admin boundaries: humanitarian Common Operational Datasets (HDX/OCHA COD-AB) or GADM.
   - Population: a WorldPop population-count raster (treat as / convert to Cloud-Optimized GeoTIFF).
   - Buildings + roads + places: Overture Maps (read GeoParquet directly from the public cloud
     bucket, filtered to the study-area bbox) OR OSM via a HOT export — make the source pluggable.
   - Health facilities: healthsites.io / OSM / HDX.
   - Flood hazard: an open flood depth/extent raster as a COG (use a real open layer if available,
     otherwise generate a plausible synthetic hazard COG for the demo — clearly labeled as demo data).
   Cache downloads; everything reprojected to a consistent analysis CRS (document the choice;
   use an appropriate equal-area/metric CRS for area and distance math, store/display in EPSG:4326).
2. **Load into PostGIS** — well-structured schema with spatial indexes (GIST), an H3 hex grid
   covering the study area (use H3 at a documented resolution), and admin units. Use the H3
   Postgres extension if available, else generate hexes in Python (h3-py) and load them.
3. **Flood-exposure analysis** — zonal statistics: sum population raster within flood-hazard
   zones, aggregated per H3 hex and per admin unit. Output population exposed and % exposed.
4. **Service-accessibility analysis** — for each populated hex, compute distance/travel time to
   the nearest health facility. Implement at least one rigorous method: pgRouting over the road
   network (preferred) OR a cost-distance/friction-surface approach over the raster. Output an
   accessibility value + class per hex, and population beyond a threshold (e.g. >5 km or >60 min).
5. **Combined priority index** — a documented, transparent composite (e.g. normalized exposure ×
   normalized inaccessibility) that flags top-priority hexes/admin units. Keep the formula explicit
   and configurable; do not hide it.
6. **Cloud-native publishing** — export results as:
   - **GeoParquet** for the hex/admin result tables (vector),
   - **COG** for any derived raster surfaces,
   - **PMTiles** for the web map layers (generate with tippecanoe or equivalent),
   - a small **STAC** catalog/items describing the output assets.
7. **Interactive web map** — a MapLibre GL JS map (load PMTiles via the pmtiles protocol plugin)
   showing: a hex choropleth of exposed population, an accessibility layer, the flood-hazard
   overlay, health-facility points, and the priority layer — with layer toggles, a legend, a
   basemap, and click-to-inspect popups showing a hex's stats. This must NOT be Folium; it is a
   real web-GIS frontend.

# Required tech stack (do not substitute the core stack)
- **Spatial database:** PostgreSQL + PostGIS (+ pgRouting for network accessibility; H3 extension
  if available). Run it via Docker.
- **Processing / ETL (Python 3.11+):** GeoPandas, Shapely 2.x, pyogrio, rasterio + rioxarray,
  rasterstats (zonal stats), h3-py / h3ronpy, DuckDB with the spatial extension (use it to read
  Overture GeoParquet efficiently), GDAL/ogr2ogr, SQLAlchemy/psycopg for DB loads.
- **Pipeline orchestration:** a clean, staged CLI (Typer or Click) with discrete, idempotent
  stages (`ingest → load → grid → exposure → accessibility → priority → export → tiles`), wired
  together by a Makefile. (Optionally wrap in Prefect/Dagster, but the CLI+Make path must work.)
- **Tiling:** tippecanoe → PMTiles for vector layers; COG (gdal/rio-cogeo) for raster.
- **Frontend:** MapLibre GL JS + the PMTiles protocol, vanilla JS/HTML/CSS (no heavy framework),
  served statically.
- **Cloud-native formats:** GeoParquet, Cloud-Optimized GeoTIFF, PMTiles, STAC.

# Architecture & engineering best practices (mandatory)
- **Reproducibility first**: one command (`make demo` / docker compose) spins up PostGIS, runs the
  full pipeline on a small bundled subset (one territory), and serves the web map — with NO manual
  steps and NO huge mandatory downloads. Provide a separate `make full` path for real full data.
- **CRS discipline**: be explicit and correct about coordinate reference systems for every dataset;
  do area/distance math in a suitable projected CRS; store/serve in EPSG:4326. Document this.
- **Spatial SQL**: do real work in PostGIS (spatial joins, ST_Intersects/ST_Within, aggregation,
  GIST indexes). Show you can use the database, not just GeoPandas in memory.
- **Data validation & provenance**: validate geometries (fix invalid), check CRS, record source +
  license + download date for every dataset in a `DATA_SOURCES.md`. Respect data licenses.
- **Config**: a single config file for study-area bbox/admin code, H3 resolution, thresholds, CRS,
  and the priority-index weights. No hard-coded magic numbers scattered in code.
- **Code structure**: a clean Python package (`georeach/`) with separated modules
  (`ingest`, `db`, `grid`, `analysis`, `export`, `tiles`), typed functions, and docstrings.
- **Testing**: pytest with small geospatial fixtures — unit-test the zonal-stats aggregation,
  the accessibility computation, the H3 gridding, and the priority-index math on tiny known inputs.
- **Observability**: structured logging through the pipeline; each stage logs inputs/outputs/row
  counts so a reviewer can see what happened.
- **Containerization**: docker-compose bringing up PostGIS + the pipeline + a static web server for
  the map. Pin the GDAL/PostGIS image versions.
- **CI**: a GitHub Actions workflow that lints (ruff), type-checks, and runs the tests (spin up a
  PostGIS service container).
- **Quality**: ruff + black + mypy, pre-commit config, `.gitignore` that excludes large data/derived
  outputs.

# Deliverables
1. Full working source: the Python package, the staged CLI, SQL/migrations, and the MapLibre frontend.
2. A small bundled subset (one territory) so `make demo` produces real results and a live map fast.
3. Scripts to fetch the full datasets for the whole province (`make full`), with sources documented.
4. A top-level **README.md** with: the question and value proposition; an architecture/data-flow
   diagram (Mermaid) showing `Open data → ingest → PostGIS → exposure + accessibility analysis →
   priority index → GeoParquet / COG / PMTiles / STAC → MapLibre web map`; screenshots/GIF of the
   web map; exact setup (the one-command demo AND manual steps); the config reference; the CRS and
   methodology notes (how exposure, accessibility, and the priority index are computed); how to run
   tests; and a clear "What this demonstrates" section aimed at hiring managers (PostGIS + spatial
   SQL, raster×vector zonal stats, network/cost-distance accessibility, H3, cloud-native outputs,
   tiled web map, reproducible pipeline). State that any synthetic hazard layer is demo data.
5. `DATA_SOURCES.md` (sources + licenses + dates), `CONTRIBUTING.md`, an MIT `LICENSE`.
6. Meaningful, conventional commit history if you control commits.

# Working method
- First propose the repo file tree, the analysis CRS, the H3 resolution, and a short methodology
  rationale, then implement.
- Build incrementally and keep the pipeline runnable at each stage on the subset.
- Put the real engineering effort into the PostGIS spatial work, the zonal-stats and accessibility
  computations, and the cloud-native export + tiling — those are what separate this from a notebook.
- Where you make an assumption (CRS, thresholds, resolution), state it and pick a sensible default.
- Single most important success criterion: a reviewer can clone the repo, run one documented command,
  and end up looking at an interactive MapLibre map of flood-exposed, hard-to-reach priority hexes
  for a DRC territory — produced by a reproducible PostGIS pipeline with cloud-native outputs, on a
  bundled subset, with no manual steps.