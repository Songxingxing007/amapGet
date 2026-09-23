import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.settings import Settings
from app.db.models import Record, Task
from app.db.session import get_engine
from app.main import app
from app.services.pipeline_poi import run_poi_task

POI = "https://restapi.amap.com/v5/place/text"
CSV = (
    "\u540d\u79f0,\u884c\u653f\u533a@@NL@@"
    "\u8d8a\u79c0\u516c\u56ed,\u8d8a\u79c0\u533a@@NL@@"
    "\u4e0d\u5b58\u5728\u7684\u516c\u56ed,\u5929\u6cb3\u533a@@NL@@"
).replace("@@NL@@", chr(10)).encode("utf-8")


def _task(tmp_path, monkeypatch) -> tuple[TestClient, int]:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    client = TestClient(app)
    created = client.post(
        "/api/tasks",
        files={"file": ("sample.csv", CSV, "text/csv")},
        data={"name_column": "\u540d\u79f0"},
    ).json()
    return client, created["task_id"]


def _settings() -> Settings:
    return Settings(keys=["testkey"], qps=0, sleep_every=0, daily_limit_per_key=50, typecode_prefix="")


@respx.mock
@pytest.mark.asyncio
async def test_round_one_expands_candidates_and_marks_misses(tmp_path, monkeypatch):
    _, task_id = _task(tmp_path, monkeypatch)
    payload = {
        "status": "1",
        "info": "OK",
        "infocode": "10000",
        "pois": [
            {
                "id": "B00140BNNF",
                "name": "\u8d8a\u79c0\u516c\u56ed",
                "type": "\u516c\u56ed",
                "typecode": "110101",
                "address": "A",
                "adname": "\u8d8a\u79c0\u533a",
                "location": "113.265561,23.140096",
            },
            {
                "id": "B0KUN7TSUW",
                "name": "\u8d8a\u79c0\u516c\u56ed(\u5730\u94c1\u7ad9)",
                "type": "\u5730\u94c1\u7ad9",
                "typecode": "150500",
                "address": "B",
                "adname": "\u8d8a\u79c0\u533a",
                "location": "113.264354,23.139941",
            },
        ],
    }
    respx.get(POI).mock(
        side_effect=[
            httpx.Response(200, json=payload),
            httpx.Response(200, json={"status": "1", "info": "OK", "infocode": "10000", "pois": []}),
        ]
    )
    await run_poi_task(task_id, _settings())

    with Session(get_engine()) as session:
        records = session.exec(select(Record).where(Record.task_id == task_id).order_by(Record.id)).all()
        task = session.get(Task, task_id)

    assert task is not None and task.status == "done"
    assert len(records) == 3
    by_poi = {record.poi_id: record for record in records if record.poi_id}
    park = by_poi["B00140BNNF"]
    assert park.match_level == "exact"
    assert park.lng_wgs84 is not None and park.lat_wgs84 is not None
    extra = by_poi["B0KUN7TSUW"]
    assert extra.match_level == "contains"
    assert extra.query_name == park.query_name
    miss = next(record for record in records if record.error_code == "no_result")
    assert miss.aoi_status == "error"


@respx.mock
@pytest.mark.asyncio
async def test_quota_error_pauses_the_task(tmp_path, monkeypatch):
    _, task_id = _task(tmp_path, monkeypatch)
    respx.get(POI).mock(
        return_value=httpx.Response(200, json={"status": "0", "info": "DAILY_QUERY_OVER_LIMIT", "infocode": "10044"})
    )
    await run_poi_task(task_id, _settings())
    with Session(get_engine()) as session:
        task = session.get(Task, task_id)
    assert task is not None
    assert task.status == "paused"
    assert "\u914d\u989d" in task.paused_reason

@pytest.mark.asyncio
async def test_overlong_name_is_rejected_without_calling_amap(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    client = TestClient(app)
    long_name = "\u6d4b" * 90
    created = client.post(
        "/api/tasks",
        files={"file": ("c.csv", f"\u540d\u79f0{chr(10)}{long_name}{chr(10)}".encode("utf-8"), "text/csv")},
        data={"name_column": "\u540d\u79f0"},
    ).json()
    route = respx.get(POI).mock(return_value=httpx.Response(200, json={"status": "1", "pois": []}))
    await run_poi_task(created["task_id"], _settings())
    assert route.call_count == 0
    with Session(get_engine()) as session:
        record = session.exec(select(Record).where(Record.task_id == created["task_id"])).one()
    assert record.error_code == "name_too_long"
