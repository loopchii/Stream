from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from stream_backend.models import RuntimeSnapshot


PAYLOAD_ORDER = (
    "representation",
    "music",
    "music_index",
    "data_engineering",
    "frontend_state",
    "critical_spine",
    "orchestration",
    "comparatives",
)


def save_snapshot(conn: sqlite3.Connection, snapshot: RuntimeSnapshot) -> None:
    from .runs import insert_run

    payload = snapshot.to_dict()
    payload_hash = (
        snapshot.frontend_state.get("payload_hash", "")
        if isinstance(snapshot.frontend_state, Mapping)
        else ""
    )
    insert_run(
        conn=conn,
        run_id=snapshot.run_id,
        created_at=snapshot.created_at,
        sample_size=snapshot.sample_size,
        synthetic_rows=int(snapshot.representation.get("row_count", 0)),
        music_rows=int(snapshot.music.get("overview", {}).get("n_songs", 0)),
        music_index_rows=int(
            snapshot.music_index.get("summary", {}).get("catalog_song_count", 0)
        ),
        payload_hash=payload_hash,
    )
    conn.execute("DELETE FROM runtime_payloads WHERE run_id = ?", (snapshot.run_id,))
    conn.execute("DELETE FROM runtime_artifacts WHERE run_id = ?", (snapshot.run_id,))
    for name in PAYLOAD_ORDER:
        conn.execute(
            "INSERT INTO runtime_payloads (run_id, payload_name, payload_json) VALUES (?, ?, ?)",
            (snapshot.run_id, name, json.dumps(payload[name], ensure_ascii=False)),
        )
    for artifact in snapshot.artifacts:
        conn.execute(
            """
            INSERT INTO runtime_artifacts (
                run_id, artifact_name, artifact_kind, artifact_path, freshness_label, row_count, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.run_id,
                artifact.name,
                artifact.kind,
                artifact.path,
                artifact.freshness_label,
                artifact.row_count,
                artifact.note,
            ),
        )
    conn.commit()


def load_latest_snapshot(conn: sqlite3.Connection) -> dict[str, Any] | None:
    latest = conn.execute(
        "SELECT run_id, created_at, sample_size FROM runtime_runs ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if latest is None:
        return None
    run_id = latest["run_id"]
    payload_rows = conn.execute(
        "SELECT payload_name, payload_json FROM runtime_payloads WHERE run_id = ?",
        (run_id,),
    ).fetchall()
    artifacts = conn.execute(
        """
        SELECT artifact_name, artifact_kind, artifact_path, freshness_label, row_count, note
        FROM runtime_artifacts
        WHERE run_id = ?
        ORDER BY artifact_name ASC
        """,
        (run_id,),
    ).fetchall()
    payload = {
        "run_id": run_id,
        "created_at": latest["created_at"],
        "sample_size": latest["sample_size"],
        "artifacts": [dict(row) for row in artifacts],
    }
    for row in payload_rows:
        payload[row["payload_name"]] = json.loads(row["payload_json"])
    return payload
