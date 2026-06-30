# Engineering Foundation

`Stream` is an open-source analytical system with a visible backend, a reproducible data pipeline, and a browser surface that reads from the same contracts the API serves. It is not a distributed streaming engine, and it should not be described as one until the operational guarantees exist.

## What ships today

- A FastAPI service in [app.py](/Users/cazandraaporbo/Desktop/LOOPCHII/Windsurf_Transfer/public-repos/Stream/app.py)
- A package-based backend spine in [stream_backend/](/Users/cazandraaporbo/Desktop/LOOPCHII/Windsurf_Transfer/public-repos/Stream/stream_backend)
- Static export generation through [build_static.py](/Users/cazandraaporbo/Desktop/LOOPCHII/Windsurf_Transfer/public-repos/Stream/build_static.py)
- A browser analysis surface in [index.html](/Users/cazandraaporbo/Desktop/LOOPCHII/Windsurf_Transfer/public-repos/Stream/index.html)
- SQLite-backed runtime materialization through `StreamRuntime`
- Public machine-readable contracts in `data/system/*.json`

## System topology

1. Land raw public inputs or generate deterministic synthetic inputs.
2. Normalize and enrich them in Python.
3. Compute analytical summaries, models, and governance surfaces.
4. Materialize the results for API responses and static hosting.
5. Render the same outputs in the browser without inventing a second truth.

The important part is parity: the browser, the static exports, and the live API all derive from the same analytical code path.

## Analytical methods already in the code

- Chi-square tests for distributional differences
- Shannon entropy for diversity surfaces
- NetworkX assortativity and graph structure analysis
- Cramer's V effect sizes
- Bootstrap confidence intervals
- Spearman and partial correlations
- Cross-validated RandomForest and GradientBoosting models
- Counterfactual decision-lab experiments
- Lorenz, Gini, and Theil inequality measures

These are not decorative labels in the UI. They are part of the backend outputs and the public artifacts committed to the repository.

## Reproducibility posture

- The synthetic representation lane is seeded and deterministic.
- Public music data is committed, labeled, and kept separate from synthetic representation data.
- `build_static.py` regenerates the same contracts used by the browser fallback mode.
- `openapi.stream.json` mirrors the API contract for offline inspection.
- `python -m stream_backend.cli.doctor` provides a local preflight before anyone trusts a run.

## Validation

Recommended local validation:

```bash
pip install -r requirements-dev.txt
python -m stream_backend.cli.doctor
pytest -q
python build_static.py
```

What these checks cover:

- import health
- required files
- SQLite path writability
- music data loading
- year and genre coverage
- static artifact presence
- API behavior
- pipeline calculations
- music decision lab integrity

## Performance posture

The benchmark script measures the real public workload:

```bash
python benchmarks/analytics_scale.py --rows 1000000
```

It benchmarks grouped aggregations used by the current analysis lane. It does not claim replay, partitioning, or event-processing guarantees the repository does not yet implement.

## Operational limits that remain visible

The repo does not yet provide:

- exactly-once processing
- checkpoint recovery
- replayable event logs
- partition and ordering guarantees
- backpressure management
- distributed tracing
- streaming fault-tolerance drills

Those limits are part of the engineering story, not something to hide. The repository gains trust by making them explicit.

## Why this matters

`Stream` should read as engineered work, not a visual concept. The backend exists, the data contracts exist, the validation path exists, and the limitations are stated plainly. That is the standard this repository should hold.
