"""Database models for tasks, records and key usage."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Task(SQLModel, table=True):
    """One upload job: round 1 (poi) or round 2 (aoi)."""

    id: int | None = Field(default=None, primary_key=True)
    kind: str = Field(default="poi")
    status: str = Field(default="pending", index=True)
    source_filename: str = ""
    total: int = 0
    done: int = 0
    failed: int = 0
    paused_reason: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Record(SQLModel, table=True):
    """One POI candidate, optionally enriched with an AOI boundary."""

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(index=True, foreign_key="task.id")
    query_name: str = Field(index=True)
    match_level: str = ""
    poi_name: str = ""
    poi_id: str = Field(default="", index=True)
    poi_type: str = ""
    typecode: str = ""
    address: str = ""
    adname: str = ""
    lng_gcj02: float | None = None
    lat_gcj02: float | None = None
    lng_wgs84: float | None = None
    lat_wgs84: float | None = None
    aoi_status: str = Field(default="pending", index=True)
    polyline_gcj02: str = ""
    aoi_area_ha: float | None = None
    selected: bool = Field(default=False)
    error_code: str = ""
    error_msg: str = ""
    updated_at: datetime = Field(default_factory=utcnow)


class KeyState(SQLModel, table=True):
    """Per-key daily request counter and disabled flag."""

    key_masked: str = Field(primary_key=True)
    used_today: int = 0
    disabled: bool = False
    last_used_at: datetime | None = None
