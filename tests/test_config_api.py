from fastapi.testclient import TestClient

from app.main import app


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return TestClient(app)


def test_config_roundtrip_masks_keys(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    payload = {
        "keys": ["abcd1234efgh5678", "  "],
        "qps": 2.0,
        "daily_limit_per_key": 100,
        "default_region": "440100",
    }
    assert client.put("/api/config", json=payload).status_code == 200
    got = client.get("/api/config").json()
    assert got["key_count"] == 1
    assert got["keys_masked"][0] == "abcd********5678"
    assert got["qps"] == 2.0
    assert got["daily_limit_per_key"] == 100
    assert got["sleep_every"] == 20


def test_put_config_rejects_blank_keys(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.put("/api/config", json={"keys": ["   "]})
    assert resp.status_code == 422


def test_put_config_rejects_inverted_sleep_window(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.put(
        "/api/config",
        json={"keys": ["abcd1234efgh5678"], "sleep_min_seconds": 9, "sleep_max_seconds": 3},
    )
    assert resp.status_code == 422
