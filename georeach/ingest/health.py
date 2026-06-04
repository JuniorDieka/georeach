"""Health facilities ingestion from healthsites.io."""

from pathlib import Path

import geopandas as gpd
import requests
from loguru import logger
from shapely.geometry import Point

from georeach.config import Config


def ingest_health_facilities(config: Config, subset: bool = False) -> None:
    """Download and process health facilities from healthsites.io."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "health_facilities.gpkg"

    if output_path.exists():
        logger.info(f"Health facilities already exist at {output_path}")
        return

    logger.info("Downloading health facilities from healthsites.io")

    bbox = config.study_area.bbox
    api_url = (
        f"https://healthsites.io/api/v2/facilities/?"
        f"extent={bbox.west},{bbox.south},{bbox.east},{bbox.north}"
        f"&page=1&api-key=healthsites"
    )

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "features" not in data or len(data["features"]) == 0:
            logger.warning("No health facilities found, creating synthetic data")
            _create_synthetic_health_facilities(config, output_path, subset)
            return

        gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

        if subset:
            gdf = gdf.head(5)
            logger.info("Using subset: first 5 facilities only")

        gdf = gdf.to_crs(config.crs.analysis)

        gdf.to_file(output_path, driver="GPKG")
        logger.info(f"Saved {len(gdf)} health facilities to {output_path}")

    except Exception as e:
        logger.warning(f"Could not fetch health facilities: {e}")
        logger.info("Creating synthetic health facilities for demo")
        _create_synthetic_health_facilities(config, output_path, subset)


def _create_synthetic_health_facilities(config: Config, output_path: Path, subset: bool) -> None:
    """Create synthetic health facility data for demo."""
    import numpy as np

    logger.warning("Creating synthetic health facilities - FOR DEMO ONLY")

    bbox = config.study_area.bbox
    n = 5 if subset else 15

    np.random.seed(42)
    lons = np.random.uniform(bbox.west, bbox.east, n)
    lats = np.random.uniform(bbox.south, bbox.north, n)

    facilities = []
    for i, (lon, lat) in enumerate(zip(lons, lats)):
        facilities.append({
            "id": f"facility_{i}",
            "name": f"Health Center {i+1}",
            "amenity": "clinic",
            "geometry": Point(lon, lat),
        })

    gdf = gpd.GeoDataFrame(facilities, crs="EPSG:4326")
    gdf = gdf.to_crs(config.crs.analysis)
    gdf.to_file(output_path, driver="GPKG")

    logger.info(f"Created {len(gdf)} synthetic health facilities at {output_path}")
