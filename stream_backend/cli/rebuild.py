from __future__ import annotations

import argparse
from pathlib import Path

from stream_backend.config import RuntimeConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Describe the Stream backend rebuild target.")
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[2])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = RuntimeConfig.from_base_dir(args.base_dir)
    print("Stream backend rebuild target")
    print(f"sqlite={config.sqlite_path}")
    print(f"system_dir={config.system_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
