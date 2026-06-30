from __future__ import annotations

from typing import Any, Mapping

from stream_backend.config import RuntimeConfig


def build_backend_contract_surface(
    config: RuntimeConfig,
    latest_run: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "runtime": "stream_backend",
        "brand": "LOOPCHii Stream",
        "languages": ["Python", "HTML", "JavaScript", "Rust", "WASM"],
        "targets": list(config.build_targets),
        "sqlite_path": str(config.sqlite_path.relative_to(config.base_dir)),
        "sample_sizes": list(config.sample_sizes),
        "latest_run_id": (latest_run or {}).get("run_id"),
        "offline_assets": [
            "data/system/frontend-state.json",
            "data/system/critical-spine.json",
            "data/system/comparatives.json",
            "data/system/runtime.json",
        ],
        "developer_entrypoints": [
            "app.py",
            "build_static.py",
            "stream_backend/cli/materialize.py",
            "stream_backend/cli/validate.py",
        ],
        "api_docs": {
            "live_swagger": "/docs",
            "live_openapi": "/openapi.json",
            "static_openapi_export": "openapi.stream.json",
        },
        "notes": list(config.notes),
    }
