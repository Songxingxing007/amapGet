"""Round 1: turn each query name into POI candidates."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from app.core.settings import Settings
from app.db.models import Record, Task
from app.db.session import get_engine
from app.services import amap_errors, coord as coord_service, runtime
from app.services.amap_client import SearchHit
from app.services.keypool import KeyPool, Pacer
from app.services.matching import classify_match
from app.services.pipeline_common import PAUSE_BUCKETS, call_with_key, pause_reason

# Amap rejects keywords longer than 80 characters, so we never spend a call on them.
MAX_KEYWORD_LEN = 80


def _now() -> datetime:
    return datetime.now(timezone.utc)


def apply_hit(record: Record, query_name: str, hit: SearchHit) -> None:
    record.poi_id = hit.poi_id
    record.poi_name = hit.name
    record.poi_type = hit.poi_type
    record.typecode = hit.typecode
    record.address = hit.address
    record.adname = hit.adname or record.adname
    record.match_level = classify_match(query_name, hit.name)
    record.lng_gcj02 = hit.lng
    record.lat_gcj02 = hit.lat
    if hit.lng is not None and hit.lat is not None:
        lng, lat = coord_service.gcj02_to_wgs84(hit.lng, hit.lat)
        record.lng_wgs84 = lng
        record.lat_wgs84 = lat
    record.updated_at = _now()


def extra_hit(query_name: str, hit: SearchHit, task_id: int) -> Record:
    row = Record(task_id=task_id, query_name=query_name, aoi_status="pending")
    apply_hit(row, query_name, hit)
    return row


async def run_poi_task(task_id: int, settings: Settings) -> None:
    engine = get_engine()
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            return
        task.status = "running"
        task.paused_reason = ""
        session.add(task)
        session.commit()
        pending = session.exec(
            select(Record).where(Record.task_id == task_id, Record.poi_id == "", Record.error_code == "")
        ).all()

    pool = KeyPool(settings.keys, settings.daily_limit_per_key)
    pacer = Pacer(settings.qps, settings.sleep_every, settings.sleep_min_seconds, settings.sleep_max_seconds)

    async with httpx.AsyncClient(timeout=25.0) as http:
        for row in pending:
            if runtime.is_paused(task_id):
                _finish(task_id, status="paused", reason="\u624b\u52a8\u6682\u505c")
                return
            if len(row.query_name) > MAX_KEYWORD_LEN:
                with Session(engine) as session:
                    current = session.get(Record, row.id)
                    if current is not None:
                        current.error_code = "name_too_long"
                        current.error_msg = f"\u540d\u79f0\u8d85\u8fc7 {MAX_KEYWORD_LEN} \u5b57\u7b26\uff0c\u9ad8\u5fb7\u4e0d\u63a5\u53d7"
                        current.aoi_status = "error"
                        session.add(current)
                    _bump(session, task_id, failed=True)
                    session.commit()
                continue
            result, bucket = await call_with_key(
                lambda client, name=row.query_name: client.search_poi(
                    name,
                    page_size=settings.poi_page_size,
                    max_pages=settings.poi_max_pages,
                    typecode_prefix=settings.typecode_prefix,
                ),
                pool,
                pacer,
                http,
                settings.default_region,
            )
            if bucket in PAUSE_BUCKETS:
                _finish(task_id, status="paused", reason=pause_reason(bucket))
                return
            hits: list[SearchHit] = list(result or [])
            with Session(engine) as session:
                current = session.get(Record, row.id)
                if current is None:
                    continue
                if bucket:
                    current.error_code = bucket
                    current.error_msg = amap_errors.message(bucket)
                    current.aoi_status = "error"
                elif not hits:
                    current.error_code = "no_result"
                    current.error_msg = "\u672a\u641c\u5230\u5339\u914d\u7684 POI\uff08\u53ef\u80fd\u88ab\u5206\u7c7b\u7801\u8fc7\u6ee4\uff09"
                    current.aoi_status = "error"
                else:
                    apply_hit(current, current.query_name, hits[0])
                    for hit in hits[1:]:
                        session.add(extra_hit(current.query_name, hit, task_id))
                session.add(current)
                _bump(session, task_id, failed=bool(bucket or not hits))
                session.commit()
    _finish(task_id, status="done", reason="")


def _bump(session: Session, task_id: int, *, failed: bool) -> None:
    task = session.get(Task, task_id)
    if task is None:
        return
    task.done = (task.done or 0) + 1
    if failed:
        task.failed = (task.failed or 0) + 1
    task.updated_at = _now()
    session.add(task)


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
