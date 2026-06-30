#!/usr/bin/env python3
"""
Stream API server.
Serves the public interactive dashboard and the analysis API.
Author: Cazandra Aporbo, MS
"""

import os
from pathlib import Path
from threading import Lock
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

import music_ingest
import music_intelligence
import music_pipeline
from music_decision_lab import build_decision_lab
from advanced_metrics import letter_grade as grade_for
from bias_library import BIAS_LIBRARY, CATEGORIES, bias_propagation_surface
from data_engineering import build_data_engineering_snapshot
from lens_sdk import default_registry, evaluate_stream
from loopchii_lite import public_playground_snapshot, simulate_governance
from media_liability_lab import (
    analyze_compulsive_usage,
    build_causal_map,
    guard_generated_buffer,
    public_media_lab_snapshot,
    sample_recommendation_events,
)
from stream_backend import RuntimeConfig, StreamRuntime
from stream_backend.analytics.streaming_readiness import build_streaming_readiness_snapshot
from stream_backend.services.catalog import build_runtime_catalog
from streamlens_processor import DataProcessor

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="LOOPCHii Stream API",
    description=(
        "Public research API for measurable media bias, music virality, cultural attention, "
        "and inspectable data-engineering contracts."
    ),
    version="1.1.0",
    contact={
        "name": "LOOPCHii Stream",
        "url": "https://github.com/loopchii/Stream",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/loopchii/Stream/blob/main/LICENSE",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


class AnalysisCache:
    """Thread-safe cache of the latest analysis run"""

    def __init__(self):
        self._lock = Lock()
        self._df: Optional[pd.DataFrame] = None
        self._results: Optional[dict] = None
        self._processor = DataProcessor()

    def run(self, n_samples: int = 5000) -> dict:
        with self._lock:
            df = self._processor.generate_synthetic_data(n_samples=n_samples)
            raw = self._processor.process_data(df)
            self._df = df
            self._results = self._processor.export_results(
                raw, filename=str(BASE_DIR / "analysis_results.json")
            )
            return self._results

    def results(self) -> dict:
        with self._lock:
            cached = self._results
        if cached is None:
            return self.run()
        return cached

    def dataframe(self) -> pd.DataFrame:
        with self._lock:
            df = self._df
        if df is None:
            self.run()
            with self._lock:
                df = self._df
        return df


cache = AnalysisCache()


class MusicCache:
    """Cache of the real-data music report (recomputed only on refresh)."""

    def __init__(self):
        self._lock = Lock()
        self._report: Optional[dict] = None

    def report(self) -> dict:
        with self._lock:
            if self._report is None:
                self._report = music_pipeline.full_report()
            return self._report

    def invalidate(self) -> None:
        with self._lock:
            self._report = None
        music_pipeline.load_dataset.cache_clear()
        music_pipeline.load_enriched_dataset.cache_clear()


music_cache = MusicCache()


class MusicIntelligenceCache:
    """Cache the score-aware music harvest so the UI can inspect it cheaply."""

    def __init__(self):
        self._lock = Lock()
        self._package: Optional[dict] = None

    def package(self) -> dict:
        with self._lock:
            if self._package is None:
                self._package = music_intelligence.build_music_data_package(
                    repo_root=BASE_DIR,
                    enable_live_enrichment=False,
                )
            return self._package

    def invalidate(self) -> None:
        with self._lock:
            self._package = None


music_intelligence_cache = MusicIntelligenceCache()

runtime_config = RuntimeConfig.from_base_dir(BASE_DIR)
runtime_service = StreamRuntime(
    config=runtime_config,
    representation_results_fn=lambda n: cache.run(n_samples=n),
    representation_df_fn=cache.dataframe,
    music_report_fn=music_cache.report,
    music_df_fn=music_pipeline.load_enriched_dataset,
    music_index_fn=music_intelligence_cache.package,
)


@app.get("/", include_in_schema=False)
def dashboard():
    index = BASE_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(index)


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    path = BASE_DIR / "manifest.webmanifest"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    return FileResponse(path, media_type="application/manifest+json")


@app.get("/service-worker.js", include_in_schema=False)
def service_worker():
    path = BASE_DIR / "service-worker.js"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Service worker not found")
    return FileResponse(path, media_type="application/javascript")


@app.get("/openapi.stream.json", include_in_schema=False)
def openapi_export():
    path = BASE_DIR / "openapi.stream.json"
    if path.exists():
        return FileResponse(path, media_type="application/json")
    return JSONResponse(app.openapi())


@app.get("/StreamLen_processors.html", include_in_schema=False)
def processors_notebook():
    path = BASE_DIR / "StreamLen_processors.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Notebook not found")
    return FileResponse(path, media_type="text/html")


