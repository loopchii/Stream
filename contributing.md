# Contributing to Stream

Thanks for spending time with `Stream`.

This repository is an open-source Loopchii research repo. The goal is to make the methods, visual reasoning, and public artifacts more useful and more inspectable without drifting into overstated claims or exposing proprietary systems that do not belong in open source.

Before you start, please read:

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [GOVERNANCE.md](GOVERNANCE.md)
- [docs/PRIVACY_AND_DATA.md](docs/PRIVACY_AND_DATA.md)
- [docs/ETHICS.md](docs/ETHICS.md)

## What We Welcome

Contributions are strongest when they improve one of these lanes:

- **Public research clarity**
  Better explanations, tighter definitions, cleaner examples, stronger README structure, and more useful walkthroughs.
- **Reproducibility**
  Test fixes, setup improvements, bug fixes, dependency cleanup, and anything that makes local runs easier to trust.
- **Visualization quality**
  Front-end polish, interaction improvements, performance fixes, accessibility improvements, and clearer storytelling in the dashboard.
- **Method transparency**
  Better documentation around metrics already present in the codebase, plus validation or correction of public claims.
- **Data hygiene**
  Fixes to committed public datasets, source notes, provenance labels, and boundary language around synthetic vs real data.

## What Does Not Belong Here

- Proprietary Loopchii runtime architecture
- Internal enforcement logic, private infrastructure, or undisclosed commercial systems
- Inflated marketing claims that the repo cannot prove
- AI-generated filler text that makes the project sound larger or stranger than the code supports
- Pull requests that blur the boundary between this public repo and private LOOPCHii systems

## Fast Setup

```bash
git clone https://github.com/loopchii/Stream.git
cd Stream

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Run the app locally:

```bash
python app.py
```

Run the environment doctor before you start changing behavior:

```bash
python -m stream_backend.cli.doctor
```

Run validation:

```bash
python3 -m py_compile app.py build_static.py music_ingest.py music_pipeline.py streamlens_processor.py advanced_metrics.py bias_library.py
pytest -q
flake8 streamlens_processor.py app.py music_decision_lab.py tests --max-line-length=120 --extend-ignore=E501,W503
```

## Suggested Branch Lanes

Keep public work narrow enough to review and easy enough to reproduce.

- `ui/...` for browser interaction, accessibility, motion, and layout work
- `backend/...` for Python surfaces, API endpoints, orchestration, and SQLite/runtime changes
- `data/...` for committed public datasets, quality notes, and source-boundary improvements
- `docs/...` for README, contribution guidance, methods notes, and public-language tightening

The branch prefix is not a rule. It is a quick signal that the work has a lane and a reason to exist.

## How To Propose Work

### Bugs

Use the bug issue template and include:

- what you ran
- what you expected
- what happened instead
- screenshots or terminal output if the problem is visual or runtime-specific

### Features

Use the feature request template when the change improves:

- readability
- trust
- onboarding
- reproducibility
- research usefulness
- front-end clarity

Frame requests in terms of what a reader, contributor, or user can do better afterward.

### Data and source improvements

If you want to contribute datasets, source notes, or real-world references:

- say where the data comes from
- confirm licensing or reuse permissions
- explain what the data improves
- explain whether it changes a claim, a visual, a metric, or only a learning surface

If the source boundary is unclear, pause and document it before asking to merge the data.

## Pull Request Expectations

Keep pull requests narrow and intentional.

Good PRs usually do one of these well:

- fix a bug
- improve a public explanation
- strengthen reproducibility
- refine the dashboard interaction model
- tighten a measured claim so it matches the code more exactly

Please include:

- a short summary
- the reasoning for the change
- validation notes
- screenshots for visible UI changes

## Public Tone

This repo should feel:

- precise
- readable
- grounded
- useful

It should not feel:

- inflated
- mystical
- vague
- like a marketing shell pretending to be research

If you are changing text, prefer clarity and disciplined confidence over hype.

## Review Standard

We are more interested in whether the repository becomes more trustworthy than whether it becomes louder.

The best contributions help the next person:

- understand the project faster
- verify a claim more easily
- run the code with less friction
- learn something real without being misled

That matters as much as code quality here. A public analysis repo becomes more valuable when its boundaries are easier to inspect, not when its prose becomes louder.
