from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def write_runtime_markdown(path: Path, snapshot_payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frontend = snapshot_payload["frontend_state"]
    music = snapshot_payload["music"]
    representation = snapshot_payload["representation"]
    lines = [
        "# Stream Runtime Surface",
        "",
        f"- Generated at: `{frontend['generated_at']}`",
        f"- Sample size: `{frontend['sample_size']}`",
        f"- Synthetic rows: `{representation.get('row_count', 0)}`",
        f"- Public music songs: `{music.get('overview', {}).get('n_songs', 0)}`",
        "",
        "## Hero Signals",
        "",
    ]
    for signal in frontend["hero"]["signals"]:
        lines.append(f"- **{signal['label']}**: `{signal['display']}` — {signal['note']}")
    lines.extend(
        [
            "",
            "## Runtime Notes",
            "",
            "- The browser surface now has a generated backend state payload.",
            "- SQLite persistence can store the latest runtime snapshot for inspection.",
            "- Synthetic and public music lanes stay distinct all the way through export.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