@app.get("/contributing.md", include_in_schema=False)
def contributing_surface():
    path = BASE_DIR / "contributing.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Contributing guide not found")
    return FileResponse(path, media_type="text/markdown")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "stream", "publisher": "loopchii", "version": "1.1.0"}


@app.get("/api/results")
def results():
    """Full analysis results (cached)"""
    return cache.results()


@app.post("/api/analyze")
def analyze(n_samples: int = Query(default=5000, ge=100, le=100000)):
    """Re-run the analysis pipeline"""
    return cache.run(n_samples=n_samples)


@app.get("/api/metrics/overview")
def overview():
    res = cache.results()
    overall = res["overall_metrics"]
    return {
        "diversity_index": overall["diversity_index"],
        "gender_parity": overall["gender_parity"],
    }


@app.get("/api/metrics/temporal")
def temporal():
    return cache.results()["temporal_analysis"]


@app.get("/api/metrics/platforms")
def platforms():
    return cache.results()["platform_comparison"]


@app.get("/api/metrics/bias")
def bias():
    return cache.results()["bias_detection"]


@app.get("/api/metrics/genres")
def genres():
    return cache.results()["genre_analysis"]


@app.get("/api/metrics/media")
def media_types():
    """Per-media-type diversity and parity metrics"""
    return cache.results().get("media_type_analysis", [])


@app.get("/api/metrics/platform-media")
def platform_media_types():
    """Per-platform media-type breakdown (film vs series vs docs, etc.)."""
    return cache.results().get("platform_media_analysis", [])


@app.get("/api/metrics/network")
def network():
    return cache.results()["network_metrics"]


@app.get("/api/metrics/intersectionality")
def intersectionality(limit: int = Query(default=10, ge=1, le=50)):
    """Most under- and over-represented intersectional groups"""
    groups = cache.results()["overall_metrics"]["intersectionality"]
    ranked = sorted(groups.items(), key=lambda kv: kv[1]["ratio"])
    fmt = [
        {"group": k, "representation": v["representation"],
         "baseline": v["baseline"], "ratio": v["ratio"]}
        for k, v in ranked
    ]
    return {
        "most_underrepresented": fmt[:limit],
        "most_overrepresented": fmt[-limit:][::-1],
    }


@app.get("/api/metrics/advanced")
def advanced_metrics():
    """Premium analytics: inequality (Gini/Lorenz/Theil), Simpson diversity,
    chi-square effect sizes, trend regression and bootstrap confidence bands."""
    return cache.results()["advanced_metrics"]


@app.get("/api/metrics/scorecard")
def scorecard():
    """Per-platform A-F report card across four representation dimensions"""
    return cache.results()["advanced_metrics"]["scorecard"]


@app.get("/api/simulate/parity")
def simulate_parity(female_ratio: float = Query(default=0.5, ge=0.0, le=1.0)):
    """What-if: gender parity index and grade for a hypothetical female lead share.

    parity = 1 - |0.5 - female_ratio| * 2. Pure formula, exposed so the
    interactive simulator round-trips through the backend like every other control.
    """
    parity = 1.0 - abs(0.5 - female_ratio) * 2.0
    if parity >= 0.9:
        verdict = "At or near a 50/50 cast — parity is effectively balanced."
    elif parity >= 0.7:
        verdict = "A visible but moderate skew toward one gender."
    elif parity >= 0.4:
        verdict = "A strong imbalance; one gender dominates the cast."
    else:
        verdict = "Near-total dominance by one gender."
    return {
        "female_ratio": round(female_ratio, 4),
        "male_ratio": round(1.0 - female_ratio, 4),
        "parity": round(parity, 4),
        "grade": grade_for(parity),
        "verdict": verdict,
    }


@app.get("/api/insights")
def insights():
    """Narrative findings generated from the latest analysis run"""
    return cache.results()["insights"]


@app.get("/api/lenses/catalog")
def lenses_catalog():
    """Public catalog of the active lens SDK registry."""
    return {"items": default_registry().catalog()}


