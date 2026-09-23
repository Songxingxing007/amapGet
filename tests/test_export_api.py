from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.models import Record, Task
from app.db.session import get_engine, init_db
from app.main import app
from app.services.export import CSV_FIELDS

RING = "113.26,23.14_113.27,23.14_113.27,23.15_113.26,23.15"


def _seed(tmp_path, monkeypatch) -> tuple[TestClient, int]:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    init_db()
    with Session(get_engine()) as session:
        task = Task(kind="poi", status="done", source_filename="c.csv", total=2)
        session.add(task)
        session.commit()
        session.refresh(task)
        session.add(
            Record(
                task_id=task.id,
                query_name="\u8d8a\u79c0\u516c\u56ed",
                match_level="exact",
                poi_name="\u8d8a\u79c0\u516c\u56ed",
                poi_id="B00140BNNF",
                typecode="110101",
                adname="\u8d8a\u79c0\u533a",
                lng_gcj02=113.265561,
                lat_gcj02=23.140096,
                lng_wgs84=113.2602,
                lat_wgs84=23.1417,
                aoi_status="ok",
                polyline_gcj02=RING,
                aoi_area_ha=113.2,
            )
        )
        session.add(
            Record(task_id=task.id, query_name="\u65e0 AOI \u7684\u516c\u56ed", aoi_status="no_aoi")
        )
        session.commit()
        task_id = task.id
    return TestClient(app), task_id


def test_csv_export_has_the_fixed_columns(tmp_path, monkeypatch):
    client, task_id = _seed(tmp_path, monkeypatch)
    resp = client.get(f"/api/tasks/{task_id}/export", params={"format": "csv"})
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert lines[0].split(",") == CSV_FIELDS
    assert len(lines) == 3


def test_geojson_export_only_includes_aoi_rows(tmp_path, monkeypatch):
    client, task_id = _seed(tmp_path, monkeypatch)
    resp = client.get(f"/api/tasks/{task_id}/export", params={"format": "geojson", "crs": "wgs84"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    ring = body["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]
    assert abs(ring[0][0] - 113.2601) < 0.01


def test_export_rejects_unknown_task(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert TestClient(app).get("/api/tasks/999/export").status_code == 404
