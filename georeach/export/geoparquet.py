"""Export results to GeoParquet format."""

from pathlib import Path

import geopandas as gpd
from loguru import logger
from sqlalchemy import create_engine

from georeach.config import Config


def export_geoparquet(config: Config) -> None:
    """Export analysis results to GeoParquet."""
    logger.info("Exporting results to GeoParquet")

    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(config.database.url)

    tables = {
        "h3_grid": "h3_results.parquet",
        "admin_boundaries": "admin_results.parquet",
    }

    for table_name, filename in tables.items():
        output_path = output_dir / filename

        logger.info(f"Exporting {table_name} to {filename}")

        try:
            gdf = gpd.read_postgis(f"SELECT * FROM {table_name}", engine, geom_col="geometry")

            gdf_4326 = gdf.to_crs(config.crs.storage)

            gdf_4326.to_parquet(
                output_path,
                compression=config.outputs.compression,
                index=False,
            )

            logger.info(f"Exported {len(gdf_4326)} rows to {output_path}")

        except Exception as e:
            logger.warning(f"Could not export {table_name}: {e}")

    logger.success("GeoParquet export complete")
