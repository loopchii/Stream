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
        "connectivity": {
            "api": "/api/*",
            "swagger": "/docs",
            "openapi": "/openapi.json",
            "static_bundle": "data/system/*.json",
            "offline_shell": "manifest.webmanifest + service-worker.js",
            "doctor": "python -m stream_backend.cli.doctor",
        },
        "jobs": [
            {
                "name": "representation",
                "description": "Synthetic representation analysis and export.",
                "output_name": "analysis_results.json",
                "depends_on": ["DataProcessor.generate_synthetic_data", "streamlens_processor.process_data"],
            },
            {
                "name": "music",
                "description": "Public music analysis and quality reporting.",
                "output_name": "data/music/*.json",
                "depends_on": ["music_pipeline.load_enriched_dataset", "music_pipeline.full_report"],
            },
            {
                "name": "decision_lab",
                "description": "Cohort drift, controlled comparisons, and trust posture for the public music lane.",
                "output_name": "data/music/decision-lab.json",
                "depends_on": ["music_decision_lab.build_decision_lab"],
            },
            {
                "name": "music_intelligence",
                "description": "Catalog + notation harvest for deeper note-level reasoning.",
                "output_name": "music_index.json",
                "depends_on": ["music_intelligence.build_music_data_package"],
            },
            {
                "name": "frontend_state",
                "description": "Generated runtime payload for the browser surface.",
                "output_name": "data/system/frontend-state.json",
                "depends_on": ["stream_backend.analytics", "data_engineering.build_data_engineering_snapshot"],
            },
            {
                "name": "critical_spine",
                "description": "Per-visual purpose, limitation, and improvement guidance.",
                "output_name": "data/system/critical-spine.json",
                "depends_on": ["stream_backend.analytics.build_critical_spine"],
            },
            {
                "name": "openapi_export",
                "description": "Static OpenAPI contract for contributors and offline readers.",
                "output_name": "openapi.stream.json",
                "depends_on": ["FastAPI.app.openapi"],
            },
        ],
    }
