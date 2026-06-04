"""Spatial SQL query utilities."""

from typing import Any, List

import geopandas as gpd
from loguru import logger
from sqlalchemy import create_engine, text

from georeach.config import Config


def execute_query(config: Config, query: str) -> gpd.GeoDataFrame:
    """Execute a spatial query and return as GeoDataFrame."""
    engine = create_engine(config.database.url)
    gdf = gpd.read_postgis(query, engine, geom_col="geometry")
    return gdf


def execute_sql(config: Config, sql: str) -> None:
    """Execute SQL statement without returning results."""
    engine = create_engine(config.database.url)
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


def get_table_count(config: Config, table_name: str) -> int:
    """Get row count for a table."""
    engine = create_engine(config.database.url)
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()
    return count or 0


def create_spatial_index(config: Config, table_name: str, geom_column: str = "geometry") -> None:
    """Create GIST spatial index on a geometry column."""
    logger.info(f"Creating spatial index on {table_name}.{geom_column}")

    index_name = f"{table_name}_{geom_column}_idx"
    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} USING GIST ({geom_column});"

    execute_sql(config, sql)
    logger.info(f"Spatial index created: {index_name}")
