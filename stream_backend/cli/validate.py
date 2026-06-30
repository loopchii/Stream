from __future__ import annotations

import argparse
from pathlib import Path

from stream_backend.config import RuntimeConfig
from stream_backend.services.snapshots import load_latest_runtime_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the latest Stream backend snapshot.")
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[2])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = RuntimeConfig.from_base_dir(args.base_dir)
    payload = load_latest_runtime_snapshot(config.sqlite_path)
    if payload is None:
        print("No persisted runtime snapshot found.")
        return 1
    print(f"Latest run: {payload['run_id']}")
    payload_names = sorted(
        key for key in payload.keys()
        if key not in {"run_id", "created_at", "sample_size", "artifacts"}
    )
    print(f"Payloads: {payload_names}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
