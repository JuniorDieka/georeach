# Data Sources

This document provides detailed information about all data sources used in GeoReach, including provenance, licenses, access dates, and usage terms.

## Administrative Boundaries

**Source:** GADM (Database of Global Administrative Areas) v4.1  
**URL:** https://gadm.org/  
**License:** Free for non-commercial and academic use  
**Access Date:** 2026-06-04  
**Coverage:** Democratic Republic of the Congo, Admin Level 3 (Territories)  
**Format:** GeoPackage  
**CRS:** EPSG:4326 (WGS 84)  

**Citation:**
```
GADM. (2022). GADM database of Global Administrative Areas, version 4.1. 
Retrieved from https://gadm.org/
```

**Usage:** Study area boundary definition and spatial aggregation of results.

**License Terms:** Free for academic and non-commercial use. Commercial use requires a license. See https://gadm.org/license.html

---

## Population Data

**Source:** WorldPop  
**URL:** https://www.worldpop.org/  
**Dataset:** Democratic Republic of the Congo 1km Population (2020, UN-adjusted)  
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)  
**Access Date:** 2026-06-04  
**Resolution:** 1km × 1km  
**Format:** GeoTIFF  
**CRS:** EPSG:4326 (WGS 84)  

**Citation:**
```
WorldPop. (2020). Democratic Republic of the Congo 1km Population. 
University of Southampton. DOI: 10.5258/SOTON/WP00645
Retrieved from https://www.worldpop.org/
```

**Usage:** Population distribution for exposure analysis and priority weighting.

**License Terms:** Free to use with attribution under CC BY 4.0. See https://creativecommons.org/licenses/by/4.0/

---

## Buildings, Roads, and Places

**Source:** Overture Maps Foundation  
**URL:** https://overturemaps.org/  
**Release:** 2024-01-17-alpha.0  
**License:** CDLA Permissive 2.0  
**Access Date:** 2026-06-04  
**Themes Used:**
- Buildings (type=building)
- Transportation (type=segment)
- Places (type=place)

**Format:** GeoParquet (cloud-native)  
**CRS:** EPSG:4326 (WGS 84)  
**Access Method:** Direct query from AWS S3 public bucket via DuckDB  

**Citation:**
```
Overture Maps Foundation. (2024). Overture Maps Data Release 2024-01-17-alpha.0.
Retrieved from https://overturemaps.org/
```

**Usage:** Infrastructure context, road network for accessibility analysis (future), settlement patterns.

**License Terms:** Community Data License Agreement – Permissive, Version 2.0. Free to use, modify, and redistribute. See https://cdla.dev/permissive-2-0/

---

## Health Facilities

**Source:** healthsites.io  
**URL:** https://healthsites.io/  
**License:** Open Database License (ODbL) 1.0  
**Access Date:** 2026-06-04  
**Data Source:** OpenStreetMap + community contributions  
**Format:** GeoJSON (via API)  
**CRS:** EPSG:4326 (WGS 84)  

**Citation:**
```
Healthsites.io. (2024). Global Health Facilities Database.
Retrieved from https://healthsites.io/
```

**Usage:** Health facility locations for accessibility analysis.

**License Terms:** ODbL 1.0 — free to share, create, and adapt with attribution and share-alike. See https://opendatacommons.org/licenses/odbl/1-0/

---

## Flood Hazard Layer

⚠️ **IMPORTANT: SYNTHETIC DEMO DATA**

**Source:** Synthetically generated for portfolio demonstration  
**License:** N/A (not real data)  
**Method:** Random flood depth values (0-3m) generated with NumPy  
**Format:** GeoTIFF  
**CRS:** EPSG:4326 (WGS 84)  

**Usage:** Demonstration of flood exposure analysis methodology only.

**⚠️ WARNING:** This is NOT real flood data. For production use, replace with authoritative flood hazard data from:

### Recommended Real Flood Data Sources:

1. **Global Flood Database (GFD)**
   - URL: https://global-flood-database.cloudtostreet.ai/
   - License: CC BY 4.0
   - Coverage: Global satellite-observed floods

2. **Fathom Global Flood Maps**
   - URL: https://www.fathom.global/
   - License: Commercial (free for research/humanitarian)
   - Coverage: Global flood hazard at 30m resolution

3. **JRC Global Flood Hazard Maps**
   - URL: https://data.jrc.ec.europa.eu/collection/floods
   - License: CC BY 4.0
   - Coverage: Global return-period flood maps

4. **GFDRR Think Hazard**
   - URL: https://thinkhazard.org/
   - License: Open
   - Coverage: Country-level hazard information

5. **Aqueduct Floods (WRI)**
   - URL: https://www.wri.org/aqueduct/tools
   - License: CC BY 4.0
   - Coverage: Global riverine and coastal flood risk

---

## Data Processing Notes

### CRS Transformations
- All source data ingested in EPSG:4326
- Reprojected to EPSG:32735 (UTM 35S) for analysis (metric units)
- Outputs stored in EPSG:4326 for web mapping

### Geometry Validation
- All geometries validated with `is_valid` check
- Invalid geometries repaired with `buffer(0)` method
- Topology preserved during clipping and reprojection

### Temporal Coverage
- Population: 2020 (most recent available)
- Admin boundaries: 2022 (GADM 4.1)
- Overture Maps: 2024-01-17 release
- Health facilities: Current (API query date: 2026-06-04)

### Data Quality Notes
- **Population:** UN-adjusted estimates, 1km resolution may not capture micro-settlement patterns
- **Health facilities:** Completeness varies; may be incomplete in remote areas
- **Overture Maps:** Alpha release; data quality improving with each release
- **Flood hazard:** SYNTHETIC — not suitable for operational decision-making

---

## Attribution Requirements

When using GeoReach outputs, include the following attribution:

```
Data sources: GADM (admin boundaries), WorldPop (population), 
Overture Maps Foundation (infrastructure), healthsites.io (health facilities).
Analysis: GeoReach platform (https://github.com/yourusername/georeach)
```

---

## Data Update Schedule

For production use, recommended update frequencies:

- **Admin boundaries:** Annual (GADM releases)
- **Population:** Annual (WorldPop releases)
- **Infrastructure:** Quarterly (Overture Maps releases)
- **Health facilities:** Monthly (healthsites.io updates)
- **Flood hazard:** As available from authoritative sources

---

## Contact for Data Issues

- GADM: https://gadm.org/contact.html
- WorldPop: wp@worldpop.org
- Overture Maps: https://overturemaps.org/community/
- healthsites.io: info@healthsites.io

---

**Last Updated:** 2026-06-04
