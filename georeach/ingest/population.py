"""WorldPop population raster ingestion."""

from pathlib import Path

import rasterio
import requests
from loguru import logger
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box

from georeach.config import Config


def ingest_population(config: Config, subset: bool = False) -> None:
    """Download and process WorldPop population raster."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "population.tif"

    if output_path.exists():
        logger.info(f"Population raster already exists at {output_path}")
        return

    logger.info("Downloading WorldPop population data")

    worldpop_url = (
        f"https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/"
        f"{config.data_sources['population']['year']}/{config.study_area.country_code.upper()}/"
        f"cod_ppp_{config.data_sources['population']['year']}_1km_Aggregated_UNadj.tif"
    )

    cache_dir = Path("data/raw")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"worldpop_{config.study_area.country_code}_{config.data_sources['population']['year']}.tif"

    if not cache_path.exists():
        logger.info(f"Downloading from {worldpop_url}")
        try:
            response = requests.get(worldpop_url, stream=True, timeout=300)
            response.raise_for_status()

            with open(cache_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded to {cache_path}")
        except Exception as e:
            logger.warning(f"Could not download WorldPop data: {e}")
            logger.info("Creating synthetic population raster for demo")
            _create_synthetic_population(config, output_path)
            return

    bbox_geom = box(*config.study_area.bbox.to_tuple())

    with rasterio.open(cache_path) as src:
        out_image, out_transform = mask(src, [bbox_geom], crop=True, nodata=src.nodata)
        out_meta = src.meta.copy()

    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "compress": "lzw",
    })

    temp_path = output_dir / "population_temp.tif"
    with rasterio.open(temp_path, "w", **out_meta) as dest:
        dest.write(out_image)

    with rasterio.open(temp_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, config.crs.analysis, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({
            "crs": config.crs.analysis,
            "transform": transform,
            "width": width,
            "height": height,
        })

        with rasterio.open(output_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=config.crs.analysis,
                    resampling=Resampling.bilinear,
                )

    temp_path.unlink()
    logger.info(f"Saved population raster to {output_path}")


def _create_synthetic_population(config: Config, output_path: Path) -> None:
    """Create a synthetic population raster for demo purposes."""
    import numpy as np

    logger.warning("Creating synthetic population data - FOR DEMO ONLY")

    bbox = config.study_area.bbox.to_tuple()
    width, height = 100, 100

    from rasterio.transform import from_bounds
    transform = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], width, height)

    np.random.seed(42)
    population = np.random.exponential(scale=50, size=(height, width)).astype(np.float32)
    population = np.clip(population, 0, 500)

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
    ) as dst:
        dst.write(population, 1)

    logger.info(f"Created synthetic population raster at {output_path}")
