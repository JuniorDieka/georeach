"""Tests for flood exposure analysis."""

import geopandas as gpd
import numpy as np


def test_exposure_calculation(
    sample_hexagons: gpd.GeoDataFrame,
) -> None:
    """Test exposure percentage calculation."""
    hexes = sample_hexagons.copy()

    hexes["exposure_pct"] = hexes["population_exposed"] / hexes["population"] * 100

    assert all(hexes["exposure_pct"] >= 0)
    assert all(hexes["exposure_pct"] <= 100)


def test_zonal_stats_aggregation(
    sample_hexagons: gpd.GeoDataFrame,
    sample_population_array: np.ndarray,
) -> None:
    """Test zonal statistics aggregation logic."""
    hexes = sample_hexagons.copy()

    total_pop = hexes["population"].sum()
    total_exposed = hexes["population_exposed"].sum()

    assert total_pop > 0
    assert total_exposed >= 0
    assert total_exposed <= total_pop


def test_exposure_with_zero_population(sample_hexagons: gpd.GeoDataFrame) -> None:
    """Test exposure calculation handles zero population."""
    hexes = sample_hexagons.copy()
    hexes.loc[0, "population"] = 0
    hexes.loc[0, "population_exposed"] = 0

    hexes["exposure_pct"] = (
        hexes["population_exposed"] / hexes["population"].replace(0, 1) * 100
    ).fillna(0)

    assert hexes.loc[0, "exposure_pct"] == 0
    assert all(hexes["exposure_pct"] >= 0)


def test_flood_mask_application(
    sample_population_array: np.ndarray,
    sample_flood_array: np.ndarray,
) -> None:
    """Test flood mask application to population."""
    exposed_pop = sample_population_array * sample_flood_array

    assert exposed_pop.shape == sample_population_array.shape
    assert np.all(exposed_pop >= 0)
    assert np.all(exposed_pop <= sample_population_array)
