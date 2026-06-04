# Contributing to GeoReach

Thank you for your interest in contributing to GeoReach! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional. We welcome contributions from everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, GDAL version)
- Relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please open an issue with:
- Clear description of the proposed feature
- Use case and motivation
- Example implementation (if applicable)
- Potential impact on existing functionality

### Pull Requests

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines below

3. **Add tests** for new functionality

4. **Run the test suite** and ensure all tests pass:
   ```bash
   make test
   ```

5. **Run linters** and fix any issues:
   ```bash
   make lint
   make format
   ```

6. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "Add network-based accessibility analysis with pgRouting"
   ```

7. **Push to your fork** and submit a pull request

8. **Describe your changes** in the PR description:
   - What problem does it solve?
   - How does it work?
   - Any breaking changes?
   - Related issues?

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/georeach.git
cd georeach

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Start PostGIS for testing
docker-compose up -d postgis
```

## Code Style Guidelines

### Python

- **Style:** Follow PEP 8
- **Formatter:** Black (line length 100)
- **Linter:** Ruff
- **Type hints:** Required for all functions
- **Docstrings:** Required for all public functions and classes

Example:
```python
def compute_distance(
    point_a: Point, 
    point_b: Point, 
    crs: str = "EPSG:32735"
) -> float:
    """
    Compute Euclidean distance between two points.
    
    Args:
        point_a: First point geometry
        point_b: Second point geometry
        crs: Coordinate reference system for distance calculation
        
    Returns:
        Distance in meters
    """
    gdf = gpd.GeoDataFrame(
        {"geometry": [point_a, point_b]}, 
        crs="EPSG:4326"
    ).to_crs(crs)
    return gdf.geometry[0].distance(gdf.geometry[1])
```

### SQL

- Use lowercase for SQL keywords
- Indent subqueries
- Add comments for complex queries
- Use meaningful table/column aliases

### JavaScript

- Use ES6+ syntax
- Consistent indentation (2 spaces)
- Meaningful variable names
- Add comments for complex logic

## Testing Guidelines

### Writing Tests

- Use pytest fixtures for reusable test data
- Test edge cases and error conditions
- Keep tests focused and independent
- Use descriptive test names

Example:
```python
def test_exposure_with_zero_population(sample_hexagons: gpd.GeoDataFrame) -> None:
    """Test exposure calculation handles zero population gracefully."""
    hexes = sample_hexagons.copy()
    hexes.loc[0, "population"] = 0
    
    hexes["exposure_pct"] = (
        hexes["population_exposed"] / hexes["population"].replace(0, 1) * 100
    ).fillna(0)
    
    assert hexes.loc[0, "exposure_pct"] == 0
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_exposure.py -v

# With coverage
pytest tests/ --cov=georeach --cov-report=html
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Update DATA_SOURCES.md for new data sources

## Commit Message Guidelines

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(accessibility): Add pgRouting network-based analysis

Implement network-based travel time calculation using pgRouting
instead of Euclidean distance. Includes road network topology
creation and Dijkstra shortest path queries.

Closes #42
```

```
fix(exposure): Handle NaN values in population raster

Replace NaN values with 0 before zonal statistics to prevent
errors in exposure calculation.

Fixes #38
```

## Priority Contribution Areas

We especially welcome contributions in these areas:

1. **Real Flood Data Integration**
   - Replace synthetic flood layer with real data sources
   - Support multiple flood scenarios (return periods)

2. **Network-Based Accessibility**
   - Implement pgRouting for road network analysis
   - Add travel time calculations with speed limits

3. **Temporal Analysis**
   - Multi-temporal flood scenarios
   - Seasonal accessibility variations

4. **Performance Optimization**
   - Parallel processing for large areas
   - Dask integration for raster operations

5. **Additional Analyses**
   - Vulnerability indicators
   - Multi-hazard exposure
   - Service coverage gaps

6. **Data Sources**
   - Additional health facility sources
   - Education facilities
   - Water points

7. **Visualization**
   - 3D terrain visualization
   - Time-series animations
   - Dashboard with summary statistics

## Questions?

If you have questions about contributing, please:
- Open a discussion on GitHub
- Check existing issues and PRs
- Review the documentation

## License

By contributing to GeoReach, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to GeoReach! 🌍
