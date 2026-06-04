-- Enable PostGIS and required extensions

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- pgRouting extension (optional, for network-based routing)
-- Not available in standard PostGIS image, using distance-based accessibility instead
-- CREATE EXTENSION IF NOT EXISTS pgrouting;

-- H3 extension (optional, will use h3-py if not available)
-- CREATE EXTENSION IF NOT EXISTS h3;
-- CREATE EXTENSION IF NOT EXISTS h3_postgis;
