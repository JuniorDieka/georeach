"""Priority index computation."""

import geopandas as gpd
import numpy as np
from loguru import logger
from sqlalchemy import create_engine, text

from georeach.config import Config


def compute_priority(config: Config) -> None:
    """Compute priority index combining exposure and accessibility."""
    logger.info("Computing priority index")

    engine = create_engine(config.database.url)

    # Read data without geometry since we only need attribute data for priority calculation
    from sqlalchemy import text
    import pandas as pd
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT h3_index, population, population_exposed, exposure_pct,
                   nearest_facility_km, accessibility_score
            FROM h3_grid
            WHERE population > 0
        """))
        hexes_gdf = pd.DataFrame(result.fetchall(), columns=result.keys())
        hexes_gdf.set_index("h3_index", inplace=True)

    logger.info(f"Computing priority for {len(hexes_gdf)} populated hexes")

    exposure_values = hexes_gdf["population_exposed"].values
    exposure_min = exposure_values.min()
    exposure_max = exposure_values.max()

    if exposure_max > exposure_min:
        exposure_normalized = (exposure_values - exposure_min) / (exposure_max - exposure_min)
    else:
        exposure_normalized = np.zeros_like(exposure_values)

    hexes_gdf["exposure_score"] = exposure_normalized

    inaccessibility_score = 1.0 - hexes_gdf["accessibility_score"].fillna(0)

    exposure_weight = config.analysis.priority.exposure_weight
    accessibility_weight = config.analysis.priority.accessibility_weight

    priority_score = (
        exposure_normalized * exposure_weight +
        inaccessibility_score.values * accessibility_weight
    )

    hexes_gdf["priority_score"] = priority_score

    top_percentile = config.analysis.priority.top_percentile
    threshold = np.percentile(priority_score, 100 - top_percentile)

    hexes_gdf["priority_class"] = np.where(
        priority_score >= threshold,
        "high",
        np.where(priority_score >= np.percentile(priority_score, 50), "medium", "low")
    )

    logger.info(f"High priority hexes: {(hexes_gdf['priority_class'] == 'high').sum()}")
    logger.info(f"Medium priority hexes: {(hexes_gdf['priority_class'] == 'medium').sum()}")
    logger.info(f"Low priority hexes: {(hexes_gdf['priority_class'] == 'low').sum()}")

    with engine.connect() as conn:
        for h3_index, row in hexes_gdf.iterrows():
            conn.execute(
                text("""
                    UPDATE h3_grid
                    SET exposure_score = :exp_score,
                        priority_score = :pri_score,
                        priority_class = :pri_class
                    WHERE h3_index = :h3_index
                """),
                {
                    "exp_score": float(row["exposure_score"]),
                    "pri_score": float(row["priority_score"]),
                    "pri_class": row["priority_class"],
                    "h3_index": h3_index,
                }
            )
        conn.commit()

    total_pop = hexes_gdf["population"].sum()
    high_priority_pop = hexes_gdf[hexes_gdf["priority_class"] == "high"]["population"].sum()

    logger.info(f"Population in high-priority areas: {high_priority_pop:.0f} ({high_priority_pop/total_pop*100:.1f}%)")

    logger.success("Priority index computation complete")
