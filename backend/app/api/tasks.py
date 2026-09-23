"""Task endpoints: upload, run, pause, and export."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.core.settings import load_settings
from app.db.models import Record, Task
from app.db.session import get_engine, init_db
from app.services import runtime
from app.services.export import dumps, to_csv, to_geojson
from app.services.ingest import detect_columns, read_table
from app.services.pipeline_aoi import run_aoi_task
from app.services.pipeline_poi import run_poi_task

router = APIRouter(tags=["tasks"])


class PreviewResult(BaseModel):
    columns: list[str]
    rows: list[list[str]]
    suggested_name_column: str | None
    suggested_adname_column: str | None
    name_confidence: str
    row_count_preview: int


class TaskCreated(BaseModel):
    task_id: int
    total: int
    skipped: int


class TaskView(BaseModel):
    id: int
    kind: str
    status: str
    source_filename: str
    total: int
    done: int
    failed: int
    paused_reason: str


class RunResult(BaseModel):
    started: bool
    pending: int


class AoiRequest(BaseModel):
    record_ids: list[int]


def _task_view(task: Task) -> TaskView:
    return TaskView(
        id=task.id or 0,
        kind=task.kind,
        status=task.status,
        source_filename=task.source_filename,
        total=task.total,
        done=task.done,
        failed=task.failed,
        paused_reason=task.paused_reason,
    )


@router.post("/tasks/preview", response_model=PreviewResult)
async def preview_task(file: UploadFile = File(...), max_rows: int = 10) -> PreviewResult:
    content = await file.read()
    table = read_table(file.filename or "", content, max_rows=max_rows)
    if not table.columns:
        raise HTTPException(status_code=400, detail="file has no header row")
    detection = detect_columns(table)
    return PreviewResult(
        columns=table.columns,
        rows=table.rows,
        suggested_name_column=detection.name_column,
        suggested_adname_column=detection.adname_column,
        name_confidence=detection.confidence,
        row_count_preview=len(table.rows),
    )


@router.post("/tasks", response_model=TaskCreated)
async def create_task(
    file: UploadFile = File(...),
    name_column: str = Form(...),
    adname_column: str | None = Form(default=None),
) -> TaskCreated:
    content = await file.read()
    table = read_table(file.filename or "", content)
    if not table.rows:
        raise HTTPException(status_code=422, detail="file has no data rows")
    if name_column not in table.columns:
        raise HTTPException(status_code=400, detail=f"column not found: {name_column}")
    name_index = table.columns.index(name_column)
    adname_index = table.columns.index(adname_column) if adname_column in table.columns else None
    init_db()
    skipped = 0
    with Session(get_engine()) as session:
        task = Task(kind="poi", status="pending", source_filename=file.filename or "", total=0)
        session.add(task)
        session.commit()
        session.refresh(task)
        created = 0
        for row in table.rows:
            name = row[name_index].strip() if name_index < len(row) else ""
            if not name:
                skipped += 1
                continue
            adname = row[adname_index].strip() if adname_index is not None and adname_index < len(row) else ""
            session.add(Record(task_id=task.id, query_name=name, adname=adname, aoi_status="pending"))
            created += 1
        task.total = created
        session.add(task)
        session.commit()
        task_id = task.id or 0
    return TaskCreated(task_id=task_id, total=created, skipped=skipped)


@router.get("/tasks", response_model=list[TaskView])
def list_tasks() -> list[TaskView]:
    init_db()
    with Session(get_engine()) as session:
        return [_task_view(t) for t in session.exec(select(Task).order_by(Task.id.desc())).all()]


@router.get("/tasks/{task_id}", response_model=TaskView)
def get_task(task_id: int) -> TaskView:
    init_db()
    with Session(get_engine()) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        done = session.exec(
            select(func.count()).select_from(Record).where(Record.task_id == task_id, Record.aoi_status != "pending")
        ).one()
        failed = session.exec(
            select(func.count()).select_from(Record).where(Record.task_id == task_id, Record.error_code != "")
        ).one()
        task.done = int(done)
        task.failed = int(failed)
        return _task_view(task)


@router.post("/tasks/{task_id}/run", response_model=RunResult)
async def run_task(task_id: int, sync: bool = Query(default=False)) -> RunResult:
    init_db()
    with Session(get_engine()) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        pending = session.exec(
            select(func.count())
            .select_from(Record)
            .where(Record.task_id == task_id, Record.poi_id == "", Record.error_code == "")
        ).one()
    settings = load_settings()
    runtime.resume(task_id)
    if sync:
        await run_poi_task(task_id, settings)
    else:
        runtime.track(task_id, asyncio.create_task(run_poi_task(task_id, settings)))
    return RunResult(started=True, pending=int(pending))


@router.post("/tasks/{task_id}/aoi", response_model=RunResult)
async def run_aoi(task_id: int, payload: AoiRequest, sync: bool = Query(default=False)) -> RunResult:
    init_db()
    with Session(get_engine()) as session:
        if not session.get(Task, task_id):
            raise HTTPException(status_code=404, detail="task not found")
    if not payload.record_ids:
        raise HTTPException(status_code=422, detail="record_ids must not be empty")
    settings = load_settings()
    runtime.resume(task_id)
    if sync:
        await run_aoi_task(task_id, payload.record_ids, settings)
    else:
        runtime.track(task_id, asyncio.create_task(run_aoi_task(task_id, payload.record_ids, settings)))
    return RunResult(started=True, pending=len(payload.record_ids))


@router.post("/tasks/{task_id}/pause", response_model=TaskView)
def pause_task(task_id: int) -> TaskView:
    init_db()
    runtime.pause(task_id)
    with Session(get_engine()) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        task.status = "paused"
        task.paused_reason = "\u624b\u52a8\u6682\u505c"
        session.add(task)
        session.commit()
        return _task_view(task)


@router.post("/tasks/{task_id}/resume", response_model=TaskView)
def resume_task(task_id: int) -> TaskView:
    init_db()
    runtime.resume(task_id)
    with Session(get_engine()) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        task.status = "pending"
        task.paused_reason = ""
        session.add(task)
        session.commit()
        return _task_view(task)


@router.get("/tasks/{task_id}/export")
def export_task(
    task_id: int,
    format: str = Query(default="csv", pattern="^(csv|geojson)$"),
    crs: str = Query(default="wgs84", pattern="^(gcj02|wgs84)$"),
) -> Response:
    init_db()
    with Session(get_engine()) as session:
        if not session.get(Task, task_id):
            raise HTTPException(status_code=404, detail="task not found")
        records = session.exec(select(Record).where(Record.task_id == task_id).order_by(Record.id)).all()
    if format == "csv":
        return PlainTextResponse(
            to_csv(records),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="task-{task_id}.csv"'},
        )
    return Response(
        content=dumps(to_geojson(records, crs)),
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="task-{task_id}-{crs}.geojson"'},
    )
