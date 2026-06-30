from __future__ import annotations

import sqlite3


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runtime_runs (
            run_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            sample_size INTEGER NOT NULL,
            synthetic_rows INTEGER NOT NULL DEFAULT 0,
            music_rows INTEGER NOT NULL DEFAULT 0,
            music_index_rows INTEGER NOT NULL DEFAULT 0,
            payload_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS runtime_payloads (
            run_id TEXT NOT NULL,
            payload_name TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (run_id, payload_name),
            FOREIGN KEY (run_id) REFERENCES runtime_runs(run_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS runtime_artifacts (
            run_id TEXT NOT NULL,
            artifact_name TEXT NOT NULL,
            artifact_kind TEXT NOT NULL,
            artifact_path TEXT NOT NULL,
            freshness_label TEXT NOT NULL,
            row_count INTEGER NOT NULL DEFAULT 0,
            note TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (run_id, artifact_name),
            FOREIGN KEY (run_id) REFERENCES runtime_runs(run_id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
