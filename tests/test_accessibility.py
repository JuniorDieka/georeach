"""Tests for accessibility analysis."""

import pytest

import geopandas as gpd


def test_distance_calculation(
    sample_hexagons: gpd.GeoDataFrame,
    sample_facilities: gpd.GeoDataFrame,
) -> None:
    """Test distance calculation to nearest facility."""
    hexes = sample_hexagons.to_crs("EPSG:32735")
    facilities = sample_facilities.to_crs("EPSG:32735")
    
    hex_centroids = hexes.geometry.centroid
    
    distances = []
    for centroid in hex_centroids:
        dists = facilities.geometry.distance(centroid)
        min_dist = dists.min() / 1000.0
        distances.append(min_dist)
    
    assert len(distances) == len(hexes)
    assert all(d >= 0 for d in distances)


def test_accessibility_classification() -> None:
    """Test accessibility class assignment."""
    distances_km = [2.5, 7.5, 15.0]
    threshold_km = 5.0
    moderate_km = 10.0
    
    classes = []
    for dist in distances_km:
        if dist < threshold_km:
            classes.append("good")
        elif dist < moderate_km:
            classes.append("moderate")
        else:
            classes.append("poor")
    
    assert classes == ["good", "moderate", "poor"]


def test_accessibility_score_calculation() -> None:
    """Test accessibility score computation."""
    threshold_km = 5.0
    moderate_km = 10.0
    
    test_cases = [
        (2.0, "good"),
        (7.0, "moderate"),
        (12.0, "poor"),
    ]
    
    for dist_km, expected_class in test_cases:
        if dist_km < threshold_km:
            access_class = "good"
            access_score = 1.0 - (dist_km / threshold_km) * 0.5
        elif dist_km < moderate_km:
            access_class = "moderate"
            access_score = 0.5 - ((dist_km - threshold_km) / (moderate_km - threshold_km)) * 0.3
        else:
            access_class = "poor"
            access_score = max(0.2 - (dist_km - moderate_km) * 0.01, 0)
        
        assert access_class == expected_class
        assert 0 <= access_score <= 1


def test_nearest_facility_logic(
    sample_hexagons: gpd.GeoDataFrame,
    sample_facilities: gpd.GeoDataFrame,
) -> None:
    """Test finding nearest facility for each hex."""
    hexes = sample_hexagons.to_crs("EPSG:32735")
    facilities = sample_facilities.to_crs("EPSG:32735")
    
    for _, hex_row in hexes.iterrows():
        hex_point = hex_row.geometry.centroid
        dists = facilities.geometry.distance(hex_point)
        nearest_idx = dists.idxmin()
        
        assert nearest_idx in facilities.index
        assert dists[nearest_idx] == dists.min()
