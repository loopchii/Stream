#!/usr/bin/env python3
"""
StreamLens Analytics - Real-data music virality pipeline.

Loads a real dataset of top YouTube music videos (``data_sources/
youtube-top-100-songs-2025.csv`` by default, or whatever ``music_ingest``
produces from the live YouTube Data API), engineers features, and computes a
deep stack of statistics - all from real numbers, nothing fabricated:

* Power law of view counts: maximum-likelihood exponent (alpha), Kolmogorov-
  Smirnov fit distance, and a bootstrap 95% confidence interval.
* Inequality of attention: Gini, Lorenz curve, Theil index and top-k channel
  concentration (who controls the views).
* Correlation architecture: Spearman rank correlation of each feature with
  views, partial correlation controlling for channel size, and bootstrap CIs.
* Archetypes: K-means clusters mapped to named viral strategies.
* Tag network: co-occurrence graph (NetworkX) with density and central tags.
* Predictability: a RandomForest + GradientBoosting ensemble, cross-validated,
  reporting an honest R-squared and feature importances.

The inequality / bootstrap / grading helpers are shared with the synthetic
representation pipeline (``advanced_metrics``) so the two halves of the app
speak the same statistical language. Deterministic given a seed.

Author: Cazandra Aporbo, MS
"""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler

from advanced_metrics import bootstrap_ci, gini, letter_grade, lorenz_points, theil_index

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = BASE_DIR / "data_sources" / "youtube-top-100-songs-2025.csv"
SEED = 42

# Human-readable labels and tooltips for every engineered feature, reused by the
# API and the front end so the meaning of each number is never ambiguous.
FEATURE_LABELS: Dict[str, str] = {
    "duration_min": "Duration (minutes)",
    "channel_follower_count": "Channel reach (subscribers)",
    "virality_coefficient": "Virality (views per subscriber)",
    "title_word_count": "Title length (words)",
    "title_char_count": "Title length (characters)",
    "tag_count": "Tag count",
    "description_len": "Description length (characters)",
    "is_official": "Official video",
}

FEATURE_HELP: Dict[str, str] = {
    "duration_min": "Track length in minutes. The data peaks near the 3-minute radio-single norm.",
    "channel_follower_count": "How many subscribers the uploading channel has - a proxy for built-in reach.",
    "virality_coefficient": "Views divided by subscribers: how far a song travelled beyond its channel's base.",
    "title_word_count": "Number of words in the video title.",
    "title_char_count": "Number of characters in the video title.",
    "tag_count": "How many YouTube tags the upload declared.",
    "description_len": "Character length of the video description.",
    "is_official": "1 if the title/tags mark it an official video, else 0.",
}

# Pre-publication predictors of view count. NOTE: ``virality_coefficient`` is
# deliberately excluded here because it is derived from views (views / followers)
# and would leak the target; it is kept only as a descriptive output metric.
PREDICTOR_FEATURES: List[str] = [
    "duration_min",
    "channel_follower_count",
    "title_word_count",
    "title_char_count",
    "tag_count",
    "description_len",
    "is_official",
]

# Five viral archetypes, ordered by mean views (assigned after clustering).
ARCHETYPES: List[Dict[str, str]] = [
    {
        "name": "Supernovas",
        "blurb": "Explosive debuts from mega-channels - massive reach, instant escape velocity.",
    },
    {
        "name": "Established Giants",
        "blurb": "Big artists converting loyal fanbases into dependable nine-figure runs.",
    },
    {
        "name": "Viral Waves",
        "blurb": "Mid-reach uploads that punch far above their subscriber base - shareability wins.",
    },
    {
        "name": "Emerging Stars",
        "blurb": "Algorithm-discovered growth; strong views-per-subscriber on a smaller base.",
    },
    {
        "name": "Hidden Gems",
        "blurb": "Niche resonance and slow-burn acceleration from the smallest channels.",
    },
]

_OFFICIAL_RE = re.compile(r"official\s*(music\s*)?video|official\s*audio|m/?v\b", re.IGNORECASE)


def _to_minutes(seconds: Sequence[float]) -> np.ndarray:
    return np.asarray(seconds, dtype=float) / 60.0


def _count_tags(value: object) -> int:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0
    parts = [p for p in re.split(r"[;,]", str(value)) if p.strip()]
    return len(parts)


