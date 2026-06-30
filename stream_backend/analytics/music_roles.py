from __future__ import annotations

from typing import Any, Mapping


def build_music_role_surface(report: Mapping[str, Any]) -> dict[str, Any]:
    bias = report.get("bias", {})
    perspectives = bias.get("role_perspectives", {})
    overview = report.get("overview", {})
    return {
        "artist": {
            "title": "Artist read",
            "summary": perspectives.get(
                "artist",
                "Artists need to know which combinations are getting rewarded "
                "and which ones are being left structurally invisible.",
            ),
            "stakes": "Exposure, collaboration timing, release shape, and category crowding.",
        },
        "consumer": {
            "title": "Consumer read",
            "summary": perspectives.get(
                "consumer",
                "Consumers benefit when the field stays legible enough to tell "
                "popularity from distribution pressure.",
            ),
            "stakes": (
                "Discovery quality, variety, and whether recommendation loops "
                "keep collapsing back to the same center."
            ),
        },
        "business": {
            "title": "Business read",
            "summary": perspectives.get(
                "business",
                "Teams need to know whether growth is broadening the field or "
                "just amplifying already dominant channels.",
            ),
            "stakes": "Channel concentration, inventory risk, promotional efficiency, and repeatable lift.",
        },
        "research": {
            "title": "Research read",
            "summary": perspectives.get(
                "research",
                "Researchers need explicit claim boundaries, source cohorts, "
                "and caveats around public data quality.",
            ),
            "stakes": "Cohort integrity, feature leakage, and longitudinal comparability.",
        },
        "catalog_size": int(overview.get("n_songs", 0)),
    }
