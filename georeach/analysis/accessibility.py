"""Service accessibility analysis."""

import geopandas as gpd
from loguru import logger
from sqlalchemy import create_engine, text

from georeach.config import Config


def compute_accessibility(config: Config) -> None:
    """Compute accessibility to nearest health facility for each hex."""
    logger.info("Computing service accessibility")

    engine = create_engine(config.database.url)

    hexes_gdf = gpd.read_postgis(
        "SELECT h3_index, centroid as geometry FROM h3_grid WHERE population > 0",
        engine,
        geom_col="geometry",
    )

    facilities_gdf = gpd.read_postgis(
        "SELECT geometry FROM health_facilities", engine, geom_col="geometry"
    )

    logger.info(
        f"Computing distances for {len(hexes_gdf)} populated hexes to {len(facilities_gdf)} facilities"
    )

    if len(facilities_gdf) == 0:
        logger.error("No health facilities found in database")
        return

    distances = []
    for _, hex_row in hexes_gdf.iterrows():
        hex_point = hex_row.geometry

        dists = facilities_gdf.geometry.distance(hex_point)
        min_dist_m = dists.min()
        min_dist_km = min_dist_m / 1000.0

        distances.append({"h3_index": hex_row["h3_index"], "distance_km": min_dist_km})

    logger.info("Updating database with accessibility metrics")

    threshold_km = config.analysis.accessibility.threshold_km
    moderate_km = config.analysis.accessibility.moderate_km

    with engine.connect() as conn:
        for dist_info in distances:
            dist_km = dist_info["distance_km"]

            if dist_km < threshold_km:
                access_class = "good"
                access_score = 1.0 - (dist_km / threshold_km) * 0.5
            elif dist_km < moderate_km:
                access_class = "moderate"
                access_score = 0.5 - ((dist_km - threshold_km) / (moderate_km - threshold_km)) * 0.3
            else:
                access_class = "poor"
                access_score = max(0.2 - (dist_km - moderate_km) * 0.01, 0)

            conn.execute(
                text(
                    """
                    UPDATE h3_grid
                    SET nearest_facility_km = :dist_km,
                        accessibility_class = :access_class,
                        accessibility_score = :access_score
                    WHERE h3_index = :h3_index
                """
                ),
                {
                    "dist_km": dist_km,
                    "access_class": access_class,
                    "access_score": access_score,
                    "h3_index": dist_info["h3_index"],
                },
            )
        conn.commit()

    avg_distance = sum(d["distance_km"] for d in distances) / len(distances)
    logger.info(f"Average distance to nearest facility: {avg_distance:.2f} km")

    poor_access = sum(1 for d in distances if d["distance_km"] > moderate_km)
    logger.info(f"Hexes with poor access (>{moderate_km}km): {poor_access}")

    logger.success("Service accessibility analysis complete")