def _looks_official(title: object, tags: object) -> int:
    blob = f"{title} {tags}"
    return 1 if _OFFICIAL_RE.search(blob) else 0


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the modelling features from the raw scraped columns."""
    out = pd.DataFrame()
    out["title"] = df["title"].astype(str)
    out["channel"] = df["channel"].astype(str)
    out["view_count"] = pd.to_numeric(df["view_count"], errors="coerce")

    duration = pd.to_numeric(df.get("duration"), errors="coerce")
    out["duration_sec"] = duration
    out["duration_min"] = _to_minutes(duration.fillna(duration.median()))

    followers = pd.to_numeric(df.get("channel_follower_count"), errors="coerce")
    out["channel_follower_count"] = followers.fillna(followers.median())

    out["virality_coefficient"] = out["view_count"] / out["channel_follower_count"].clip(lower=1.0)
    out["title_char_count"] = out["title"].str.len().astype(float)
    out["title_word_count"] = out["title"].str.split().apply(len).astype(float)
    out["tag_count"] = df.get("tags").apply(_count_tags).astype(float) if "tags" in df else 0.0
    desc = df.get("description")
    out["description_len"] = (
        desc.astype(str).str.len().astype(float) if desc is not None else 0.0
    )
    out["is_official"] = [
        _looks_official(t, g)
        for t, g in zip(df["title"], df.get("tags", pd.Series([""] * len(df))))
    ]
    out["thumbnail"] = df.get("thumbnail", pd.Series([""] * len(df))).astype(str)
    out["channel_url"] = df.get("channel_url", pd.Series([""] * len(df))).astype(str)

    out = out.dropna(subset=["view_count"]).reset_index(drop=True)
    out["view_count"] = out["view_count"].astype(float)
    return out


@lru_cache(maxsize=4)
def load_dataset(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Load and feature-engineer the music dataset (cached per path)."""
    path = Path(csv_path) if csv_path else DEFAULT_CSV
    raw = pd.read_csv(path)
    return engineer_features(raw)


# --------------------------------------------------------------------------- #
# Power law
# --------------------------------------------------------------------------- #
def mle_alpha(values: Sequence[float], xmin: float) -> float:
    """Maximum-likelihood Pareto/Zipf exponent for x >= xmin (Clauset et al.)."""
    x = np.asarray([v for v in values if v >= xmin], dtype=float)
    if x.size == 0 or xmin <= 0:
        return 0.0
    return float(1.0 + x.size / np.sum(np.log(x / xmin)))


def select_xmin(values: Sequence[float]) -> Tuple[float, float, float]:
    """Pick xmin minimizing the KS distance (Clauset-Shalizi-Newman), returning
    (xmin, alpha, ks). Scans the unique candidate lower bounds in the tail."""
    v = np.sort(np.asarray(values, dtype=float))
    candidates = np.unique(v)
    # Keep enough tail mass for a stable fit.
    candidates = candidates[candidates <= np.percentile(v, 90)]
    best = (float(candidates[0]) if candidates.size else float(v[0]), 0.0, 1.0)
    for xmin in candidates:
        tail = v[v >= xmin]
        if tail.size < 10:
            continue
        alpha = mle_alpha(tail, xmin)
        if alpha <= 1.0:
            continue
        ks = ks_distance(tail, alpha, xmin)
        if ks < best[2]:
            best = (float(xmin), float(alpha), float(ks))
    return best


def ks_distance(values: Sequence[float], alpha: float, xmin: float) -> float:
    """Kolmogorov-Smirnov distance between the empirical and fitted Pareto CDF."""
    x = np.sort(np.asarray([v for v in values if v >= xmin], dtype=float))
    n = x.size
    if n == 0 or alpha <= 1.0:
        return 1.0
    ecdf = np.arange(1, n + 1) / n
    model_cdf = 1.0 - (x / xmin) ** (-(alpha - 1.0))
    return float(np.max(np.abs(ecdf - model_cdf)))


