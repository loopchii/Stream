"""Derived analytical surfaces for the public Stream backend."""

from .comparative import build_comparative_surface
from .contracts import build_backend_contract_surface
from .critical_spine import build_critical_spine
from .frontend_state import build_frontend_state
from .governance import build_governance_surface
from .hero import build_hero_surface
from .music_roles import build_music_role_surface
from .narrative import build_narrative_surface
from .note_signals import build_note_signal_surface
from .quality import build_runtime_quality_surface
from .synthetic_roles import build_synthetic_role_surface
from .timeline import build_freshness_surface

__all__ = [
    "build_backend_contract_surface",
    "build_comparative_surface",
    "build_critical_spine",
    "build_frontend_state",
    "build_freshness_surface",
    "build_governance_surface",
    "build_hero_surface",
    "build_music_role_surface",
    "build_narrative_surface",
    "build_note_signal_surface",
    "build_runtime_quality_surface",
    "build_synthetic_role_surface",
]
