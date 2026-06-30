from __future__ import annotations

from stream_backend.exporters.markdown_exports import write_runtime_markdown
from tests.runtime_fixtures import build_runtime


def test_markdown_export_contains_runtime_summary(tmp_path):
    runtime = build_runtime(tmp_path)
    payload = runtime.build_snapshot(sample_size=900)
    output = write_runtime_markdown(tmp_path / "runtime.md", payload)
    text = output.read_text(encoding="utf-8")
    assert "Stream Runtime Surface" in text
    assert "Hero Signals" in text
    assert "Representation parity" in text
