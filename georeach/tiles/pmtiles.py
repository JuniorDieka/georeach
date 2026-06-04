"""Generate PMTiles for web mapping."""

import subprocess
from pathlib import Path

import geopandas as gpd
from loguru import logger
from sqlalchemy import create_engine

from georeach.config import Config


def generate_pmtiles(config: Config) -> None:
    """Generate PMTiles from analysis results using tippecanoe."""
    logger.info("Generating PMTiles")

    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = Path("data/outputs/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(config.database.url)

    layers = {
        "h3_grid": {
            "query": """
                SELECT h3_index, population, population_exposed, exposure_pct,
                       nearest_facility_km, accessibility_class, priority_score, priority_class,
                       geometry
                FROM h3_grid
                WHERE population > 0
            """,
            "output": "h3_grid.pmtiles",
        },
        "health_facilities": {
            "query": "SELECT * FROM health_facilities",
            "output": "health_facilities.pmtiles",
        },
    }

    for layer_name, layer_info in layers.items():
        logger.info(f"Processing layer: {layer_name}")

        try:
            gdf = gpd.read_postgis(
                layer_info["query"],
                engine,
                geom_col="geometry"
            )

            gdf_4326 = gdf.to_crs(config.crs.storage)

            geojson_path = temp_dir / f"{layer_name}.geojson"
            gdf_4326.to_file(geojson_path, driver="GeoJSON")

            pmtiles_path = output_dir / layer_info["output"]

            try:
                result = subprocess.run(
                    [
                        "tippecanoe",
                        "-o", str(pmtiles_path),
                        "-Z", "6",
                        "-z", "14",
                        "-l", layer_name,
                        "--drop-densest-as-needed",
                        "--extend-zooms-if-still-dropping",
                        str(geojson_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                logger.info(f"Created PMTiles: {pmtiles_path}")

            except subprocess.CalledProcessError as e:
                logger.warning(f"tippecanoe not available or failed: {e}")
                logger.info("Copying GeoJSON as fallback (PMTiles requires tippecanoe)")

                fallback_path = output_dir / f"{layer_name}.geojson"
                gdf_4326.to_file(fallback_path, driver="GeoJSON")
                logger.info(f"Saved GeoJSON fallback: {fallback_path}")

            except FileNotFoundError:
                logger.warning("tippecanoe not found in PATH")
                logger.info("Install tippecanoe or use GeoJSON fallback")

                fallback_path = output_dir / f"{layer_name}.geojson"
                gdf_4326.to_file(fallback_path, driver="GeoJSON")
                logger.info(f"Saved GeoJSON fallback: {fallback_path}")

        except Exception as e:
            logger.error(f"Failed to process {layer_name}: {e}")

    logger.success("Tile generation complete")
