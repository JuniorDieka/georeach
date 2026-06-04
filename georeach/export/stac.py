"""Generate STAC catalog for outputs."""

from datetime import datetime
from pathlib import Path

from loguru import logger
from pystac import Asset, Catalog, Collection, Extent, Item, SpatialExtent, TemporalExtent

from georeach.config import Config


def generate_stac_catalog(config: Config) -> None:
    """Generate STAC catalog describing output assets."""
    logger.info("Generating STAC catalog")

    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog = Catalog(
        id="georeach-outputs",
        description="GeoReach flood exposure and accessibility analysis outputs",
    )

    bbox = config.study_area.bbox.to_tuple()
    spatial_extent = SpatialExtent(bboxes=[bbox])
    temporal_extent = TemporalExtent(intervals=[[datetime.now(), None]])
    extent = Extent(spatial=spatial_extent, temporal=temporal_extent)

    collection = Collection(
        id="georeach-analysis",
        description=f"Analysis results for {config.study_area.name}",
        extent=extent,
    )

    item = Item(
        id="georeach-results",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]],
                ]
            ],
        },
        bbox=bbox,
        datetime=datetime.now(),
        properties={
            "study_area": config.study_area.name,
            "h3_resolution": config.h3.resolution,
            "analysis_crs": config.crs.analysis,
        },
    )

    assets = {
        "h3_results": {
            "href": "./h3_results.parquet",
            "type": "application/vnd.apache.parquet",
            "roles": ["data"],
            "title": "H3 Grid Analysis Results",
        },
        "admin_results": {
            "href": "./admin_results.parquet",
            "type": "application/vnd.apache.parquet",
            "roles": ["data"],
            "title": "Admin Boundaries Results",
        },
        "population_cog": {
            "href": "./population_cog.tif",
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "roles": ["data"],
            "title": "Population Raster (COG)",
        },
        "flood_hazard_cog": {
            "href": "./flood_hazard_cog.tif",
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "roles": ["data"],
            "title": "Flood Hazard Raster (COG)",
        },
        "h3_tiles": {
            "href": "./h3_grid.pmtiles",
            "type": "application/vnd.pmtiles",
            "roles": ["tiles"],
            "title": "H3 Grid Vector Tiles",
        },
    }

    for asset_id, asset_info in assets.items():
        item.add_asset(
            asset_id,
            Asset(
                href=asset_info["href"],
                media_type=asset_info["type"],
                roles=asset_info["roles"],
                title=asset_info["title"],
            ),
        )

    collection.add_item(item)
    catalog.add_child(collection)

    catalog_path = output_dir / "catalog.json"
    catalog.normalize_and_save(str(output_dir), catalog_type="SELF_CONTAINED")

    logger.info(f"STAC catalog saved to {catalog_path}")
    logger.success("STAC catalog generation complete")