@app.get("/api/lenses/demo-stream")
def lenses_demo_stream(limit: int = Query(default=18, ge=1, le=80)):
    """Evaluate grouped stream records with the public lens registry."""
    evaluations = evaluate_stream(cache.dataframe(), registry=default_registry(), max_groups=limit)
    return {
        "count": len(evaluations),
        "items": evaluations,
    }


@app.get("/api/media-lab/overview")
def media_lab_overview():
    """Public enterprise-media research snapshot."""
    return public_media_lab_snapshot()


@app.get("/api/media-lab/compulsive-loop")
def media_lab_compulsive_loop():
    """Analyze a deterministic sample recommendation stream for compulsive-loop risk."""
    return analyze_compulsive_usage(sample_recommendation_events())


@app.get("/api/media-lab/generative-guard")
def media_lab_generative_guard():
    """Run the public generative buffer guard against a sample liability payload."""
    return guard_generated_buffer(b"safe-frame|copyrighted-castle|soundtrack-stem")


@app.get("/api/media-lab/causal-map")
def media_lab_causal_map():
    """Export a readable causal map of recommendation flow."""
    return build_causal_map(sample_recommendation_events())


@app.get("/api/export")
def export():
    """Download the full analysis results as JSON"""
    return JSONResponse(
        content=cache.results(),
        headers={"Content-Disposition": "attachment; filename=stream_results.json"},
    )


LEARN_CONTENT = [
    {
        "id": "shannon",
        "title": "Shannon Diversity Index",
        "summary": "Borrowed from ecology, it measures how evenly demographic groups are represented.",
        "detail": ("H = -sum(p_i * ln(p_i)), normalized by ln(k). A score of 1.0 means every "
                   "group appears equally often; 0 means a single group dominates entirely. "
                   "Stream applies it to character race distributions per platform, genre, and year."),
        "try_it": "Filter to Documentary vs Action in Explore Data and compare the diversity values.",
    },
    {
        "id": "parity",
        "title": "Gender Parity Index",
        "summary": "Distance from a 50/50 gender split, scaled 0-1.",
        "detail": ("Parity = 1 - |0.5 - female_ratio| * 2. A cast that is 50% female scores 1.0; "
                   "a 70/30 split scores 0.6. It is intentionally simple so trends over time are "
                   "easy to read."),
        "try_it": "Drag the year slider on the Dashboard and watch the parity index climb.",
    },
    {
        "id": "chi-square",
        "title": "Chi-Square Bias Detection",
        "summary": "Compares observed dialogue/role distributions against an unbiased expectation.",
        "detail": ("chi2 = (observed - expected)^2 / expected. Large values mean a demographic gets far "
                   "more or less dialogue than chance would predict. Stream runs this per gender "
                   "on dialogue word counts and per role type for stereotyping."),
        "try_it": "Open GET /api/metrics/bias in the API docs to see raw chi-square scores.",
    },
    {
        "id": "homophily",
        "title": "Network Homophily",
        "summary": "Do similar characters only interact with each other?",
        "detail": ("Using the assortativity coefficient on character interaction graphs: +1 means "
                   "characters interact only within their demographic group, 0 means mixing is random, "
                   "and negative values mean cross-group interaction dominates."),
        "try_it": "Drag nodes in the Character Interaction Network and look for color clustering.",
    },
    {
        "id": "intersectionality",
        "title": "Intersectionality Scores",
        "summary": "Representation measured at the intersection of gender, race, and age.",
        "detail": ("Each gender x race x age group is compared to a uniform population baseline. "
                   "A ratio below 1.0 means the group is underrepresented relative to that baseline. "
                   "Single-axis metrics can hide gaps that only appear at intersections."),
        "try_it": "Check the Insights tab for the most underrepresented intersectional groups.",
    },
    {
        "id": "bechdel",
        "title": "Extended Bechdel Tests",
        "summary": "Classic and extended low-bar tests of meaningful representation.",
        "detail": ("The classic test asks whether two women talk about something other than a man. "
                   "Stream extends the idea to race and age: do minority characters interact "
                   "meaningfully with each other at all?"),
        "try_it": "See BiasDetector.calculate_bechdel_extension in streamlens_processor.py.",
    },
    {
        "id": "sentiment-bias",
        "title": "Sentiment Bias",
        "summary": "Are some demographics consistently written with more negative tone?",
        "detail": ("Mean sentiment score per gender is compared against the overall mean. Systematic "
                   "deviations indicate a writing-room bias in how characters from a group are framed, "
                   "independent of how much screen time they get."),
        "try_it": "Open GET /api/metrics/bias and inspect the sentiment_bias section.",
    },
    {
        "id": "screen-time",
        "title": "Screen Time Ratio",
        "summary": "Minutes on screen per demographic vs the overall average.",
        "detail": ("A ratio of 1.0 means a group gets exactly average screen time. Values above or below "
                   "reveal structural visibility gaps that persist even when casting numbers look balanced."),
        "try_it": "Compare screen_time_bias ratios in GET /api/metrics/bias.",
    },
    {
        "id": "force-physics",
        "title": "Force-Directed Physics",
        "summary": "The network graph is a real physics simulation.",
        "detail": ("Nodes repel each other (many-body charge force), links act as springs, and a collision "
                   "force prevents overlap. The layout that emerges is not designed — it is the equilibrium "
                   "of these forces, which is why tightly connected communities visually cluster together."),
        "try_it": "Drag a node in the network graph and watch the system re-equilibrate.",
    },
    {
        "id": "synthetic-data",
        "title": "About the Data (Honesty Note)",
        "summary": "This demo runs on clearly-labeled synthetic data — no fabricated real-world claims.",
        "detail": ("Every record is generated by a documented statistical model (seeded NumPy distributions) "
                   "that encodes bias patterns reported in published media-representation research. All "
                   "numbers on screen are computed live from that dataset — nothing is hard-coded — and the "
                   "same pipeline can ingest real catalog data without code changes."),
        "try_it": "Read DataProcessor.generate_synthetic_data to see exactly how each field is produced.",
    },
    {
        "id": "data-contracts",
        "title": "Data Contracts and Grain",
        "summary": "A trustworthy dashboard starts with row grain, keys, and partition rules.",
        "detail": ("Before a chart is allowed to feel persuasive, the underlying dataset needs a declared grain, "
                   "a key strategy, and enough quality checks to prove rows have not drifted into nonsense. "
                   "Stream now exposes those contracts directly for both the synthetic representation lane and "
                   "the public music lane."),
        "try_it": "Open GET /api/system/data-engineering and inspect the contract list, quality checks, and partition keys.",
    },
    {
        "id": "data-lineage",
        "title": "Lineage and Serving Layers",
        "summary": "Good analysis is a system: landing, standardizing, modeling, and serving are different jobs.",
        "detail": ("The repo now exposes an explicit bronze → silver → gold → serving path so readers can see where "
                   "raw files stop, standardization begins, and business-facing metrics finally become safe to publish. "
                   "That separation matters because a chart should never outrun the part of the system that made it."),
        "try_it": "Use the Learn tab's data platform section to follow lineage from source files through contracts into the UI.",
    },
]


