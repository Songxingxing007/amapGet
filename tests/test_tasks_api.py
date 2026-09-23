import io

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app

CSV = (
    "名称,行政区\n"
    "越秀公园,越秀区\n"
    "天河公园,天河区\n"
    ",海珠区\n"
).encode("utf-8")


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return TestClient(app)


def test_preview_csv(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.post("/api/tasks/preview", files={"file": ("sample.csv", CSV, "text/csv")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["columns"] == ["名称", "行政区"]
    assert body["suggested_name_column"] == "名称"
    assert body["suggested_adname_column"] == "行政区"
    assert len(body["rows"]) == 3


def test_preview_xlsx(tmp_path, monkeypatch):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["公园名称", "行政区"])
    sheet.append(["越秀公园", "越秀区"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    client = _client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/tasks/preview",
        files={
            "file": (
                "sample.xlsx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 200
    assert resp.json()["suggested_name_column"] == "公园名称"


def test_create_task_skips_blank_names(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/tasks",
        files={"file": ("sample.csv", CSV, "text/csv")},
        data={"name_column": "名称", "adname_column": "行政区"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["skipped"] == 1
    task_id = body["task_id"]
    got = client.get(f"/api/tasks/{task_id}").json()
    assert got["total"] == 2
    assert got["status"] == "pending"
    assert got["done"] == 0
    records = client.get("/api/records", params={"task_id": task_id}).json()
    assert records["total"] == 2
    assert records["items"][0]["query_name"] == "越秀公园"
    assert records["items"][0]["adname"] == "越秀区"


def test_create_task_rejects_unknown_column(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/tasks",
        files={"file": ("sample.csv", CSV, "text/csv")},
        data={"name_column": "不存在"},
    )
    assert resp.status_code == 400


def test_get_unknown_task_returns_404(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    assert client.get("/api/tasks/999").status_code == 404

def test_preview_rejects_empty_file(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.post("/api/tasks/preview", files={"file": ("empty.csv", b"", "text/csv")})
    assert resp.status_code == 400


def test_create_task_rejects_header_only_file(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/tasks",
        files={"file": ("only.csv", "\u540d\u79f0,\u884c\u653f\u533a".encode("utf-8"), "text/csv")},
        data={"name_column": "\u540d\u79f0"},
    )
    assert resp.status_code == 422


def test_ten_thousand_rows_import_quickly(tmp_path, monkeypatch):
    import time

    client = _client(tmp_path, monkeypatch)
    lines = ["\u540d\u79f0,\u884c\u653f\u533a"]
    lines += [f"\u6d4b\u8bd5\u516c\u56ed{i},\u8d8a\u79c0\u533a" for i in range(10000)]
    payload = chr(10).join(lines).encode("utf-8")
    started = time.perf_counter()
    resp = client.post(
        "/api/tasks",
        files={"file": ("big.csv", payload, "text/csv")},
        data={"name_column": "\u540d\u79f0", "adname_column": "\u884c\u653f\u533a"},
    )
    elapsed = time.perf_counter() - started
    assert resp.status_code == 200
    assert resp.json()["total"] == 10000
    assert elapsed < 30, elapsed
    task_id = resp.json()["task_id"]
    page = client.get("/api/records", params={"task_id": task_id, "page": 200, "page_size": 50}).json()
    assert page["total"] == 10000
    assert len(page["items"]) == 50
