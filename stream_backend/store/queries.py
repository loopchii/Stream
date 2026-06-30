from __future__ import annotations

import sqlite3


def latest_payload_names(conn: sqlite3.Connection) -> list[str]:
    row = conn.execute(
        "SELECT run_id FROM runtime_runs ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return []
    rows = conn.execute(
        "SELECT payload_name FROM runtime_payloads WHERE run_id = ? ORDER BY payload_name ASC",
        (row["run_id"],),
    ).fetchall()
    return [str(item["payload_name"]) for item in rows]
