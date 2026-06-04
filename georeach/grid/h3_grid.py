"""H3 hexagonal grid generation."""

import geopandas as gpd
import h3
from loguru import logger
from shapely.geometry import Polygon
from sqlalchemy import create_engine, text

from georeach.config import Config


def generate_and_load_grid(config: Config) -> None:
    """Generate H3 hex grid covering the study area and load into PostGIS."""
    logger.info(f"Generating H3 grid at resolution {config.h3.resolution}")

    engine = create_engine(config.database.url)

    admin_gdf = gpd.read_postgis(
        "SELECT geometry FROM admin_boundaries",
        engine,
        geom_col="geometry"
    )

    if len(admin_gdf) == 0:
        logger.error("No admin boundaries found in database")
        return

    study_area = admin_gdf.unary_union

    study_area_4326 = gpd.GeoSeries([study_area], crs=config.crs.analysis).to_crs("EPSG:4326")[0]

    h3_indexes = h3.polyfill_geojson(
        study_area_4326.__geo_interface__,
        config.h3.resolution
    )

    logger.info(f"Generated {len(h3_indexes)} hexagons")

    hexagons = []
    for h3_index in h3_indexes:
        boundary = h3.h3_to_geo_boundary(h3_index, geo_json=True)
        polygon = Polygon(boundary)

        hexagons.append({
            "h3_index": h3_index,
            "resolution": config.h3.resolution,
            "geometry": polygon,
        })

    gdf = gpd.GeoDataFrame(hexagons, crs="EPSG:4326")
    gdf = gdf.to_crs(config.crs.analysis)

    gdf["centroid"] = gdf.geometry.centroid
    gdf["area_km2"] = gdf.geometry.area / 1_000_000

    # Drop and recreate table to ensure correct schema
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS h3_grid CASCADE"))
        conn.execute(text("""
            CREATE TABLE h3_grid (
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
            )
        """))
        conn.commit()
        
        # Verify table was created with correct schema
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'h3_grid' ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result]
        logger.info(f"Created h3_grid table with columns: {columns}")

    # Insert data using only the basic columns
    srid = int(config.crs.analysis.split(":")[1])
    
    insert_data = []
    for _, row in gdf.iterrows():
        insert_data.append({
            "h3_index": row["h3_index"],
            "resolution": row["resolution"],
            "geom": row["geometry"].wkt,
            "centroid": row["centroid"].wkt,
            "srid": srid,
            "area_km2": float(row["area_km2"]),
        })
    
    # Batch insert in chunks of 1000
    batch_size = 1000
    with engine.connect() as conn:
        for i in range(0, len(insert_data), batch_size):
            batch = insert_data[i:i+batch_size]
            conn.execute(
                text("""
                    INSERT INTO h3_grid (h3_index, resolution, geometry, centroid, area_km2)
                    VALUES (:h3_index, :resolution, ST_GeomFromText(:geom, :srid), 
                            ST_GeomFromText(:centroid, :srid), :area_km2)
                """),
                batch
            )
        conn.commit()

    logger.success(f"Loaded {len(gdf)} hexagons into PostGIS")

    # Create spatial index on geometry column only
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS h3_grid_geom_idx ON h3_grid USING GIST (geometry)"))
        conn.commit()

    logger.info("Spatial index created on geometry column")
