from __future__ import annotations

from typing import Any, Mapping

from stream_backend.analytics import build_frontend_state


def build_frontend_state_payload(
    generated_at: str,
    sample_size: int,
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
    music_index: Mapping[str, Any],
    data_engineering: Mapping[str, Any],
) -> dict[str, Any]:
    return build_frontend_state(
        generated_at=generated_at,
        sample_size=sample_size,
        representation=representation,
        music_report=music_report,
        music_index=music_index,
        data_engineering=data_engineering,
    )
