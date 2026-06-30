from __future__ import annotations

from pathlib import Path

from stream_backend.cli.doctor import build_report


def test_stream_doctor_report_has_core_checks():
    report = build_report(Path(__file__).resolve().parents[1])
    assert report["overall"] in {"pass", "warn"}
    names = {row["name"] for row in report["checks"]}
    assert "python" in names
    assert "music-load" in names
    assert "music-genre-coverage" in names
    assert "decision-lab" in names