@app.get("/api/bias-library")
def bias_library(category: Optional[str] = None):
    """Library of 50+ documented bias types; optional ?category= filter"""
    items = BIAS_LIBRARY
    if category:
        items = [b for b in items if b["category"] == category]
    return {"total": len(items), "categories": CATEGORIES, "items": items}


@app.get("/api/system/bias-propagation")
def bias_propagation():
    """Public map of where bias enters and how it tends to propagate."""
    return bias_propagation_surface()


@app.get("/api/learn")
def learn():
    """Educational explanations of every metric used in the analysis"""
    return LEARN_CONTENT


@app.get("/api/system/data-engineering")
def data_engineering_surface():
    """Public contract, lineage, and quality surface for the Stream repo."""
    synthetic_results = cache.results()
    synthetic_df = cache.dataframe()
    music_df = music_pipeline.load_enriched_dataset()
    music_quality = music_pipeline.quality_report(music_df)
    return build_data_engineering_snapshot(
        synthetic_df=synthetic_df,
        synthetic_results=synthetic_results,
        music_df=music_df,
        music_quality=music_quality,
    )


@app.get("/api/system/trojan-horse")
def trojan_horse_surface():
    """Public zero-friction adoption surface for the browser playground."""
    return public_playground_snapshot()


@app.get("/api/system/catalog")
def system_catalog():
    """High-level catalog of the repo's polyglot backend surfaces."""
    return build_runtime_catalog(runtime_config)


@app.get("/api/system/runtime")
def system_runtime(sample_size: int = Query(default=5000, ge=100, le=100000)):
    """Generated runtime state computed by the Python orchestration spine."""
    return runtime_service.build_snapshot(sample_size=sample_size)


