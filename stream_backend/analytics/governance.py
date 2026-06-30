from __future__ import annotations

from typing import Any, Mapping


def build_governance_surface(
    data_engineering: Mapping[str, Any],
    representation: Mapping[str, Any],
) -> dict[str, Any]:
    synthetic = data_engineering.get("synthetic_contract", {})
    music = data_engineering.get("music_contract", {})
    quality_checks = synthetic.get("quality_checks", []) + music.get("quality_checks", [])
    pass_count = sum(1 for check in quality_checks if check.get("status") == "pass")
    return {
        "quality_check_count": len(quality_checks),
        "pass_count": pass_count,
        "warn_count": sum(1 for check in quality_checks if check.get("status") == "warn"),
        "fail_count": sum(1 for check in quality_checks if check.get("status") == "fail"),
        "contracts": {
            "synthetic_dataset": synthetic.get("dataset_id"),
            "music_dataset": music.get("dataset_id"),
        },
        "insight_count": (
            len(representation.get("insights", []))
            if isinstance(representation.get("insights"), list)
            else 0
        ),
    }
