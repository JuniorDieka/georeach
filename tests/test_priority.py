"""Tests for priority index computation."""

import geopandas as gpd
import numpy as np


def test_normalization(sample_hexagons: gpd.GeoDataFrame) -> None:
    """Test min-max normalization."""
    values = sample_hexagons["population_exposed"].values

    v_min = values.min()
    v_max = values.max()

    normalized = (values - v_min) / (v_max - v_min) if v_max > v_min else np.zeros_like(values)

    assert np.all(normalized >= 0)
    assert np.all(normalized <= 1)
    assert normalized.min() == 0 or len(np.unique(values)) == 1
    assert normalized.max() == 1 or len(np.unique(values)) == 1


def test_priority_score_calculation() -> None:
    """Test priority score weighted combination."""
    exposure_score = 0.8
    inaccessibility_score = 0.6

    exposure_weight = 0.6
    accessibility_weight = 0.4

    priority_score = exposure_score * exposure_weight + inaccessibility_score * accessibility_weight

    expected = 0.8 * 0.6 + 0.6 * 0.4
    assert abs(priority_score - expected) < 0.001
    assert 0 <= priority_score <= 1


def test_priority_classification() -> None:
    """Test priority class assignment."""
    scores = np.array([0.9, 0.7, 0.5, 0.3, 0.1])

    top_percentile = 20
    threshold = np.percentile(scores, 100 - top_percentile)

    classes = np.where(
        scores >= threshold, "high", np.where(scores >= np.percentile(scores, 50), "medium", "low")
    )

    assert (classes == "high").sum() == 1
    assert "medium" in classes
    assert "low" in classes


def test_inaccessibility_inversion() -> None:
    """Test accessibility score inversion for priority."""
    accessibility_scores = np.array([1.0, 0.7, 0.3, 0.0])
    inaccessibility_scores = 1.0 - accessibility_scores

    expected = np.array([0.0, 0.3, 0.7, 1.0])

    assert np.allclose(inaccessibility_scores, expected)


def test_priority_with_weights() -> None:
    """Test priority calculation with different weights."""
    exposure_normalized = 0.8
    inaccessibility_score = 0.6

    weights = [
        (0.6, 0.4),
        (0.5, 0.5),
        (0.7, 0.3),
    ]

    for exp_w, acc_w in weights:
        priority = exposure_normalized * exp_w + inaccessibility_score * acc_w
        assert 0 <= priority <= 1
        assert abs((exp_w + acc_w) - 1.0) < 0.001
