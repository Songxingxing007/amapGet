from fastapi.testclient import TestClient

from app.main import app

CSV = (
    "公园名称,行政区\n"
    "越秀公园,越秀区\n"
    "天河公园,天河区\n"
    "流花湖公园,越秀区\n"
).encode("utf-8")


def _seed(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    client = TestClient(app)
    created = client.post(
        "/api/tasks",
        files={"file": ("sample.csv", CSV, "text/csv")},
        data={"name_column": "公园名称", "adname_column": "行政区"},
    ).json()
    return client, created["task_id"]


def test_filter_by_adname_and_keyword(tmp_path, monkeypatch):
    client, task_id = _seed(tmp_path, monkeypatch)
    got = client.get("/api/records", params={"task_id": task_id, "adname": "越秀区"}).json()
    assert got["total"] == 2
    got = client.get("/api/records", params={"task_id": task_id, "keyword": "天河"}).json()
    assert got["total"] == 1
    assert got["items"][0]["query_name"] == "天河公园"


def test_pagination_and_ids(tmp_path, monkeypatch):
    client, task_id = _seed(tmp_path, monkeypatch)
    page = client.get("/api/records", params={"task_id": task_id, "page": 2, "page_size": 2}).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1
    assert len(page["ids"]) == 3
    ids_only = client.get("/api/records", params={"task_id": task_id, "all_ids_only": True}).json()
    assert ids_only["items"] == []
    assert ids_only["ids"] == page["ids"]


def test_unknown_task_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert TestClient(app).get("/api/records", params={"task_id": 42}).status_code == 404
