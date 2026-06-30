from __future__ import annotations

from typing import Any, Mapping


def build_music_role_surface(report: Mapping[str, Any]) -> dict[str, Any]:
    bias = report.get("bias", {})
    perspectives = bias.get("role_perspectives", {})
    overview = report.get("overview", {})

    def perspective_block(
        key: str,
        *,
        title: str,
        fallback_summary: str,
        stakes: str,
    ) -> dict[str, Any]:
        perspective = perspectives.get(key, {}) if isinstance(perspectives.get(key, {}), Mapping) else {}
        return {
            "title": title,
            "summary": perspective.get("summary", fallback_summary),
            "question": perspective.get("question", ""),
            "next_moves": perspective.get("next_moves", []),
            "stakes": stakes,
        }

    return {
        "artist": perspective_block(
            "artist",
            title="Artist read",
            fallback_summary=(
                "Artists need to know which combinations are getting rewarded "
                "and which ones are being left structurally invisible."
            ),
            stakes="Exposure, collaboration timing, release shape, and category crowding.",
        ),
        "consumer": perspective_block(
            "consumer",
            title="Consumer read",
            fallback_summary=(
                "Consumers benefit when the field stays legible enough to tell "
                "popularity from distribution pressure."
            ),
            stakes=(
                "Discovery quality, variety, and whether recommendation loops "
                "keep collapsing back to the same center."
            ),
        ),
        "business": perspective_block(
            "business",
            title="Business read",
            fallback_summary=(
                "Teams need to know whether growth is broadening the field or "
                "just amplifying already dominant channels."
            ),
            stakes="Channel concentration, inventory risk, promotional efficiency, and repeatable lift.",
        ),
        "research": perspective_block(
            "research",
            title="Research read",
            fallback_summary=(
                "Researchers need explicit claim boundaries, source cohorts, "
                "and caveats around public data quality."
            ),
            stakes="Cohort integrity, feature leakage, and longitudinal comparability.",
        ),
        "catalog_size": int(overview.get("n_songs", 0)),
    }
