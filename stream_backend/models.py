from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping


@dataclass
class RuntimeArtifact:
    name: str
    kind: str
    path: str
    freshness_label: str
    row_count: int = 0
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeSnapshot:
    run_id: str
    created_at: str
    sample_size: int
    representation: Mapping[str, Any]
    music: Mapping[str, Any]
    music_index: Mapping[str, Any]
    data_engineering: Mapping[str, Any]
    frontend_state: Mapping[str, Any]
    orchestration: Mapping[str, Any]
    comparatives: Mapping[str, Any]
    artifacts: List[RuntimeArtifact] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        return payload


@dataclass
class FrontendStateEnvelope:
    generated_at: str
    sample_size: int
    hero: Mapping[str, Any]
    roles: Mapping[str, Any]
    narratives: Mapping[str, Any]
    comparatives: Mapping[str, Any]
    note_signals: Mapping[str, Any]
    governance: Mapping[str, Any]
    freshness: Mapping[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
