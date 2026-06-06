# Architecture & Design Decisions

This document explains the key technical choices made in the GeoReach platform and the rationale behind them.

## Table of Contents

- [Coordinate Reference Systems](#coordinate-reference-systems)
- [H3 Hexagonal Grid System](#h3-hexagonal-grid-system)
- [Accessibility Analysis Approach](#accessibility-analysis-approach)
- [Database & Spatial Engine](#database--spatial-engine)
- [Data Pipeline Architecture](#data-pipeline-architecture)
- [Output Formats](#output-formats)
- [Web Mapping Stack](#web-mapping-stack)

---

## Coordinate Reference Systems

### Analysis CRS: EPSG:32735 (WGS 84 / UTM Zone 35S)

**Choice:** All spatial analysis operations are performed in UTM Zone 35S.

**Rationale:**
- **Metric measurements**: UTM provides accurate distance and area calculations in meters, essential for accessibility analysis and population density calculations
- **Geographic appropriateness**: Zone 35S covers the study area (Fizi Territory, DRC) at approximately 27-28°E longitude, minimizing projection distortion
- **Reduced distortion**: Within a UTM zone, distance and area distortions are minimal (<0.1% near the central meridian)
- **Industry standard**: UTM is widely used in humanitarian GIS and field operations in East Africa

**Trade-offs:**
- Not suitable for global analysis (limited to ~6° longitude bands)
- Requires reprojection from source data (typically WGS 84)
- Different zones needed for multi-region analysis

### Storage/Display CRS: EPSG:4326 (WGS 84)

**Choice:** All outputs and web map data use WGS 84 geographic coordinates.

**Rationale:**
- **Web mapping standard**: All web mapping libraries (MapLibre, Leaflet, Google Maps) expect WGS 84
- **Interoperability**: GeoJSON, PMTiles, and most GIS tools default to WGS 84
- **Data exchange**: Simplifies sharing with other systems and organizations
- **No tile reprojection**: Web Mercator (EPSG:3857) tiles can be generated directly from WGS 84

**Implementation:**
```python
# Analysis in UTM
gdf = gdf.to_crs("EPSG:32735")
distances = gdf.geometry.distance(facilities)

# Export in WGS 84
gdf.to_crs("EPSG:4326").to_file("output.geojson")
```

---

## H3 Hexagonal Grid System

### Resolution 6 (~36 km² per hex)

**Choice:** H3 resolution 6 is used for the demo, with configurable resolution for production.

**Rationale:**

**Why Hexagons (vs. squares)?**
- **Uniform neighbor distance**: Every hexagon has 6 neighbors at equal distance from the center
- **No edge effects**: Hexagons tile perfectly without orientation bias
- **Better sampling**: Hexagons approximate circles better than squares, reducing sampling artifacts
- **Spatial statistics**: Preferred for spatial aggregation in epidemiology and accessibility studies

**Why H3 specifically?**
- **Hierarchical**: Parent-child relationships enable multi-scale analysis
- **Global standard**: Used by Uber, Meta, and humanitarian organizations
- **Efficient indexing**: String-based IDs enable fast spatial joins
- **Open source**: Well-maintained library with Python bindings

**Why Resolution 6?**
- **Demo performance**: ~500 hexagons cover the study area (vs. ~100,000 at resolution 8)
- **Meaningful scale**: 36 km² hexagons align with district-level planning
- **Visual clarity**: Hexagons are large enough to see on the web map
- **Computational efficiency**: Zonal statistics complete in <1 minute

**Production Recommendation:**
- **Resolution 8** (~0.74 km² per hex): Suitable for village-level analysis
- **Resolution 9** (~0.10 km² per hex): For detailed urban planning
- **Resolution 7** (~5.16 km² per hex): Balance between detail and performance

**Configuration:**
```yaml
h3:
  resolution: 6  # Change to 8 for production
```

---

## Accessibility Analysis Approach

### Euclidean Distance (Not Network Routing)

**Choice:** Accessibility is measured using straight-line (Euclidean) distance to the nearest health facility, not road network routing.

**Rationale:**

**Why Euclidean Distance?**
- **Data availability**: Road network data for rural DRC is incomplete or outdated
- **Computational efficiency**: Distance calculations are O(n×m) vs. O(n×m×log(m)) for routing
- **Reasonable proxy**: In rural areas with limited infrastructure, straight-line distance correlates with travel time
- **Reproducibility**: No dependency on external routing services or complex network topology
- **Demo simplicity**: Demonstrates spatial analysis concepts without infrastructure complexity

**Why Not pgRouting?**
- **Missing road data**: OSM road coverage in Fizi Territory is sparse and unverified
- **Network quality**: Rural roads may not be passable year-round (seasonal flooding)
- **Complexity**: Requires road network topology, turn restrictions, and speed profiles
- **Scope**: This demo focuses on exposure × accessibility, not detailed routing

**When to Use pgRouting:**
- Urban areas with complete road networks
- Multi-modal transport analysis (walking, driving, public transit)
- Time-based accessibility (isochrones)
- Scenarios where road infrastructure is a key variable

**Current Implementation:**
```python
# Calculate distance to nearest facility
facilities_utm = facilities.to_crs(config.crs.analysis)
hexes_utm = hexes.to_crs(config.crs.analysis)

for idx, hex_row in hexes_utm.iterrows():
    distances = facilities_utm.distance(hex_row.geometry.centroid)
    nearest_km = distances.min() / 1000  # Convert to km
```

**Future Enhancement:**
- Add optional pgRouting support for areas with good road data
- Implement travel time estimation using terrain and road quality factors
- Use satellite imagery to validate road accessibility

---

## Database & Spatial Engine

### PostGIS 3.4 on PostgreSQL 16

**Choice:** PostGIS is the spatial database engine for all analysis.

**Rationale:**

**Why PostGIS?**
- **Industry standard**: De facto standard for open-source spatial databases
- **Rich spatial functions**: 400+ spatial operations (ST_Distance, ST_Intersects, ST_Buffer, etc.)
- **GIST indexes**: Spatial indexing for fast queries on millions of geometries
- **SQL interface**: Familiar query language for data analysts
- **Proven scalability**: Handles datasets from KB to TB

**Why Not Alternatives?**
- **SpatiaLite**: Limited concurrency, no server mode
- **DuckDB Spatial**: Newer, less mature ecosystem
- **MongoDB Geospatial**: NoSQL trade-offs, less spatial functionality
- **BigQuery GIS**: Cloud-only, cost implications

**Key Features Used:**
- `ST_Distance`: Accessibility calculations
- `ST_Intersects`: Spatial joins between hexagons and admin boundaries
- `ST_Centroid`: Hex center points for distance calculations
- `GIST indexes`: Fast spatial queries on 500+ hexagons

**Performance:**
- ~30 seconds for full pipeline (ingestion → analysis → export)
- Spatial index creation: <1 second for 500 hexagons
- Distance calculations: <5 seconds for 500 hexagons × 15 facilities

---

## Data Pipeline Architecture

### Sequential Python Modules (Not Airflow/Prefect)

**Choice:** The pipeline is a sequential Python CLI with explicit module dependencies.

**Rationale:**

**Why Sequential?**
- **Simplicity**: Easy to understand, debug, and modify
- **Reproducibility**: Same input → same output, every time
- **Dependency clarity**: Explicit order (ingest → load → grid → exposure → accessibility → priority → export)
- **Demo-appropriate**: No need for scheduling, retries, or distributed execution

**Why Not Workflow Orchestration?**
- **Airflow/Prefect**: Overkill for a single-run demo pipeline
- **Complexity overhead**: DAG definition, scheduler setup, monitoring
- **Local execution**: No need for distributed task execution
- **Learning curve**: Adds complexity without clear benefit for this use case

**Pipeline Stages:**
```
1. ingest    → Download/generate raw data
2. load      → Load data into PostGIS
3. grid      → Generate H3 hexagonal grid
4. exposure  → Calculate flood exposure (zonal stats)
5. access    → Calculate health facility accessibility
6. priority  → Compute composite priority index
7. export    → Generate GeoParquet, COG, STAC outputs
8. tiles     → Generate PMTiles for web map (optional)
```

**When to Use Orchestration:**
- Production pipelines with scheduling requirements
- Multi-step pipelines with conditional branching
- Distributed processing across multiple machines
- Pipelines requiring monitoring and alerting

---

## Output Formats

### Cloud-Native Geospatial Formats

**Choice:** Outputs use modern, cloud-optimized formats (GeoParquet, COG, PMTiles, STAC).

**Rationale:**

**GeoParquet (Vector Data)**
- **Columnar storage**: 10-100× smaller than Shapefile/GeoJSON
- **Fast queries**: Predicate pushdown for filtering
- **Type safety**: Proper data types (vs. Shapefile limitations)
- **Cloud-ready**: Works with S3, GCS, Azure Blob Storage

**Cloud-Optimized GeoTIFF (Raster Data)**
- **HTTP range requests**: Read only the tiles you need
- **Internal tiling**: 256×256 or 512×512 pixel tiles
- **Overviews**: Pre-computed pyramids for fast zooming
- **Compression**: LZW or DEFLATE for smaller files

**PMTiles (Vector Tiles)**
- **Single file**: No directory of thousands of tiles
- **HTTP range requests**: Serverless tile serving
- **Hilbert curve**: Spatial locality for efficient caching
- **Open format**: No vendor lock-in

**STAC (Metadata Catalog)**
- **Discoverability**: Machine-readable metadata
- **Interoperability**: Works with QGIS, ArcGIS, Python
- **Standardized**: JSON-based, widely adopted
- **Extensible**: Custom properties for domain-specific metadata

**Why Not Legacy Formats?**
- **Shapefile**: 2GB limit, no UTF-8 support, 10-character field names
- **GeoTIFF (non-COG)**: Must download entire file to read a small area
- **MBTiles**: SQLite-based, not cloud-optimized
- **Proprietary formats**: Vendor lock-in, licensing issues

---

## Web Mapping Stack

### MapLibre GL JS (Not Leaflet)

**Choice:** MapLibre GL JS is used for the interactive web map.

**Rationale:**

**Why MapLibre?**
- **Vector tiles**: Client-side rendering, smooth zooming
- **WebGL performance**: GPU-accelerated rendering
- **Modern styling**: Mapbox Style Spec for declarative styling
- **Open source**: Fork of Mapbox GL JS v1 (before proprietary license change)
- **Active development**: Maintained by the MapLibre community

**Why Not Leaflet?**
- **Raster-first**: Designed for raster tiles, vector support is limited
- **No WebGL**: Canvas-based rendering, slower for large datasets
- **Styling limitations**: Programmatic styling, not declarative
- **Use case**: Leaflet is better for simple maps with markers/polygons

**Why Not OpenLayers?**
- **Complexity**: More features, steeper learning curve
- **Bundle size**: Larger JavaScript payload
- **Use case**: OpenLayers is better for complex GIS applications

**Features Used:**
- **GeoJSON sources**: Load hexagons and facilities
- **Data-driven styling**: Color hexagons by priority score
- **Popups**: Display hex statistics on click
- **Layer toggles**: Show/hide different analysis layers
- **Responsive design**: Works on desktop and mobile

**Performance:**
- 500 hexagons render in <100ms
- Smooth panning and zooming at 60 FPS
- Client-side filtering and styling

---

## Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Analysis CRS** | EPSG:32735 (UTM 35S) | Metric measurements, low distortion |
| **Display CRS** | EPSG:4326 (WGS 84) | Web mapping standard, interoperability |
| **Spatial Grid** | H3 Resolution 6 | Demo performance, hierarchical, hexagonal benefits |
| **Accessibility** | Euclidean distance | Data availability, simplicity, reasonable proxy |
| **Database** | PostGIS 3.4 | Industry standard, rich spatial functions |
| **Pipeline** | Sequential Python CLI | Simplicity, reproducibility, clarity |
| **Vector Format** | GeoParquet | Cloud-native, columnar, fast queries |
| **Raster Format** | Cloud-Optimized GeoTIFF | HTTP range requests, internal tiling |
| **Tile Format** | PMTiles | Single file, serverless, open format |
| **Web Map** | MapLibre GL JS | Vector tiles, WebGL, open source |

---

## Production Considerations

When adapting this platform for production use, consider:

1. **H3 Resolution**: Increase to 8 or 9 for finer spatial detail
2. **Road Network**: Integrate pgRouting for areas with good OSM coverage
3. **Real Flood Data**: Replace synthetic flood layer with actual hazard maps
4. **Temporal Analysis**: Add time-series support for seasonal flooding
5. **Multi-Region**: Implement dynamic CRS selection based on study area
6. **Scalability**: Add workflow orchestration (Airflow) for large-scale processing
7. **API Layer**: Expose analysis results via REST API (FastAPI/PostgREST)
8. **Monitoring**: Add logging, metrics, and alerting for production pipelines

---

## References

- **H3**: https://h3geo.org/
- **PostGIS**: https://postgis.net/
- **MapLibre GL JS**: https://maplibre.org/
- **GeoParquet**: https://geoparquet.org/
- **Cloud-Optimized GeoTIFF**: https://www.cogeo.org/
- **PMTiles**: https://protomaps.com/docs/pmtiles
- **STAC**: https://stacspec.org/

---

**Last Updated:** June 2026  
**Author:** Junior Dieka  
**License:** MIT
