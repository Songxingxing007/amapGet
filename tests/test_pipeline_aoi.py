import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.settings import Settings
from app.db.models import Record, Task
from app.db.session import get_engine
from app.main import app
from app.services.pipeline_aoi import run_aoi_task

AOI = "https://restapi.amap.com/v5/aoi/polyline"
RING = "113.26,23.14_113.27,23.14_113.27,23.15_113.26,23.15"


def _seed(tmp_path, monkeypatch) -> tuple[int, list[int]]:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    client = TestClient(app)
    created = client.post(
        "/api/tasks",
        files={"file": ("c.csv", "\u540d\u79f0@@NL@@\u8d8a\u79c0\u516c\u56ed@@NL@@".replace("@@NL@@", chr(10)).encode("utf-8"), "text/csv")},
        data={"name_column": "\u540d\u79f0"},
    ).json()
    task_id = created["task_id"]
    with Session(get_engine()) as session:
        record = session.exec(select(Record).where(Record.task_id == task_id)).one()
        record.poi_id = "B00140BNNF"
        record.poi_name = "\u8d8a\u79c0\u516c\u56ed"
        session.add(record)
        session.commit()
        record_id = record.id
    return task_id, [record_id]


def _settings() -> Settings:
    return Settings(keys=["testkey"], qps=0, sleep_every=0, daily_limit_per_key=50)


@respx.mock
@pytest.mark.asyncio
async def test_aoi_success_stores_polyline_and_area(tmp_path, monkeypatch):
    task_id, ids = _seed(tmp_path, monkeypatch)
    respx.get(AOI).mock(
        return_value=httpx.Response(
            200, json={"status": "1", "info": "OK", "infocode": "10000", "aois": [{"polyline": RING}]}
        )
    )
    await run_aoi_task(task_id, ids, _settings())
    with Session(get_engine()) as session:
        record = session.get(Record, ids[0])
    assert record is not None
    assert record.aoi_status == "ok"
    assert record.polyline_gcj02 == RING
    assert record.aoi_area_ha is not None and 100 < record.aoi_area_ha < 130


@respx.mock
@pytest.mark.asyncio
async def test_missing_aoi_is_recorded_without_error(tmp_path, monkeypatch):
    task_id, ids = _seed(tmp_path, monkeypatch)
    respx.get(AOI).mock(
        return_value=httpx.Response(200, json={"status": "1", "info": "OK", "infocode": "10000", "aois": []})
    )
    await run_aoi_task(task_id, ids, _settings())
    with Session(get_engine()) as session:
        record = session.get(Record, ids[0])
    assert record is not None
    assert record.aoi_status == "no_aoi"
    assert record.error_code == ""


@respx.mock
@pytest.mark.asyncio
async def test_permission_error_marks_the_record(tmp_path, monkeypatch):
    task_id, ids = _seed(tmp_path, monkeypatch)
    respx.get(AOI).mock(
        return_value=httpx.Response(
            200, json={"status": "0", "info": "INSUFFICIENT_PRIVILEGES", "infocode": "10012"}
        )
    )
    await run_aoi_task(task_id, ids, _settings())
    with Session(get_engine()) as session:
        record = session.get(Record, ids[0])
        task = session.get(Task, task_id)
    assert record is not None and task is not None
    # a key without AOI permission stays unusable, so the task pauses instead
    # of marking every record as failed
    assert task.status == "paused"
    assert "工单" in task.paused_reason
    assert record.aoi_status == "pending"
