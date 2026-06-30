from __future__ import annotations

from typing import Any, Mapping

from stream_backend.models import RuntimeSnapshot
from stream_backend.orchestration.assets import build_runtime_artifacts
from stream_backend.utils import stable_hash


def build_runtime_snapshot(
    base_dir,
    run_id: str,
    generated_at: str,
    sample_size: int,
    payloads: Mapping[str, Any],
) -> RuntimeSnapshot:
    frontend_state = dict(payloads["frontend_state"])
    frontend_state["payload_hash"] = stable_hash(frontend_state)
    artifacts = build_runtime_artifacts(
        base_dir=base_dir,
        frontend_state=frontend_state,
        representation=payloads["representation"],
        music_index=payloads["music_index"],
    )
    return RuntimeSnapshot(
        run_id=run_id,
        created_at=generated_at,
        sample_size=sample_size,
        representation=payloads["representation"],
        music=payloads["music"],
        music_index=payloads["music_index"],
        data_engineering=payloads["data_engineering"],
        frontend_state=frontend_state,
        critical_spine=payloads.get("critical_spine", {}),
        orchestration=payloads.get("orchestration", {}),
        comparatives=payloads.get("comparatives", {}),
        artifacts=artifacts,
    )
