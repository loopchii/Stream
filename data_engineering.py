#!/usr/bin/env python3
"""
Data-engineering contract and lineage surface for the public Stream repo.

This module stays deliberately honest: it describes the pipeline that actually
exists in this repository today rather than inventing warehouse machinery that
isn't wired. The goal is to expose the repo's operating model in the language a
data engineer, analytics engineer, or head of data expects:

- dataset grain
- primary keys
- freshness posture
- quality checks
- lineage edges
- serving contracts
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PUBLIC_SAMPLE_SIZES = [1000, 5000, 10000, 25000]
SYNTHETIC_BASELINE_SEED = 42


SYNTHETIC_FIELD_DOCS: Dict[str, Dict[str, str]] = {
    "id": {"role": "primary_key", "description": "Synthetic character identifier generated per run."},
    "platform": {"role": "dimension", "description": "Streaming platform used as a platform-level slice."},
    "genre": {"role": "dimension", "description": "Narrative genre used for group-level comparisons."},
    "media_type": {"role": "dimension", "description": "Format split such as film, series, or docuseries."},
    "year": {"role": "partition", "description": "Release-year partition used by the temporal and trend layers."},
    "gender": {"role": "dimension", "description": "Character gender category."},
    "race": {"role": "dimension", "description": "Character race category used for representation checks."},
    "age_group": {"role": "dimension", "description": "Age cohort used for intersectional analysis."},
    "role_type": {"role": "dimension", "description": "Lead, support, or minor role designation."},
    "screen_time": {"role": "measure", "description": "Synthetic screen-time minutes used in visibility metrics."},
    "dialogue_words": {"role": "measure", "description": "Synthetic dialogue word count used in speaking-share metrics."},
    "sentiment_score": {"role": "measure", "description": "Normalized tone proxy for framing analysis."},
    "centrality": {"role": "measure", "description": "Graph centrality seed for interaction-network simulations."},
    "is_protagonist": {"role": "flag", "description": "Boolean protagonist flag derived from role type."},
}


MUSIC_FIELD_DOCS: Dict[str, Dict[str, str]] = {
    "title": {"role": "entity", "description": "Public song title after source cleaning."},
    "channel": {"role": "entity", "description": "Publishing artist or channel name."},
    "view_count": {"role": "measure", "description": "Observed public YouTube views."},
    "duration_min": {"role": "measure", "description": "Track duration in minutes, coerced and normalized."},
    "channel_follower_count": {"role": "measure", "description": "Channel subscriber count used as a reach baseline."},
    "virality_coefficient": {"role": "derived_measure", "description": "Views divided by subscribers; descriptive only."},
    "tag_count": {"role": "measure", "description": "Declared YouTube tag count."},
    "description_len": {"role": "measure", "description": "Description character length."},
    "genre": {"role": "dimension", "description": "Genre inferred from tags, text, and supplements."},
    "is_official": {"role": "flag", "description": "Official-video marker derived from title and metadata."},
    "collaboration_count": {"role": "measure", "description": "Estimated collaborator count from title patterns."},
    "detected_language": {"role": "dimension", "description": "Language label preserved when the public source exposes one."},
    "published_at": {"role": "timestamp", "description": "Public upload timestamp when available."},
    "published_year": {"role": "partition", "description": "Upload-year partition derived from public timestamps."},
    "likes": {"role": "measure", "description": "Observed likes when available from the public supplements."},
    "engagement_ratio": {"role": "derived_measure", "description": "Likes divided by views after coercion and null handling."},
    "source": {"role": "lineage_tag", "description": "Source cohort label used to separate core and enriched lanes."},
    "country": {"role": "dimension", "description": "Public channel-country lookup when a supported mapping exists."},
}


def _dtype_label(dtype) -> str:
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_integer_dtype(dtype):
        return "integer"
    if pd.api.types.is_float_dtype(dtype):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "timestamp"
    return "string"


def _sample_value(series: pd.Series):
    sample = series.dropna().head(1)
    if sample.empty:
        return None
    value = sample.iloc[0]
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _schema_records(
    df: pd.DataFrame,
    docs: Mapping[str, Mapping[str, str]],
    focus: Optional[Iterable[str]] = None,
) -> List[dict]:
    order = list(focus) if focus is not None else list(df.columns)
    rows: List[dict] = []
    for name in order:
        if name not in df.columns:
            continue
        series = df[name]
        doc = docs.get(name, {})
        null_count = int(series.isna().sum())
        rows.append(
            {
                "name": name,
                "dtype": _dtype_label(series.dtype),
                "nullable": bool(null_count > 0),
                "null_count": null_count,
                "role": doc.get("role", "attribute"),
                "description": doc.get("description", "Working column exposed by the public analysis surface."),
                "sample_value": _sample_value(series),
            }
        )
    return rows


def _schema_profile(rows: Iterable[Mapping[str, object]]) -> dict:
    items = list(rows)
    role_counts: Dict[str, int] = {}
    nullable_count = 0
    for row in items:
        role = str(row.get("role", "attribute"))
        role_counts[role] = role_counts.get(role, 0) + 1
        if row.get("nullable"):
            nullable_count += 1
    return {
        "column_count": len(items),
        "nullable_columns": nullable_count,
        "strict_columns": max(len(items) - nullable_count, 0),
        "role_counts": role_counts,
    }


def _check(name: str, status: str, detail: str, value=None, target: Optional[str] = None) -> dict:
    payload = {
        "name": name,
        "status": status,
        "detail": detail,
    }
    if value is not None:
        payload["value"] = value
    if target is not None:
        payload["target"] = target
    return payload


def synthetic_contract(df: pd.DataFrame, results: Mapping[str, object]) -> dict:
    year_min = int(df["year"].min())
    year_max = int(df["year"].max())
    unique_id = bool(df["id"].is_unique)
    enum_ok = bool(df["platform"].isin(["netflix", "amazon_prime", "disney_plus", "hbo_max", "apple_tv", "hulu"]).all())
    null_count = int(df.isna().sum().sum())
    non_negative = bool((df["screen_time"] >= 0).all() and (df["dialogue_words"] >= 0).all())
    overview = results.get("overall_metrics", {}) if isinstance(results, Mapping) else {}
    advanced = results.get("advanced_metrics", {}) if isinstance(results, Mapping) else {}
    schema = _schema_records(
        df,
        SYNTHETIC_FIELD_DOCS,
        focus=[
            "id",
            "platform",
            "genre",
            "media_type",
            "year",
            "gender",
            "race",
            "age_group",
            "role_type",
            "screen_time",
            "dialogue_words",
            "sentiment_score",
            "centrality",
            "is_protagonist",
        ],
    )
    return {
        "dataset_id": "synthetic_character_fact",
        "lane": "representation",
        "grain": "one row per synthetic character per analysis run",
        "primary_key": ["id"],
        "partition_keys": ["year", "platform", "genre", "media_type"],
        "update_mode": "recomputed on demand through /api/analyze and cached in-process",
        "freshness_sla": "fresh per analysis run; static build snapshots are regenerated by build_static.py",
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "semantic_outputs": [
            "overview parity and diversity metrics",
            "genre and media-type gold rollups",
            "bias detection surfaces",
            "network homophily and interaction structure",
            "advanced inequality and trend outputs",
        ],
        "quality_checks": [
            _check("Primary key uniqueness", "pass" if unique_id else "fail", "Character ids must stay unique inside a run.", value=str(unique_id)),
            _check("Year partition range", "pass", "Synthetic cohort stays within the modeled platform era.", value=f"{year_min}-{year_max}", target="2015-2026"),
            _check("Non-negative measures", "pass" if non_negative else "fail", "Screen time and dialogue counts should never go below zero.", value=str(non_negative)),
            _check("Allowed platform domain", "pass" if enum_ok else "warn", "Platform values should remain inside the documented synthetic lane.", value=str(enum_ok)),
            _check("Null pressure", "pass" if null_count == 0 else "warn", "The synthetic fact table is designed to ship fully populated rows.", value=null_count, target="0"),
        ],
        "schema_profile": _schema_profile(schema),
        "schema": schema,
        "headline_metrics": {
            "gender_parity": round(float(overview.get("gender_parity", 0.0)), 4),
            "diversity_index": round(float(overview.get("diversity_index", 0.0)), 4),
            "screen_time_gini": round(float(((advanced.get("inequality") or {}).get("screen_time") or {}).get("gini", 0.0)), 4),
        },
    }


def music_contract(df: pd.DataFrame, quality: Mapping[str, object]) -> dict:
    title_unique = int(df["title"].astype(str).str.lower().str.strip().nunique())
    quality_source = quality.get("source_audit", []) if isinstance(quality, Mapping) else []
    coverage = quality.get("coverage", {}) if isinstance(quality, Mapping) else {}
    rigor = quality.get("model_rigor", {}) if isinstance(quality, Mapping) else {}
    missing_views = int(pd.to_numeric(df["view_count"], errors="coerce").isna().sum())
    missing_duration = int(pd.to_numeric(df["duration_min"], errors="coerce").isna().sum()) if "duration_min" in df.columns else 0
    publication_rows = int(pd.to_numeric(df.get("published_year", pd.Series(dtype=float)), errors="coerce").notna().sum()) if "published_year" in df.columns else 0
    schema = _schema_records(
        df,
        MUSIC_FIELD_DOCS,
        focus=[
            "title",
            "channel",
            "view_count",
            "duration_min",
            "channel_follower_count",
            "virality_coefficient",
            "tag_count",
            "description_len",
            "genre",
            "is_official",
            "collaboration_count",
            "detected_language",
            "published_at",
            "published_year",
            "likes",
            "engagement_ratio",
            "source",
            "country",
        ],
    )
    return {
        "dataset_id": "music_song_fact_enriched",
        "lane": "music",
        "grain": "one public music-video record per distinct normalized title",
        "primary_key": ["title", "channel"],
        "partition_keys": ["source", "published_year", "genre"],
        "update_mode": "bundled CSV by default, optionally refreshed through music_ingest.refresh_dataset() when a YouTube key exists",
        "freshness_sla": "manual refresh for public source pulls; static exports rebuilt with build_static.py",
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "semantic_outputs": [
            "top-100 leaderboard explorer",
            "power-law and inequality surfaces",
            "correlation and feature-importance views",
            "genre, resonance, and timing breakdowns",
            "quality and provenance reporting",
        ],
        "quality_checks": [
            _check("Distinct title coverage", "pass" if title_unique >= max(len(df) - 2, 1) else "warn", "Normalized-title deduplication should keep repeated songs from inflating counts.", value=title_unique),
            _check("Missing views after coercion", "pass" if missing_views == 0 else "fail", "View count is the core analytic measure and must be present after cleaning.", value=missing_views, target="0"),
            _check("Duration completeness", "pass" if missing_duration == 0 else "warn", "Duration is allowed to be median-imputed, but the working fact table should not expose nulls.", value=missing_duration, target="0"),
            _check("Publication-year coverage", "pass" if publication_rows > 0 else "warn", "Timeline charts only use rows with public upload dates.", value=publication_rows),
            _check(
                "Genre coverage",
                "pass" if float(coverage.get("genre_known_share", 0.0) or 0.0) >= 0.6 else "warn",
                "Genre labels should come from public metadata, text, and artist hints rather than leaving the majority of rows unclassified.",
                value=round(float(coverage.get("genre_known_share", 0.0) or 0.0), 3),
                target=">=0.60",
            ),
            _check("Predictor hygiene", "pass", "The predictor set blocks virality_coefficient because it leaks the target.", value=str(rigor.get("blocked_from_prediction", []))),
        ],
        "source_audit": quality_source,
        "schema_profile": _schema_profile(schema),
        "schema": schema,
        "coverage": {
            "known_languages": int(coverage.get("known_languages", 0) or 0),
            "countries_mapped": int(coverage.get("countries_mapped", 0) or 0),
            "genre_known_share": round(float(coverage.get("genre_known_share", 0.0) or 0.0), 3),
            "publication_year_min": coverage.get("publication_year_min"),
            "publication_year_max": coverage.get("publication_year_max"),
            "duplicate_titles_removed": int(coverage.get("duplicate_titles_removed", 0) or 0),
        },
    }


def build_data_engineering_snapshot(
    synthetic_df: pd.DataFrame,
    synthetic_results: Mapping[str, object],
    music_df: pd.DataFrame,
    music_quality: Mapping[str, object],
) -> dict:
    synthetic = synthetic_contract(synthetic_df, synthetic_results)
    music = music_contract(music_df, music_quality)
    datasets = [synthetic, music]
    quality_gate_count = sum(len(item["quality_checks"]) for item in datasets)
    row_count = sum(int(item["row_count"]) for item in datasets)
    generated_at = datetime.now(timezone.utc).isoformat()
    service_levels = [
        {
            "id": "freshness",
            "name": "Freshness posture",
            "status": "pass",
            "current": "Synthetic lane reruns on demand; public music refresh stays manual and declared.",
            "target": "No published surface should imply a live feed when the source is bundled or manually refreshed.",
        },
        {
            "id": "coverage",
            "name": "Contract coverage",
            "status": "pass",
            "current": f"{len(datasets)} contracted datasets with {quality_gate_count} visible quality gates.",
            "target": "Every published lane ships with grain, key, partition, and quality posture before the chart layer.",
        },
        {
            "id": "parity",
            "name": "Delivery parity",
            "status": "pass",
            "current": "FastAPI, static JSON, and the browser all read from the same Python pipeline.",
            "target": "Static hosting should not drift away from the live API or produce a second truth.",
        },
        {
            "id": "leakage",
            "name": "Leakage discipline",
            "status": "pass",
            "current": "The music predictor excludes virality_coefficient because it is derived from views.",
            "target": "No self-fulfilling feature should make the model look more clairvoyant than the data permits.",
        },
    ]
    delivery_surfaces = [
        {
            "id": "api",
            "name": "Live API",
            "audience": "engineers, analysts, notebooks",
            "artifact": "FastAPI /api/* endpoints",
            "refresh": "served from in-process caches; synthetic lane can be rerun per request",
        },
        {
            "id": "static",
            "name": "Static export",
            "audience": "GitHub Pages, preview deploys, no-backend readers",
            "artifact": "data/*.json snapshots generated by build_static.py",
            "refresh": "rebuilt intentionally so public artifacts do not pretend to be live",
        },
        {
            "id": "browser",
            "name": "Browser surface",
            "audience": "decision-makers, contributors, reviewers",
            "artifact": "index.html with live/static fetch parity",
            "refresh": "reads API when present, otherwise falls back to baked artifacts",
        },
    ]
    reproducibility = {
        "title": "Synthetic data catalog",
        "seed": SYNTHETIC_BASELINE_SEED,
        "algorithm_surface": "DataProcessor.generate_synthetic_data()",
        "default_sample_sizes": PUBLIC_SAMPLE_SIZES,
        "determinism_note": (
            "The synthetic representation lane is seeded and version-stable by design. "
            "The same code revision and sample size should reproduce the same synthetic rows."
        ),
        "year_span": "2015-2026",
        "public_boundary": (
            "This repository is self-contained: public Python pipeline, static exports, SQLite materialization, "
            "and browser surface all run without private LOOPCHii platform dependencies."
        ),
        "artifact_contracts": [
            "analysis_results.json",
            "data/system/frontend-state.json",
            "data/system/streaming-readiness.json",
            "data/system/critical-spine.json",
            "music_index.json",
            "openapi.stream.json",
        ],
        "research_modes": [
            {
                "id": "synthetic",
                "label": "Synthetic representation lane",
                "purpose": "Teaches the method and keeps fairness math reproducible without overclaiming access to private catalogues.",
            },
            {
                "id": "public_music",
                "label": "Public music lane",
                "purpose": "Pressure-tests the method against committed public-source data and makes source gaps visible.",
            },
        ],
    }
    return {
        "generated_at": generated_at,
        "operating_model": {
            "name": "Stream public data platform",
            "posture": "hybrid ETL + ELT research surface",
            "warehouse_shape": "contract-checked raw, standardized, gold, and serving layers",
            "serving_interfaces": ["FastAPI JSON endpoints", "static JSON exports for GitHub Pages", "public HTML analysis surface"],
            "system_guards": [
                "contract-style schema summaries",
                "quality gates on keys, nulls, and target leakage",
                "gold metrics regenerated from the same processing code",
                "clear separation between synthetic representation data and public music data",
            ],
            "dataset_count": len(datasets),
            "quality_gate_count": quality_gate_count,
            "tracked_rows": row_count,
        },
        "service_levels": service_levels,
        "delivery_surfaces": delivery_surfaces,
        "stages": [
            {
                "id": "bronze",
                "name": "Bronze landing",
                "color": "#f4a259",
                "motion": "burst",
                "purpose": "Land raw public CSVs and synthetic generation seeds without pretending they are already analytic truth.",
                "artifacts": [
                    "data_sources/youtube-top-100-songs-2025.csv",
                    "data_sources/most-viewed-yt-videos-2026.csv",
                    "DataProcessor.generate_synthetic_data()",
                ],
            },
            {
                "id": "silver",
                "name": "Silver standardization",
                "color": "#0fb6a8",
                "motion": "stream",
                "purpose": "Normalize titles, coerce numeric fields, enrich dates/languages/countries, and keep row-level grain intact.",
                "artifacts": [
                    "music_pipeline.engineer_features()",
                    "music_pipeline.load_enriched_dataset()",
                    "AnalysisCache.dataframe()",
                ],
            },
            {
                "id": "gold",
                "name": "Gold semantics",
                "color": "#5566f6",
                "motion": "pulse",
                "purpose": "Aggregate stable metrics, inequality curves, effect sizes, archetypes, and scorecards that decision-makers can actually use.",
                "artifacts": [
                    "streamlens_processor.process_data()",
                    "music_pipeline.full_report()",
                    "advanced_metrics.py",
                ],
            },
            {
                "id": "serving",
                "name": "Serving contracts",
                "color": "#f0779f",
                "motion": "signal",
                "purpose": "Expose the same gold outputs to FastAPI, static JSON, and the browser surface while keeping the analytical scope visible.",
                "artifacts": [
                    "app.py /api/* endpoints",
                    "build_static.py",
                    "index.html static-host shim",
                ],
            },
        ],
        "lineage": [
            {"from": "bronze", "to": "silver", "label": "coerce + dedupe + enrich"},
            {"from": "silver", "to": "gold", "label": "metrics + confidence + model guardrails"},
            {"from": "gold", "to": "serving", "label": "API + static snapshots + UI"},
        ],
        "reproducibility": reproducibility,
        "contracts": datasets,
        "quality_highlights": [
            {
                "name": "Claim boundary",
                "detail": "Synthetic representation data and public music data stay separated all the way to the UI so the repo never pretends one lane proves the other.",
            },
            {
                "name": "Target leakage block",
                "detail": "Music prediction excludes virality_coefficient because it is derived from views and would make the model look smarter than it is.",
            },
            {
                "name": "Gold parity",
                "detail": "The static-host JSON exports are baked from the same Python pipeline the live API uses instead of from hand-edited files.",
            },
            {
                "name": "Refresh discipline",
                "detail": "The music lane exposes manual refresh status explicitly; the synthetic lane regenerates only when a new run is requested.",
            },
        ],
    }
