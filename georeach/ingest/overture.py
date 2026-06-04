"""Overture Maps data ingestion via DuckDB."""

from pathlib import Path

import duckdb
import geopandas as gpd
from loguru import logger

from georeach.config import Config


def ingest_overture_data(config: Config, subset: bool = False) -> None:
    """Ingest Overture Maps buildings, places, and roads using DuckDB."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    bbox = config.study_area.bbox

    themes = {
        "buildings": "s3://overturemaps-us-west-2/release/2024-01-17-alpha.0/theme=buildings/type=building/*",
        "places": "s3://overturemaps-us-west-2/release/2024-01-17-alpha.0/theme=places/type=place/*",
        "transportation": "s3://overturemaps-us-west-2/release/2024-01-17-alpha.0/theme=transportation/type=segment/*",
    }

    for theme_name, s3_path in themes.items():
        output_path = output_dir / f"overture_{theme_name}.gpkg"

        if output_path.exists():
            logger.info(f"Overture {theme_name} already exists at {output_path}")
            continue

        logger.info(f"Querying Overture Maps {theme_name} data")

        try:
            con = duckdb.connect()
            con.execute("INSTALL spatial; LOAD spatial;")
            con.execute("INSTALL httpfs; LOAD httpfs;")
            con.execute("SET s3_region='us-west-2';")

            query = f"""
            SELECT *
            FROM read_parquet('{s3_path}', filename=true, hive_partitioning=1)
            WHERE bbox.xmin >= {bbox.west}
              AND bbox.xmax <= {bbox.east}
              AND bbox.ymin >= {bbox.south}
              AND bbox.ymax <= {bbox.north}
            """

            if subset:
                query += " LIMIT 100"

            result = con.execute(query).fetchdf()

            if len(result) == 0:
                logger.warning(f"No {theme_name} data found in bbox, creating synthetic data")
                _create_synthetic_overture(config, theme_name, output_path)
                continue

            gdf = gpd.GeoDataFrame(result, geometry="geometry", crs="EPSG:4326")
            gdf = gdf.to_crs(config.crs.analysis)
            gdf.to_file(output_path, driver="GPKG")

            logger.info(f"Saved {len(gdf)} {theme_name} features to {output_path}")

        except Exception as e:
            logger.warning(f"Could not fetch Overture {theme_name}: {e}")
            logger.info(f"Creating synthetic {theme_name} data for demo")
            _create_synthetic_overture(config, theme_name, output_path)


def _create_synthetic_overture(config: Config, theme: str, output_path: Path) -> None:
    """Create synthetic Overture-like data for demo."""
    import numpy as np
    from shapely.geometry import LineString, Point

    logger.warning(f"Creating synthetic {theme} data - FOR DEMO ONLY")

    bbox = config.study_area.bbox
    np.random.seed(42)

    if theme == "buildings":
        n = 50 if config else 50
        lons = np.random.uniform(bbox.west, bbox.east, n)
        lats = np.random.uniform(bbox.south, bbox.north, n)
        geometries = [Point(lon, lat).buffer(0.001) for lon, lat in zip(lons, lats, strict=False)]
        data = {"id": [f"building_{i}" for i in range(n)], "geometry": geometries}

    elif theme == "places":
        n = 20
        lons = np.random.uniform(bbox.west, bbox.east, n)
        lats = np.random.uniform(bbox.south, bbox.north, n)
        geometries = [Point(lon, lat) for lon, lat in zip(lons, lats, strict=False)]
        data = {"id": [f"place_{i}" for i in range(n)], "geometry": geometries}

    elif theme == "transportation":
        n = 30
        geometries = []
        for _i in range(n):
            lon1, lon2 = np.random.uniform(bbox.west, bbox.east, 2)
            lat1, lat2 = np.random.uniform(bbox.south, bbox.north, 2)
            geometries.append(LineString([(lon1, lat1), (lon2, lat2)]))
        data = {"id": [f"road_{i}" for i in range(n)], "geometry": geometries}

    else:
        data = {"id": [], "geometry": []}

    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    gdf = gdf.to_crs(config.crs.analysis)
    gdf.to_file(output_path, driver="GPKG")

    logger.info(f"Created synthetic {theme} data at {output_path}")
