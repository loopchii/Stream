from __future__ import annotations

from typing import Any, Mapping

from stream_backend.utils import safe_div


def build_comparative_surface(
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
    music_index: Mapping[str, Any],
) -> dict[str, Any]:
    overall = representation.get("overall_metrics", {})
    ineq = music_report.get("inequality", {})
    note_summary = music_index.get("summary", {})
    matched = note_summary.get("matched_catalog_songs", 0)
    catalog = note_summary.get("catalog_song_count", 0)
    return {
        "synthetic_vs_public": [
            {
                "topic": "Breadth vs concentration",
                "representation": round(float(overall.get("diversity_index", 0.0) or 0.0), 4),
                "music": round(float(ineq.get("gini", 0.0) or 0.0), 4),
                "note": "One lane asks how broad the field looks; the other asks how tightly attention concentrates.",
            },
            {
                "topic": "Parity vs dominance",
                "representation": round(float(overall.get("gender_parity", 0.0) or 0.0), 4),
                "music": round(float(ineq.get("top3_channel_share", 0.0) or 0.0), 4),
                "note": "Parity is not the same question as market control, but both reveal where the center hardens.",
            },
            {
                "topic": "Note-linked depth",
                "representation": None,
                "music": round(safe_div(matched, catalog), 4),
                "note": "The music lane can now report how much of the catalog is connected to score-level evidence.",
            },
        ]
    }
