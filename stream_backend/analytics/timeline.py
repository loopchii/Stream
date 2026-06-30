from __future__ import annotations

from typing import Any, Mapping


def build_freshness_surface(
    created_at: str,
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
    music_index: Mapping[str, Any],
) -> dict[str, Any]:
    quality = music_report.get("quality", {})
    coverage = quality.get("coverage", {})
    note_summary = music_index.get("summary", {})
    return {
        "generated_at": created_at,
        "representation_run_rows": int(representation.get("row_count", 0)),
        "publication_year_share": round(float(coverage.get("publication_year_explicit_share", 0.0) or 0.0), 4),
        "inferred_year_share": round(float(coverage.get("publication_year_inferred_share", 0.0) or 0.0), 4),
        "notation_files": int(note_summary.get("discovered_music_files", 0)),
        "matched_catalog_songs": int(note_summary.get("matched_catalog_songs", 0)),
    }
