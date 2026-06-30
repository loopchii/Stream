from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_runtime_json_exports(base_dir: Path, snapshot_payload: Mapping[str, Any]) -> list[Path]:
    system_dir = base_dir / "data" / "system"
    outputs = {
        system_dir / "frontend-state.json": snapshot_payload["frontend_state"],
        system_dir / "comparatives.json": snapshot_payload["comparatives"],
        system_dir / "runtime.json": snapshot_payload["orchestration"],
        system_dir / "contracts.json": snapshot_payload["data_engineering"],
    }
    written: list[Path] = []
    for path, payload in outputs.items():
        _write_json(path, payload)
        written.append(path)
    return written
