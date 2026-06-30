from __future__ import annotations

from typing import Any, Mapping

from .critical_spine import build_critical_spine
from stream_backend.models import FrontendStateEnvelope
from stream_backend.utils import stable_hash

from .comparative import build_comparative_surface
from .governance import build_governance_surface
from .hero import build_hero_surface
from .music_roles import build_music_role_surface
from .narrative import build_narrative_surface
from .note_signals import build_note_signal_surface
from .synthetic_roles import build_synthetic_role_surface
from .timeline import build_freshness_surface


def build_frontend_state(
    generated_at: str,
    sample_size: int,
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
    music_index: Mapping[str, Any],
    data_engineering: Mapping[str, Any],
) -> dict[str, Any]:
    critical_spine = build_critical_spine(
        generated_at=generated_at,
        sample_size=sample_size,
        representation=representation,
        music_report=music_report,
        music_index=music_index,
        data_engineering=data_engineering,
    )
    envelope = FrontendStateEnvelope(
        generated_at=generated_at,
        sample_size=sample_size,
        hero=build_hero_surface(representation, music_report, music_index),
        roles={
            "synthetic": build_synthetic_role_surface(representation),
            "music": build_music_role_surface(music_report),
        },
        narratives=build_narrative_surface(representation, music_report),
        comparatives=build_comparative_surface(representation, music_report, music_index),
        critical_spine=critical_spine,
        note_signals=build_note_signal_surface(music_index),
        governance=build_governance_surface(data_engineering, representation, music_report),
        freshness=build_freshness_surface(generated_at, representation, music_report, music_index),
    )
    payload = envelope.to_dict()
    payload["payload_hash"] = stable_hash(payload)
    return payload
