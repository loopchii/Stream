from __future__ import annotations

from typing import Any, Mapping

from stream_backend.utils import clamp, pct, safe_div


def build_hero_surface(
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
    music_index: Mapping[str, Any],
) -> dict[str, Any]:
    overall = representation.get("overall_metrics", {})
    overview = music_report.get("overview", {})
    music_summary = music_index.get("summary", {})
    parity = clamp(overall.get("gender_parity", 0.0))
    diversity = clamp(overall.get("diversity_index", 0.0))
    top_share = float(
        ((music_report.get("inequality") or {}).get("top3_channel_share")) or 0.0
    )
    note_coverage = safe_div(
        music_summary.get("matched_catalog_songs", 0),
        music_summary.get("catalog_song_count", 0),
    )
    return {
        "headline": "Public analysis should be able to survive a second question.",
        "subheadline": (
            "The same backend now computes the music lane, representation lane, "
            "runtime summaries, and front-end state."
        ),
        "signals": [
            {
                "id": "representation_parity",
                "label": "Representation parity",
                "value": round(parity, 3),
                "display": f"{parity:.3f}",
                "note": "Share balance in the active representation surface.",
            },
            {
                "id": "representation_diversity",
                "label": "Representation breadth",
                "value": pct(diversity, 1),
                "display": f"{pct(diversity, 1):.1f}%",
                "note": (
                    "Synthetic lane diversity index, computed in Python "
                    "and exported for the UI."
                ),
            },
            {
                "id": "music_top_share",
                "label": "Attention concentration",
                "value": round(top_share, 4),
                "display": f"{top_share:.1%}",
                "note": "Top-3 channel control share in the public music lane.",
            },
            {
                "id": "notation_coverage",
                "label": "Notation-linked coverage",
                "value": round(note_coverage, 4),
                "display": f"{note_coverage:.1%}",
                "note": (
                    "Share of catalog songs with directly linked score or "
                    "notation support."
                ),
            },
        ],
        "music_summary": {
            "songs": int(overview.get("n_songs", 0)),
            "views": int(overview.get("total_views", 0)),
            "channels": int(overview.get("n_channels", 0)),
        },
    }
