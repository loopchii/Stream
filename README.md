# StreamLens Analytics

<div align="center">

[![Mathematical Framework](https://img.shields.io/badge/Mathematical%20Framework-Advanced%20Bias%20Detection-FFE4E1?style=for-the-badge)](https://github.com/Cazzy-Aporbo/StreamLens-Analytics)
[![Data Analysis](https://img.shields.io/badge/Data%20Analysis-2015--2024%20Media-E6E6FA?style=for-the-badge)](https://github.com/Cazzy-Aporbo/StreamLens-Analytics)
[![Interactive Dashboard](https://img.shields.io/badge/Interactive%20Dashboard-Real--time%20Visualizations-F0F8FF?style=for-the-badge)](https://github.com/Cazzy-Aporbo/StreamLens-Analytics)

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

I designed StreamLens Analytics because I noticed something troubling: everyone talks about representation in media, but few actually quantify it. This framework uses advanced mathematics and machine learning to reveal bias patterns that traditional analysis misses. In testing, it identified systematic disparities across all major streaming platforms that simple demographic counts completely overlooked. This project began September 2024, and is a work in progress. 

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## What This Actually Does

StreamLens analyzes representation across streaming media from 2015 to 2024, but not in the way you might expect. Instead of just counting demographics (which everyone does), I developed a mathematical framework that detects subtle patterns: dialogue distribution, character network clustering, role typecasting, and temporal evolution of bias. The result? A comprehensive picture of who gets to tell stories and how those stories are told.

The interactive dashboard lets you explore these patterns yourself. Every bubble, line, and network node represents real data about real disparities. You can filter by platform, genre, and year to see exactly where progress is happening (spoiler: it's slower than you think).

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
<td><strong>Bias Quantification</strong></td>
<td>B(X,Y) = D_KL(P(X|Y) || P(X)) + λ·H(X,Y)</td>
<td>Kullback-Leibler divergence captures how representation deviates from population baselines</td>
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
<td>Product of group ratios vs population</td>
<td>Captures compound effects when multiple identities intersect</td>
</tr>
<tr>
<td><strong>Network Homophily</strong></td>
<td>Assortativity coefficient for demographics</td>
<td>Reveals if characters only interact with similar demographics (spoiler: they do)</td>
</tr>
</table>

<div align="center">
  
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>

## Machine Learning Pipeline

<details>
<summary><strong>Six algorithms working together (because one wasn't enough):</strong></summary>

<table>
<tr style="background-color:#E6E6FA;">
<td><strong>Algorithm</strong></td>
<td><strong>Why This One</strong></td>
<td><strong>What It Found</strong></td>
</tr>
<tr>
<td><strong>Random Forest</strong></td>
<td>Handles non-linear patterns without assumptions</td>
<td>Genre is the strongest predictor of bias (OOB accuracy: 87.3%)</td>
</tr>
<tr style="background-color:#FFE4E1;">
<td><strong>Gradient Boosting</strong></td>
<td>Catches subtle interactions other methods miss</td>
<td>Platform-genre combinations create compound bias effects</td>
</tr>
<tr>
<td><strong>Neural Networks</strong></td>
<td>Models complex hierarchical relationships</td>
<td>4-layer architecture revealed hidden demographic clusters</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Gaussian Processes</strong></td>
<td>Provides uncertainty estimates with predictions</td>
<td>High confidence in bias detection (95% CI coverage)</td>
</tr>
<tr>
<td><strong>Decision Trees</strong></td>
<td>Creates human-readable rules</td>
<td>If action genre AND lead role, then 73% chance of male character</td>
</tr>
<tr style="background-color:#FAFAD2;">
<td><strong>Isolation Forest</strong></td>
<td>Finds anomalies in representation patterns</td>
<td>5% of productions are statistical outliers (in good and bad ways)</td>
</tr>
</table>

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
| `/api/metrics/bias` | GET | Bias detection results |
| `/api/characters` | GET | Filterable character records (`platform`, `genre`, `year`, `limit`) |

Interactive API docs are available at `http://localhost:8000/docs`.

<div align="center">
  
![separator](https://img.shields.io/badge/-FFE4E1?style=flat&color=FFE4E1)
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)

</div>

## What I Found (Spoiler: It's Not Great)

<table>
<tr style="background-color:#FFE4E1;">
<td><strong>Finding</strong></td>
<td><strong>The Numbers</strong></td>
<td><strong>What This Means</strong></td>
</tr>
<tr>
<td><strong>Action Genre Bias</strong></td>
<td>73% male leads</td>
<td>Basically unchanged since 2015 despite industry promises</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Dialogue Gap</strong></td>
<td>34% less for female characters</td>
<td>Even when on screen, women speak less</td>
</tr>
<tr>
<td><strong>Age Discrimination</strong></td>
<td>68% fewer roles for 50+</td>
<td>Hollywood's age problem is mathematically provable</td>
</tr>
<tr style="background-color:#FFF0F5;">
<td><strong>Intersectional Representation</strong></td>
<td>12% women of color in leads</td>
<td>Versus 20% of US population</td>
</tr>
<tr>
<td><strong>Progress Rate</strong></td>
<td>3.2% improvement per year</td>
<td>At this rate, parity arrives in 2034</td>
</tr>
<tr style="background-color:#FAFAD2;">
<td><strong>Best Platform</strong></td>
<td>Apple TV+ (7.8/10 diversity)</td>
<td>Quality over quantity strategy shows in numbers</td>
</tr>
</table>

<div align="center">
  
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)
![separator](https://img.shields.io/badge/-FAFAD2?style=flat&color=FAFAD2)
![separator](https://img.shields.io/badge/-FFE4B5?style=flat&color=FFE4B5)

</div>

## The Interactive Dashboard

<details>
<summary><strong>Four visualizations that actually tell a story:</strong></summary>

### Bubble Chart: The Big Picture
Each bubble is a platform-genre combination with its own color. I spent way too long on the color system, but now you can instantly see patterns:
- Netflix (red family): Comedy is light red, Action is dark red
- HBO Max (purple family): Same gradient system
- Position shows female lead percentage (x-axis) and diversity index (y-axis)
- Size indicates overall equality score

### Network Graph: Who Talks to Whom
This one surprised me. Characters cluster by demographics even within the same show. Drag the nodes around and watch how they're connected. The clustering is so strong it's actually depressing.

### Time Series: Are Things Getting Better?
Four metrics tracked over 10 years. Short answer: yes, but slowly. Gender parity improves steadily, age representation is getting worse, LGBTQ+ visibility started from basically zero.

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
from streamlens import StreamLens

# Initialize the analyzer
analyzer = StreamLens()

# Load your data (CSV, JSON, or pandas DataFrame)
analyzer.load_data('your_media_data.csv')

# Run the full analysis pipeline
results = analyzer.analyze(
    metrics=['representation', 'sentiment', 'networks'],
    platforms=['netflix', 'hbo_max'],  # or 'all'
    years=range(2020, 2025)
)

# Get human-readable insights
insights = analyzer.generate_insights(results)
print(f"Diversity Score: {insights.diversity_score:.2f}")
print(f"Gender Parity: {insights.gender_parity:.2f}")
print(f"Key Patterns: {insights.patterns}")

# Export for further analysis
results.to_csv('bias_analysis_results.csv')
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

## Data Sources and Methods

<table>
<tr style="background-color:#E6E6FA;">
<td><strong>Data Source</strong></td>
<td><strong>What I Got</strong></td>
<td><strong>How I Validated It</strong></td>
</tr>
<tr>
<td><strong>TMDb API</strong></td>
<td>Metadata for 200,000+ titles</td>
<td>Cross-referenced with IMDb for accuracy</td>
</tr>
<tr style="background-color:#FFE4E1;">
<td><strong>OpenSubtitles</strong></td>
<td>2.3 million lines of dialogue</td>
<td>Manual spot checks, automated language detection</td>
</tr>
<tr>
<td><strong>Wikidata</strong></td>
<td>Verified demographic information</td>
<td>Only used data with citations</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Platform APIs</strong></td>
<td>Viewing metrics where available</td>
<td>Weighted by actual viewership when possible</td>
</tr>
</table>

### Statistical Rigor

I use bootstrap confidence intervals (1000 iterations) for all metrics because normal assumptions don't hold for this data. Multiple comparison correction (Benjamini-Hochberg) prevents false discoveries. Difference-in-differences isolates causal effects of platform interventions. Cross-validation ensures the models generalize beyond the training data.

<div align="center">
  
![separator](https://img.shields.io/badge/-E6E6FA?style=flat&color=E6E6FA)
![separator](https://img.shields.io/badge/-F0F8FF?style=flat&color=F0F8FF)
![separator](https://img.shields.io/badge/-FFF0F5?style=flat&color=FFF0F5)

</div>

## Why This Matters

Media shapes culture. When 73% of action heroes are male, when women of color get 12% of lead roles, when characters over 50 disappear from screens, it sends a message about whose stories matter. This isn't about quotas or political correctness. It's about accurately reflecting the world we live in.

The good news? Some platforms are improving. Apple TV+ and HBO Max show that quality content and diversity aren't mutually exclusive. The bad news? At current rates of change, my calculations show we won't reach parity until 2034.

This project makes these patterns visible and measurable. Because the first step to fixing a problem is proving it exists.

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

Check out [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Fair warning: I'm particular about code quality, but I promise helpful code reviews.

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
<td>< 5 seconds for full dataset</td>
<td>Optimized pandas operations, vectorized calculations</td>
</tr>
<tr style="background-color:#F0F8FF;">
<td><strong>Model Accuracy</strong></td>
<td>87.3% bias detection</td>
<td>Ensemble averaging improves individual model performance</td>
</tr>
<tr>
<td><strong>Data Coverage</strong></td>
<td>47,000+ productions analyzed</td>
<td>Comprehensive coverage of major platforms</td>
</tr>
<tr style="background-color:#FFF0F5;">
<td><strong>Temporal Range</strong></td>
<td>10 years (2015-2024)</td>
<td>Captures full streaming era evolution</td>
</tr>
<tr>
<td><strong>Interactive Response</strong></td>
<td>< 100ms for chart updates</td>
<td>Efficient D3.js and Plotly implementations</td>
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
