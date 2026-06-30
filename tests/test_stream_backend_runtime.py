from __future__ import annotations

from tests.runtime_fixtures import build_runtime


def test_runtime_materializes_json_sqlite_and_markdown(tmp_path):
    runtime = build_runtime(tmp_path)
    payload = runtime.materialize(sample_size=1200, persist_sqlite=True)

    assert payload["sample_size"] == 1200
    assert "frontend_state" in payload
    assert "comparatives" in payload
    assert runtime.config.sqlite_path.exists()
    assert (tmp_path / "data" / "system" / "frontend-state.json").exists()
    assert (tmp_path / "data" / "system" / "critical-spine.json").exists()
    assert (tmp_path / "data" / "system" / "comparatives.json").exists()
    assert (tmp_path / "data" / "system" / "runtime.json").exists()
    assert (tmp_path / "data" / "system" / "contracts.json").exists()
    assert (tmp_path / "data" / "system" / "runtime_surface.md").exists()


def test_runtime_latest_snapshot_round_trips(tmp_path):
    runtime = build_runtime(tmp_path)
    payload = runtime.materialize(sample_size=5000, persist_sqlite=True)
    latest = runtime.latest_snapshot()

    assert latest is not None
    assert latest["run_id"] == payload["run_id"]
    assert latest["sample_size"] == 5000
    assert "frontend_state" in latest
    assert "critical_spine" in latest
