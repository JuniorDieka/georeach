"""Command-line interface for GeoReach pipeline."""

from pathlib import Path

import typer
from loguru import logger

from georeach.config import load_config

app = typer.Typer(
    name="georeach",
    help="GeoReach: Flood-Exposure & Service-Accessibility Geospatial Platform",
    add_completion=False,
)


@app.command()
def ingest(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
    subset: bool = typer.Option(False, "--subset", help="Use subset data for demo"),
) -> None:
    """Ingest and preprocess source data."""
    config = load_config(config_path)
    logger.info(f"Starting data ingestion for {config.study_area.name}")

    from georeach.ingest.admin import ingest_admin_boundaries
    from georeach.ingest.flood import ingest_flood_hazard
    from georeach.ingest.health import ingest_health_facilities
    from georeach.ingest.overture import ingest_overture_data
    from georeach.ingest.population import ingest_population

    ingest_admin_boundaries(config, subset=subset)
    ingest_population(config, subset=subset)
    ingest_overture_data(config, subset=subset)
    ingest_health_facilities(config, subset=subset)
    ingest_flood_hazard(config, subset=subset)

    logger.success("Data ingestion complete")


@app.command()
def load(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
) -> None:
    """Load processed data into PostGIS."""
    config = load_config(config_path)
    logger.info("Loading data into PostGIS")

    from georeach.db.loader import load_all_data
    from georeach.db.schema import init_database

    init_database(config)
    load_all_data(config)

    logger.success("Data loaded into PostGIS")


@app.command()
def grid(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
) -> None:
    """Generate H3 hex grid and load into PostGIS."""
    config = load_config(config_path)
    logger.info(f"Generating H3 grid at resolution {config.h3.resolution}")

    from georeach.grid.h3_grid import generate_and_load_grid

    generate_and_load_grid(config)

    logger.success("H3 grid generated and loaded")


@app.command()
def exposure(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
) -> None:
    """Compute flood exposure analysis."""
    config = load_config(config_path)
    logger.info("Computing flood exposure")

    from georeach.analysis.exposure import compute_exposure

    compute_exposure(config)

    logger.success("Flood exposure analysis complete")


@app.command()
def accessibility(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
) -> None:
    """Compute service accessibility analysis."""
    config = load_config(config_path)
    logger.info("Computing service accessibility")

    from georeach.analysis.accessibility import compute_accessibility

    compute_accessibility(config)

    logger.success("Service accessibility analysis complete")


@app.command()
def priority(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
) -> None:
    """Compute priority index."""
    config = load_config(config_path)
    logger.info("Computing priority index")

    from georeach.analysis.priority import compute_priority

    compute_priority(config)

    logger.success("Priority index computed")


@app.command()
def export(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
) -> None:
    """Export results to cloud-native formats."""
    config = load_config(config_path)
    logger.info("Exporting results")

    from georeach.export.cog import export_cog
    from georeach.export.geoparquet import export_geoparquet
    from georeach.export.stac import generate_stac_catalog

    export_geoparquet(config)
    export_cog(config)
    generate_stac_catalog(config)

    logger.success("Export complete")


@app.command()
def tiles(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
) -> None:
    """Generate PMTiles for web map."""
    config = load_config(config_path)
    logger.info("Generating PMTiles")

    from georeach.tiles.pmtiles import generate_pmtiles

    generate_pmtiles(config)

    logger.success("PMTiles generated")


@app.command()
def pipeline(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
    subset: bool = typer.Option(False, "--subset", help="Use subset data for demo"),
) -> None:
    """Run the complete pipeline end-to-end."""
    config = load_config(config_path)
    logger.info(f"Starting full pipeline for {config.study_area.name}")

    ingest(config_path, subset)
    load(config_path)
    grid(config_path)
    exposure(config_path)
    accessibility(config_path)
    priority(config_path)
    export(config_path)
    tiles(config_path)

    logger.success("Pipeline complete!")


@app.command()
def version() -> None:
    """Show version information."""
    from georeach import __version__

    typer.echo(f"GeoReach version {__version__}")


if __name__ == "__main__":
    app()
