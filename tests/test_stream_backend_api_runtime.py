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


def test_system_critical_spine_endpoint():
    client = TestClient(app)
    res = client.get("/api/system/critical-spine", params={"sample_size": 700})
    assert res.status_code == 200
    body = res.json()
    assert body["sample_size"] == 700
    assert "visuals" in body
    assert "dashFieldMap" in body["visuals"]


def test_system_runtime_endpoint():
    client = TestClient(app)
    res = client.get("/api/system/runtime", params={"sample_size": 600})
    assert res.status_code == 200
    body = res.json()
    assert body["sample_size"] == 600
    assert "orchestration" in body
    assert "catalog" in body


def test_public_shell_support_files_are_served():
    client = TestClient(app)

    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert "LOOPCHii Stream" in manifest.text

    service_worker = client.get("/service-worker.js")
    assert service_worker.status_code == 200
    assert "CACHE_NAME" in service_worker.text

    openapi_export = client.get("/openapi.stream.json")
    assert openapi_export.status_code == 200
    assert openapi_export.json()["info"]["title"] == "LOOPCHii Stream API"

    brand_asset = client.get("/assets/loopchii.svg")
    assert brand_asset.status_code == 200
    assert "<svg" in brand_asset.text
