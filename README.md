# Stream

<p align="center">
  <strong>Loopchii Stream</strong> is a public research repository for media bias, music virality, cultural attention, and inspectable analysis.
</p>

<p align="center">
  It is meant to be readable, checkable, and useful without pretending public research and private runtime systems are the same thing.
</p>

<p align="center">
  <a href="https://htmlpreview.github.io/?https://github.com/loopchii/Stream/blob/main/index.html">Launch the dashboard preview</a>
  ·
  <a href="https://htmlpreview.github.io/?https://github.com/loopchii/Stream/blob/main/StreamLen_processors.html">Open the methods notebook</a>
  ·
  <a href="https://github.com/loopchii/Stream/actions/workflows/ci.yml">View CI</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Loopchii-Public%20Research%20Surface-5B55FF?style=for-the-badge" alt="Loopchii public research surface">
  <img src="https://img.shields.io/badge/Media%20Analysis-Representation%20%26%20Attention-FF6F9F?style=for-the-badge" alt="Media analysis">
  <img src="https://img.shields.io/badge/Inspectable-Dashboard%20%26%20Methods-48C9C2?style=for-the-badge" alt="Inspectable dashboard and methods">
  <img src="https://img.shields.io/github/actions/workflow/status/loopchii/Stream/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI status">
  <img src="https://img.shields.io/github/license/loopchii/Stream?style=for-the-badge" alt="License">
</p>

> **Why this exists:** public work should not ask for trust before it shows its inputs, boundaries, and tradeoffs. Stream exists to make the work visible enough to inspect, challenge, and improve.

Stream is where Loopchii publishes a bounded public surface: reproducible methods, readable visual reasoning, and a contribution path that does not depend on private infrastructure. Some lanes are synthetic and clearly labeled because they are here to teach the method. Some lanes are built from public music data because they are here to test what the method can actually hold when the inputs are real. The repo separates those two jobs on purpose.

## Start Here

Pick the route that matches how you like to learn:

