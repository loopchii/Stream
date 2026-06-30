from __future__ import annotations

import argparse
import importlib
import os
import platform
import sys
from pathlib import Path
from typing import Any

from stream_backend.config import RuntimeConfig


REQUIRED_MODULES = (
    "numpy",
    "pandas",
    "scipy",
    "fastapi",
    "uvicorn",
    "sklearn",
    "networkx",
)


REQUIRED_FILES = (
    "index.html",
    "app.py",
    "README.md",
    "contributing.md",
    "requirements.txt",
    "requirements-dev.txt",
    "manifest.webmanifest",
    "service-worker.js",
    "data_sources/youtube-top-100-songs-2025.csv",
)


STATIC_ARTIFACTS = (
    "data/music/overview.json",
    "data/music/quality.json",
    "data/music/decision-lab.json",
    "data/system/frontend-state.json",
    "data/system/streaming-readiness.json",
    "openapi.stream.json",
)


def _status(name: str, level: str, detail: str, **extra: Any) -> dict[str, Any]:
    row = {"name": name, "level": level, "detail": detail}
    row.update(extra)
    return row


def build_report(base_dir: Path) -> dict[str, Any]:
    from music_decision_lab import build_decision_lab
    import music_pipeline

    config = RuntimeConfig.from_base_dir(base_dir)
    checks: list[dict[str, Any]] = []

    python_ok = sys.version_info >= (3, 10)
    checks.append(
        _status(
            "python",
            "pass" if python_ok else "fail",
            f"Python {platform.python_version()} on {platform.system()} {platform.machine()}",
            required=">=3.10",
        )
    )

    for module_name in REQUIRED_MODULES:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "unknown")
            checks.append(_status(f"module:{module_name}", "pass", f"{module_name} importable", version=version))
        except Exception as exc:  # pragma: no cover - exercised in real env, not unit forcing failures
            checks.append(_status(f"module:{module_name}", "fail", f"{module_name} failed to import", error=str(exc)))

    for relative in REQUIRED_FILES:
        path = config.base_dir / relative
        checks.append(
            _status(
                f"file:{relative}",
                "pass" if path.exists() else "fail",
                "Required repo file present" if path.exists() else "Required repo file missing",
            )
        )

    config.db_dir.mkdir(parents=True, exist_ok=True)
    sqlite_writable = os.access(config.db_dir, os.W_OK)
    checks.append(
        _status(
            "sqlite-path",
            "pass" if sqlite_writable else "fail",
            f"SQLite directory {'is' if sqlite_writable else 'is not'} writable",
            path=str(config.sqlite_path.relative_to(config.base_dir)),
        )
    )

    try:
        df = music_pipeline.load_enriched_dataset()
        quality = music_pipeline.quality_report(df)
        checks.append(_status("music-load", "pass", "Public music dataset loaded", rows=int(len(df))))
        year_rows = int(df["published_year"].fillna(0).astype(int).gt(0).sum()) if "published_year" in df.columns else 0
        checks.append(
            _status(
                "music-years",
                "pass" if year_rows > 0 else "warn",
                "Publication years available for timeline analysis" if year_rows > 0 else "Timeline coverage is currently sparse",
                dated_rows=year_rows,
                coverage=round(year_rows / len(df), 3) if len(df) else 0.0,
            )
        )
        genre_share = float((quality.get("coverage") or {}).get("genre_known_share", 0.0) or 0.0)
        checks.append(
            _status(
                "music-genre-coverage",
                "pass" if genre_share >= 0.6 else "warn",
                "Public music rows should resolve to a usable genre label often enough to support comparative analysis.",
                coverage=round(genre_share, 3),
                target=">=0.60",
            )
        )
        decision_lab = build_decision_lab(df)
        strongest = ((decision_lab.get("experiments") or {}).get("strongest") or {}).get("label", "n/a")
        checks.append(
            _status(
                "decision-lab",
                "pass",
                "Decision lab generated from the current public corpus",
                strongest_experiment=strongest,
            )
        )
    except Exception as exc:  # pragma: no cover - real failure path
        checks.append(_status("music-load", "fail", "Music pipeline failed to load", error=str(exc)))

    for relative in STATIC_ARTIFACTS:
        path = config.base_dir / relative
        checks.append(
            _status(
                f"artifact:{relative}",
                "pass" if path.exists() else "warn",
                "Static artifact available" if path.exists() else "Static artifact not built yet",
            )
        )

    counts = {
        "pass": sum(1 for row in checks if row["level"] == "pass"),
        "warn": sum(1 for row in checks if row["level"] == "warn"),
        "fail": sum(1 for row in checks if row["level"] == "fail"),
    }
    overall = "fail" if counts["fail"] else "warn" if counts["warn"] else "pass"
    return {
        "overall": overall,
        "counts": counts,
        "checks": checks,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local runtime and environment doctor for Stream.")
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true", help="Emit the report as compact JSON.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = build_report(args.base_dir)
    if args.json:
        import json

        print(json.dumps(report, indent=2))
    else:
        print("Stream doctor")
        print(f"overall={report['overall']} pass={report['counts']['pass']} warn={report['counts']['warn']} fail={report['counts']['fail']}")
        for row in report["checks"]:
            print(f"[{row['level'].upper()}] {row['name']}: {row['detail']}")
    return 1 if report["overall"] == "fail" else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
