#!/usr/bin/env python3
"""
StreamLens Analytics API Server
Serves the interactive dashboard and a REST API over the analysis pipeline.
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

from streamlens_processor import DataProcessor

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="StreamLens Analytics API",
    description="Quantitative bias and representation analysis for streaming media",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
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
        if self._df is None:
            self.run()
        return self._df


cache = AnalysisCache()


@app.get("/", include_in_schema=False)
def dashboard():
    index = BASE_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(index)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "streamlens-analytics", "version": "1.0.0"}


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


@app.get("/api/insights")
def insights():
    """Narrative findings generated from the latest analysis run"""
    return cache.results()["insights"]


@app.get("/api/export")
def export():
    """Download the full analysis results as JSON"""
    return JSONResponse(
        content=cache.results(),
        headers={"Content-Disposition": "attachment; filename=streamlens_results.json"},
    )


LEARN_CONTENT = [
    {
        "id": "shannon",
        "title": "Shannon Diversity Index",
        "summary": "Borrowed from ecology, it measures how evenly demographic groups are represented.",
        "detail": ("H = -sum(p_i * ln(p_i)), normalized by ln(k). A score of 1.0 means every "
                   "group appears equally often; 0 means a single group dominates entirely. "
                   "StreamLens applies it to character race distributions per platform, genre, and year."),
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
                   "more or less dialogue than chance would predict. StreamLens runs this per gender "
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
                   "StreamLens extends the idea to race and age: do minority characters interact "
                   "meaningfully with each other at all?"),
        "try_it": "See BiasDetector.calculate_bechdel_extension in streamlens_processor.py.",
    },
]


@app.get("/api/learn")
def learn():
    """Educational explanations of every metric used in the analysis"""
    return LEARN_CONTENT


@app.get("/api/characters")
def characters(
    platform: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=5000),
):
    """Filterable character-level records from the latest analysis run"""
    df = cache.dataframe()
    if platform:
        df = df[df["platform"] == platform]
    if genre:
        df = df[df["genre"] == genre]
    if year:
        df = df[df["year"] == year]
    return df.head(limit).to_dict("records")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
