from __future__ import annotations

from typing import Any, Mapping


def build_note_signal_surface(music_index: Mapping[str, Any]) -> dict[str, Any]:
    summary = music_index.get("summary", {})
    pieces = music_index.get("pieces", []) if isinstance(music_index.get("pieces"), list) else []
    note_profile = [piece.get("note_profile", {}) for piece in pieces if piece.get("note_profile")]
    note_events = sum(int(profile.get("note_events", 0)) for profile in note_profile)
    return {
        "catalog_song_count": int(summary.get("catalog_song_count", 0)),
        "discovered_music_files": int(summary.get("discovered_music_files", 0)),
        "matched_catalog_songs": int(summary.get("matched_catalog_songs", 0)),
        "parsed_note_events": int(summary.get("parsed_note_events", note_events)),
        "top_titles": [piece.get("title", "") for piece in pieces[:5] if piece.get("title")],
    }
