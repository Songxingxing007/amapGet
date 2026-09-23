"""Record listing with the filters the result table needs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.models import Record, Task
from app.db.session import get_engine, init_db

router = APIRouter(tags=["records"])


class RecordRow(BaseModel):
    id: int
    task_id: int
    query_name: str
    match_level: str
    poi_name: str
    poi_id: str
    poi_type: str
    typecode: str
    address: str
    adname: str
    lng_gcj02: float | None
    lat_gcj02: float | None
    lng_wgs84: float | None
    lat_wgs84: float | None
    aoi_status: str
    aoi_area_ha: float | None
    selected: bool


class RecordPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RecordRow]
    ids: list[int]


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get("/records", response_model=RecordPage)
def list_records(
    task_id: int,
    match_level: str | None = None,
    adname: str | None = None,
    keyword: str | None = None,
    has_aoi: bool | None = None,
    selected: bool | None = None,
    page: int = 1,
    page_size: int = 50,
    all_ids_only: bool = False,
) -> RecordPage:
    init_db()
    if page < 1 or page_size < 1 or page_size > 500:
        raise HTTPException(status_code=422, detail="page must be >=1 and page_size between 1 and 500")
    with Session(get_engine()) as session:
        if not session.get(Task, task_id):
            raise HTTPException(status_code=404, detail="task not found")
        statement = select(Record).where(Record.task_id == task_id)
        levels = _split(match_level)
        if levels:
            statement = statement.where(Record.match_level.in_(levels))
        adnames = _split(adname)
        if adnames:
            statement = statement.where(Record.adname.in_(adnames))
        if keyword:
            pattern = f"%{keyword}%"
            statement = statement.where(Record.query_name.like(pattern) | Record.poi_name.like(pattern))
        if has_aoi is not None:
            statement = statement.where(Record.aoi_status == ("ok" if has_aoi else "pending"))
        if selected is not None:
            statement = statement.where(Record.selected == selected)
        all_rows = session.exec(statement.order_by(Record.id)).all()
        ids = [r.id or 0 for r in all_rows]
        if all_ids_only:
            return RecordPage(total=len(ids), page=1, page_size=len(ids), items=[], ids=ids)
        start = (page - 1) * page_size
        window = all_rows[start : start + page_size]
        items = [
            RecordRow(
                id=r.id or 0,
                task_id=r.task_id,
                query_name=r.query_name,
                match_level=r.match_level,
                poi_name=r.poi_name,
                poi_id=r.poi_id,
                poi_type=r.poi_type,
                typecode=r.typecode,
                address=r.address,
                adname=r.adname,
                lng_gcj02=r.lng_gcj02,
                lat_gcj02=r.lat_gcj02,
                lng_wgs84=r.lng_wgs84,
                lat_wgs84=r.lat_wgs84,
                aoi_status=r.aoi_status,
                aoi_area_ha=r.aoi_area_ha,
                selected=r.selected,
            )
            for r in window
        ]
        return RecordPage(total=len(ids), page=page, page_size=page_size, items=items, ids=ids)
