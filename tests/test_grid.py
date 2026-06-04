"""Tests for H3 grid generation."""

import h3
import pytest
from shapely.geometry import box

import geopandas as gpd


def test_h3_polyfill(sample_bbox: tuple[float, float, float, float]) -> None:
    """Test H3 polyfill generates hexagons."""
    bbox_geom = box(*sample_bbox)
    
    h3_indexes = h3.polyfill_geojson(bbox_geom.__geo_interface__, 8)
    
    assert len(h3_indexes) > 0
    assert all(isinstance(idx, str) for idx in h3_indexes)


def test_h3_to_polygon(sample_bbox: tuple[float, float, float, float]) -> None:
    """Test converting H3 index to polygon geometry."""
    bbox_geom = box(*sample_bbox)
    h3_indexes = h3.polyfill_geojson(bbox_geom.__geo_interface__, 8)
    
    first_hex = list(h3_indexes)[0]
    boundary = h3.h3_to_geo_boundary(first_hex, geo_json=True)
    
    assert len(boundary) >= 6
    assert all(isinstance(coord, (list, tuple)) and len(coord) == 2 for coord in boundary)


def test_hex_area_calculation(sample_hexagons: gpd.GeoDataFrame) -> None:
    """Test hex area calculation."""
    hexes = sample_hexagons.to_crs("EPSG:32735")
    hexes["area_km2"] = hexes.geometry.area / 1_000_000
    
    assert all(hexes["area_km2"] > 0)
    assert all(hexes["area_km2"] < 100)


def test_hex_centroid(sample_hexagons: gpd.GeoDataFrame) -> None:
    """Test hex centroid calculation."""
    hexes = sample_hexagons.copy()
    hexes["centroid"] = hexes.geometry.centroid
    
    assert all(hexes["centroid"].is_valid)
    assert all(hexes.geometry.contains(hexes["centroid"]))
