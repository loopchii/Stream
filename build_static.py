#!/usr/bin/env python3
"""Bake the StreamLens analysis pipeline into static JSON for a backend-free site.

Runs the real analysis pipeline once per UI-offered sample size and writes every
API response into ``data/`` at the repo root. The dashboard's ``index.html`` ships
with a host-gated fetch shim that, on a static host (GitHub Pages / ``file://``),
serves these files instead of calling the Python API - so the whole dashboard
works with no server. On localhost the shim stays inert and ``python app.py`` is
used. Every number here is computed by the same pipeline the live API uses -
nothing is hand-written. Re-run whenever the analysis code changes:

    python build_static.py

Author: Cazandra Aporbo, MS
"""

import json
from pathlib import Path

import app as backend
import music_intelligence
import music_pipeline

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
SIZES = [1000, 5000, 10000, 25000]
DEFAULT_SIZE = 5000
CHAR_CAP_DEFAULT = 5000
CHAR_CAP_OTHER = 200


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")
    print(f"  wrote {path.relative_to(BASE)}")


def build_data() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    # Sample-size independent content.
    write_json(DATA / "learn.json", backend.learn())
    write_json(DATA / "bias-library.json", backend.bias_library())
    write_json(DATA / "system" / "data-engineering.json", backend.data_engineering_surface())
    write_json(DATA / "system" / "bias-propagation.json", backend.bias_propagation())
    write_json(DATA / "system" / "trojan-horse.json", backend.trojan_horse_surface())
    write_json(DATA / "system" / "catalog.json", backend.system_catalog())
    write_json(BASE / "openapi.stream.json", backend.app.openapi())

    for n in SIZES:
        print(f"Running pipeline at n_samples={n} ...")
        backend.cache.run(n_samples=n)
        out = DATA / f"n{n}"
        write_json(out / "overview.json", backend.overview())
        write_json(out / "genres.json", backend.genres())
        write_json(out / "media.json", backend.media_types())
        write_json(out / "platform-media.json", backend.results().get("platform_media_analysis", []))
        write_json(out / "bias.json", backend.bias())
        write_json(out / "insights.json", backend.insights())
        write_json(out / "intersectionality.json", backend.intersectionality(limit=8))
        write_json(out / "advanced.json", backend.advanced_metrics())
        cap = CHAR_CAP_DEFAULT if n == DEFAULT_SIZE else CHAR_CAP_OTHER
        write_json(out / "characters.json", backend.characters(limit=cap))
        if n == DEFAULT_SIZE:
            write_json(out / "results.json", backend.results())
            write_json(DATA / "system" / "frontend-state.json", backend.system_frontend_state(sample_size=n))
            write_json(DATA / "system" / "critical-spine.json", backend.system_critical_spine(sample_size=n))
            write_json(DATA / "system" / "comparatives.json", backend.system_comparatives(sample_size=n))
            write_json(DATA / "system" / "runtime.json", backend.system_runtime(sample_size=n))

    build_music()
    backend.runtime_service.materialize(sample_size=DEFAULT_SIZE, persist_sqlite=True)

    # Disable Jekyll so GitHub Pages serves the data/ files verbatim.
    (BASE / ".nojekyll").write_text("", encoding="utf-8")
    print("  wrote .nojekyll")


def build_music() -> None:
    """Bake the real-data music virality module into data/music/*.json."""
    print("Running real-data music pipeline ...")
    out = DATA / "music"
    report = music_pipeline.full_report()
    write_json(out / "overview.json", report["overview"])
    write_json(out / "powerlaw.json", report["power_law"])
    write_json(out / "inequality.json", report["inequality"])
    write_json(out / "correlations.json", report["correlations"])
    write_json(out / "archetypes.json", report["archetypes"])
    write_json(out / "network.json", report["network"])
    write_json(out / "predictability.json", report["predictability"])
    write_json(out / "resonance.json", report["resonance"])
    write_json(out / "songs.json", report["songs"])
    write_json(out / "bias.json", report["bias"])
    write_json(out / "quality.json", report["quality"])
    write_json(out / "genres.json", report["bias"].get("genre_breakdown", []))
    write_json(out / "timeline.json", report["bias"].get("publication_timeline", {}))
    write_json(out / "status.json", {"live_available": False, "source": "bundled_csv",
                                     "note": "Static build - committed real dataset."})
    write_json(out / "simulate.json", music_pipeline.simulate_grid())
    intelligence = music_intelligence.build_music_data_package(
        repo_root=BASE,
        enable_live_enrichment=False,
    )
    write_json(out / "intelligence.json", intelligence["summary"])
    write_json(out / "index.json", intelligence["pieces"])
    music_intelligence.write_package(
        intelligence,
        BASE / "music_index.json",
        BASE / "music_index.csv",
        BASE / "music_analysis_report.md",
    )


if __name__ == "__main__":
    print("Baking static StreamLens data into data/ ...")
    build_data()
    print("Done. Preview the static site with:")
    print("  python -m http.server 8001   then open  http://localhost:8001/?static=1")
