-- Create schema and tables for GeoReach

-- H3 hex grid table
CREATE TABLE IF NOT EXISTS h3_grid (
    h3_index VARCHAR(15) PRIMARY KEY,
    resolution INTEGER NOT NULL,
    geometry GEOMETRY(POLYGON, 32735),
    centroid GEOMETRY(POINT, 32735),
    area_km2 DOUBLE PRECISION,
    population DOUBLE PRECISION DEFAULT 0,
    population_exposed DOUBLE PRECISION DEFAULT 0,
    exposure_pct DOUBLE PRECISION DEFAULT 0,
    nearest_facility_km DOUBLE PRECISION,
    accessibility_class VARCHAR(20),
    accessibility_score DOUBLE PRECISION,
    exposure_score DOUBLE PRECISION,
    priority_score DOUBLE PRECISION,
    priority_class VARCHAR(20)
);

-- Indexes will be created after data is loaded

-- Admin boundaries (loaded from file)
-- Will have columns from source data plus geometry

-- Health facilities (loaded from file)
-- Will have columns from source data plus geometry

-- Road network for pgRouting
CREATE TABLE IF NOT EXISTS road_network (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100),
    geometry GEOMETRY(LINESTRING, 32735),
    length_m DOUBLE PRECISION,
    source INTEGER,
    target INTEGER,
    cost DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS road_network_geom_idx ON road_network USING GIST (geometry);

-- Results summary table
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    analysis_date TIMESTAMP DEFAULT NOW(),
    total_hexes INTEGER,
    total_population DOUBLE PRECISION,
    exposed_population DOUBLE PRECISION,
    high_priority_hexes INTEGER,
    avg_facility_distance_km DOUBLE PRECISION
);
