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

    for n in SIZES:
        print(f"Running pipeline at n_samples={n} ...")
        backend.cache.run(n_samples=n)
        out = DATA / f"n{n}"
        write_json(out / "overview.json", backend.overview())
        write_json(out / "genres.json", backend.genres())
        write_json(out / "media.json", backend.media_types())
        write_json(out / "bias.json", backend.bias())
        write_json(out / "insights.json", backend.insights())
        write_json(out / "intersectionality.json", backend.intersectionality(limit=8))
        write_json(out / "advanced.json", backend.advanced_metrics())
        cap = CHAR_CAP_DEFAULT if n == DEFAULT_SIZE else CHAR_CAP_OTHER
        write_json(out / "characters.json", backend.characters(limit=cap))
        if n == DEFAULT_SIZE:
            write_json(out / "results.json", backend.results())

    # Disable Jekyll so GitHub Pages serves the data/ files verbatim.
    (BASE / ".nojekyll").write_text("", encoding="utf-8")
    print("  wrote .nojekyll")


if __name__ == "__main__":
    print("Baking static StreamLens data into data/ ...")
    build_data()
    print("Done. Preview the static site with:")
    print("  python -m http.server 8001   then open  http://localhost:8001/?static=1")