| If you want to... | Go here | What you get |
|---|---|---|
| See the browser surface first | [Dashboard Preview](https://htmlpreview.github.io/?https://github.com/loopchii/Stream/blob/main/index.html) | The public UI with charts, story flow, the real-data music lane, and the clickable audit layer |
| Read the processing choices first | [`StreamLen_processors.html`](https://htmlpreview.github.io/?https://github.com/loopchii/Stream/blob/main/StreamLen_processors.html) | A notebook-style walkthrough of how the data is cleaned, shaped, and measured |
| Try the smallest working tool | `python lens_visualizer.py` | A terminal-first demo with public lens findings and instant visual feedback |
| Review the setup and contribution lanes | [contributing.md](contributing.md) | Local setup, accepted scopes, and how to add public value without overclaiming |
| Start with the public scope | [What This Actually Does](#what-this-actually-does) | The quickest way to understand what this repo is for, what it is not, and how the data is bounded |

## Navigation

- [What This Actually Does](#what-this-actually-does)
- [Browser Playground](#browser-playground)
- [Public Lens SDK](#public-lens-sdk)
- [Media Liability Lab](#media-liability-lab)
- [Why Engineers Trust This Repo](#why-engineers-trust-this-repo)
- [Music Virality Module — Real YouTube Data](#music-virality-module--real-youtube-data)
- [Quick Start](#quick-start)
- [What the Pipeline Surfaces](#what-the-pipeline-surfaces)
- [The Interactive Dashboard](#the-interactive-dashboard)
- [Project Structure](#project-structure)
- [Data and Methods](#data-and-methods)
- [Contributing](#contributing)
- [License and Citation](#license-and-citation)

## Why Engineers Trust This Repo

- The claim boundary is explicit. Synthetic representation data is labeled throughout, and the real-data music lane is kept separate on purpose.
- The artifacts are inspectable. The dashboard, methods notebook, static exports, and API surfaces all trace back to code in this repository.
- The same pipeline feeds local runs, static JSON exports, and API responses. There is less room for the public story to drift away from what the code actually does.
- CI runs tests on push so contributors can change the repo without turning it into a slideshow of unverifiable screenshots.

## Data Engineering Surface

Stream now exposes its public analytical operating model directly instead of hiding it behind screenshots and prose. The Learn tab and `/api/system/data-engineering` surface show the same things a data engineer or analytics lead would ask for before trusting a public number:

- dataset grain and primary keys
- partition strategy and refresh posture
- quality checks on nulls, uniqueness, domain control, and leakage
- bronze → silver → gold → serving lineage
- delivery parity across FastAPI, static JSON exports, and the browser surface

This is deliberate. A chart should not be the first place someone learns how a system behaves. The pipeline, the contract boundary, and the publishing discipline should be visible before anyone is asked to trust the result.

## Backend Runtime Spine

The repo is no longer just a front-end shell with a Python API bolted on. The public surface now runs through a package-based backend spine in `stream_backend/` that does four jobs:

- computes role-aware analytical state for the browser instead of leaving those numbers trapped in `index.html`
- materializes a repeatable public runtime snapshot into `data/system/*.json`
- persists run metadata and artifacts into a local SQLite database for replay and inspection
- keeps the live API, static build, and exported research artifacts aligned from the same code path

The result is intentionally polyglot but still bounded: Python drives the analysis and orchestration, JavaScript renders the public browser surface, and the repo's existing Rust/WASM lane remains available for lighter-weight public demos. The public value is in the connective tissue between those layers, not in any one language by itself.

## Choose Your Path

| Reader | Best first stop | Why |
|---|---|---|
| Engineer | [Quick Start](#quick-start) | Run it locally, inspect the API, and trace outputs back to code |
| Researcher | [Data and Methods](#data-and-methods) | Review assumptions, metrics, and the synthetic-vs-real boundary before citing anything |
| Designer or writer | [The Interactive Dashboard](#the-interactive-dashboard) | See how the visual flow, narrative pacing, and explanation strategy are structured |
| Contributor | [contributing.md](contributing.md) | Find the accepted lanes for code, data, docs, and public research support |

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## What This Actually Does

Stream models representation across streaming media from 2015 to 2026. Instead of stopping at demographic counts, it computes measurable signals: dialogue distribution, character-network clustering, role typecasting, screen-time and sentiment gaps, intersectional representation ratios, platform-by-media differences, and temporal drift.

**Honesty note:** the base entertainment dataset is synthetic — generated with a fixed random seed (`np.random.seed(42)`) and shaped to mirror patterns reported in media-representation research. It is good for learning, testing, and explaining the methods. It is not a claim about real catalogues or real studios.

The interactive dashboard lets you inspect those patterns across seven tabs — Dashboard, Explore Data, Insights, Bias Library, Learn, Verdict, and **Music Virality** — with filtering by platform, genre, media type, and year. The music tab now adds role lenses for artists, consumers, business teams, and researchers so the same evidence can be framed for different readers without changing the underlying numbers.

## What This Repo Is Not

- It is not a hidden proprietary Loopchii runtime.
- It is not a claim about private studio catalogues, internal platform data, or undisclosed production systems.
- It is not a generic “AI for media” wrapper. The value here is in clear methods, bounded interpretation, and visible public artifacts.

## Browser Playground

The fastest path into Stream is now the public split-screen playground in [`index.html`](https://htmlpreview.github.io/?https://github.com/loopchii/Stream/blob/main/index.html). It exists for one reason: most public research repos make people read for ten minutes before they can feel any value. This one should not.

What it gives you immediately:

- a browser-side comparison between a typical wrapper that reacts after risky material renders and a governed path that stops the fragment before it lands
- a tiny public wrapper surface in [`packages/loopchii-lite`](packages/loopchii-lite) for contributors who want something they can inspect and adapt in minutes
- a deterministic set of nuisance cases that map to ordinary engineering headaches: direct identifiers, leaked secrets, protected text, and unsafe retention prompts

The playground is intentionally public and bounded. It does **not** claim private runtime enforcement, hardware binding, or proprietary Loopchii internals. Its job is adoption: prove usefulness quickly, invite contribution honestly, and give engineers something concrete to extend.

Minimal public example:

```js
import { govern } from "@loopchii/loopchii-lite";

const result = govern({
  prompt: "Draft a reply using the customer email export and phone numbers.",
  draftResponse: "Here are the contacts: jordan@example.com ..."
});

return result.allowed ? result.standardResponse : result.safeResponse;
```

## Public Lens SDK

`Stream` now exposes a small public extension surface for contributors who want something more active than a static dashboard:

- `lens_sdk.py` provides a minimal `KineticLens` protocol plus grouped `StreamRecord` inputs and typed `GeometricMask` findings.
- `lens_visualizer.py` gives a terminal-first demo path so contributors can run a live grouped stream and watch findings surface immediately.
- `/api/lenses/catalog` publishes the active public lenses.
- `/api/lenses/demo-stream` evaluates the cached grouped stream through the same public registry.

This is intentionally scoped. It gives contributors a truthful place to add assessors, heuristics, and public reasoning layers without opening private Loopchii architecture.

## Media Liability Lab

The repo now includes a public research harness for media-platform risk questions:

- **Compulsive loop analysis** via `media_liability_lab.py`, which scores how repetitive and sticky a recommendation stream looks.
- **Generative guard simulation**, which screens an output buffer against public signatures and zeroizes it when a match is detected.
- **Causal map export**, which turns a recommendation sequence into nodes, edges, and repeat-path risk markers.

The public API exposes this through:

- `/api/media-lab/overview`
- `/api/media-lab/compulsive-loop`
- `/api/media-lab/generative-guard`
- `/api/media-lab/causal-map`

This is a public research harness, not a claim that the repo contains private production enforcement. Its value is that contributors can test the logic, extend the heuristics, and inspect the outputs directly.

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

## Music Virality Module — Real YouTube Data

The newest module goes beyond synthetic data entirely. It analyses the **100 most-watched YouTube music videos of 2025** — 10.59 billion real views from 65 channels — using the actual `youtube-top-100-songs-2025.csv` dataset.

| Analysis | What It Computes | Where to See It |
|---|---|---|
| **Power-law fit** | MLE exponent α with bootstrap 95% CI + KS distance (Clauset method) | Movement 01 — log-log CCDF scatter |
| **Inequality** | Gini coefficient, Lorenz curve, Theil entropy, top-k channel concentration | Movement 02 — Lorenz curve + channel bar |
| **Correlation architecture** | Spearman ρ + partial correlations controlling for channel size, with bootstrap CIs | Movement 03 — heatmap + ranked bar chart (toggle raw/partial) |
| **Viral archetypes** | K-means (k=5) on log-views, virality, channel size, duration → named strategies | Movement 04 — scatter coloured by cluster |
| **Tag co-occurrence network** | NetworkX graph of shared tags, greedy-modularity communities, density | Movement 05 — D3 force-directed graph |
| **Predictability** | RandomForest + GradientBoosting ensemble, 5-fold cross-validated R² | Movement 06 — skill-vs-luck gauge + importances |
| **What-If virality predictor** | Trained model maps hypothetical (duration, subscribers, tags, official) → percentile | Movement 07 — slider controls + grade gauge |
| **Resonance mapper** | Public proxy for repetition, release pressure, and attention oscillation across the real music catalog | Movement 08 — 3D resonance core + clickable track list |
| **Bias analysis** | Gender parity, genre concentration (Gini), collaboration patterns, duration bias, attention concentration, per-genre breakdowns, and a publication timeline drawn from public upload dates | Movement 09 — equity grade + 7 charts + genre table |
| **3D virality landscape** | Plotly 3D scatter of views × virality × subscribers, coloured by archetype cluster | Movement 10 — interactive 3D orbit |
| **Real songs explorer** | Sortable, searchable table of all 100 tracks with computed features | Movement 11 — sortable table |

**Live data extraction (optional):** If you set a `YOUTUBE_API_KEY` environment variable, the built-in `music_ingest.py` module calls the YouTube Data API v3 to refresh view counts and pull additional tracks on demand — no code changes needed. Without a key, the app serves the committed real dataset.

Data sources: YouTube Top 100 (2025), Most Viewed Music Videos (2026, Kaggle), YouTube Music Data (Kaggle), YouTube Top Channels (2026, Kaggle). **636 real songs** from 3 datasets. No synthetic data is used in this module.

### Score-Aware Music Intelligence

The repo now includes a separate harvest layer for score and notation work:

- `music_intelligence.py` scans the repository for MusicXML, MIDI, ABC, LilyPond, tabs, and chord charts.
- `music_index.json` and `music_index.csv` export the piece-level index.
- `music_analysis_report.md` summarizes what is actually linked today.

This layer keeps the claim boundary strict:

- the public song catalog and the score layer are separate on purpose
- note and chord claims appear only when the repository contains notation-bearing files
- when the repo has no linked score material, the surface shows the gap instead of faking musical certainty

That means contributors can deepen the music lane in a very concrete way: add notation files under `scores/`, `music/`, `notation/`, or similar public folders and rerun the build. The UI will fold those files back into the song index automatically and start surfacing note families, chord movement, key distribution, and the score-link coverage rate.

## The Mathematical Framework

<table>
<tr style="background-color:#FFE4E1;">
<td><strong>Component</strong></td>
<td><strong>What It Means</strong></td>
<td><strong>Why I Chose It</strong></td>
</tr>
<tr>
<td><strong>Dialogue Bias</strong></td>
<td>Chi-square test on word counts by group</td>
<td>Tests whether dialogue is distributed evenly across demographics, with a p-value</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Diversity Index</strong></td>
<td>Shannon entropy across demographics</td>
<td>Information theory perfectly captures "variety" in mathematical terms</td>
</tr>
<tr>
<td><strong>Gender Parity</strong></td>
<td>1 - |0.5 - female_ratio| × 2</td>
<td>Simple but effective: 1.0 means perfect parity, 0 means complete imbalance</td>
</tr>
<tr style="background-color:#FFF0F5;">
<td><strong>Intersectionality Score</strong></td>
<td>Group share vs a uniform 1/45 baseline (3 genders × 5 races × 3 age bands)</td>
<td>Captures compound effects when multiple identities intersect</td>
</tr>
<tr>
<td><strong>Network Homophily</strong></td>
<td>NetworkX attribute assortativity coefficient</td>
<td>Reveals whether characters interact mostly with similar demographics</td>
</tr>
</table>

<div align="center">
  
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>

## Analysis Pipeline (What Actually Runs)

<details>
<summary><strong>The methods implemented in <code>streamlens_processor.py</code>:</strong></summary>

<table>
<tr style="background-color:#E6E6FA;">
<td><strong>Method</strong></td>
<td><strong>Where</strong></td>
<td><strong>What It Computes</strong></td>
</tr>
<tr>
<td><strong>Shannon Entropy</strong></td>
<td><code>calculate_diversity_index</code></td>
<td>Normalized diversity index over demographic distributions</td>
</tr>
<tr style="background-color:#FFE4E1;">
<td><strong>Chi-Square Test</strong></td>
<td><code>detect_dialogue_bias</code></td>
<td>Whether dialogue word counts deviate from an even split (gender and race)</td>
</tr>
<tr>
<td><strong>Intersectionality Ratios</strong></td>
<td><code>calculate_intersectionality_score</code></td>
<td>Each gender×race×age group's share vs a uniform baseline</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Network Analysis</strong></td>
<td><code>build_character_network</code>, <code>detect_homophily</code></td>
<td>Character interaction graph, centrality, assortativity by demographic</td>
</tr>
<tr>
<td><strong>Role Stereotyping</strong></td>
<td><code>detect_role_stereotyping</code></td>
<td>Over/under-representation of demographics in lead vs supporting roles</td>
</tr>
<tr style="background-color:#FAFAD2;">
<td><strong>Bias Dimensions</strong></td>
<td><code>process_data</code></td>
<td>Age, sentiment, and screen-time bias as group deviations from overall means</td>
</tr>
</table>

No machine-learning models are trained in this pipeline — every number is a transparent statistical computation you can step through in the source.

</details>

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## Quick Start

```bash
# Clone the repository
git clone https://github.com/loopchii/Stream.git
cd Stream

# Set up environment (I use venv, but conda works too)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch the API server + dashboard
python app.py
# Then open http://localhost:8000 in your browser

# Or get the terminal-first lens demo
python lens_visualizer.py

# Or run the analysis pipeline standalone
python streamlens_processor.py

# Or materialize the public runtime and static exports
python build_static.py

# Or just open index.html directly in your browser for the static dashboard
```

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Interactive dashboard |
| `/api/health` | GET | Health check |
| `/api/results` | GET | Full cached analysis results |
| `/api/analyze?n_samples=N` | POST | Re-run the analysis pipeline |
| `/api/metrics/overview` | GET | Diversity index + gender parity |
| `/api/metrics/temporal` | GET | Year-over-year metrics |
| `/api/metrics/platforms` | GET | Per-platform comparison |
| `/api/metrics/bias` | GET | Bias detection: dialogue, age, racial dialogue, sentiment, screen time |
| `/api/metrics/genres` | GET | Per-genre diversity, parity, lead share, dialogue gap |
| `/api/metrics/media` | GET | Per-media-type (series, film, docuseries, animation…) metrics |
| `/api/metrics/platform-media` | GET | Per-platform media-type breakdown (format-specific analysis) |
| `/api/metrics/network` | GET | Interaction network homophily and density |
| `/api/metrics/intersectionality` | GET | Most under/over-represented intersectional groups |
| `/api/insights` | GET | Narrative findings generated from the data |
| `/api/lenses/catalog` | GET | Public catalog of the active lens registry |
| `/api/lenses/demo-stream` | GET | Grouped stream records evaluated by the public lens SDK |
| `/api/media-lab/overview` | GET | Combined public snapshot of recommendation, guard, and causal-map research outputs |
| `/api/media-lab/compulsive-loop` | GET | Compulsive-loop risk score and recommended friction for a sample recommendation stream |
| `/api/media-lab/generative-guard` | GET | Public generative buffer screening and zeroization demo |
| `/api/media-lab/causal-map` | GET | Topological recommendation-flow export with repeat-path risk edges |
| `/api/system/catalog` | GET | Public catalog of runtime surfaces, generated assets, and active analytical lanes |
| `/api/system/runtime` | GET | Fresh materialized runtime snapshot spanning synthetic, music, and orchestration surfaces |
| `/api/system/runtime/latest` | GET | Latest persisted runtime snapshot from the local SQLite-backed run history |
| `/api/system/frontend-state` | GET | Browser-ready payload generated by the backend instead of hand-authored view math |
| `/api/system/comparatives` | GET | Comparative framing surface for role-aware reading across the same evidence |
| `/api/system/materialize` | POST | Force a runtime materialization pass and write updated public artifacts |
| `/api/metrics/advanced` | GET | Inequality (Gini/Theil/Lorenz), Simpson/Theil diversity, Cramér's V effect sizes, bootstrap CIs, fitted year trend |
| `/api/metrics/scorecard` | GET | Per-platform A–F report card across four representation dimensions |
| `/api/simulate/parity?female_ratio=R` | GET | What-If parity index, letter grade, and verdict for a hypothetical female lead share |
| `/api/learn` | GET | Educational explanations of every metric |
| `/api/bias-library` | GET | 50+ documented bias types, filterable by `?category=` |
| `/api/export` | GET | Download full results as JSON |
| `/api/characters` | GET | Filterable character records (`platform`, `genre`, `year`, `limit`) |
| `/api/music/overview` | GET | Headline stats: songs, channels, total views |
| `/api/music/powerlaw` | GET | Power-law fit: α, KS distance, bootstrap CI, CCDF |
| `/api/music/inequality` | GET | Gini, Lorenz, Theil, top-k channel concentration |
| `/api/music/correlations` | GET | Spearman + partial correlations with bootstrap CIs |
| `/api/music/archetypes` | GET | K-means viral archetype clusters + scatter |
| `/api/music/network` | GET | Tag co-occurrence graph (nodes, edges, communities) |
| `/api/music/predictability` | GET | Cross-validated ensemble R² and feature importances |
| `/api/music/songs` | GET | Real songs table (sortable, `?limit=` `?sort_by=`) |
| `/api/music/simulate` | GET | What-If virality predictor (`?duration_min=` `?channel_follower_count=` `?tag_count=`) |
| `/api/music/bias` | GET | Gender, genre, collaboration, duration, and concentration bias metrics |
| `/api/music/genres` | GET | Per-genre breakdown with view share, duration, collaboration mix, and top track |
| `/api/music/timeline` | GET | Publication timeline built from public upload dates and views |
| `/api/music/status` | GET | Whether a YouTube API key is configured for live data |
| `/api/music/refresh` | POST | Pull fresh data from YouTube Data API v3 (needs key) |

Interactive API docs are available at `http://localhost:8000/docs`.

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

## What the Pipeline Surfaces

Findings are generated live from the current dataset by `/api/insights` — they are computed, not pre-written. On the default seeded dataset the pipeline surfaces patterns like:

<table>
<tr style="background-color:#FFE4E1;">
<td><strong>Signal</strong></td>
<td><strong>How It's Measured</strong></td>
<td><strong>Where to See It</strong></td>
</tr>
<tr>
<td><strong>Gender lead gap</strong></td>
<td>Lead-role share by gender, per genre and platform</td>
<td>Dashboard bubble chart, Insights tab</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Dialogue gap</strong></td>
<td>Chi-square on dialogue word counts by gender and race</td>
<td>Insights → Bias Breakdown</td>
</tr>
<tr>
<td><strong>Age representation</strong></td>
<td>Share of 50+ characters and their dialogue deviation</td>
<td>Insights tab, time series</td>
</tr>
<tr style="background-color:#FFF0F5;">
<td><strong>Intersectional gaps</strong></td>
<td>Gender×race×age group shares vs uniform baseline</td>
<td>Insights → Intersectionality table</td>
</tr>
<tr>
<td><strong>Network homophily</strong></td>
<td>Assortativity of the character interaction graph</td>
<td>Dashboard network graph</td>
</tr>
<tr style="background-color:#FAFAD2;">
<td><strong>Temporal trends</strong></td>
<td>Year-over-year diversity and parity, 2015–2026</td>
<td>Year slider with era readouts, time series</td>
</tr>
</table>

Because the data is synthetic, treat the exact values as demonstrations of the method — not real-world measurements.

<div align="center">
  
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>

## The Interactive Dashboard

<details>
<summary><strong>Five screens with a story arc (Act I–V), plus the core visualizations:</strong></summary>

### The Screens
- **Dashboard (Act I)** — live stat cards, year slider with era readouts, bubble chart, 3D representation landscape, network graph, time series, radar chart
- **Explore Data (Act II)** — the raw character-level records behind every metric, filterable by platform, genre, media type, and year; media-mix donut
- **Insights (Act III)** — findings generated by the pipeline, plus the bias breakdown and intersectionality tables
- **Bias Library (Act IV)** — 57 documented bias types across 8 categories, searchable, with the ones Stream quantifies marked
- **Learn (Act V)** — plain-language explanations of every metric, with pointers into the source code
- **Verdict (Act VI)** — a platform A–F report card, a Lorenz/Gini inequality curve, Cramér's V effect-size bars, a fitted decade trend line, and a What-If parity simulator wired to the backend
- **Music Virality (Real Data)** — eight-movement deep dive into 100 real YouTube music videos: power-law, inequality, correlations, archetypes, tag network, predictability, What-If predictor, and a sortable real-songs explorer

### Bubble Chart: The Big Picture
Each bubble is a platform-genre combination with its own color. I spent way too long on the color system, but now you can instantly see patterns:
- Netflix (red family): Comedy is light red, Action is dark red
- HBO Max (purple family): Same gradient system
- Position shows female lead percentage (x-axis) and diversity index (y-axis)
- Size indicates overall equality score

### Network Graph: Who Talks to Whom
This one surprised me. Characters cluster by demographics even within the same show. Drag the nodes around and watch how they're connected. The clustering is so strong it's actually depressing.

### Time Series: Are Things Getting Better?
Four metrics tracked across 2015–2026. In the synthetic dataset, gender parity and diversity improve gradually year over year — mirroring the slow-progress pattern reported in representation research.

### Radar Chart: Character Archetypes
Shows which demographics get which roles. Men dominate protagonists and antagonists, women are overrepresented as romantic interests, non-binary characters barely register. The pattern is consistent across all platforms.

</details>

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## How to Use This for Your Own Analysis

```python
from streamlens_processor import DataProcessor

processor = DataProcessor()

# Generate the seeded synthetic dataset (or substitute your own DataFrame
# with the same columns: platform, genre, media_type, year, gender, race,
# age_group, role_type, screen_time, dialogue_words, sentiment_score)
df = processor.generate_synthetic_data(n_samples=5000)

# Run the full analysis pipeline
results = processor.process_data(df)
print(results['overall_metrics'])          # diversity_index, gender_parity, …
print(results['bias_detection'].keys())    # dialogue, age, sentiment, screen time …

# Human-readable findings
for insight in processor.generate_insights(df, results):
    print(insight['title'], '—', insight['detail'])

# Export everything as JSON (also what the API serves)
processor.export_results(results, filename='analysis_results.json')
```

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

## Project Structure

```
Stream/
│
├── index.html                    # The interactive dashboard (start here)
├── app.py                        # FastAPI server (dashboard + REST API)
├── build_static.py               # Static export builder for GitHub Pages / no-server preview
├── lens_sdk.py                   # Public extension protocol for grouped stream assessors
├── lens_visualizer.py            # Terminal-first demo of the public lens registry
├── media_liability_lab.py        # Public media-platform risk research harness
├── streamlens_processor.py       # Main processing pipeline
├── bias_library.py               # 57 documented bias types served at /api/bias-library
├── music_pipeline.py             # Real-data music virality analysis (power-law, Gini, clustering, RF, role lenses)
├── music_ingest.py               # YouTube Data API v3 live extraction (key-optional)
├── stream_backend/               # Package-based runtime spine: analytics, orchestration, export, SQLite store
│   ├── analytics/                # Role lenses, comparative framing, quality surfaces, narrative outputs
│   ├── orchestration/            # Runtime jobs, epochs, asset mapping, materialization flow
│   ├── services/                 # High-level runtime and frontend-state services
│   ├── store/                    # SQLite schema, run history, artifact persistence
│   ├── exporters/                # JSON, markdown, and SQLite export helpers
│   └── cli/                      # Rebuild, validate, and materialize entrypoints
├── data_sources/                 # Real CSV data (youtube-top-100-songs-2025.csv)
├── data/system/                  # Generated public runtime artifacts for the static browser surface
├── StreamLen_processors.ipynb    # Jupyter notebook with full analysis
├── streaming-bias-index.html     # Legacy static dashboard
├── analysis_results.json         # Latest exported analysis results
├── requirements.txt              # Core Python dependencies
├── requirements-full.txt         # Extended research stack
│
├── tests/
│   ├── test_analyzer.py          # Unit tests for the pipeline
│   ├── test_api.py               # API tests
│   ├── test_lens_sdk.py          # Public lens SDK tests
│   ├── test_media_liability_lab.py  # Media-platform research harness tests
│   └── test_music.py             # Music pipeline + API tests
│
└── .github/workflows/ci.yml     # CI: lint + tests on Python 3.11/3.12
```

<div align="center">
  
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>

## Data and Methods

<table>
<tr style="background-color:#E6E6FA;">
<td><strong>Aspect</strong></td>
<td><strong>What It Is</strong></td>
<td><strong>Why</strong></td>
</tr>
<tr>
<td><strong>Dataset</strong></td>
<td>Synthetic, generated in <code>generate_synthetic_data()</code> with <code>np.random.seed(42)</code></td>
<td>Fully reproducible; every chart can be traced to the generating code</td>
</tr>
<tr style="background-color:#FFE4E1;">
<td><strong>Scope</strong></td>
<td>5,000 characters by default · 6 platforms · 6 genres · 11 media types · 2015–2026</td>
<td>Re-runnable at 1,000–25,000 samples from the dashboard or <code>POST /api/analyze</code></td>
</tr>
<tr>
<td><strong>Shape</strong></td>
<td>Distributions mirror patterns reported in media-representation research, improving gradually by year</td>
<td>Demonstrates the methods on realistic structure without claiming real measurements</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Bias Library</strong></td>
<td>57 named bias types with conceptual definitions and examples; no invented statistics</td>
<td>Field knowledge stays truthful — definitions describe documented concepts only</td>
</tr>
</table>

### Statistical Rigor

The synthetic representation lane uses chi-square goodness-of-fit testing for dialogue distribution (with p-values), normalized Shannon entropy for diversity, attribute assortativity for network homophily, and deviation-from-mean comparisons for age, sentiment, and screen-time bias.

The real-data music lane goes further: it includes bootstrap confidence intervals for the power-law tail, partial Spearman checks for feature relationships, a cross-validated ensemble regressor for the what-if predictor, and a public audit surface that shows how rows were filtered, deduplicated, or held back before any chart claims to be meaningful.

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## Why This Matters

Media shapes culture. When most action heroes are male, when women of color rarely hold lead roles, when characters over 50 fade from screens, it sends a message about whose stories matter. This isn't about quotas or political correctness. It's about accurately reflecting the world we live in.

Stream exists to make those patterns measurable and readable at the same time. The Bias Library names documented patterns so you can spot them; the Learn tab explains the math so you can verify it; the Explore tab hands you the raw rows so you never have to trust a summary by default.

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

## Contributing

I'd love help making this better. Areas where I particularly need assistance:

- **Data Collection**: More international content, more platforms
- **Statistical Methods**: Always room for improvement in bias detection
- **Visualization**: Making complex patterns more intuitive
- **Documentation**: Explaining the math in simpler terms

Check out [contributing.md](contributing.md) for guidelines. The repo also ships issue templates for bugs, feature requests, and data/source improvements so contributors can plug in without guessing the expected shape.

<div align="center">
  
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>

## Technical Performance

<table>
<tr style="background-color:#FFE4E1;">
<td><strong>Metric</strong></td>
<td><strong>Performance</strong></td>
<td><strong>Notes</strong></td>
</tr>
<tr>
<td><strong>Processing Speed</strong></td>
<td>A few seconds for the default 5,000-sample run</td>
<td>Vectorized pandas operations</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Test Coverage</strong></td>
<td>111 pytest tests (pipeline + API + music + public lens SDK + media liability lab)</td>
<td>Run with <code>pytest tests -q</code>; CI on Python 3.11/3.12</td>
</tr>
<tr>
<td><strong>Data Coverage</strong></td>
<td>5,000 synthetic characters by default (1,000–25,000 configurable)</td>
<td>6 platforms × 6 genres × 11 media types</td>
</tr>
<tr style="background-color:#FFF0F5;">
<td><strong>Temporal Range</strong></td>
<td>12 years (2015–2026)</td>
<td>Captures the streaming era through the present</td>
</tr>
<tr>
<td><strong>Visualization Stack</strong></td>
<td>D3.js, Plotly WebGL/3D, Chart.js, Apache ECharts, Three.js</td>
<td>Single-file dashboard, no build step</td>
</tr>
</table>

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## License and Citation

MIT License - use this code for anything you want. If you find something interesting or build on this work, I'd love to hear about it.

If you use Stream in research:

```bibtex
@software{streamlens2025,
  title = {Stream: Loopchii Public Research Surface for Media Bias and Attention Analysis},
  author = {Aporbo, Cazandra},
  year = {2025},
  url = {https://github.com/loopchii/Stream}
}
```

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

## Contact

**Author**: Cazandra Aporbo, MS  
**Repository**: [github.com/loopchii/Stream](https://github.com/loopchii/Stream)  
**Issues**: [Report bugs or request features](https://github.com/loopchii/Stream/issues)

Currently working on expanding this to include international content and historical analysis pre-2015. If you have access to good datasets or want to collaborate, reach out through GitHub issues.

<div align="center">

<br>

Building transparency in media representation through rigorous mathematical analysis.

<br>

![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>
