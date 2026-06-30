from __future__ import annotations

from stream_backend.store import connect_sqlite, ensure_schema, load_latest_snapshot


def load_latest_runtime_snapshot(sqlite_path):
    conn = connect_sqlite(sqlite_path)
    try:
        ensure_schema(conn)
        return load_latest_snapshot(conn)
    finally:
        conn.close()
