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
from fastapi.responses import FileResponse, JSONResponse

import music_ingest
import music_pipeline
from advanced_metrics import letter_grade as grade_for
from bias_library import BIAS_LIBRARY, CATEGORIES
from lens_sdk import default_registry, evaluate_stream
from media_liability_lab import (
    analyze_compulsive_usage,
    build_causal_map,
    guard_generated_buffer,
    public_media_lab_snapshot,
    sample_recommendation_events,
)
from streamlens_processor import DataProcessor

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Stream API",
    description="Loopchii public research API for measurable media bias, representation, and attention analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


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


music_cache = MusicCache()


@app.get("/", include_in_schema=False)
def dashboard():
    index = BASE_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(index)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "stream", "publisher": "loopchii", "version": "1.0.0"}


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
]


@app.get("/api/bias-library")
def bias_library(category: Optional[str] = None):
    """Library of 50+ documented bias types; optional ?category= filter"""
    items = BIAS_LIBRARY
    if category:
        items = [b for b in items if b["category"] == category]
    return {"total": len(items), "categories": CATEGORIES, "items": items}


@app.get("/api/learn")
def learn():
    """Educational explanations of every metric used in the analysis"""
    return LEARN_CONTENT


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


@app.get("/api/music/songs")
def music_songs(
    limit: int = Query(default=100, ge=1, le=1000),
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
    return {"refreshed": True, "path": str(path), "overview": music_cache.report()["overview"]}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
