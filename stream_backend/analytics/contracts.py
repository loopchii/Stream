from __future__ import annotations

from typing import Any, Mapping

from stream_backend.config import RuntimeConfig


def build_backend_contract_surface(
    config: RuntimeConfig,
    latest_run: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "runtime": "stream_backend",
        "languages": ["Python", "HTML", "JavaScript", "Rust", "WASM"],
        "targets": list(config.build_targets),
        "sqlite_path": str(config.sqlite_path.relative_to(config.base_dir)),
        "sample_sizes": list(config.sample_sizes),
        "latest_run_id": (latest_run or {}).get("run_id"),
        "notes": list(config.notes),
    }
