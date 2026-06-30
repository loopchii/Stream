from __future__ import annotations

import sqlite3


def insert_run(
    conn: sqlite3.Connection,
    run_id: str,
    created_at: str,
    sample_size: int,
    synthetic_rows: int,
    music_rows: int,
    music_index_rows: int,
    payload_hash: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO runtime_runs (
            run_id, created_at, sample_size, synthetic_rows, music_rows, music_index_rows, payload_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            created_at,
            sample_size,
            synthetic_rows,
            music_rows,
            music_index_rows,
            payload_hash,
        ),
    )


def list_runs(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT run_id, created_at, sample_size, synthetic_rows, music_rows, music_index_rows, payload_hash
        FROM runtime_runs
        ORDER BY created_at DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]
