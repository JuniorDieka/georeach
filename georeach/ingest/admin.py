"""Admin boundaries ingestion from HDX/GADM."""

from pathlib import Path

import geopandas as gpd
import requests
from loguru import logger
from shapely.geometry import box

from georeach.config import Config


def ingest_admin_boundaries(config: Config, subset: bool = False) -> None:
    """Download and process admin boundaries for the study area."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "admin_boundaries.gpkg"

    if output_path.exists():
        logger.info(f"Admin boundaries already exist at {output_path}")
        return

    logger.info("Downloading admin boundaries from GADM")

    gadm_url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_{config.study_area.country_code}.gpkg"
    cache_dir = Path("data/raw")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"gadm41_{config.study_area.country_code}.gpkg"

    if not cache_path.exists():
        logger.info(f"Downloading from {gadm_url}")
        response = requests.get(gadm_url, stream=True)
        response.raise_for_status()

        with open(cache_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded to {cache_path}")

    try:
        layer_name = f"ADM_ADM_{config.study_area.admin_level}"
        gdf = gpd.read_file(cache_path, layer=layer_name)
    except Exception as e:
        logger.warning(f"Could not read layer {layer_name}: {e}")
        logger.info("Trying alternative layer name format")
        try:
            layer_name = f"gadm41_{config.study_area.country_code}_{config.study_area.admin_level}"
            gdf = gpd.read_file(cache_path, layer=layer_name)
        except Exception as e2:
            logger.error(f"Could not read GADM data: {e2}")
            logger.info("Creating synthetic admin boundary for demo")
            _create_synthetic_admin(config, output_path)
            return

    bbox_geom = box(*config.study_area.bbox.to_tuple())
    bbox_gdf = gpd.GeoDataFrame([{"geometry": bbox_geom}], crs="EPSG:4326")

    gdf = gdf.to_crs("EPSG:4326")
    gdf_clipped = gpd.overlay(gdf, bbox_gdf, how="intersection")

    if subset:
        gdf_clipped = gdf_clipped.head(1)
        logger.info("Using subset: first admin unit only")

    gdf_clipped = gdf_clipped.to_crs(config.crs.analysis)

    if not gdf_clipped.is_valid.all():
        logger.warning("Fixing invalid geometries")
        gdf_clipped["geometry"] = gdf_clipped["geometry"].buffer(0)

    gdf_clipped.to_file(output_path, driver="GPKG")
    logger.info(f"Saved {len(gdf_clipped)} admin units to {output_path}")


def _create_synthetic_admin(config: Config, output_path: Path) -> None:
    """Create synthetic admin boundary for demo purposes."""
    from shapely.geometry import box
    
    logger.warning("Creating synthetic admin boundary - FOR DEMO ONLY")
    
    bbox_geom = box(*config.study_area.bbox.to_tuple())
    
    gdf = gpd.GeoDataFrame(
        [{
            "GID_0": config.study_area.country_code,
            "NAME_0": "Democratic Republic of the Congo",
            "GID_3": f"{config.study_area.country_code}.1.1.1",
            "NAME_3": config.study_area.name,
            "geometry": bbox_geom
        }],
        crs="EPSG:4326"
    )
    
    gdf = gdf.to_crs(config.crs.analysis)
    gdf.to_file(output_path, driver="GPKG")
    
    logger.info(f"Created synthetic admin boundary at {output_path}")
