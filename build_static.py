#!/usr/bin/env python3
"""Build a fully static, backend-free version of the StreamLens dashboard.

Runs the real analysis pipeline once per UI-offered sample size and bakes every
API response into static JSON under ``docs/data/``. A small fetch shim injected
into ``docs/index.html`` maps ``/api/*`` calls to those files (and computes the
two trivial dynamic endpoints in the browser), so the entire dashboard works
from a static host such as GitHub Pages.

Every number is computed by the same pipeline the live API uses - nothing is
hand-written. Re-run this whenever the analysis code or the dashboard changes:

    python build_static.py

Author: Cazandra Aporbo, MS
"""

import json
from pathlib import Path

import app as backend

BASE = Path(__file__).resolve().parent
DOCS = BASE / "docs"
DATA = DOCS / "data"
SIZES = [1000, 5000, 10000, 25000]
DEFAULT_SIZE = 5000
CHAR_CAP_DEFAULT = 5000
CHAR_CAP_OTHER = 200

# Injected into docs/index.html only. Intercepts fetch('/api/...') and serves
# the baked JSON, keeping a "current sample size" so "Run New Analysis" works.
FETCH_SHIM = """
    <script>
    /* Static GitHub Pages shim: serve baked analysis JSON instead of a live API. */
    (function () {
        var BASE = 'data/';
        var state = { n: '5000' };
        var SIZES = ['1000', '5000', '10000', '25000'];
        function J(obj, status) {
            return new Response(JSON.stringify(obj), {
                status: status || 200,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        function load(path) { return fetch(BASE + path).then(function (r) { return r.json(); }); }
        function grade(s) {
            var b = [[0.95, 'A+'], [0.90, 'A'], [0.85, 'A-'], [0.80, 'B+'], [0.75, 'B'],
                     [0.70, 'B-'], [0.65, 'C+'], [0.60, 'C'], [0.55, 'C-'], [0.50, 'D+'],
                     [0.45, 'D'], [0.40, 'D-']];
            s = Math.max(0, Math.min(1, s));
            for (var i = 0; i < b.length; i++) { if (s >= b[i][0]) return b[i][1]; }
            return 'F';
        }
        var orig = window.fetch.bind(window);
        window.fetch = function (input, init) {
            var url = (typeof input === 'string') ? input : (input && input.url) || '';
            var at = url.indexOf('/api/');
            if (at === -1) return orig(input, init);
            var path = url.slice(at), qs = {}, qi = path.indexOf('?');
            if (qi !== -1) {
                new URLSearchParams(path.slice(qi + 1)).forEach(function (v, k) { qs[k] = v; });
                path = path.slice(0, qi);
            }
            if (path === '/api/health')
                return Promise.resolve(J({ status: 'ok', service: 'streamlens-analytics', version: 'static' }));
            if (path === '/api/analyze') {
                var n = qs.n_samples || '5000';
                if (SIZES.indexOf(n) === -1) n = '5000';
                state.n = n;
                return load('n' + n + '/overview.json').then(function (o) {
                    return J({ overall_metrics: o, n_samples: Number(n) });
                });
            }
            if (path === '/api/metrics/overview') return load('n' + state.n + '/overview.json').then(J);
            if (path === '/api/metrics/genres') return load('n' + state.n + '/genres.json').then(J);
            if (path === '/api/metrics/media') return load('n' + state.n + '/media.json').then(J);
            if (path === '/api/metrics/bias') return load('n' + state.n + '/bias.json').then(J);
            if (path === '/api/insights') return load('n' + state.n + '/insights.json').then(J);
            if (path === '/api/metrics/intersectionality') return load('n' + state.n + '/intersectionality.json').then(J);
            if (path === '/api/metrics/advanced') return load('n' + state.n + '/advanced.json').then(J);
            if (path === '/api/metrics/scorecard') return load('n' + state.n + '/advanced.json').then(function (a) { return J(a.scorecard); });
            if (path === '/api/learn') return load('learn.json').then(J);
            if (path === '/api/bias-library') {
                return load('bias-library.json').then(function (d) {
                    if (qs.category) {
                        var items = d.items.filter(function (b) { return b.category === qs.category; });
                        return J({ total: items.length, categories: d.categories, items: items });
                    }
                    return J(d);
                });
            }
            if (path === '/api/characters') {
                return load('n' + state.n + '/characters.json').then(function (rows) {
                    var out = rows.filter(function (r) {
                        if (qs.platform && r.platform !== qs.platform) return false;
                        if (qs.genre && r.genre !== qs.genre) return false;
                        if (qs.media_type && r.media_type !== qs.media_type) return false;
                        if (qs.year && String(r.year) !== String(qs.year)) return false;
                        return true;
                    });
                    return J(out.slice(0, parseInt(qs.limit || '100', 10)));
                });
            }
            if (path === '/api/simulate/parity') {
                var fr = parseFloat(qs.female_ratio || '0.5');
                var parity = 1 - Math.abs(0.5 - fr) * 2, verdict;
                if (parity >= 0.9) verdict = 'At or near a 50/50 cast \\u2014 parity is effectively balanced.';
                else if (parity >= 0.7) verdict = 'A visible but moderate skew toward one gender.';
                else if (parity >= 0.4) verdict = 'A strong imbalance; one gender dominates the cast.';
                else verdict = 'Near-total dominance by one gender.';
                return Promise.resolve(J({
                    female_ratio: Math.round(fr * 1e4) / 1e4,
                    male_ratio: Math.round((1 - fr) * 1e4) / 1e4,
                    parity: Math.round(parity * 1e4) / 1e4,
                    grade: grade(parity), verdict: verdict
                }));
            }
            if (path === '/api/results' || path === '/api/export') return load('n5000/results.json').then(J);
            return Promise.resolve(J({ detail: 'Not found in static build' }, 404));
        };
    })();
    </script>
"""


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


def build_html() -> None:
    src = (BASE / "index.html").read_text(encoding="utf-8")
    src = src.replace('href="/api/export"', 'href="data/n5000/results.json"')
    src = src.replace("</head>", FETCH_SHIM + "</head>", 1)
    (DOCS / "index.html").write_text(src, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print("  wrote docs/index.html and docs/.nojekyll")


if __name__ == "__main__":
    print("Building static StreamLens site into docs/ ...")
    build_data()
    build_html()
    print("Done. Serve with:  python -m http.server -d docs 8001")
