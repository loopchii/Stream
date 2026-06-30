from __future__ import annotations

from stream_backend.config import RuntimeConfig


def build_runtime_catalog(config: RuntimeConfig) -> dict:
    return {
        "runtime": "stream_backend",
        "languages": ["Python", "SQLite", "JavaScript", "HTML", "Rust"],
        "modules": [
            "analytics",
            "orchestration",
            "store",
            "exporters",
            "services",
            "cli",
        ],
        "sqlite_path": str(config.sqlite_path.relative_to(config.base_dir)),
    }
