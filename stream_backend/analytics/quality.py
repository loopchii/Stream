from __future__ import annotations

from typing import Any, Mapping


def build_runtime_quality_surface(
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
    data_engineering: Mapping[str, Any],
) -> dict[str, Any]:
    representation_checks = (data_engineering.get("synthetic_contract") or {}).get("quality_checks", [])
    music_checks = (data_engineering.get("music_contract") or {}).get("quality_checks", [])
    return {
        "representation_checks": representation_checks,
        "music_checks": music_checks,
        "music_quality": music_report.get("quality", {}),
        "representation_scorecard": representation.get("advanced_metrics", {}),
    }
