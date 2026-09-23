"""Round 2: fetch AOI boundaries for the selected records."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlmodel import Session

from app.core.settings import Settings
from app.db.models import Record, Task
from app.db.session import get_engine
from app.services import amap_errors, runtime
from app.services.geometry import parse_polyline, ring_area_ha
from app.services.keypool import KeyPool, Pacer
from app.services.pipeline_common import PAUSE_BUCKETS, call_with_key, pause_reason


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def run_aoi_task(task_id: int, record_ids: list[int], settings: Settings) -> None:
    engine = get_engine()
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            return
        task.kind = "aoi"
        task.status = "running"
        task.total = len(record_ids)
        task.done = 0
        task.failed = 0
        task.paused_reason = ""
        session.add(task)
        session.commit()

    pool = KeyPool(settings.keys, settings.daily_limit_per_key)
    pacer = Pacer(settings.qps, settings.sleep_every, settings.sleep_min_seconds, settings.sleep_max_seconds)

    async with httpx.AsyncClient(timeout=25.0) as http:
        for record_id in record_ids:
            if runtime.is_paused(task_id):
                _finish(task_id, status="paused", reason="\u624b\u52a8\u6682\u505c")
                return
            with Session(engine) as session:
                record = session.get(Record, record_id)
                poi_id = record.poi_id if record else ""
            if not poi_id:
                _store(engine, record_id, task_id, status="error", code="missing_poi")
                continue
            result, bucket = await call_with_key(
                lambda client, pid=poi_id: client.aoi_polyline(pid),
                pool,
                pacer,
                http,
                settings.default_region,
            )
            if bucket in PAUSE_BUCKETS:
                _finish(task_id, status="paused", reason=pause_reason(bucket))
                return
            if bucket:
                _store(engine, record_id, task_id, status="error", code=bucket, message=amap_errors.message(bucket))
                continue
            polyline = result if isinstance(result, str) else None
            if not polyline:
                _store(engine, record_id, task_id, status="no_aoi")
                continue
            ring = parse_polyline(polyline)
            _store(engine, record_id, task_id, status="ok", polyline=polyline, area=ring_area_ha(ring))
    _finish(task_id, status="done", reason="")


def _store(
    engine,
    record_id: int,
    task_id: int,
    *,
    status: str,
    code: str = "",
    message: str = "",
    polyline: str = "",
    area: float | None = None,
) -> None:
    with Session(engine) as session:
        record = session.get(Record, record_id)
        if record is not None:
            record.aoi_status = status
            record.error_code = code
            record.error_msg = message
            if polyline:
                record.polyline_gcj02 = polyline
            if area is not None:
                record.aoi_area_ha = area
            record.updated_at = _now()
            session.add(record)
        task = session.get(Task, task_id)
        if task is not None:
            task.done = (task.done or 0) + 1
            if status == "error":
                task.failed = (task.failed or 0) + 1
            task.updated_at = _now()
            session.add(task)
        session.commit()


def _finish(task_id: int, *, status: str, reason: str) -> None:
    with Session(get_engine()) as session:
        task = session.get(Task, task_id)
        if task is None:
            return
        task.status = status
        task.paused_reason = reason
        task.updated_at = _now()
        session.add(task)
        session.commit()
