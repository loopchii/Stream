# StreamLens Analytics

<div align="center">

[![Mathematical Framework](https://img.shields.io/badge/Mathematical%20Framework-Advanced%20Bias%20Detection-FFE4E1?style=for-the-badge)](https://github.com/Cazzy-Aporbo/StreamLens-Analytics)
[![Data Analysis](https://img.shields.io/badge/Data%20Analysis-2015--2026%20Media-E6E6FA?style=for-the-badge)](https://github.com/Cazzy-Aporbo/StreamLens-Analytics)
[![Interactive Dashboard](https://img.shields.io/badge/Interactive%20Dashboard-Real--time%20Visualizations-F0F8FF?style=for-the-badge)](https://github.com/Cazzy-Aporbo/StreamLens-Analytics)

</div>

<div align="center">

### [▶ Launch the Live Dashboard](https://cazzy-aporbo.github.io/StreamLens-Analytics/)

[![Open Live App](https://img.shields.io/badge/Live%20Demo-Open%20StreamLens%20in%20your%20browser-FFB6C1?style=for-the-badge)](https://cazzy-aporbo.github.io/StreamLens-Analytics/)

<sub>The full dashboard — all six screens, charts, the Verdict scorecard, and the What‑If simulator — runs entirely in your browser. No install, no server. Every number is pre‑computed by the same Python pipeline in this repo (run `python build_static.py` to regenerate), so the live figures match the API exactly.</sub>

</div>

<div align="center">
  
<div align="center">
  
 [StreamLens‑Analytics/streaming‑bias‑index.html](https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/StreamLens-Analytics/blob/main/streaming-bias-index.html)  
<sub>A comprehensive exploration of the Streaming Bias Index within the StreamLens Analytics framework</sub>
</div>


<div align="center">
  
 [StreamLen_processors.html](https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/StreamLens-Analytics/blob/main/StreamLen_processors.html)  
<sub>A deep‑dive into the data‑processing pipeline of the StreamLens Analytics project</sub>
</div>

<div align="center">



![separator](https://img.shields.io/badge/-FFE4E1?style=flat-square&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat-square&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat-square&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat-square&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat-square&color=FAFAD2)

</div>

> **My Philosophy for This Project:** Media representation should be measurable, patterns should be visible, and bias should be quantifiable. If we can't measure it, we can't fix it.

I designed StreamLens Analytics because I noticed something troubling: everyone talks about representation in media, but few actually quantify it. This framework uses information theory, statistical testing, and network analysis to surface bias patterns that simple demographic counts miss. It currently runs on a clearly-labeled synthetic dataset (seeded and reproducible) so every metric, chart, and insight can be traced back to code you can read. This project began September 2024, and is a work in progress. 

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## What This Actually Does

StreamLens models representation across streaming media from 2015 to 2026. Instead of just counting demographics (which everyone does), it computes a framework of measurable signals: dialogue distribution (chi-square), character network clustering (homophily/assortativity), role typecasting, screen-time and sentiment gaps, intersectional representation ratios, and temporal evolution of bias.

**Honesty note:** the dataset is synthetic — generated with a fixed random seed (`np.random.seed(42)`) and shaped to mirror patterns reported in media-representation research. It is ideal for learning and demonstrating the methods; it is not a measurement of real shows. Every screen in the app discloses this.

The interactive dashboard lets you explore these patterns yourself across six screens — Dashboard, Explore Data, Insights, a 57-entry Bias Library, Learn, and a Verdict scorecard — filtering by platform, genre, media type, and year.

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

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
git clone https://github.com/Cazzy-Aporbo/StreamLens-Analytics.git
cd StreamLens-Analytics

# Set up environment (I use venv, but conda works too)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch the API server + dashboard
python app.py
# Then open http://localhost:8000 in your browser

# Or run the analysis pipeline standalone
python streamlens_processor.py

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
| `/api/metrics/network` | GET | Interaction network homophily and density |
| `/api/metrics/intersectionality` | GET | Most under/over-represented intersectional groups |
| `/api/insights` | GET | Narrative findings generated from the data |
| `/api/metrics/advanced` | GET | Inequality (Gini/Theil/Lorenz), Simpson/Theil diversity, Cramér's V effect sizes, bootstrap CIs, fitted year trend |
| `/api/metrics/scorecard` | GET | Per-platform A–F report card across four representation dimensions |
| `/api/simulate/parity?female_ratio=R` | GET | What-If parity index, letter grade, and verdict for a hypothetical female lead share |
| `/api/learn` | GET | Educational explanations of every metric |
| `/api/bias-library` | GET | 50+ documented bias types, filterable by `?category=` |
| `/api/export` | GET | Download full results as JSON |
| `/api/characters` | GET | Filterable character records (`platform`, `genre`, `year`, `limit`) |

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
- **Bias Library (Act IV)** — 57 documented bias types across 8 categories, searchable, with the ones StreamLens quantifies marked
- **Learn (Act V)** — plain-language explanations of every metric, with pointers into the source code
- **Verdict (Act VI)** — a platform A–F report card, a Lorenz/Gini inequality curve, Cramér's V effect-size bars, a fitted decade trend line, and a What-If parity simulator wired to the backend

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
StreamLens-Analytics/
│
├── index.html                    # The interactive dashboard (start here)
├── app.py                        # FastAPI server (dashboard + REST API)
├── streamlens_processor.py       # Main processing pipeline
├── bias_library.py               # 57 documented bias types served at /api/bias-library
├── StreamLen_processors.ipynb    # Jupyter notebook with full analysis
├── streaming-bias-index.html     # Legacy static dashboard
├── analysis_results.json         # Latest exported analysis results
├── requirements.txt              # Core Python dependencies
├── requirements-full.txt         # Extended research stack
│
├── tests/
│   ├── test_analyzer.py          # Unit tests for the pipeline
│   └── test_api.py               # API tests
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

The pipeline uses a chi-square goodness-of-fit test for dialogue distribution (with p-values), normalized Shannon entropy for diversity, attribute assortativity for network homophily, and deviation-from-mean comparisons for age, sentiment, and screen-time bias. There are no trained models, bootstraps, or causal estimators in the current codebase — and the README won't pretend otherwise.

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## Why This Matters

Media shapes culture. When most action heroes are male, when women of color rarely hold lead roles, when characters over 50 fade from screens, it sends a message about whose stories matter. This isn't about quotas or political correctness. It's about accurately reflecting the world we live in.

StreamLens exists to make those patterns measurable — and to teach the measuring. The Bias Library names 57 documented patterns so you can spot them; the Learn tab explains the math so you can verify it; the Explore tab hands you the raw rows so you never have to take a summary on faith. Because the first step to fixing a problem is proving it exists.

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

Check out [contributing.md](contributing.md) for guidelines. Fair warning: I'm particular about code quality, but I promise helpful code reviews.

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
<td>35 pytest tests (pipeline + API)</td>
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
<td>D3.js, Plotly (incl. 3D), Chart.js</td>
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

If you use StreamLens Analytics in research:

```bibtex
@software{streamlens2025,
  title = {StreamLens Analytics: Mathematical Framework for Media Bias Detection},
  author = {Aporbo, Cazandra},
  year = {2025},
  url = {https://github.com/Cazzy-Aporbo/StreamLens-Analytics}
}
```

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

## Contact

**Author**: Cazandra Aporbo, MS  
**Repository**: [github.com/Cazzy-Aporbo/StreamLens-Analytics](https://github.com/Cazzy-Aporbo/StreamLens-Analytics)  
**Issues**: [Report bugs or request features](https://github.com/Cazzy-Aporbo/StreamLens-Analytics/issues)

Currently working on expanding this to include international content and historical analysis pre-2015. If you have access to good datasets or want to collaborate, reach out through GitHub issues.

<div align="center">

<br>

Building transparency in media representation through rigorous mathematical analysis.

<br>

![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>
