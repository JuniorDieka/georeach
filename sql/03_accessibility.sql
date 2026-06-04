-- pgRouting accessibility queries

-- Prepare road network for routing
-- This assumes road_network table has been populated with source/target nodes

-- Create topology for road network
-- SELECT pgr_createTopology('road_network', 0.001, 'geometry', 'id');

-- Query to find nearest facility using Dijkstra
-- Example query structure (to be executed from Python with parameters):
/*
WITH nearest_facility AS (
    SELECT
        h.h3_index,
        f.id AS facility_id,
        ST_Distance(h.centroid, f.geometry) AS euclidean_dist
    FROM h3_grid h
    CROSS JOIN LATERAL (
        SELECT id, geometry
        FROM health_facilities
        ORDER BY h.centroid <-> geometry
        LIMIT 1
    ) f
)
UPDATE h3_grid h
SET
    nearest_facility_km = nf.euclidean_dist / 1000.0,
    accessibility_class = CASE
        WHEN nf.euclidean_dist / 1000.0 < 5 THEN 'good'
        WHEN nf.euclidean_dist / 1000.0 < 10 THEN 'moderate'
        ELSE 'poor'
    END
FROM nearest_facility nf
WHERE h.h3_index = nf.h3_index;
*/
