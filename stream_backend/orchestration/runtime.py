from __future__ import annotations

from typing import Any

from stream_backend.config import RuntimeConfig


def build_orchestration_surface(
    config: RuntimeConfig,
    generated_at: str,
    sample_size: int,
) -> dict[str, Any]:
    return {
        "runtime": "stream_backend",
        "generated_at": generated_at,
        "sample_size": sample_size,
        "languages": list(config.tags),
        "targets": list(config.build_targets),
        "sqlite_path": str(config.sqlite_path.relative_to(config.base_dir)),
        "jobs": [
            {
                "name": "representation",
                "description": "Synthetic representation analysis and export.",
                "output_name": "analysis_results.json",
            },
            {
                "name": "music",
                "description": "Public music analysis and quality reporting.",
                "output_name": "data/music/*.json",
            },
            {
                "name": "music_intelligence",
                "description": "Catalog + notation harvest for deeper note-level reasoning.",
                "output_name": "music_index.json",
            },
            {
                "name": "frontend_state",
                "description": "Generated runtime payload for the browser surface.",
                "output_name": "data/system/frontend-state.json",
            },
        ],
    }
