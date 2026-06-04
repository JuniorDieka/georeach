"""Flood exposure analysis using zonal statistics."""

from pathlib import Path

import geopandas as gpd
import rasterio
from loguru import logger
from rasterstats import zonal_stats
from sqlalchemy import create_engine, text

from georeach.config import Config


def compute_exposure(config: Config) -> None:
    """Compute flood exposure for each H3 hex using zonal statistics."""
    logger.info("Computing flood exposure analysis")

    engine = create_engine(config.database.url)

    hexes_gdf = gpd.read_postgis(
        "SELECT h3_index, geometry FROM h3_grid", engine, geom_col="geometry"
    )

    logger.info(f"Loaded {len(hexes_gdf)} hexagons from database")

    population_path = Path("data/processed/population.tif")
    flood_path = Path("data/processed/flood_hazard.tif")

    if not population_path.exists():
        logger.error(f"Population raster not found: {population_path}")
        return

    if not flood_path.exists():
        logger.error(f"Flood hazard raster not found: {flood_path}")
        return

    hexes_4326 = hexes_gdf.to_crs("EPSG:4326")

    logger.info("Computing population per hex (processing in batches)")

    # Process in batches of 1000 to avoid memory issues
    batch_size = 1000
    pop_values = []

    for i in range(0, len(hexes_4326), batch_size):
        batch = hexes_4326.iloc[i : i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(hexes_4326)-1)//batch_size + 1}")

        batch_stats = zonal_stats(
            batch.geometry,
            str(population_path),
            stats=["sum"],
            nodata=0,
        )
        pop_values.extend([stat["sum"] if stat["sum"] is not None else 0 for stat in batch_stats])

    hexes_gdf["population"] = pop_values

    logger.info("Computing exposed population per hex")

    with rasterio.open(flood_path) as flood_src:
        flood_4326_path = Path("data/processed/flood_hazard_4326.tif")

        if flood_src.crs != "EPSG:4326":
            from rasterio.warp import Resampling, calculate_default_transform, reproject

            transform, width, height = calculate_default_transform(
                flood_src.crs, "EPSG:4326", flood_src.width, flood_src.height, *flood_src.bounds
            )

            kwargs = flood_src.meta.copy()
            kwargs.update(
                {
                    "crs": "EPSG:4326",
                    "transform": transform,
                    "width": width,
                    "height": height,
                }
            )

            with rasterio.open(flood_4326_path, "w", **kwargs) as dst:
                reproject(
                    source=rasterio.band(flood_src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=flood_src.transform,
                    src_crs=flood_src.crs,
                    dst_transform=transform,
                    dst_crs="EPSG:4326",
                    resampling=Resampling.nearest,
                )
        else:
            flood_4326_path = flood_path

    with rasterio.open(population_path) as pop_src, rasterio.open(flood_4326_path) as flood_src:
        pop_array = pop_src.read(1)
        flood_array = flood_src.read(1)

        from rasterio.warp import Resampling, reproject

        if pop_src.shape != flood_src.shape or pop_src.bounds != flood_src.bounds:
            logger.info("Reprojecting flood to match population raster")
            flood_aligned = pop_array.copy() * 0

            reproject(
                source=flood_array,
                destination=flood_aligned,
                src_transform=flood_src.transform,
                src_crs=flood_src.crs,
                dst_transform=pop_src.transform,
                dst_crs=pop_src.crs,
                resampling=Resampling.nearest,
            )
            flood_array = flood_aligned

        exposed_pop = pop_array * (flood_array > 0)

        temp_path = Path("data/processed/exposed_population.tif")
        with rasterio.open(
            temp_path,
            "w",
            driver="GTiff",
            height=exposed_pop.shape[0],
            width=exposed_pop.shape[1],
            count=1,
            dtype=exposed_pop.dtype,
            crs=pop_src.crs,
            transform=pop_src.transform,
            compress="lzw",
        ) as dst:
            dst.write(exposed_pop, 1)

    logger.info("Computing exposed population per hex (processing in batches)")

    exposed_values = []
    for i in range(0, len(hexes_4326), batch_size):
        batch = hexes_4326.iloc[i : i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(hexes_4326)-1)//batch_size + 1}")

        batch_stats = zonal_stats(
            batch.geometry,
            str(temp_path),
            stats=["sum"],
            nodata=0,
        )
        exposed_values.extend(
            [stat["sum"] if stat["sum"] is not None else 0 for stat in batch_stats]
        )

    hexes_gdf["population_exposed"] = exposed_values

    hexes_gdf["exposure_pct"] = (
        hexes_gdf["population_exposed"] / hexes_gdf["population"].replace(0, 1) * 100
    ).fillna(0)

    logger.info(f"Total population: {hexes_gdf['population'].sum():.0f}")
    logger.info(f"Exposed population: {hexes_gdf['population_exposed'].sum():.0f}")

    with engine.connect() as conn:
        for _, row in hexes_gdf.iterrows():
            conn.execute(
                text(
                    """
                    UPDATE h3_grid
                    SET population = :pop,
                        population_exposed = :pop_exp,
                        exposure_pct = :exp_pct
                    WHERE h3_index = :h3_index
                """
                ),
                {
                    "pop": float(row["population"]),
                    "pop_exp": float(row["population_exposed"]),
                    "exp_pct": float(row["exposure_pct"]),
                    "h3_index": row["h3_index"],
                },
            )
        conn.commit()

    logger.success("Flood exposure analysis complete")
