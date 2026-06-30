from __future__ import annotations

from fastapi.testclient import TestClient

from app import app


def test_system_catalog_endpoint():
    client = TestClient(app)
    res = client.get("/api/system/catalog")
    assert res.status_code == 200
    body = res.json()
    assert body["runtime"] == "stream_backend"
    assert "Python" in body["languages"]
    assert "sqlite_path" in body


def test_system_frontend_state_endpoint():
    client = TestClient(app)
    res = client.get("/api/system/frontend-state", params={"sample_size": 500})
    assert res.status_code == 200
    body = res.json()
    assert "hero" in body
    assert "roles" in body
    assert "payload_hash" in body


def test_system_runtime_endpoint():
    client = TestClient(app)
    res = client.get("/api/system/runtime", params={"sample_size": 600})
    assert res.status_code == 200
    body = res.json()
    assert body["sample_size"] == 600
    assert "orchestration" in body
    assert "catalog" in body
