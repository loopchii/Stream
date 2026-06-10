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
from fastapi.responses import FileResponse

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