@app.get("/api/system/runtime/latest")
def system_runtime_latest():
    """Last persisted runtime snapshot when SQLite materialization has been run."""
    latest = runtime_service.latest_snapshot()
    if latest is None:
        raise HTTPException(status_code=404, detail="No persisted runtime snapshot found yet.")
    return latest


@app.get("/api/system/frontend-state")
def system_frontend_state(sample_size: int = Query(default=5000, ge=100, le=100000)):
    """Frontend payload generated from Python so the browser owns less logic."""
    return runtime_service.build_snapshot(sample_size=sample_size)["frontend_state"]


@app.get("/api/system/governance")
def system_governance(sample_size: int = Query(default=5000, ge=100, le=100000)):
    """Public governance contract for fairness, claim boundaries, and review posture."""
    frontend_state = runtime_service.build_snapshot(sample_size=sample_size)["frontend_state"]
    return frontend_state["governance"]


@app.get("/api/system/streaming-readiness")
def system_streaming_readiness():
    """Candid streaming-systems review of the public repo's current operating posture."""
    music_df = music_pipeline.load_enriched_dataset()
    music_quality = music_pipeline.quality_report(music_df)
    data_engineering = build_data_engineering_snapshot(
        synthetic_df=cache.dataframe(),
        synthetic_results=cache.results(),
        music_df=music_df,
        music_quality=music_quality,
    )
    return build_streaming_readiness_snapshot(
        music_quality=music_quality,
        data_engineering=data_engineering,
    )


@app.get("/api/system/critical-spine")
def system_critical_spine(sample_size: int = Query(default=5000, ge=100, le=100000)):
    """Per-visual purpose, caveat, and improvement guidance generated by the backend."""
    return runtime_service.build_snapshot(sample_size=sample_size)["critical_spine"]


@app.get("/api/system/comparatives")
def system_comparatives(sample_size: int = Query(default=5000, ge=100, le=100000)):
    """Cross-lane comparative surface for synthetic vs public music evidence."""
    return runtime_service.build_snapshot(sample_size=sample_size)["comparatives"]


@app.post("/api/system/materialize")
def system_materialize(sample_size: int = Query(default=5000, ge=100, le=100000)):
    """Write the runtime snapshot to JSON exports and SQLite for local inspection."""
    payload = runtime_service.materialize(sample_size=sample_size, persist_sqlite=True)
    return {
        "materialized": True,
        "run_id": payload["run_id"],
        "sqlite_path": str(runtime_config.sqlite_path),
        "artifacts": payload["artifacts"],
    }


@app.get("/api/playground/simulate")
def playground_simulate(prompt: str = Query(..., min_length=4, max_length=600)):
    """Deterministic public guard simulation for the split-screen playground."""
    return simulate_governance(prompt)


@app.get("/api/characters")
def characters(
    platform: Optional[str] = None,
    genre: Optional[str] = None,
    media_type: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=5000),
):
    """Filterable character-level records from the latest analysis run"""
    df = cache.dataframe()
    if platform:
        df = df[df["platform"] == platform]
    if genre:
        df = df[df["genre"] == genre]
    if media_type:
        df = df[df["media_type"] == media_type]
    if year:
        df = df[df["year"] == year]
    return df.head(limit).to_dict("records")


# --------------------------------------------------------------------------- #
# Music Virality (real YouTube data)
# --------------------------------------------------------------------------- #
@app.get("/api/music/overview")
def music_overview():
    """Headline stats for the real top-music dataset."""
    return music_cache.report()["overview"]


@app.get("/api/music/powerlaw")
def music_powerlaw():
    """Power-law fit of view counts (alpha, KS, bootstrap CI, CCDF points)."""
    return music_cache.report()["power_law"]


@app.get("/api/music/inequality")
def music_inequality():
    """Attention inequality: Gini, Lorenz, Theil, channel concentration."""
    return music_cache.report()["inequality"]


@app.get("/api/music/correlations")
def music_correlations():
    """Spearman + partial correlations of each feature with view count."""
    return music_cache.report()["correlations"]


@app.get("/api/music/archetypes")
def music_archetypes():
    """K-means viral archetypes and the per-song scatter."""
    return music_cache.report()["archetypes"]


@app.get("/api/music/network")
def music_network():
    """Tag co-occurrence graph (nodes, edges, density, communities)."""
    return music_cache.report()["network"]


