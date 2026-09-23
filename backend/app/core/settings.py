"""Application settings, persisted to data/config.json."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

DEFAULT_CONFIG_PATH = Path("data/config.json")


def config_path() -> Path:
    """Resolve the config file, honouring DATA_DIR so tests can redirect it."""
    data_dir = os.environ.get("DATA_DIR")
    if data_dir:
        return Path(data_dir) / "config.json"
    return DEFAULT_CONFIG_PATH


class Settings(BaseModel):
    keys: list[str] = Field(default_factory=list)
    qps: float = Field(default=3.0, ge=0, le=1000)  # 0 means no rate limit
    daily_limit_per_key: int = Field(default=4500, gt=0)
    default_region: str = "440100"
    sleep_every: int = Field(default=20, ge=0)
    sleep_min_seconds: float = Field(default=3.0, ge=0)
    sleep_max_seconds: float = Field(default=8.0, ge=0)
    poi_page_size: int = Field(default=25, ge=1, le=25)
    poi_max_pages: int = Field(default=1, ge=1, le=8)
    typecode_prefix: str = "11"

    @model_validator(mode="after")
    def _check_sleep_window(self) -> "Settings":
        if self.sleep_min_seconds > self.sleep_max_seconds:
            raise ValueError("sleep_min_seconds must not exceed sleep_max_seconds")
        return self


class ConfigPayload(Settings):
    """Request body for PUT /api/config."""


class ConfigView(BaseModel):
    keys_masked: list[str]
    key_count: int
    qps: float
    daily_limit_per_key: int
    default_region: str
    sleep_every: int
    sleep_min_seconds: float
    sleep_max_seconds: float
    poi_page_size: int
    poi_max_pages: int
    typecode_prefix: str


def load_settings() -> Settings:
    path = config_path()
    if path.exists():
        return Settings.model_validate_json(path.read_text(encoding="utf-8"))
    return Settings()


def save_settings(settings: Settings) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(settings.model_dump_json(indent=2), encoding="utf-8")


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def to_view(settings: Settings) -> ConfigView:
    return ConfigView(
        keys_masked=[mask_key(k) for k in settings.keys],
        key_count=len(settings.keys),
        qps=settings.qps,
        daily_limit_per_key=settings.daily_limit_per_key,
        default_region=settings.default_region,
        sleep_every=settings.sleep_every,
        sleep_min_seconds=settings.sleep_min_seconds,
        sleep_max_seconds=settings.sleep_max_seconds,
        poi_page_size=settings.poi_page_size,
        poi_max_pages=settings.poi_max_pages,
        typecode_prefix=settings.typecode_prefix,
    )
