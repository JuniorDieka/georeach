"""Pytest fixtures for GeoReach tests."""

import numpy as np
import pytest
from shapely.geometry import Point, Polygon

import geopandas as gpd


@pytest.fixture
def sample_bbox() -> tuple[float, float, float, float]:
    """Sample bounding box for testing."""
    return (27.5, -4.0, 28.0, -3.5)


@pytest.fixture
def sample_hexagons() -> gpd.GeoDataFrame:
    """Create sample H3-like hexagons for testing."""
    hexagons = []
    for i in range(5):
        lon = 27.6 + i * 0.05
        lat = -3.8 + i * 0.05
        hex_geom = Point(lon, lat).buffer(0.02, resolution=6)
        hexagons.append({
            "h3_index": f"8{i:014d}",
            "geometry": hex_geom,
            "population": 100 + i * 50,
            "population_exposed": 20 + i * 10,
        })
    
    return gpd.GeoDataFrame(hexagons, crs="EPSG:4326")


@pytest.fixture
def sample_facilities() -> gpd.GeoDataFrame:
    """Create sample health facilities for testing."""
    facilities = []
    for i in range(3):
        lon = 27.65 + i * 0.1
        lat = -3.75 + i * 0.1
        facilities.append({
            "id": f"facility_{i}",
            "name": f"Health Center {i+1}",
            "geometry": Point(lon, lat),
        })
    
    return gpd.GeoDataFrame(facilities, crs="EPSG:4326")


@pytest.fixture
def sample_population_array() -> np.ndarray:
    """Create sample population raster array."""
    np.random.seed(42)
    return np.random.exponential(scale=50, size=(10, 10)).astype(np.float32)


@pytest.fixture
def sample_flood_array() -> np.ndarray:
    """Create sample flood hazard array."""
    np.random.seed(123)
    base = np.random.rand(10, 10)
    flood_mask = base > 0.7
    return flood_mask.astype(np.float32)
