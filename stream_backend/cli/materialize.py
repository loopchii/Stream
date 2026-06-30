from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize the Stream backend runtime snapshot.")
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--sample-size", type=int, default=5000)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(
        "stream_backend.cli.materialize is a thin entrypoint. "
        "Instantiate StreamRuntime from app/build_static integration to use it."
    )
    print(f"base_dir={args.base_dir} sample_size={args.sample_size}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
