from __future__ import annotations

from stream_backend.models import RuntimeSnapshot
from stream_backend.store import connect_sqlite, ensure_schema, save_snapshot


def persist_runtime_snapshot(sqlite_path, snapshot: RuntimeSnapshot) -> None:
    conn = connect_sqlite(sqlite_path)
    try:
        ensure_schema(conn)
        save_snapshot(conn, snapshot)
    finally:
        conn.close()
