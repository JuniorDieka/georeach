"""Export rasters as Cloud-Optimized GeoTIFFs."""

from pathlib import Path

from loguru import logger
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from georeach.config import Config


def export_cog(config: Config) -> None:
    """Convert rasters to Cloud-Optimized GeoTIFF format."""
    logger.info("Exporting rasters as COGs")

    processed_dir = Path("data/processed")
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    rasters = {
        "population.tif": "population_cog.tif",
        "flood_hazard.tif": "flood_hazard_cog.tif",
    }

    for input_name, output_name in rasters.items():
        input_path = processed_dir / input_name
        output_path = output_dir / output_name

        if not input_path.exists():
            logger.warning(f"Input raster not found: {input_path}")
            continue

        logger.info(f"Converting {input_name} to COG")

        try:
            cog_translate(
                str(input_path),
                str(output_path),
                cog_profiles.get("lzw"),
                quiet=True,
            )

            logger.info(f"Created COG: {output_path}")

        except Exception as e:
            logger.error(f"Failed to create COG for {input_name}: {e}")

    logger.success("COG export complete")
