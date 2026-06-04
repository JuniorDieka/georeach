"""Flood hazard layer ingestion."""

from pathlib import Path

import numpy as np
import rasterio
from loguru import logger
from rasterio.transform import from_bounds

from georeach.config import Config


def ingest_flood_hazard(config: Config, subset: bool = False) -> None:
    """Create synthetic flood hazard raster for demo."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "flood_hazard.tif"

    if output_path.exists():
        logger.info(f"Flood hazard already exists at {output_path}")
        return

    logger.warning("Creating synthetic flood hazard layer - FOR DEMO ONLY")
    logger.info("In production, use real flood data from GFDRR, Fathom, or similar")

    bbox = config.study_area.bbox.to_tuple()
    width, height = 100, 100

    transform = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], width, height)

    np.random.seed(123)
    base = np.random.rand(height, width)

    flood_mask = base > 0.7
    flood_depth = np.where(flood_mask, np.random.uniform(0.5, 3.0, (height, width)), 0)
    flood_depth = flood_depth.astype(np.float32)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=rasterio.float32,
        crs="EPSG:4326",
        transform=transform,
        compress="lzw",
        nodata=0,
    ) as dst:
        dst.write(flood_depth, 1)

    logger.info(f"Created synthetic flood hazard raster at {output_path}")
    logger.warning("Remember: This is DEMO DATA for portfolio purposes only")
