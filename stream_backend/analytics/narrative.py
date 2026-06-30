from __future__ import annotations

from typing import Any, Mapping


def build_narrative_surface(
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
) -> dict[str, Any]:
    insights = (
        representation.get("insights", [])
        if isinstance(representation.get("insights"), list)
        else []
    )
    top_music = (music_report.get("songs") or [])[:3]
    return {
        "intro": (
            "The backend is now responsible for the repo's analytical posture: "
            "what is fresh, what is public, what is synthetic, and what still "
            "needs caution."
        ),
        "representation": {
            "top_titles": [item.get("title", "") for item in insights[:3] if item.get("title")],
            "summary": "Representation findings stay small enough to inspect and specific enough to challenge.",
        },
        "music": {
            "top_tracks": [row.get("title", "") for row in top_music if row.get("title")],
            "summary": (
                "The public music lane stays separate so virality, concentration, "
                "and boost dynamics can be read on their own terms."
            ),
        },
    }
