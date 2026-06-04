"""Load processed data into PostGIS."""

from pathlib import Path

import geopandas as gpd
from loguru import logger
from sqlalchemy import create_engine

from georeach.config import Config


def load_all_data(config: Config) -> None:
    """Load all processed data into PostGIS."""
    engine = create_engine(config.database.url)

    data_dir = Path("data/processed")

    datasets = {
        "admin_boundaries": "admin_boundaries.gpkg",
        "health_facilities": "health_facilities.gpkg",
        "overture_buildings": "overture_buildings.gpkg",
        "overture_places": "overture_places.gpkg",
        "overture_transportation": "overture_transportation.gpkg",
    }

    for table_name, filename in datasets.items():
        file_path = data_dir / filename

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}, skipping")
            continue

        logger.info(f"Loading {table_name} from {filename}")

        gdf = gpd.read_file(file_path, engine="pyogrio")

        gdf.to_postgis(
            table_name,
            engine,
            if_exists="replace",
            index=False,
            chunksize=1000,
        )

        logger.info(f"Loaded {len(gdf)} rows into {table_name}")

    logger.success("All data loaded into PostGIS")
