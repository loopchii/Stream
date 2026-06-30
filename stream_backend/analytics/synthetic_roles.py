from __future__ import annotations

from typing import Any, Mapping

from advanced_metrics import letter_grade


def build_synthetic_role_surface(representation: Mapping[str, Any]) -> dict[str, Any]:
    overall = representation.get("overall_metrics", {})
    advanced = representation.get("advanced_metrics", {})
    score = float(advanced.get("equity_score", 0.0) or 0.0)
    return {
        "researcher": {
            "title": "Research lane",
            "summary": (
                "Use the synthetic lane to test method, drift, and category "
                "structure before claiming anything about a private catalog."
            ),
        },
        "engineer": {
            "title": "Engineering lane",
            "summary": (
                "The representation surface is structured for reproducibility: "
                "deterministic seeds, explicit exports, and inspectable metrics."
            ),
        },
        "buyer": {
            "title": "Buyer lane",
            "summary": (
                "The public surface is strongest when it helps a team see where "
                "a narrow field is being mistaken for a neutral one."
            ),
        },
        "grade": letter_grade(score),
        "equity_score": round(score, 4),
        "diversity_index": round(float(overall.get("diversity_index", 0.0) or 0.0), 4),
    }
