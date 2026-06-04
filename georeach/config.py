"""Configuration management for GeoReach."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class BBox(BaseSettings):
    west: float
    south: float
    east: float
    north: float

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.west, self.south, self.east, self.north)


class StudyArea(BaseSettings):
    name: str
    admin_level: int
    country_code: str
    bbox: BBox


class CRS(BaseSettings):
    analysis: str
    storage: str


class H3Config(BaseSettings):
    resolution: int


class Database(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="georeach")
    user: str = Field(default="georeach")
    password: str = Field(default="georeach")

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class DataSource(BaseSettings):
    source: str
    url: str | None = None
    note: str | None = None
    year: int | None = None
    release: str | None = None
    theme: list[str] | None = None


class AccessibilityConfig(BaseSettings):
    threshold_km: float
    moderate_km: float
    method: str


class PriorityConfig(BaseSettings):
    exposure_weight: float
    accessibility_weight: float
    top_percentile: int


class AnalysisConfig(BaseSettings):
    accessibility: AccessibilityConfig
    priority: PriorityConfig


class OutputsConfig(BaseSettings):
    formats: list[str]
    compression: str


class LoggingConfig(BaseSettings):
    level: str
    format: str


class Config(BaseSettings):
    study_area: StudyArea
    crs: CRS
    h3: H3Config
    database: Database
    data_sources: dict[str, Any]
    analysis: AnalysisConfig
    outputs: OutputsConfig
    logging: LoggingConfig

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Config":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            raw_config = yaml.safe_load(f)

        raw_config = cls._expand_env_vars(raw_config)
        return cls(**raw_config)

    @staticmethod
    def _expand_env_vars(config: dict[str, Any]) -> dict[str, Any]:
        if isinstance(config, dict):
            return {k: Config._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [Config._expand_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            var_spec = config[2:-1]
            if ":" in var_spec:
                var_name, default = var_spec.split(":", 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_spec, "")
        return config


def load_config(config_path: Path | str | None = None) -> Config:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    return Config.from_yaml(config_path)
