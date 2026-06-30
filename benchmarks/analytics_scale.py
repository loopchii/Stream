#!/usr/bin/env python3
"""Benchmark the public music lane at larger row counts.

This stays honest about what exists today:

- pandas is the required baseline
- Polars and DuckDB are optional accelerators if already installed
- the benchmark measures the real kinds of aggregations the repo performs now

Usage:
    python benchmarks/analytics_scale.py --rows 1000000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import music_pipeline
from music_pipeline import load_enriched_dataset

try:  # pragma: no cover - optional acceleration path
    import polars as pl  # type: ignore
except Exception:  # pragma: no cover
    pl = None

try:  # pragma: no cover - optional acceleration path
    import duckdb  # type: ignore
except Exception:  # pragma: no cover
    duckdb = None


def amplify(df: pd.DataFrame, rows: int) -> pd.DataFrame:
    if rows <= len(df):
        return df.head(rows).copy()
    copies = (rows // len(df)) + 1
    expanded = pd.concat([df] * copies, ignore_index=True).head(rows).copy()
    expanded["synthetic_row_id"] = range(len(expanded))
    return expanded


def pandas_workload(df: pd.DataFrame) -> dict:
    start = time.perf_counter()
    grouped = (
        df.groupby(["source", "genre"], dropna=False)
        .agg(
            songs=("title", "count"),
            total_views=("view_count", "sum"),
            avg_views=("view_count", "mean"),
            avg_duration=("duration_min", "mean"),
            avg_engagement=("engagement_ratio", "mean"),
        )
        .reset_index()
        .sort_values("total_views", ascending=False)
    )
    elapsed = time.perf_counter() - start
    return {
        "engine": "pandas",
        "seconds": round(elapsed, 4),
        "rows_out": int(len(grouped)),
    }


def polars_workload(df: pd.DataFrame) -> dict | None:
    if pl is None:
        return None
    start = time.perf_counter()
    grouped = (
        pl.from_pandas(df)
        .group_by(["source", "genre"])
        .agg(
            pl.len().alias("songs"),
            pl.sum("view_count").alias("total_views"),
            pl.mean("view_count").alias("avg_views"),
            pl.mean("duration_min").alias("avg_duration"),
            pl.mean("engagement_ratio").alias("avg_engagement"),
        )
        .sort("total_views", descending=True)
    )
    elapsed = time.perf_counter() - start
    return {
        "engine": "polars",
        "seconds": round(elapsed, 4),
        "rows_out": int(grouped.height),
    }


def duckdb_workload(df: pd.DataFrame) -> dict | None:
    if duckdb is None:
        return None
    start = time.perf_counter()
    con = duckdb.connect(database=":memory:")
    con.register("songs", df)
    grouped = con.execute(
        """
        SELECT
            source,
            genre,
            COUNT(*) AS songs,
            SUM(view_count) AS total_views,
            AVG(view_count) AS avg_views,
            AVG(duration_min) AS avg_duration,
            AVG(engagement_ratio) AS avg_engagement
        FROM songs
        GROUP BY 1, 2
        ORDER BY total_views DESC
        """
    ).df()
    elapsed = time.perf_counter() - start
    return {
        "engine": "duckdb",
        "seconds": round(elapsed, 4),
        "rows_out": int(len(grouped)),
    }


def build_report(rows: int) -> dict:
    base = load_enriched_dataset()
    if "genre" not in base.columns:
        base["genre"] = [
            music_pipeline._classify_genre(tags, title, channel, description, language)[0]
            for tags, title, channel, description, language in zip(
                base.get("_raw_tags", pd.Series([""] * len(base))),
                base["title"],
                base["channel"],
                base.get("description", pd.Series([""] * len(base))),
                base.get("detected_language", pd.Series([""] * len(base))),
            )
        ]
    expanded = amplify(base, rows)
    results = [pandas_workload(expanded)]
    for optional in (polars_workload(expanded), duckdb_workload(expanded)):
        if optional is not None:
            results.append(optional)
    fastest = min(results, key=lambda row: row["seconds"]) if results else None
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows_benchmarked": int(len(expanded)),
        "source_rows": int(len(base)),
        "workload": "groupby(source, genre) with aggregate metrics used by the public analysis lane",
        "results": results,
        "fastest": fastest,
        "notes": [
            "This benchmark measures the current public workload, not a distributed event-processing topology.",
            "Optional engines appear only when they are installed locally.",
            "Use this as evidence for scale posture, not as a substitute for replay, ordering, or checkpoint guarantees.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the Stream public analytics lane.")
    parser.add_argument("--rows", type=int, default=1_000_000, help="Expanded row count to benchmark.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    report = build_report(args.rows)
    payload = json.dumps(report, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