def power_law_analysis(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    df = load_dataset() if df is None else df
    views = df["view_count"].to_numpy(dtype=float)
    xmin, alpha, ks = select_xmin(views)
    ci = bootstrap_ci(
        [v for v in views if v >= xmin],
        lambda a: mle_alpha(a, xmin),
        n_boot=500,
        seed=SEED,
    )
    # Log-log survival (CCDF) points for plotting the heavy tail.
    sorted_v = np.sort(views)[::-1]
    n = sorted_v.size
    ccdf = np.arange(1, n + 1) / n
    points = [
        {"views": float(v), "p_at_least": float(p)}
        for v, p in zip(sorted_v, ccdf)
    ]
    return {
        "alpha": round(alpha, 3),
        "alpha_ci": {"low": round(ci["low"], 3), "high": round(ci["high"], 3)},
        "xmin": xmin,
        "ks_distance": round(ks, 4),
        "n": int(n),
        "interpretation": (
            f"View counts follow a power law with exponent {alpha:.2f}: a winner-take-most "
            "regime where a few videos capture most of the attention."
        ),
        "ccdf": points,
    }


# --------------------------------------------------------------------------- #
# Inequality
# --------------------------------------------------------------------------- #
def inequality_analysis(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    df = load_dataset() if df is None else df
    views = df["view_count"].to_numpy(dtype=float)
    channel_views = (
        df.groupby("channel")["view_count"].sum().sort_values(ascending=False)
    )
    total = float(views.sum())
    g = gini(views)
    top3 = float(channel_views.head(3).sum() / total) if total else 0.0
    top10 = float(channel_views.head(10).sum() / total) if total else 0.0
    return {
        "gini": round(g, 3),
        "theil": round(theil_index(views), 3),
        "lorenz": lorenz_points(views, buckets=20),
        "top3_channel_share": round(top3, 3),
        "top10_channel_share": round(top10, 3),
        "n_channels": int(df["channel"].nunique()),
        "total_views": total,
        "top_channels": [
            {"channel": ch, "views": float(v), "share": round(float(v / total), 4)}
            for ch, v in channel_views.head(10).items()
        ],
        "interpretation": (
            f"A Gini of {g:.2f} means attention is extremely concentrated - the top 3 channels "
            f"alone hold {top3 * 100:.0f}% of all views."
        ),
    }


# --------------------------------------------------------------------------- #
# Correlation architecture
# --------------------------------------------------------------------------- #
def _rankdata(a: np.ndarray) -> np.ndarray:
    order = a.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    return ranks


def _partial_spearman(
    df: pd.DataFrame, x: str, y: str, control: str
) -> float:
    """Spearman partial correlation of x and y controlling for `control`."""
    ranks = df[[x, y, control]].rank(method="average")
    c = np.column_stack([np.ones(len(ranks)), ranks[control].to_numpy()])

    def resid(col: str) -> np.ndarray:
        vec = ranks[col].to_numpy()
        beta, *_ = np.linalg.lstsq(c, vec, rcond=None)
        return vec - c.dot(beta)

    rx, ry = resid(x), resid(y)
    denom = np.linalg.norm(rx) * np.linalg.norm(ry)
    if denom == 0:
        return 0.0
    return float(np.dot(rx, ry) / denom)


def correlation_analysis(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    df = load_dataset() if df is None else df
    target = "view_count"
    features = [f for f in PREDICTOR_FEATURES if df[f].nunique() > 1]
    rows = []
    for f in features:
        rho, p = spearmanr(df[target], df[f])
        rho = 0.0 if np.isnan(rho) else float(rho)
        partial = _partial_spearman(df, f, target, "channel_follower_count") if f != "channel_follower_count" else rho
        # Bootstrap CI on the rank correlation.
        rng = np.random.default_rng(SEED)
        xv, yv = df[f].to_numpy(), df[target].to_numpy()
        boot = []
        for _ in range(400):
            idx = rng.integers(0, len(xv), len(xv))
            r, _ = spearmanr(xv[idx], yv[idx])
            boot.append(0.0 if np.isnan(r) else r)
        rows.append(
            {
                "feature": f,
                "label": FEATURE_LABELS.get(f, f),
                "help": FEATURE_HELP.get(f, ""),
                "spearman": round(rho, 3),
                "partial_spearman": round(partial, 3),
                "p_value": round(float(p), 4) if not np.isnan(p) else 1.0,
                "ci_low": round(float(np.percentile(boot, 2.5)), 3),
                "ci_high": round(float(np.percentile(boot, 97.5)), 3),
            }
        )
    rows.sort(key=lambda r: abs(r["spearman"]), reverse=True)

    # Full feature-vs-feature Spearman matrix for the heatmap.
    matrix_cols = [target] + features
    corr = df[matrix_cols].corr(method="spearman").round(3)
    heatmap = {
        "labels": [FEATURE_LABELS.get(c, "Views" if c == target else c) for c in matrix_cols],
        "matrix": corr.to_numpy().tolist(),
    }
    return {"target": target, "rows": rows, "heatmap": heatmap}


# --------------------------------------------------------------------------- #
# Archetypes (clustering)
# --------------------------------------------------------------------------- #
def archetype_analysis(df: Optional[pd.DataFrame] = None, k: int = 5) -> Dict[str, object]:
    df = load_dataset() if df is None else df
    feats = ["view_count", "virality_coefficient", "channel_follower_count", "duration_min"]
    x = df[feats].to_numpy(dtype=float)
    # Log-scale the heavy-tailed columns before standardizing.
    x_log = np.column_stack(
        [np.log1p(x[:, 0]), np.log1p(x[:, 1]), np.log1p(x[:, 2]), x[:, 3]]
    )
    scaled = StandardScaler().fit_transform(x_log)
    k = min(k, len(df))
    km = KMeans(n_clusters=k, random_state=SEED, n_init=10)
    labels = km.fit_predict(scaled)

    # Order clusters by mean views so naming is stable (highest -> Supernovas).
    order = (
        pd.Series(df["view_count"].to_numpy())
        .groupby(labels)
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    rank = {cluster: i for i, cluster in enumerate(order)}
    names = [ARCHETYPES[min(rank[c], len(ARCHETYPES) - 1)]["name"] for c in labels]

    clusters = []
    for i, cluster in enumerate(order):
        mask = labels == cluster
        meta = ARCHETYPES[min(i, len(ARCHETYPES) - 1)]
        clusters.append(
            {
                "name": meta["name"],
                "blurb": meta["blurb"],
                "count": int(mask.sum()),
                "avg_views": float(df.loc[mask, "view_count"].mean()),
                "avg_virality": float(df.loc[mask, "virality_coefficient"].mean()),
                "avg_duration_min": float(df.loc[mask, "duration_min"].mean()),
            }
        )
    scatter = [
        {
            "title": t,
            "channel": ch,
            "views": float(v),
            "virality": float(vir),
            "followers": float(fol),
            "duration_min": float(d),
            "archetype": name,
        }
        for t, ch, v, vir, fol, d, name in zip(
            df["title"], df["channel"], df["view_count"],
            df["virality_coefficient"], df["channel_follower_count"],
            df["duration_min"], names,
        )
    ]
    return {"k": k, "clusters": clusters, "points": scatter}


# --------------------------------------------------------------------------- #
# Tag co-occurrence network
# --------------------------------------------------------------------------- #
def _split_tags(value: object) -> List[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    return [t.strip().lower() for t in re.split(r"[;,]", str(value)) if t.strip()]


def network_analysis(
    raw_csv: Optional[str] = None, top_tags: int = 30
) -> Dict[str, object]:
    """Tag co-occurrence graph from the raw tags column."""
    path = Path(raw_csv) if raw_csv else DEFAULT_CSV
    raw = pd.read_csv(path)
    tag_lists = [_split_tags(v) for v in raw.get("tags", [])]
    freq = Counter(t for tags in tag_lists for t in set(tags))
    keep = {t for t, _ in freq.most_common(top_tags)}

    g = nx.Graph()
    for tags in tag_lists:
        present = sorted(set(t for t in tags if t in keep))
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                a, b = present[i], present[j]
                if g.has_edge(a, b):
                    g[a][b]["weight"] += 1
                else:
                    g.add_edge(a, b, weight=1)
    for t in keep:
        if t not in g:
            g.add_node(t)

    if g.number_of_nodes() == 0:
        return {"nodes": [], "edges": [], "density": 0.0, "n_nodes": 0, "n_edges": 0}

    degree = dict(g.degree(weight="weight"))
    communities = _greedy_communities(g)
    comm_of = {node: ci for ci, comm in enumerate(communities) for node in comm}
    nodes = [
        {
            "id": t,
            "freq": int(freq.get(t, 0)),
            "degree": int(degree.get(t, 0)),
            "community": comm_of.get(t, 0),
        }
        for t in g.nodes()
    ]
    edges = [
        {"source": a, "target": b, "weight": int(d["weight"])}
        for a, b, d in g.edges(data=True)
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "density": round(nx.density(g), 4),
        "n_nodes": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "n_communities": len(communities),
        "interpretation": (
            f"{g.number_of_nodes()} of the most common tags form {g.number_of_edges()} "
            f"co-occurrence links (density {nx.density(g):.2f}): shared tags cluster songs "
            "into genre neighbourhoods."
        ),
    }


def _greedy_communities(g: nx.Graph) -> List[List[str]]:
    try:
        from networkx.algorithms.community import greedy_modularity_communities

        return [sorted(c) for c in greedy_modularity_communities(g, weight="weight")]
    except Exception:
        return [sorted(g.nodes())]


# --------------------------------------------------------------------------- #
# Predictability (ensemble)
# --------------------------------------------------------------------------- #
def _build_models() -> List[Tuple[str, object]]:
    return [
        ("RandomForest", RandomForestRegressor(n_estimators=200, random_state=SEED)),
        (
            "GradientBoosting",
            GradientBoostingRegressor(n_estimators=150, random_state=SEED),
        ),
    ]


def predictability_analysis(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    df = load_dataset() if df is None else df
    features = [f for f in PREDICTOR_FEATURES if df[f].nunique() > 1]
    x = df[features].to_numpy(dtype=float)
    y = np.log1p(df["view_count"].to_numpy(dtype=float))  # log target: heavy tail
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)

    per_model = {}
    for name, model in _build_models():
        scores = cross_val_score(model, x, y, cv=kf, scoring="r2")
        per_model[name] = float(np.clip(scores.mean(), -1.0, 1.0))

    # Ensemble = simple average of out-of-fold predictions.
    oof = np.zeros(len(y))
    for _, model in _build_models():
        fold_pred = np.zeros(len(y))
        for tr, te in kf.split(x):
            model.fit(x[tr], y[tr])
            fold_pred[te] = model.predict(x[te])
        oof += fold_pred
    oof /= len(_build_models())
    ss_res = float(np.sum((y - oof) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    ensemble_r2 = float(np.clip(1.0 - ss_res / ss_tot, -1.0, 1.0)) if ss_tot else 0.0

    # Feature importances from a RandomForest fit on all data.
    rf = RandomForestRegressor(n_estimators=300, random_state=SEED).fit(x, y)
    importances = sorted(
        (
            {
                "feature": f,
                "label": FEATURE_LABELS.get(f, f),
                "importance": round(float(imp), 4),
            }
            for f, imp in zip(features, rf.feature_importances_)
        ),
        key=lambda d: d["importance"],
        reverse=True,
    )
    return {
        "ensemble_r2": round(ensemble_r2, 3),
        "per_model_r2": {k: round(v, 3) for k, v in per_model.items()},
        "predictable_pct": round(max(0.0, ensemble_r2) * 100, 1),
        "luck_pct": round((1.0 - max(0.0, ensemble_r2)) * 100, 1),
        "features": importances,
        "interpretation": (
            f"A cross-validated ensemble explains {max(0.0, ensemble_r2) * 100:.0f}% of the "
            "variation in (log) views - the rest is timing, culture and chance."
        ),
    }


def _predict_percentile(df: pd.DataFrame, features: List[str], query: Dict[str, float]) -> Dict[str, object]:
    x = df[features].to_numpy(dtype=float)
    y = np.log1p(df["view_count"].to_numpy(dtype=float))
    model = RandomForestRegressor(n_estimators=300, random_state=SEED).fit(x, y)
    vec = np.array([[float(query.get(f, float(np.median(df[f])))) for f in features]])
    pred_log = float(model.predict(vec)[0])
    pred_views = float(np.expm1(pred_log))
    percentile = float((y < pred_log).mean() * 100.0)
    return {"predicted_views": pred_views, "percentile": round(percentile, 1)}


# --------------------------------------------------------------------------- #
# Music-specific bias analysis
# --------------------------------------------------------------------------- #

# Artist gender mapping — hand-labeled from the real 65-channel list.
# Categories: "female", "male", "mixed" (group/collab), "non-binary".
# Channels not listed default to "unknown".
_ARTIST_GENDER: Dict[str, str] = {
    "ROSÉ": "female", "Lady Gaga": "female", "Reneé Rapp": "female",
    "Billie Eilish": "female", "Sabrina Carpenter": "female",
    "Ariana Grande": "female", "Charli xcx": "female",
    "Chappell Roan": "female", "Dua Lipa": "female",
    "Gracie Abrams": "female", "Lola Young": "female",
    "Miley Cyrus": "female", "Selena Gomez": "female",
    "Tate McRae": "female", "Taylor Swift": "female", "Tyla": "female",
    "Addison Rae": "female", "Claudia Valentina": "female",
    "Doechii": "female", "Ravyn Lenae": "female", "JENNIE": "female",
    "Sevdaliza": "female",
    "Ed Sheeran": "male", "Kendrick Lamar": "male", "Drake": "male",
    "Post Malone": "male", "Tommy Richman": "male", "Shaboozey": "male",
    "Benson Boone": "male", "Alex Warren": "male", "Dean Lewis": "male",
    "Justin Bieber": "male", "Damiano David": "male",
    "Myles Smith": "male", "Sean Paul": "male", "Teddy Swims": "male",
    "yung kai": "male", "d4vd": "male", "keshi": "male",
    "Jackson Wang": "male", "ROLE MODEL": "male", "GIVĒON": "male",
    "Roy Woods": "male", "Vex Prince": "male", "sombr": "male",
    "David Guetta": "male", "keinemusik": "male",
    "LLOUD Official": "male", "HoodTrophy Bino": "male",
    "RAAHiiM": "male", "PJ": "male",
    "Coldplay": "mixed", "Maroon 5": "mixed", "ImagineDragons": "mixed",
    "The Weeknd": "male",
}

# Genre heuristics from tags and title keywords.
_GENRE_KEYWORDS: Dict[str, List[str]] = {
    "Pop": ["pop", "dance pop", "synth", "electropop"],
    "Hip-Hop/Rap": ["hip hop", "rap", "trap", "hip-hop", "rapper"],
    "R&B/Soul": ["r&b", "rnb", "soul", "r & b"],
    "Rock/Alternative": ["rock", "alternative", "indie rock", "punk"],
    "Electronic/Dance": ["edm", "electronic", "house", "techno", "dance", "dj"],
    "Country": ["country", "americana", "cowboy"],
    "Latin": ["latin", "reggaeton", "salsa", "bachata", "latino"],
    "K-Pop": ["k-pop", "kpop", "k pop", "yg entertainment", "blackpink", "jennie"],
}


def _classify_gender(channel: str) -> str:
    return _ARTIST_GENDER.get(channel.strip(), "unknown")


def _classify_genre(tags: object, title: object) -> str:
    blob = f"{tags} {title}".lower()
    for genre, keywords in _GENRE_KEYWORDS.items():
        for kw in keywords:
            if kw in blob:
                return genre
    return "Other/Unclassified"


def _detect_collab(title: str) -> bool:
    indicators = [" ft.", " feat.", " ft ", " feat ", " x ", " & ", " with ", " featuring "]
    low = title.lower()
    return any(ind in low for ind in indicators)


def bias_analysis(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """Compute music-specific bias dimensions from the real dataset."""
    df = load_dataset() if df is None else df
    raw = pd.read_csv(DEFAULT_CSV)

    # --- Gender representation ---
    df["artist_gender"] = df["channel"].apply(_classify_gender)
    gender_counts = df["artist_gender"].value_counts().to_dict()
    gender_views: Dict[str, float] = {}
    for g in df["artist_gender"].unique():
        gender_views[g] = float(df.loc[df["artist_gender"] == g, "view_count"].sum())
    total_views = float(df["view_count"].sum())
    gender_view_share = {g: round(v / total_views, 4) for g, v in gender_views.items()}

    # Female vs male parity
    female_songs = gender_counts.get("female", 0)
    male_songs = gender_counts.get("male", 0)
    total_gendered = female_songs + male_songs
    female_ratio = female_songs / total_gendered if total_gendered else 0.5
    gender_parity = round(1.0 - abs(0.5 - female_ratio) * 2, 3)

    # Gender × views disparity (do female artists get fewer views per song?)
    avg_views_by_gender = {}
    for g in ["female", "male", "mixed"]:
        subset = df[df["artist_gender"] == g]
        if len(subset) > 0:
            avg_views_by_gender[g] = round(float(subset["view_count"].mean()))
    # Views parity: ratio of female avg to male avg (1.0 = equal)
    f_avg = avg_views_by_gender.get("female", 0)
    m_avg = avg_views_by_gender.get("male", 1)
    views_parity = round(f_avg / m_avg, 3) if m_avg > 0 else 0.0

    # --- Genre concentration ---
    tags_col = raw.get("tags", pd.Series([""] * len(raw)))
    df["genre"] = [
        _classify_genre(t, ti) for t, ti in zip(tags_col.fillna(""), df["title"])
    ]
    genre_counts_dict = df["genre"].value_counts().to_dict()
    genre_views_dict: Dict[str, float] = {}
    for g in df["genre"].unique():
        genre_views_dict[g] = float(df.loc[df["genre"] == g, "view_count"].sum())
    genre_gini = round(float(gini(list(genre_views_dict.values()))), 3)

    # --- Collaboration patterns ---
    df["is_collab"] = df["title"].apply(_detect_collab)
    collab_count = int(df["is_collab"].sum())
    collab_view_share = round(
        float(df.loc[df["is_collab"], "view_count"].sum()) / total_views, 4
    )

    # --- Duration bias (do longer songs get fewer views?) ---
    short = df[df["duration_min"] < 3.0]
    medium = df[(df["duration_min"] >= 3.0) & (df["duration_min"] <= 4.0)]
    long_ = df[df["duration_min"] > 4.0]
    duration_bias = {
        "short_under_3min": {
            "count": int(len(short)),
            "avg_views": round(float(short["view_count"].mean())) if len(short) else 0,
        },
        "medium_3to4min": {
            "count": int(len(medium)),
            "avg_views": round(float(medium["view_count"].mean())) if len(medium) else 0,
        },
        "long_over_4min": {
            "count": int(len(long_)),
            "avg_views": round(float(long_["view_count"].mean())) if len(long_) else 0,
        },
    }

    # --- Official vs unofficial bias ---
    official = df[df["is_official"] == 1]
    unofficial = df[df["is_official"] == 0]
    official_bias = {
        "official_count": int(len(official)),
        "unofficial_count": int(len(unofficial)),
        "official_avg_views": round(float(official["view_count"].mean())) if len(official) else 0,
        "unofficial_avg_views": round(float(unofficial["view_count"].mean())) if len(unofficial) else 0,
        "official_view_share": round(
            float(official["view_count"].sum()) / total_views, 4
        ) if total_views > 0 else 0.0,
    }

    # --- Top artist concentration (is the top too concentrated?) ---
    channel_views = df.groupby("channel")["view_count"].sum().sort_values(ascending=False)
    top5_share = round(float(channel_views.head(5).sum()) / total_views, 4)
    top10_share = round(float(channel_views.head(10).sum()) / total_views, 4)
    bottom50_share = round(
        float(channel_views.tail(len(channel_views) // 2).sum()) / total_views, 4
    )

    # --- Summary bias scores ---
    bias_scores = {
        "gender_parity": gender_parity,
        "views_parity": views_parity,
        "genre_diversity": round(1.0 - genre_gini, 3),
        "collab_rate": round(collab_count / len(df), 3),
        "concentration_top5": top5_share,
    }
    overall_bias_grade = letter_grade(
        (gender_parity + min(views_parity, 1.0) + (1.0 - genre_gini) + (1.0 - top5_share)) / 4.0
    )

    interpretation = (
        f"Gender parity in the top 100 is {gender_parity:.2f} "
        f"({'near-equal' if gender_parity > 0.8 else 'skewed'}). "
        f"Female artists average {f_avg:,.0f} views/song vs male {m_avg:,.0f} "
        f"(ratio {views_parity:.2f}). "
        f"Genre concentration (Gini {genre_gini}) suggests "
        f"{'broad' if genre_gini < 0.4 else 'moderate' if genre_gini < 0.6 else 'high'} diversity. "
        f"The top 5 channels control {top5_share * 100:.0f}% of all views."
    )

    return {
        "gender": {
            "counts": gender_counts,
            "view_share": gender_view_share,
            "avg_views_by_gender": avg_views_by_gender,
            "gender_parity": gender_parity,
            "views_parity": views_parity,
            "female_ratio": round(female_ratio, 3),
        },
        "genres": {
            "counts": genre_counts_dict,
            "views": {k: round(v) for k, v in genre_views_dict.items()},
            "gini": genre_gini,
        },
        "collaboration": {
            "collab_count": collab_count,
            "solo_count": int(len(df) - collab_count),
            "collab_view_share": collab_view_share,
        },
        "duration_bias": duration_bias,
        "official_bias": official_bias,
        "concentration": {
            "top5_share": top5_share,
            "top10_share": top10_share,
            "bottom50_share": bottom50_share,
        },
        "bias_scores": bias_scores,
        "overall_grade": overall_bias_grade,
        "interpretation": interpretation,
    }


# --------------------------------------------------------------------------- #
# What-if predictor + overview
# --------------------------------------------------------------------------- #
def simulate_virality(
    duration_min: float,
    channel_follower_count: float,
    tag_count: float,
    is_official: float = 1.0,
    df: Optional[pd.DataFrame] = None,
) -> Dict[str, object]:
    df = load_dataset() if df is None else df
    features = [f for f in PREDICTOR_FEATURES if df[f].nunique() > 1]
    med = {f: float(np.median(df[f])) for f in features}
    query = dict(med)
    query.update(
        {
            "duration_min": duration_min,
            "channel_follower_count": channel_follower_count,
            "tag_count": tag_count,
            "is_official": is_official,
        }
    )
    res = _predict_percentile(df, features, query)
    pct = res["percentile"]
    grade = letter_grade(pct / 100.0)
    verdict = _verdict_for(pct)
    return {
        "inputs": {
            "duration_min": duration_min,
            "channel_follower_count": channel_follower_count,
            "tag_count": tag_count,
            "is_official": is_official,
        },
        "predicted_views": res["predicted_views"],
        "percentile": pct,
        "grade": grade,
        "verdict": verdict,
    }


def _verdict_for(pct: float) -> str:
    if pct >= 80:
        return "Primed to go viral - this profile sits in the top fifth of real hits."
    if pct >= 55:
        return "Above-average odds; a credible contender with the right timing."
    if pct >= 30:
        return "Middle of the pack - it would need a cultural spark to break out."
    return "Long-shot profile relative to the songs that actually charted."


# Canonical grid used to bake the What-If predictor for the static (no-server)
# site. The live API answers continuous queries; the static build snaps to the
# nearest grid point of the same real RandomForest model.
GRID_DURATION = [1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0]
GRID_FOLLOWERS = [1e4, 1e5, 5e5, 1e6, 5e6, 1e7, 5e7, 1e8, 3e8]
GRID_TAGS = [0.0, 5.0, 10.0, 20.0, 30.0, 50.0]
GRID_OFFICIAL = [0.0, 1.0]


def simulate_grid(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """Precompute What-If predictions over a grid (one RF fit, vectorised)."""
    df = load_dataset() if df is None else df
    features = [f for f in PREDICTOR_FEATURES if df[f].nunique() > 1]
    x = df[features].to_numpy(dtype=float)
    y = np.log1p(df["view_count"].to_numpy(dtype=float))
    y_sorted = np.sort(y)
    model = RandomForestRegressor(n_estimators=300, random_state=SEED).fit(x, y)
    med = {f: float(np.median(df[f])) for f in features}

    rows = []
    queries = []
    for d in GRID_DURATION:
        for fol in GRID_FOLLOWERS:
            for t in GRID_TAGS:
                for o in GRID_OFFICIAL:
                    q = dict(med)
                    q.update(
                        {
                            "duration_min": d,
                            "channel_follower_count": fol,
                            "tag_count": t,
                            "is_official": o,
                        }
                    )
                    queries.append((d, fol, t, o))
                    rows.append([float(q.get(f, med[f])) for f in features])
    preds = model.predict(np.asarray(rows, dtype=float))
    grid = []
    for (d, fol, t, o), pred_log in zip(queries, preds):
        pct = float((y_sorted < pred_log).mean() * 100.0)
        grid.append(
            {
                "duration_min": d,
                "channel_follower_count": fol,
                "tag_count": t,
                "is_official": o,
                "predicted_views": float(np.expm1(pred_log)),
                "percentile": round(pct, 1),
                "grade": letter_grade(pct / 100.0),
                "verdict": _verdict_for(pct),
            }
        )
    return {
        "axes": {
            "duration_min": GRID_DURATION,
            "channel_follower_count": GRID_FOLLOWERS,
            "tag_count": GRID_TAGS,
            "is_official": GRID_OFFICIAL,
        },
        "grid": grid,
    }


def overview(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    df = load_dataset() if df is None else df
    views = df["view_count"].to_numpy(dtype=float)
    durations = df["duration_min"].to_numpy(dtype=float)
    return {
        "n_songs": int(len(df)),
        "n_channels": int(df["channel"].nunique()),
        "total_views": float(views.sum()),
        "median_views": float(np.median(views)),
        "max_views": float(views.max()),
        "top_song": str(df.loc[df["view_count"].idxmax(), "title"]),
        "top_channel": str(df.loc[df["view_count"].idxmax(), "channel"]),
        "median_duration_min": round(float(np.median(durations)), 2),
        "official_share": round(float(df["is_official"].mean()), 3),
        "data_source": "Real YouTube data - top music videos, 2025",
    }


def songs_table(
    df: Optional[pd.DataFrame] = None, limit: int = 100, sort_by: str = "view_count"
) -> List[Dict[str, object]]:
    df = load_dataset() if df is None else df
    sort_col = sort_by if sort_by in df.columns else "view_count"
    ordered = df.sort_values(sort_col, ascending=False).head(limit)
    records = []
    for _, r in ordered.iterrows():
        records.append(
            {
                "title": str(r["title"]),
                "channel": str(r["channel"]),
                "view_count": float(r["view_count"]),
                "duration_min": round(float(r["duration_min"]), 2),
                "channel_follower_count": float(r["channel_follower_count"]),
                "virality_coefficient": round(float(r["virality_coefficient"]), 3),
                "tag_count": int(r["tag_count"]),
                "is_official": int(r["is_official"]),
            }
        )
    return records


def full_report(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """Everything in one payload - used to bake the static site."""
    df = load_dataset() if df is None else df
    return {
        "overview": overview(df),
        "power_law": power_law_analysis(df),
        "inequality": inequality_analysis(df),
        "correlations": correlation_analysis(df),
        "archetypes": archetype_analysis(df),
        "network": network_analysis(),
        "predictability": predictability_analysis(df),
        "songs": songs_table(df, limit=100),
        "bias": bias_analysis(df),
        "feature_labels": FEATURE_LABELS,
    }


if __name__ == "__main__":
    import json

    report = full_report()
    print(json.dumps(report["overview"], indent=2))
    print("power-law alpha:", report["power_law"]["alpha"], report["power_law"]["alpha_ci"])
    print("gini:", report["inequality"]["gini"], "top3:", report["inequality"]["top3_channel_share"])
    print("ensemble R2:", report["predictability"]["ensemble_r2"])
    print("archetypes:", [(c["name"], c["count"]) for c in report["archetypes"]["clusters"]])
    print("network:", report["network"]["n_nodes"], "nodes", report["network"]["n_edges"], "edges")