@app.get("/api/music/predictability")
def music_predictability():
    """Cross-validated ensemble R-squared and feature importances."""
    return music_cache.report()["predictability"]


@app.get("/api/music/resonance")
def music_resonance():
    """Public resonance proxy: repetition, concentration, and release pressure."""
    return music_cache.report()["resonance"]


@app.get("/api/music/songs")
def music_songs(
    limit: int = Query(default=700, ge=1, le=1000),
    sort_by: str = "view_count",
):
    """The real songs table, sortable for the explorer."""
    return music_pipeline.songs_table(limit=limit, sort_by=sort_by)


@app.get("/api/music/simulate")
def music_simulate(
    duration_min: float = Query(default=3.2, ge=0.2, le=15.0),
    channel_follower_count: float = Query(default=5_000_000, ge=0, le=500_000_000),
    tag_count: float = Query(default=20, ge=0, le=200),
    is_official: float = Query(default=1.0, ge=0.0, le=1.0),
):
    """What-if virality predictor: maps a hypothetical upload to a view percentile."""
    return music_pipeline.simulate_virality(
        duration_min=duration_min,
        channel_follower_count=channel_follower_count,
        tag_count=tag_count,
        is_official=is_official,
    )


@app.get("/api/music/status")
def music_status():
    """Whether live YouTube Data API extraction is wired (key present) or not."""
    return music_ingest.status()


@app.get("/api/music/bias")
def music_bias():
    """Gender, genre, collaboration, and concentration bias metrics."""
    return music_cache.report()["bias"]


@app.get("/api/music/quality")
def music_quality():
    """Source audit, cleaning steps, and model guardrails for the music lane."""
    return music_cache.report()["quality"]


@app.get("/api/music/decision-lab")
def music_decision_lab():
    """Higher-rigor cohort drift and controlled comparison surface for the music lane."""
    report = music_cache.report()
    if "decision_lab" in report:
        return report["decision_lab"]
    return build_decision_lab(music_pipeline.load_enriched_dataset())


@app.get("/api/music/intelligence")
def music_intelligence_summary():
    """Score-aware repository harvest for note, chord, and notation coverage."""
    summary = dict(music_intelligence_cache.package()["summary"])
    summary["living_media"] = music_cache.report().get("living_media", {})
    return summary


@app.get("/api/music/living-media")
def music_living_media():
    """Living media field read built from public structural proxies."""
    return music_cache.report()["living_media"]


@app.get("/api/music/index")
def music_index(
    limit: int = Query(default=60, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=5000),
    q: str = Query(default="", max_length=200),
    score_linked: Optional[bool] = None,
):
    """Piece-level index linking catalog songs to any local notation assets."""
    items = music_intelligence_cache.package()["pieces"]
    query = q.strip().lower()
    if score_linked is not None:
        items = [
            item
            for item in items
            if bool((item.get("notation_summary") or {}).get("matched_file_count")) is score_linked
        ]
    if query:
        items = [
            item
            for item in items
            if query
            in " ".join(
                [
                    str(item.get("title") or ""),
                    str(item.get("artist") or ""),
                    str(item.get("composer") or ""),
                    " ".join(source.get("path", "") for source in item.get("source_files") or []),
                ]
            ).lower()
        ]
    window = items[offset:offset + limit]
    return {
        "total": len(items),
        "offset": offset,
        "limit": limit,
        "count": len(window),
        "items": window,
    }


@app.get("/api/music/genres")
def music_genres():
    """Per-genre breakdown with view share, duration, and collaboration mix."""
    return music_cache.report()["bias"].get("genre_breakdown", [])


@app.get("/api/music/timeline")
def music_timeline():
    """Upload/publication time series from the public supplemental datasets."""
    return music_cache.report()["bias"].get("publication_timeline", {})


@app.post("/api/music/refresh")
def music_refresh(
    max_results: int = Query(default=100, ge=10, le=200),
    region: str = "US",
):
    """Pull a fresh, larger sample from the YouTube Data API (needs a key)."""
    if not music_ingest.available():
        raise HTTPException(
            status_code=503,
            detail="No YOUTUBE_API_KEY configured; serving the bundled real dataset.",
        )
    path = music_ingest.refresh_dataset(max_results=max_results, region=region)
    music_cache.invalidate()
    music_intelligence_cache.invalidate()
    return {"refreshed": True, "path": str(path), "overview": music_cache.report()["overview"]}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
