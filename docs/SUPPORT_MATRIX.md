# Stream Support Matrix

This repository is designed to run in a few different modes. The important distinction is not just operating system support, but **which runtime lane you are trying to use**.

## Supported lanes

| Lane | What it does | Required | Typical command |
|---|---|---|---|
| Static public surface | Serves the baked dashboard and JSON without Python API calls | Any modern browser | `python -m http.server 8001` |
| Live API | Runs FastAPI plus the analysis pipeline locally | Python 3.10+ | `python app.py` |
| Static rebuild | Recomputes `data/` and `openapi.stream.json` from source | Python 3.10+ | `python build_static.py` |
| Runtime doctor | Checks imports, files, SQLite path, public data health, and built artifacts | Python 3.10+ | `python -m stream_backend.cli.doctor` |
| Container lane | Builds static assets first, then serves the live API | Docker | `docker build -t loopchii-stream .` |

## Quick setup by environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m stream_backend.cli.doctor
python build_static.py
python -m http.server 8001
```

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m stream_backend.cli.doctor
python build_static.py
python -m http.server 8001
```

### Browser-only preview

If you only want the public surface and not the live API, you do not need Uvicorn. Build once, then serve the repository root with any static file server so `index.html` can fetch the baked `data/` JSON.

### Container lane

```bash
docker build -t loopchii-stream .
docker run --rm -p 8001:8001 loopchii-stream
```

## Operating systems

| System | Status | Notes |
|---|---|---|
| macOS (Apple Silicon / Intel) | Supported | Best-tested local contributor path. |
| Linux | Supported | Recommended for CI-like local runs and container work. |
| Windows | Supported through Python + venv | Prefer PowerShell or WSL2 if you want a Linux-like shell. |

## Python versions

| Version | Status | Notes |
|---|---|---|
| 3.10 | Supported | Good baseline for contributors. |
| 3.11 | Supported | Recommended local development target. |
| 3.12 | Supported | Expected to work; run the doctor after install. |
| < 3.10 | Not supported | Some typing, package, and build assumptions will fail. |

## Core dependency posture

The public pipeline expects these libraries to import successfully:

- `numpy`
- `pandas`
- `scipy`
- `scikit-learn`
- `networkx`
- `fastapi`
- `uvicorn`

Why these matter:

- `numpy`, `pandas`, `scipy`, and `scikit-learn` drive the statistical and model-backed analysis paths.
- `networkx` powers the tag and relationship surfaces.
- `fastapi` and `uvicorn` keep the live API contract aligned with the static exports.
- `httpx` is used by the test and integration surface.

If one of these is missing, run:

```bash
pip install -r requirements-dev.txt
python -m stream_backend.cli.doctor
```

## What the doctor checks

The runtime doctor is intentionally simple and fast. It confirms:

- Python version and platform
- required import availability
- committed repo files are present
- the SQLite snapshot directory is writable
- the public music dataset loads
- the decision lab can be generated from the current corpus
- static build artifacts exist or need rebuilding

This is meant to answer the first trust questions quickly:

- *Will it run here?*
- *Is the public corpus healthy enough to study?*
- *Has the static site drifted away from the backend?*
- *Do the timeline and decision surfaces have enough public metadata to say anything useful?*

## If something looks wrong in the UI

Start here before assuming the analysis is broken:

1. Run `python -m stream_backend.cli.doctor`
2. Rebuild with `python build_static.py`
3. Hard refresh the browser
4. Check whether the issue is a data-gap warning, a stale static export, or a runtime rendering failure

That order matters. Stream keeps uncertainty visible on purpose, so “thin evidence” and “broken surface” are not the same thing.

## Common recovery moves

| Symptom | Likely cause | Fix |
|---|---|---|
| Music lane loads with empty panels | Static build is stale or the front-end runtime hit an exception | Rebuild with `python build_static.py`, then reload the page |
| API starts but docs feel old | Static exports were not refreshed after code changes | Re-run `python build_static.py` |
| `ModuleNotFoundError: scipy` | Runtime requirements are incomplete in the environment | `pip install -r requirements-dev.txt` |
| `decision-lab` or `runtime` artifacts missing | Static outputs have not been baked on this clone yet | `python build_static.py` |
| SQLite snapshot errors | Directory permissions or a stale runtime folder | Check write access under `data/system/runtime/` and rerun the doctor |

## Related boundary documents

If the question is not "will it run?" but "what is this allowed to do?" or "what kind of public repo is this?", go next to:

- [PRIVACY_AND_DATA.md](PRIVACY_AND_DATA.md)
- [ETHICS.md](ETHICS.md)
- [../GOVERNANCE.md](../GOVERNANCE.md)
- [../TERMS.md](../TERMS.md)
- [../data/README.md](../data/README.md)
