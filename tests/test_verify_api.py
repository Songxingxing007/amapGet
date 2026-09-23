import httpx
import respx
from fastapi.testclient import TestClient

from app.main import app

GEO = "https://restapi.amap.com/v3/geocode/geo"
AOI = "https://restapi.amap.com/v5/aoi/polyline"


def _prepare(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    client = TestClient(app)
    client.put("/api/config", json={"keys": ["abcd1234efgh5678"], "default_region": "440100"})
    return client


@respx.mock
def test_verify_reports_aoi_permission_missing(tmp_path, monkeypatch):
    client = _prepare(tmp_path, monkeypatch)
    respx.get(GEO).mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "1",
                "info": "OK",
                "infocode": "10000",
                "geocodes": [
                    {"formatted_address": "广东省广州市越秀区越秀公园", "location": "113.264354,23.139941"}
                ],
            },
        )
    )
    respx.get(AOI).mock(
        return_value=httpx.Response(
            200,
            json={"status": "0", "info": "INSUFFICIENT_PRIVILEGES", "infocode": "10012"},
        )
    )
    got = client.post("/api/config/verify").json()
    assert got["key_status"] == "ok"
    assert got["geocode_location"] == "113.264354,23.139941"
    assert got["aoi_status"] == "insufficient_privileges"
    assert "ticket" in got["aoi_hint"]


@respx.mock
def test_verify_reports_aoi_available(tmp_path, monkeypatch):
    client = _prepare(tmp_path, monkeypatch)
    respx.get(GEO).mock(
        return_value=httpx.Response(
            200,
            json={"status": "1", "info": "OK", "infocode": "10000", "geocodes": [{"location": "113.1,23.1"}]},
        )
    )
    respx.get(AOI).mock(
        return_value=httpx.Response(
            200,
            json={"status": "1", "info": "OK", "infocode": "10000", "aois": [{"id": "B00140BNNF"}]},
        )
    )
    got = client.post("/api/config/verify").json()
    assert got["aoi_status"] == "ok"
    assert got["aoi_hint"] == ""


@respx.mock
def test_verify_flags_invalid_key(tmp_path, monkeypatch):
    client = _prepare(tmp_path, monkeypatch)
    respx.get(GEO).mock(
        return_value=httpx.Response(200, json={"status": "0", "info": "INVALID_USER_KEY", "infocode": "10001"})
    )
    respx.get(AOI).mock(
        return_value=httpx.Response(200, json={"status": "0", "info": "INVALID_USER_KEY", "infocode": "10001"})
    )
    got = client.post("/api/config/verify").json()
    assert got["key_status"] == "key_invalid"
    assert got["aoi_status"] == "key_invalid"


def test_verify_requires_configured_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert TestClient(app).post("/api/config/verify").status_code == 422
