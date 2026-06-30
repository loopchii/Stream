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
import html
from collections import Counter
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from advanced_metrics import bootstrap_ci, gini, letter_grade, lorenz_points, theil_index
from music_decision_lab import build_decision_lab
from music_field_proxies import (
    build_living_media_surface,
    build_public_music_proxy_table,
    vitality_signature_labels,
)

try:  # pragma: no cover - optional dependency in the preview venv
    import networkx as nx  # type: ignore
except Exception:  # pragma: no cover - fallback keeps the module importable
    class _FallbackGraph:
        def __init__(self):
            self._adj = {}

        def add_node(self, node):
            self._adj.setdefault(node, {})

        def add_edge(self, a, b, weight=1):
            self.add_node(a)
            self.add_node(b)
            self._adj[a].setdefault(b, {"weight": 0})
            self._adj[b].setdefault(a, {"weight": 0})
            self._adj[a][b]["weight"] += weight
            self._adj[b][a]["weight"] += weight

        def has_edge(self, a, b):
            return b in self._adj.get(a, {})

        def __contains__(self, node):
            return node in self._adj

        def __getitem__(self, node):
            return self._adj[node]

        def nodes(self):
            return list(self._adj.keys())

        def edges(self, data=False):
            seen = set()
            for a, nbrs in self._adj.items():
                for b, payload in nbrs.items():
                    key = tuple(sorted((a, b)))
                    if key in seen:
                        continue
                    seen.add(key)
                    if data:
                        yield a, b, payload
                    else:
                        yield a, b

        def degree(self, weight=None):
            result = []
            for node, nbrs in self._adj.items():
                if weight == "weight":
                    score = sum(float(payload.get("weight", 1)) for payload in nbrs.values())
                else:
                    score = len(nbrs)
                result.append((node, score))
            return result

        def number_of_nodes(self):
            return len(self._adj)

        def number_of_edges(self):
            return sum(len(nbrs) for nbrs in self._adj.values()) // 2

    class _FallbackNetworkX:
        Graph = _FallbackGraph

        @staticmethod
        def density(g):
            n = g.number_of_nodes()
            m = g.number_of_edges()
            return 0.0 if n < 2 else (2.0 * m) / (n * (n - 1))

    nx = _FallbackNetworkX()  # type: ignore

try:  # pragma: no cover - optional dependency in the preview venv
    from sklearn.cluster import KMeans  # type: ignore
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor  # type: ignore
    from sklearn.model_selection import KFold, cross_val_score  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore
except Exception:  # pragma: no cover - deterministic lightweight fallback
    class StandardScaler:
        def fit_transform(self, x):
            arr = np.asarray(x, dtype=float)
            self.mean_ = arr.mean(axis=0)
            self.scale_ = arr.std(axis=0)
            self.scale_[self.scale_ == 0] = 1.0
            return (arr - self.mean_) / self.scale_

    class KFold:
        def __init__(self, n_splits=5, shuffle=False, random_state=None):
            self.n_splits = int(n_splits)
            self.shuffle = bool(shuffle)
            self.random_state = random_state

        def split(self, x):
            n = len(x)
            idx = np.arange(n)
            if self.shuffle:
                rng = np.random.default_rng(self.random_state)
                rng.shuffle(idx)
            folds = np.array_split(idx, self.n_splits)
            for i in range(self.n_splits):
                test = folds[i]
                train = np.concatenate([folds[j] for j in range(self.n_splits) if j != i])
                yield train, test

    def _r2_score(y_true, y_pred):
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        ss_res = float(np.sum((y_true - y_pred) ** 2))
        ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
        return 0.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot

    class _LinearLikeRegressor:
        def __init__(self, **kwargs):
            self._params = dict(kwargs)
            self.coef_ = None
            self.intercept_ = 0.0
            self.feature_importances_ = None

        def fit(self, x, y):
            x = np.asarray(x, dtype=float)
            y = np.asarray(y, dtype=float)
            x_aug = np.column_stack([np.ones(len(x)), x])
            coef, *_ = np.linalg.lstsq(x_aug, y, rcond=None)
            self.intercept_ = float(coef[0])
            self.coef_ = coef[1:]
            weights = np.abs(self.coef_)
            total = float(weights.sum()) or 1.0
            self.feature_importances_ = weights / total
            return self

        def predict(self, x):
            x = np.asarray(x, dtype=float)
            return x @ self.coef_ + self.intercept_

    class RandomForestRegressor(_LinearLikeRegressor):
        pass

    class GradientBoostingRegressor(_LinearLikeRegressor):
        pass

    class KMeans:
        def __init__(self, n_clusters=8, random_state=None, n_init=10, max_iter=30):
            self.n_clusters = int(n_clusters)
            self.random_state = random_state
            self.n_init = n_init
            self.max_iter = max_iter

        def fit_predict(self, x):
            arr = np.asarray(x, dtype=float)
            n = len(arr)
            k = max(1, min(self.n_clusters, n))
            if n == 0:
                self.cluster_centers_ = np.empty((0, arr.shape[1] if arr.ndim > 1 else 0))
                return np.array([], dtype=int)
            idx = np.linspace(0, n - 1, k, dtype=int)
            centers = arr[idx].copy()
            labels = np.zeros(n, dtype=int)
            for _ in range(self.max_iter):
                dist = ((arr[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
                new_labels = dist.argmin(axis=1)
                if np.array_equal(new_labels, labels):
                    break
                labels = new_labels
                for i in range(k):
                    mask = labels == i
                    centers[i] = arr[mask].mean(axis=0) if np.any(mask) else arr[i % n]
            self.cluster_centers_ = centers
            self.labels_ = labels
            return labels

    def cross_val_score(model, x, y, cv, scoring="r2"):
        scores = []
        for tr, te in cv.split(x):
            est = model.__class__(**getattr(model, "_params", {}))
            est.fit(x[tr], y[tr])
            pred = est.predict(x[te])
            scores.append(_r2_score(y[te], pred))
        return np.array(scores, dtype=float)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = BASE_DIR / "data_sources" / "youtube-top-100-songs-2025.csv"
SUPPLEMENT_MOST_VIEWED = BASE_DIR / "data_sources" / "most-viewed-yt-videos-2026.csv"
SUPPLEMENT_MUSIC_DATA = BASE_DIR / "data_sources" / "youtube-music-data.csv"
SUPPLEMENT_CHANNELS = BASE_DIR / "data_sources" / "youtube-top-channels-2026.csv"
SEED = 42
CURRENT_YEAR = date.today().year
RECENT_PUBLIC_YEAR_MIN = 2018

_YEAR_HINT_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")
_COPYRIGHT_YEAR_RE = re.compile(r"[©℗]\s*(20\d{2})")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

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


def _coerce_recent_public_year(value: object) -> int:
    try:
        year = int(value)
    except (TypeError, ValueError):
        return 0
    if RECENT_PUBLIC_YEAR_MIN <= year <= CURRENT_YEAR + 1:
        return year
    return 0


def _infer_publication_year_from_text(*fields: object) -> Tuple[int, str]:
    """Extract a conservative year hint from public text.

    This is deliberately narrow. A year is admitted only when either:

    1. a copyright / rights marker carries a recent year, or
    2. the visible public text collapses to exactly one distinct recent year.

    Anything more ambiguous stays unknown.
    """
    text = " ".join(str(field or "") for field in fields if field is not None)
    if not text.strip():
        return 0, "unknown"

    copyright_hits = [
        year
        for year in (_coerce_recent_public_year(hit) for hit in _COPYRIGHT_YEAR_RE.findall(text))
        if year
    ]
    if copyright_hits:
        return max(copyright_hits), "copyright_notice"

    recent_hits = [
        year
        for year in (_coerce_recent_public_year(hit) for hit in _YEAR_HINT_RE.findall(text))
        if year
    ]
    distinct = sorted(set(recent_hits))
    if len(distinct) == 1:
        return distinct[0], "single_recent_year_hint"

    return 0, "unknown"


def _clean_public_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = html.unescape(str(value))
    text = _HTML_TAG_RE.sub(" ", text)
    text = text.replace("|", " ")
    text = text.replace("/", " ")
    text = text.replace("&", " and ")
    return _WHITESPACE_RE.sub(" ", text).strip()


def _genre_hint_blob(*fields: object) -> str:
    return " ".join(
        cleaned.lower()
        for cleaned in (_clean_public_text(field) for field in fields)
        if cleaned
    )


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the modelling features from the raw scraped columns."""
    out = pd.DataFrame()
    out["title"] = df["title"].astype(str)
    out["channel"] = df["channel"].astype(str)
    out["view_count"] = pd.to_numeric(df["view_count"], errors="coerce")
    out["description"] = df.get("description", pd.Series([""] * len(df))).astype(str)

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
    out["_raw_tags"] = df.get("tags", pd.Series([""] * len(df))).astype(str)

    if "date" in df.columns:
        parsed = pd.to_datetime(df["date"], errors="coerce", utc=True)
        out["published_at"] = parsed.dt.strftime("%Y-%m-%d").fillna("")
        out["published_year"] = parsed.dt.year.fillna(0).astype(int)
        out["published_year_source"] = np.where(parsed.notna(), "explicit_date", "unknown")
    else:
        inferred = df.apply(
            lambda row: _infer_publication_year_from_text(
                row.get("title"),
                row.get("fulltitle"),
                row.get("description"),
            ),
            axis=1,
        )
        out["published_at"] = ""
        out["published_year"] = inferred.apply(lambda item: item[0]).astype(int)
        out["published_year_source"] = inferred.apply(lambda item: item[1]).astype(str)

    out = out.dropna(subset=["view_count"]).reset_index(drop=True)
    out["view_count"] = out["view_count"].astype(float)
    return out


def _parse_human_number(v: object) -> float:
    """Parse '8.97B', '123M', '5.6K' → float."""
    s = str(v).strip()
    for suffix, mult in [("B", 1e9), ("b", 1e9), ("M", 1e6), ("m", 1e6),
                         ("K", 1e3), ("k", 1e3)]:
        if s.endswith(suffix):
            try:
                return float(s[:-1]) * mult
            except ValueError:
                return 0.0
    try:
        return float(s.replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def _parse_duration_string(d: object) -> float:
    """Parse '3:40' or '1:18:42' → seconds."""
    parts = str(d).split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, TypeError):
        pass
    return 0.0


def _load_supplement_most_viewed() -> pd.DataFrame:
    """Load DS1: top 1000 most-viewed YT videos, filter to music, normalise."""
    if not SUPPLEMENT_MOST_VIEWED.exists():
        return pd.DataFrame()
    df = pd.read_csv(SUPPLEMENT_MOST_VIEWED)
    music = df[df["content_type"] == "Music Video"].copy()
    if music.empty:
        return pd.DataFrame()

    def _extract_channel(title: str) -> str:
        for sep in [" - ", " – "]:
            if sep in title:
                return title.split(sep)[0].strip()
        return "Unknown"

    out = pd.DataFrame()
    out["title"] = music["title"].astype(str)
    out["channel"] = music["title"].apply(_extract_channel)
    out["view_count"] = music["views"].apply(_parse_human_number)
    out["likes"] = music["likes"].apply(_parse_human_number)
    out["detected_language"] = music.get(
        "detected_language", pd.Series(["Unknown"] * len(music))
    ).astype(str)
    out["tags"] = music.apply(
        lambda row: _genre_hint_blob(
            row.get("title"),
            row.get("content_type"),
            row.get("detected_language"),
        ),
        axis=1,
    )
    out["description"] = out["tags"]
    out["has_hashtags"] = music.get("has_hashtags", 0)
    out["source"] = "most_viewed_2026"
    return out.reset_index(drop=True)


def _load_supplement_music_data() -> pd.DataFrame:
    """Load DS2: 157 YouTube music videos with duration/likes/subs."""
    if not SUPPLEMENT_MUSIC_DATA.exists():
        return pd.DataFrame()
    df = pd.read_csv(SUPPLEMENT_MUSIC_DATA)
    if df.empty:
        return pd.DataFrame()
    out = pd.DataFrame()
    out["title"] = df["title"].astype(str)
    out["channel"] = df["channelName"].astype(str)
    out["view_count"] = pd.to_numeric(df["viewCount"], errors="coerce")
    out["likes"] = pd.to_numeric(df["likes"], errors="coerce")
    out["duration"] = df["duration"].apply(_parse_duration_string)
    out["channel_follower_count"] = pd.to_numeric(
        df["numberOfSubscribers"], errors="coerce"
    )
    text_col = df.get("text", pd.Series([""] * len(df), index=df.index))
    details_col = df.get("details", pd.Series([""] * len(df), index=df.index))
    out["tags"] = [
        _genre_hint_blob(title, text, details)
        for title, text, details in zip(df["title"], text_col, details_col)
    ]
    out["description"] = [
        _genre_hint_blob(text, details)
        for text, details in zip(text_col, details_col)
    ]
    if "date" in df.columns:
        parsed = pd.to_datetime(df["date"], errors="coerce", utc=True)
        out["published_at"] = parsed.dt.strftime("%Y-%m-%d").fillna("")
        out["published_year"] = parsed.dt.year.fillna(0).astype(int)
        out["published_year_source"] = np.where(parsed.notna(), "explicit_date", "unknown")
    out["source"] = "youtube_music_data"
    return out.dropna(subset=["view_count"]).reset_index(drop=True)


def _load_channel_countries() -> Dict[str, str]:
    """Load DS3: channel name → country mapping."""
    if not SUPPLEMENT_CHANNELS.exists():
        return {}
    df = pd.read_csv(SUPPLEMENT_CHANNELS)
    mapping: Dict[str, str] = {}
    for _, row in df.iterrows():
        name = str(row.get("Channel Name", "")).strip()
        country = str(row.get("Country", "Unknown")).strip()
        if name and country and country != "Unknown":
            mapping[name] = country
    return mapping


def _normalise_titles(values: pd.Series) -> pd.Series:
    return values.astype(str).str.lower().str.strip()


@lru_cache(maxsize=2)
def load_enriched_dataset() -> pd.DataFrame:
    """Build the unified music dataset from all available sources.

    Priority: the primary CSV (100 songs) is the authoritative source.
    Supplementary datasets are merged only for rows not already present
    (deduplicated on normalised title). Extra columns (likes,
    detected_language, country) are attached where available.
    """
    primary = load_dataset()

    # --- Supplement 1: most-viewed music videos ---
    sup1 = _load_supplement_most_viewed()

    # --- Supplement 2: YouTube music data ---
    sup2 = _load_supplement_music_data()

    # Deduplicate by normalised title
    seen = set(_normalise_titles(primary["title"]))
    extras = []
    for sup in [sup1, sup2]:
        if sup.empty:
            continue
        sup["_norm"] = _normalise_titles(sup["title"])
        novel = sup[~sup["_norm"].isin(seen)].copy()
        seen.update(novel["_norm"])
        extras.append(novel.drop(columns=["_norm"]))

    if extras:
        combined_extras = pd.concat(extras, ignore_index=True)
        # Engineer features for supplementary data
        sup_eng = pd.DataFrame()
        sup_eng["title"] = combined_extras["title"]
        sup_eng["channel"] = combined_extras["channel"]
        sup_eng["view_count"] = combined_extras["view_count"].astype(float)
        dur = combined_extras.get("duration")
        if dur is not None:
            sup_eng["duration_sec"] = pd.to_numeric(dur, errors="coerce")
        else:
            sup_eng["duration_sec"] = float("nan")
        med_dur = primary["duration_min"].median() * 60
        sup_eng["duration_min"] = (
            sup_eng["duration_sec"].fillna(med_dur) / 60.0
        )
        fol = combined_extras.get("channel_follower_count")
        if fol is not None:
            sup_eng["channel_follower_count"] = pd.to_numeric(
                fol, errors="coerce"
            ).fillna(primary["channel_follower_count"].median())
        else:
            sup_eng["channel_follower_count"] = primary[
                "channel_follower_count"
            ].median()
        sup_eng["virality_coefficient"] = (
            sup_eng["view_count"]
            / sup_eng["channel_follower_count"].clip(lower=1.0)
        )
        sup_eng["title_char_count"] = (
            sup_eng["title"].str.len().astype(float)
        )
        sup_eng["title_word_count"] = (
            sup_eng["title"].str.split().apply(len).astype(float)
        )
        sup_eng["tag_count"] = 0.0
        sup_eng["description_len"] = 0.0
        sup_eng["is_official"] = [
            _looks_official(t, "") for t in sup_eng["title"]
        ]
        sup_eng["thumbnail"] = ""
        sup_eng["channel_url"] = ""
        sup_eng["_raw_tags"] = ""
        # Carry over extra columns
        if "likes" in combined_extras:
            sup_eng["likes"] = pd.to_numeric(
                combined_extras["likes"], errors="coerce"
            ).fillna(0)
        if "detected_language" in combined_extras:
            sup_eng["detected_language"] = (
                combined_extras["detected_language"].fillna("Unknown")
            )
        if "published_at" in combined_extras:
            sup_eng["published_at"] = combined_extras["published_at"].fillna("")
        if "published_year" in combined_extras:
            sup_eng["published_year"] = pd.to_numeric(
                combined_extras["published_year"], errors="coerce"
            ).fillna(0).astype(int)
        if "published_year_source" in combined_extras:
            sup_eng["published_year_source"] = combined_extras["published_year_source"].fillna("unknown").astype(str)
        elif "published_year" in sup_eng.columns:
            sup_eng["published_year_source"] = np.where(
                sup_eng["published_year"].astype(int) > 0,
                "explicit_date",
                "unknown",
            )
        if "source" in combined_extras:
            sup_eng["source"] = combined_extras["source"]
        if "description" in combined_extras:
            sup_eng["description"] = combined_extras["description"].fillna("").astype(str)
        else:
            sup_eng["description"] = ""
        if "tags" in combined_extras:
            sup_eng["_raw_tags"] = combined_extras["tags"].fillna("").astype(str)
        else:
            sup_eng["_raw_tags"] = ""

        # Mark primary rows
        primary_out = primary.copy()
        if "likes" not in primary_out.columns:
            primary_out["likes"] = float("nan")
        if "detected_language" not in primary_out.columns:
            primary_out["detected_language"] = "Unknown"
        if "published_at" not in primary_out.columns:
            primary_out["published_at"] = ""
        if "published_year" not in primary_out.columns:
            primary_out["published_year"] = 0
        if "published_year_source" not in primary_out.columns:
            primary_out["published_year_source"] = "unknown"
        primary_out["source"] = "primary_top100"
        if "description" not in primary_out.columns:
            primary_out["description"] = ""

        merged = pd.concat(
            [primary_out, sup_eng], ignore_index=True
        )
    else:
        merged = primary.copy()
        merged["source"] = "primary_top100"
        if "likes" not in merged.columns:
            merged["likes"] = float("nan")
        if "detected_language" not in merged.columns:
            merged["detected_language"] = "Unknown"
        if "published_at" not in merged.columns:
            merged["published_at"] = ""
        if "published_year" not in merged.columns:
            merged["published_year"] = 0
        if "published_year_source" not in merged.columns:
            merged["published_year_source"] = "unknown"
        if "description" not in merged.columns:
            merged["description"] = ""

    # --- Repair row-level public metadata so the song table can carry the same
    # structural evidence that the aggregate bias surfaces already use. ---
    if "genre" not in merged.columns:
        merged["genre"] = "Unknown"
    existing_genres = merged["genre"].fillna("Unknown").astype(str)
    genre_needs_fill = existing_genres.str.strip().str.lower().isin(
        {"", "unknown", "other/unclassified"}
    )
    genre_pairs = [
        _classify_genre(tags, title, channel, description, language)
        for tags, title, channel, description, language in zip(
            merged.get("_raw_tags", pd.Series([""] * len(merged))),
            merged["title"],
            merged["channel"],
            merged.get("description", pd.Series([""] * len(merged))),
            merged.get("detected_language", pd.Series(["Unknown"] * len(merged))),
        )
    ]
    inferred_genres = pd.Series([label for label, _ in genre_pairs], index=merged.index)
    inferred_genre_sources = pd.Series([source for _, source in genre_pairs], index=merged.index)
    merged["genre"] = existing_genres.where(~genre_needs_fill, inferred_genres)
    merged["genre_source"] = np.where(
        genre_needs_fill,
        inferred_genre_sources,
        merged.get("genre_source", pd.Series(["existing"] * len(merged))).fillna("existing"),
    )

    if "published_year" not in merged.columns:
        merged["published_year"] = 0
    if "published_year_source" not in merged.columns:
        merged["published_year_source"] = "unknown"
    existing_years = pd.to_numeric(merged["published_year"], errors="coerce").fillna(0).astype(int)
    existing_year_sources = merged["published_year_source"].fillna("unknown").astype(str)
    inferred_year_pairs = merged.apply(
        lambda row: _infer_publication_year_from_text(
            row.get("published_at"),
            row.get("title"),
            row.get("fulltitle"),
            row.get("description"),
        ),
        axis=1,
    )
    inferred_years = inferred_year_pairs.apply(lambda item: int(item[0] or 0)).astype(int)
    inferred_year_sources = inferred_year_pairs.apply(lambda item: str(item[1] or "unknown"))
    year_needs_fill = existing_years.le(0)
    inferred_year_mask = year_needs_fill & inferred_years.gt(0)
    merged["published_year"] = existing_years.where(~inferred_year_mask, inferred_years)
    merged["published_year_source"] = existing_year_sources.where(~inferred_year_mask, inferred_year_sources)

    # --- Enrich with channel country from DS3 ---
    countries = _load_channel_countries()
    merged["country"] = merged["channel"].map(
        lambda c: countries.get(c.strip(), "Unknown")
    )

    # --- Engagement ratio ---
    likes = pd.to_numeric(merged.get("likes"), errors="coerce").fillna(0)
    merged["engagement_ratio"] = (
        likes / merged["view_count"].clip(lower=1.0)
    )

    merged = merged.dropna(subset=["view_count"]).reset_index(drop=True)
    return merged


@lru_cache(maxsize=4)
def load_dataset(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Load and feature-engineer the music dataset (cached per path)."""
    path = Path(csv_path) if csv_path else DEFAULT_CSV
    raw = pd.read_csv(path)
    return engineer_features(raw)


def quality_report(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """Document source coverage, cleaning choices, and model guardrails."""
    primary_raw = pd.read_csv(DEFAULT_CSV)
    primary = load_dataset() if df is None else df.copy()
    enriched = load_enriched_dataset()

    primary_norm = _normalise_titles(primary_raw["title"])
    primary_seen = set(primary_norm)

    sup1_raw_rows = 0
    sup1_music_rows = 0
    sup1_added = 0
    sup1_deduped = 0
    sup1_missing_views = 0
    sup1_missing_language = 0
    if SUPPLEMENT_MOST_VIEWED.exists():
        sup1_raw = pd.read_csv(SUPPLEMENT_MOST_VIEWED)
        sup1_raw_rows = int(len(sup1_raw))
        sup1_music = sup1_raw[sup1_raw["content_type"] == "Music Video"].copy()
        sup1_music_rows = int(len(sup1_music))
        sup1_missing_views = int(
            sup1_music["views"].apply(_parse_human_number).eq(0).sum()
        )
        if "detected_language" in sup1_music.columns:
            sup1_missing_language = int(
                sup1_music["detected_language"].fillna("").astype(str).str.strip().eq("").sum()
            )
        sup1_norm = _normalise_titles(sup1_music["title"])
        sup1_novel_mask = ~sup1_norm.isin(primary_seen)
        sup1_added = int(sup1_novel_mask.sum())
        sup1_deduped = int(len(sup1_music) - sup1_added)
        primary_seen.update(sup1_norm[sup1_novel_mask])

    sup2_raw_rows = 0
    sup2_added = 0
    sup2_deduped = 0
    sup2_missing_views = 0
    sup2_missing_duration = 0
    sup2_missing_followers = 0
    sup2_rows_with_dates = 0
    if SUPPLEMENT_MUSIC_DATA.exists():
        sup2_raw = pd.read_csv(SUPPLEMENT_MUSIC_DATA)
        sup2_raw_rows = int(len(sup2_raw))
        sup2_missing_views = int(pd.to_numeric(sup2_raw["viewCount"], errors="coerce").isna().sum())
        sup2_missing_duration = int(sup2_raw["duration"].isna().sum())
        sup2_missing_followers = int(pd.to_numeric(sup2_raw["numberOfSubscribers"], errors="coerce").isna().sum())
        if "date" in sup2_raw.columns:
            sup2_rows_with_dates = int(pd.to_datetime(sup2_raw["date"], errors="coerce", utc=True).notna().sum())
        sup2_clean = sup2_raw[pd.to_numeric(sup2_raw["viewCount"], errors="coerce").notna()].copy()
        sup2_norm = _normalise_titles(sup2_clean["title"])
        sup2_novel_mask = ~sup2_norm.isin(primary_seen)
        sup2_added = int(sup2_novel_mask.sum())
        sup2_deduped = int(len(sup2_clean) - sup2_added)
        primary_seen.update(sup2_norm[sup2_novel_mask])

    primary_missing_views = int(pd.to_numeric(primary_raw["view_count"], errors="coerce").isna().sum())
    primary_missing_duration = int(pd.to_numeric(primary_raw["duration"], errors="coerce").isna().sum())
    primary_missing_followers = int(pd.to_numeric(primary_raw["channel_follower_count"], errors="coerce").isna().sum())
    primary_year_hints = 0
    if "published_year" in primary.columns:
        primary_year_hints = int(pd.to_numeric(primary["published_year"], errors="coerce").fillna(0).astype(int).gt(0).sum())

    known_languages = 0
    if "detected_language" in enriched.columns:
        known_languages = int(
            enriched["detected_language"]
            .fillna("Unknown")
            .astype(str)
            .loc[lambda s: ~s.isin(["", "Unknown"])]
            .nunique()
        )

    genre_probe = [
        _classify_genre(tags, title, channel, description, language)
        for tags, title, channel, description, language in zip(
            enriched.get("_raw_tags", pd.Series([""] * len(enriched))),
            enriched["title"],
            enriched["channel"],
            enriched.get("description", pd.Series([""] * len(enriched))),
            enriched.get("detected_language", pd.Series([""] * len(enriched))),
        )
    ]
    known_genre_rows = int(sum(1 for label, _ in genre_probe if label != "Other/Unclassified"))
    genre_source_counts = Counter(
        source for label, source in genre_probe if label != "Other/Unclassified"
    )

    published_years = pd.to_numeric(
        enriched.get("published_year", pd.Series([0] * len(enriched))),
        errors="coerce",
    ).fillna(0).astype(int)
    published_year_sources = enriched.get(
        "published_year_source",
        pd.Series(["unknown"] * len(enriched), index=enriched.index),
    ).fillna("unknown").astype(str)
    explicit_year_rows = int(((published_years > 0) & published_year_sources.eq("explicit_date")).sum())
    inferred_year_rows = int(((published_years > 0) & ~published_year_sources.isin(["explicit_date", "unknown"])).sum())
    published_years = published_years[published_years > 0]

    source_audit = [
        {
            "source": "Top 100 (2025)",
            "file": DEFAULT_CSV.name,
            "raw_rows": int(len(primary_raw)),
            "admitted_rows": int(len(primary)),
            "duplicates_removed": 0,
            "missing_views_dropped": primary_missing_views,
            "missing_duration_imputed": primary_missing_duration,
            "missing_followers_imputed": primary_missing_followers,
            "rows_with_year_hints": primary_year_hints,
            "notes": "Primary cohort used for the core charts and leaderboard surfaces.",
        },
        {
            "source": "Most Viewed (2026)",
            "file": SUPPLEMENT_MOST_VIEWED.name,
            "raw_rows": sup1_raw_rows,
            "music_rows_after_filter": sup1_music_rows,
            "admitted_rows": sup1_added,
            "duplicates_removed": sup1_deduped,
            "missing_views_dropped": sup1_missing_views,
            "missing_language_labels": sup1_missing_language,
            "notes": "Filtered to music videos before deduplication against the primary cohort.",
        },
        {
            "source": "YouTube Music Data",
            "file": SUPPLEMENT_MUSIC_DATA.name,
            "raw_rows": sup2_raw_rows,
            "admitted_rows": sup2_added,
            "duplicates_removed": sup2_deduped,
            "missing_views_dropped": sup2_missing_views,
            "missing_duration_imputed": sup2_missing_duration,
            "missing_followers_imputed": sup2_missing_followers,
            "rows_with_publication_dates": sup2_rows_with_dates,
            "notes": "Adds duration, engagement, subscriber, and publication timing context where available.",
        },
    ]

    feature_manifest = [
        {
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "description": FEATURE_HELP.get(name, ""),
            "used_for_prediction": name in PREDICTOR_FEATURES,
            "descriptive_only": name not in PREDICTOR_FEATURES,
        }
        for name in FEATURE_LABELS
    ]

    return {
        "generated_at": date.today().isoformat(),
        "cohorts": {
            "core_top_100": {
                "songs": int(len(primary)),
                "channels": int(primary["channel"].nunique()),
                "purpose": "Used for the core view, inequality, correlation, archetype, network, and prediction charts.",
            },
            "enriched_context": {
                "songs": int(len(enriched)),
                "sources": {str(k): int(v) for k, v in enriched["source"].value_counts().to_dict().items()},
                "purpose": "Used where broader structural checks matter: bias, language mix, publication timing, and resonance context.",
            },
        },
        "source_audit": source_audit,
        "cleaning_steps": [
            "Coerce view counts to numeric and drop rows that still cannot be measured.",
            "Normalize title strings before cross-source deduplication so the same song is not counted twice.",
            "Convert durations to minutes and fill missing durations with the source median rather than inventing a default.",
            "Fill missing subscriber counts with the source median so reach-adjusted comparisons remain stable.",
            "Map channel countries only when a public lookup exists; otherwise keep the value as Unknown instead of guessing.",
            "Carry publication years directly from public date fields, and only infer a year from free text when a single recent year or copyright marker is unambiguous.",
            "Recover genre hints from public tags, title language, artist/channel entities, and supplemental public descriptions before labeling a row as unclassified.",
            "Keep the top-100 cohort separate from the enriched context so broad structural claims do not overwrite the core leaderboard.",
        ],
        "guardrails": [
            "Virality coefficient is excluded from the predictor set because it is derived from views and would leak the target.",
            "All prediction scores are reported out-of-fold with 5-fold cross-validation, not in-sample fit.",
            "Power-law confidence intervals use 500 bootstrap resamples over the fitted tail only.",
            "Correlation rows include partial Spearman checks so raw associations are not mistaken for independent effects.",
            "Publication timelines are shown only for rows with explicit public dates or conservative text-resolved year hints; missing years are not backfilled.",
            "Years inferred from description text are marked separately from explicit upload dates so time claims stay auditable.",
            "Embodied and vitality signals are public proxies from duration, engagement, virality, packaging, language spread, and release timing; they are not biometric or waveform claims.",
        ],
        "model_rigor": {
            "target": "log1p(view_count)",
            "cv_folds": 5,
            "bootstrap_power_law": 500,
            "bootstrap_correlations": 400,
            "predictor_features": [FEATURE_LABELS.get(name, name) for name in PREDICTOR_FEATURES],
            "blocked_from_prediction": ["Virality (views per subscriber)"],
        },
        "coverage": {
            "known_languages": known_languages,
            "countries_mapped": int(
                enriched.get("country", pd.Series([], dtype=str))
                .astype(str)
                .loc[lambda s: ~s.isin(["", "Unknown"])]
                .nunique()
            ),
            "publication_year_min": int(published_years.min()) if not published_years.empty else None,
            "publication_year_max": int(published_years.max()) if not published_years.empty else None,
            "publication_year_explicit_rows": explicit_year_rows,
            "publication_year_inferred_rows": inferred_year_rows,
            "publication_year_explicit_share": round(float(explicit_year_rows) / len(enriched), 3) if len(enriched) else 0.0,
            "publication_year_inferred_share": round(float(inferred_year_rows) / len(enriched), 3) if len(enriched) else 0.0,
            "genre_known_rows": known_genre_rows,
            "genre_known_share": round(float(known_genre_rows) / len(enriched), 3) if len(enriched) else 0.0,
            "genre_signal_sources": {str(k): int(v) for k, v in genre_source_counts.most_common(12)},
            "duplicate_titles_removed": int(sup1_deduped + sup2_deduped),
        },
        "feature_manifest": feature_manifest,
    }


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
    "LLOUD Official": "female", "HoodTrophy Bino": "male",
    "RAAHiiM": "male", "PJ": "male",
    "Coldplay": "mixed", "Maroon 5": "mixed", "ImagineDragons": "mixed",
    "The Weeknd": "male",
}

# Genre heuristics from tags and title keywords.
_GENRE_KEYWORDS: Dict[str, List[str]] = {
    "K-Pop": ["k-pop", "kpop", "k pop", "yg entertainment", "blackpink", "jennie"],
    "Latin": ["latin", "reggaeton", "salsa", "bachata", "latino", "corridos", "regional mexicano", "urbano latino"],
    "Hip-Hop/Rap": ["hip hop", "hip-hop", "rap", "trap", "drill", "freestyle", "cypher", "disstrack", "diss track", "lyricist"],
    "Electronic/Dance": ["edm", "electronic", "house", "techno", "dance", "dj", "remix", "club", "party mix", "festival", "amapiano"],
    "Rock/Alternative": ["rock", "alternative", "alt", "indie rock", "punk", "grunge"],
    "Country": ["country", "americana", "cowboy", "nashville"],
    "Afrobeats/Amapiano": ["afrobeats", "afrobeat", "afro disco", "afropop", "amapiano"],
    "R&B/Soul": ["r&b", "rnb", "soul", "r and b", "r & b", "neo soul"],
    "Folk/Acoustic": ["acoustic", "folk", "singer songwriter", "singer-songwriter", "ballad"],
    "Soundtrack/Family": ["soundtrack", "from moana", "dreamworks", "trolls", "disney", "animation"],
    "Pop": ["pop", "dance pop", "synth", "electropop", "radio pop"],
}

_GENRE_ENTITY_HINTS: Dict[str, str] = {
    "rosé": "K-Pop",
    "jennie": "K-Pop",
    "blackpink": "K-Pop",
    "bts": "K-Pop",
    "lady gaga": "Pop",
    "billie eilish": "Pop",
    "renee rapp": "Pop",
    "reneé rapp": "Pop",
    "ed sheeran": "Folk/Acoustic",
    "a-ha": "Pop",
    "alex warren": "Pop",
    "lola young": "Pop",
    "myles smith": "Folk/Acoustic",
    "tate mcrae": "Pop",
    "benson boone": "Pop",
    "taylor swift": "Pop",
    "miley cyrus": "Pop",
    "charli xcx": "Pop",
    "dua lipa": "Pop",
    "ariana grande": "Pop",
    "bruno mars": "Pop",
    "kendrick lamar": "Hip-Hop/Rap",
    "drake": "Hip-Hop/Rap",
    "tommy richman": "Hip-Hop/Rap",
    "doechii": "Hip-Hop/Rap",
    "hoodtrophy bino": "Hip-Hop/Rap",
    "nelly wap": "Hip-Hop/Rap",
    "zillionaire doe": "Hip-Hop/Rap",
    "french montana": "Hip-Hop/Rap",
    "xxxtentacion": "Hip-Hop/Rap",
    "migos": "Hip-Hop/Rap",
    "lil pump": "Hip-Hop/Rap",
    "cardi b": "Hip-Hop/Rap",
    "juice wrld": "Hip-Hop/Rap",
    "post malone": "Hip-Hop/Rap",
    "lil huddy": "Rock/Alternative",
    "the weeknd": "R&B/Soul",
    "giveon": "R&B/Soul",
    "ravyn lenae": "R&B/Soul",
    "raahiim": "R&B/Soul",
    "tyla": "Afrobeats/Amapiano",
    "sevdaliza": "Electronic/Dance",
    "david guetta": "Electronic/Dance",
    "keinemusik": "Electronic/Dance",
    "magic music": "Electronic/Dance",
    "skrillex": "Electronic/Dance",
    "diplo": "Electronic/Dance",
    "aronchupa": "Electronic/Dance",
    "stromae": "Electronic/Dance",
    "niickii": "Electronic/Dance",
    "adam port": "Electronic/Dance",
    "coldplay": "Rock/Alternative",
    "damiano david": "Rock/Alternative",
    "imagine dragons": "Rock/Alternative",
    "onerepublic": "Rock/Alternative",
    "shaboozey": "Country",
    "bebe rexha": "Country",
    "morgan wallen": "Country",
    "zach bryan": "Country",
    "luis fonsi": "Latin",
    "daddy yankee": "Latin",
    "bad bunny": "Latin",
    "karol g": "Latin",
    "j balvin": "Latin",
    "maluma": "Latin",
    "ozuna": "Latin",
    "anitta": "Latin",
    "shakira": "Latin",
    "wiz khalifa": "Hip-Hop/Rap",
    "crazy frog": "Electronic/Dance",
    "el chombo": "Latin",
    "maroon 5": "Pop",
    "katy perry": "Pop",
    "passenger": "Folk/Acoustic",
    "enrique iglesias": "Latin",
    "charlie puth": "Pop",
    "the chainsmokers": "Electronic/Dance",
    "adele": "Pop",
    "twenty one pilots": "Rock/Alternative",
    "eminem": "Hip-Hop/Rap",
    "fifth harmony": "Pop",
    "calvin harris": "Electronic/Dance",
    "sia": "Pop",
    "christina perri": "Pop",
    "meghan trainor": "Pop",
    "marshmello": "Electronic/Dance",
    "john legend": "R&B/Soul",
    "magic!": "Pop",
    "gotye": "Pop",
    "avicii": "Electronic/Dance",
    "ellie goulding": "Pop",
    "los ángeles azules": "Latin",
    "romeo santos": "Latin",
    "prince royce": "Latin",
    "nicky jam": "Latin",
    "becky g": "Latin",
    "natti natasha": "Latin",
    "piso 21": "Latin",
    "j. balvin": "Latin",
    "j balvin": "Latin",
    "ricky martin": "Latin",
    "arcángel": "Latin",
    "arcangel": "Latin",
    "marc anthony": "Latin",
    "melendi": "Latin",
    "michel teló": "Latin",
    "michel telo": "Latin",
    "grupo frontera": "Latin",
    "grupo firme": "Latin",
    "yiyo sarante": "Latin",
    "willy william": "Latin",
    "rag'n'bone man": "R&B/Soul",
    "nirvana": "Rock/Alternative",
    "4 non blondes": "Rock/Alternative",
    "manuel turizo": "Latin",
    "michael jackson": "Pop",
    "camila cabello": "Pop",
    "queen": "Rock/Alternative",
    "p!nk": "Pop",
    "pink": "Pop",
    "coolio": "Hip-Hop/Rap",
    "macklemore": "Hip-Hop/Rap",
    "justin timberlake": "Pop",
    "carlos vives": "Latin",
    "sebastián yatra": "Latin",
    "sebastian yatra": "Latin",
    "mc fioti": "Latin",
    "guns n' roses": "Rock/Alternative",
    "martin garrix": "Electronic/Dance",
    "dwayne johnson": "Soundtrack/Family",
    "the cranberries": "Rock/Alternative",
    "nelly": "Hip-Hop/Rap",
    "sam smith": "Pop",
    "tyga": "Hip-Hop/Rap",
    "rick astley": "Pop",
    "lukas graham": "Pop",
    "gente de zona": "Latin",
    "ac/dc": "Rock/Alternative",
    "shawn mendes": "Pop",
    "evanescence": "Rock/Alternative",
    "aqua": "Pop",
    "one direction": "Pop",
    "dr. dre": "Hip-Hop/Rap",
    "don omar": "Latin",
    "christian nodal": "Latin",
    "pitbull": "Latin",
    "george michael": "Pop",
    "harry styles": "Pop",
    "audioslave": "Rock/Alternative",
    "auli'i cravalho": "Soundtrack/Family",
    "ricardo arjona": "Latin",
    "lil nas x": "Country",
    "clean bandit": "Electronic/Dance",
    "r.e.m.": "Rock/Alternative",
    "metallica": "Rock/Alternative",
    "the police": "Rock/Alternative",
    "bon jovi": "Rock/Alternative",
    "europe": "Rock/Alternative",
    "arctic monkeys": "Rock/Alternative",
    "linkin park": "Rock/Alternative",
    "chris brown": "R&B/Soul",
    "pharrell williams": "Pop",
    "akon": "R&B/Soul",
    "6ix9ine": "Hip-Hop/Rap",
    "jason derulo": "Pop",
    "jass manak": "Pop",
    "indila": "Pop",
    "calum scott": "Pop",
    "bonnie tyler": "Pop",
    "the black eyed peas": "Pop",
    "zayn": "Pop",
    "rihanna": "Pop",
    "justin bieber": "Pop",
    "foster the people": "Rock/Alternative",
    "hoobastank": "Rock/Alternative",
    "scorpions": "Rock/Alternative",
    "usher": "R&B/Soul",
    "rema": "Afrobeats/Amapiano",
    "khalid": "R&B/Soul",
    "ylvis": "Pop",
}


def _classify_gender(channel: str) -> str:
    return _ARTIST_GENDER.get(channel.strip(), "unknown")


def _classify_genre(
    tags: object,
    title: object,
    channel: object = "",
    description: object = "",
    detected_language: object = "",
) -> Tuple[str, str]:
    blob = _genre_hint_blob(tags, title, channel, description, detected_language)
    if not blob:
        return "Other/Unclassified", "fallback"
    for genre, keywords in _GENRE_KEYWORDS.items():
        for kw in keywords:
            if kw in blob:
                return genre, f"keyword:{kw}"
    for entity, genre in _GENRE_ENTITY_HINTS.items():
        if entity in blob:
            return genre, f"entity:{entity}"
    if re.search(r"\b(mix|playlist|remix|edit|visualizer|visualiser|dj)\b", blob):
        return "Electronic/Dance", "pattern:mix"
    if re.search(r"\b(acoustic|ballad|stripped)\b", blob):
        return "Folk/Acoustic", "pattern:acoustic"
    return "Other/Unclassified", "fallback"


def _detect_collab(title: str) -> bool:
    indicators = [" ft.", " feat.", " ft ", " feat ", " x ", " & ", " with ", " featuring "]
    low = title.lower()
    return any(ind in low for ind in indicators)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def bias_analysis(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """Compute music-specific bias dimensions from the real dataset."""
    analysis_df = load_enriched_dataset().copy() if df is None else df.copy()
    edf = analysis_df

    # --- Gender representation ---
    analysis_df["artist_gender"] = analysis_df["channel"].apply(_classify_gender)
    gender_counts = analysis_df["artist_gender"].value_counts().to_dict()
    gender_views: Dict[str, float] = {}
    for g in analysis_df["artist_gender"].unique():
        gender_views[g] = float(
            analysis_df.loc[analysis_df["artist_gender"] == g, "view_count"].sum()
        )
    total_views = float(analysis_df["view_count"].sum())
    gender_view_share = {g: round(v / total_views, 4) for g, v in gender_views.items()}

    # Female vs male parity
    female_songs = gender_counts.get("female", 0)
    male_songs = gender_counts.get("male", 0)
    total_gendered = female_songs + male_songs
    female_ratio = female_songs / total_gendered if total_gendered else 0.5
    gender_parity = round(1.0 - abs(0.5 - female_ratio) * 2, 3)
    gender_known_share = round(total_gendered / len(analysis_df), 3) if len(analysis_df) else 0.0

    # Gender × views disparity (do female artists get fewer views per song?)
    avg_views_by_gender = {}
    for g in ["female", "male", "mixed"]:
        subset = analysis_df[analysis_df["artist_gender"] == g]
        if len(subset) > 0:
            avg_views_by_gender[g] = round(float(subset["view_count"].mean()))
    # Views parity: ratio of female avg to male avg (1.0 = equal)
    f_avg = avg_views_by_gender.get("female", 0)
    m_avg = avg_views_by_gender.get("male", 1)
    views_parity = round(f_avg / m_avg, 3) if m_avg > 0 else 0.0

    # --- Genre concentration ---
    tags_col = analysis_df["_raw_tags"].fillna("") if "_raw_tags" in analysis_df.columns else pd.Series([""] * len(analysis_df))
    desc_col = analysis_df.get("description", pd.Series([""] * len(analysis_df)))
    lang_col = analysis_df.get("detected_language", pd.Series([""] * len(analysis_df)))
    genre_pairs = [
        _classify_genre(t, ti, ch, desc, lang)
        for t, ti, ch, desc, lang in zip(tags_col, analysis_df["title"], analysis_df["channel"], desc_col, lang_col)
    ]
    analysis_df["genre"] = [label for label, _ in genre_pairs]
    analysis_df["genre_source"] = [source for _, source in genre_pairs]
    genre_counts_dict = analysis_df["genre"].value_counts().to_dict()
    genre_views_dict: Dict[str, float] = {}
    genre_breakdown = []
    for g in analysis_df["genre"].unique():
        genre_df = analysis_df[analysis_df["genre"] == g]
        genre_views_dict[g] = float(genre_df["view_count"].sum())
        genre_breakdown.append(
            {
                "genre": g,
                "song_count": int(len(genre_df)),
                "view_share": round(float(genre_df["view_count"].sum()) / total_views, 4) if total_views else 0.0,
                "avg_views": round(float(genre_df["view_count"].mean())) if len(genre_df) else 0,
                "median_views": round(float(genre_df["view_count"].median())) if len(genre_df) else 0,
                "avg_duration_min": round(float(genre_df["duration_min"].mean()), 2) if len(genre_df) else 0.0,
                "collab_share": round(float(genre_df["title"].apply(_detect_collab).mean()), 3) if len(genre_df) else 0.0,
                "top_song": str(genre_df.sort_values("view_count", ascending=False).iloc[0]["title"]) if len(genre_df) else "",
                "top_channel": str(genre_df.sort_values("view_count", ascending=False).iloc[0]["channel"]) if len(genre_df) else "",
            }
        )
    genre_gini = round(float(gini(list(genre_views_dict.values()))), 3)
    classified_genre_df = analysis_df[analysis_df["genre"] != "Other/Unclassified"].copy()
    classified_genre_share = round(float(len(classified_genre_df)) / len(analysis_df), 3) if len(analysis_df) else 0.0
    classified_genre_views = float(classified_genre_df["view_count"].sum()) if len(classified_genre_df) else 0.0
    classified_view_share = round(classified_genre_views / total_views, 4) if total_views else 0.0
    classified_genre_breakdown = []
    classified_views_dict: Dict[str, float] = {}
    if len(classified_genre_df):
        for g in classified_genre_df["genre"].unique():
            genre_df = classified_genre_df[classified_genre_df["genre"] == g]
            genre_total_views = float(genre_df["view_count"].sum())
            classified_views_dict[g] = genre_total_views
            classified_genre_breakdown.append(
                {
                    "genre": g,
                    "song_count": int(len(genre_df)),
                    "view_share": round(genre_total_views / total_views, 4) if total_views else 0.0,
                    "classified_view_share": round(genre_total_views / classified_genre_views, 4) if classified_genre_views else 0.0,
                    "avg_views": round(float(genre_df["view_count"].mean())) if len(genre_df) else 0,
                    "median_views": round(float(genre_df["view_count"].median())) if len(genre_df) else 0,
                    "avg_duration_min": round(float(genre_df["duration_min"].mean()), 2) if len(genre_df) else 0.0,
                    "collab_share": round(float(genre_df["title"].apply(_detect_collab).mean()), 3) if len(genre_df) else 0.0,
                    "top_song": str(genre_df.sort_values("view_count", ascending=False).iloc[0]["title"]) if len(genre_df) else "",
                    "top_channel": str(genre_df.sort_values("view_count", ascending=False).iloc[0]["channel"]) if len(genre_df) else "",
                }
            )
    classified_genre_gini = round(float(gini(list(classified_views_dict.values()))), 3) if classified_views_dict else 0.0
    classified_genre_diversity = round(1.0 - classified_genre_gini, 3) if classified_views_dict else 0.0

    # --- Collaboration patterns ---
    analysis_df["is_collab"] = analysis_df["title"].apply(_detect_collab)
    collab_count = int(analysis_df["is_collab"].sum())
    collab_view_share = round(
        float(analysis_df.loc[analysis_df["is_collab"], "view_count"].sum()) / total_views, 4
    )

    # --- Duration bias (do longer songs get fewer views?) ---
    short = analysis_df[analysis_df["duration_min"] < 3.0]
    medium = analysis_df[(analysis_df["duration_min"] >= 3.0) & (analysis_df["duration_min"] <= 4.0)]
    long_ = analysis_df[analysis_df["duration_min"] > 4.0]
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
    official = analysis_df[analysis_df["is_official"] == 1]
    unofficial = analysis_df[analysis_df["is_official"] == 0]
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
    channel_views = analysis_df.groupby("channel")["view_count"].sum().sort_values(ascending=False)
    top5_share = round(float(channel_views.head(5).sum()) / total_views, 4)
    top10_share = round(float(channel_views.head(10).sum()) / total_views, 4)
    bottom50_share = round(
        float(channel_views.tail(len(channel_views) // 2).sum()) / total_views, 4
    )

    # --- Language bias (from enriched dataset) ---
    try:
        lang_counts = edf["detected_language"].value_counts().to_dict()
        lang_views: Dict[str, float] = {}
        etotal = float(edf["view_count"].sum())
        for lang in edf["detected_language"].unique():
            lang_views[lang] = round(
                float(edf.loc[edf["detected_language"] == lang, "view_count"].sum())
            )
        eng_share = round(lang_views.get("English", 0) / etotal, 4) if etotal else 0
        lang_gini = round(float(gini(list(lang_views.values()))), 3)
        language_bias = {
            "counts": lang_counts,
            "views": lang_views,
            "english_share": eng_share,
            "gini": lang_gini,
            "n_languages": len([k for k in lang_counts if k != "Unknown"]),
        }
        language_known_share = round(
            float(edf["detected_language"].fillna("Unknown").astype(str).loc[lambda s: ~s.isin(["", "Unknown"])].shape[0]) / len(edf),
            3,
        ) if len(edf) else 0.0

        # --- Engagement bias ---
        eng_ratio = edf["engagement_ratio"].dropna()
        engagement_bias = {
            "median_engagement": round(float(eng_ratio.median()), 5),
            "mean_engagement": round(float(eng_ratio.mean()), 5),
            "top_engaged_songs": [],
        }
        if len(eng_ratio) > 0:
            top_eng = edf.nlargest(5, "engagement_ratio")
            engagement_bias["top_engaged_songs"] = [
                {
                    "title": str(r["title"])[:60],
                    "engagement": round(float(r["engagement_ratio"]), 5),
                    "views": float(r["view_count"]),
                }
                for _, r in top_eng.iterrows()
            ]

        # --- Country bias ---
        country_counts = edf["country"].value_counts().to_dict()
        country_views: Dict[str, float] = {}
        for c in edf["country"].unique():
            country_views[c] = round(
                float(edf.loc[edf["country"] == c, "view_count"].sum())
            )
        country_bias = {
            "counts": {k: v for k, v in country_counts.items() if k != "Unknown"},
            "views": {k: round(v) for k, v in country_views.items() if k != "Unknown"},
            "unknown_count": country_counts.get("Unknown", 0),
        }

        enriched_stats = {
            "total_songs": int(len(edf)),
            "sources": edf["source"].value_counts().to_dict(),
        }
    except Exception:
        language_bias = {"counts": {}, "views": {}, "english_share": 0,
                         "gini": 0, "n_languages": 0}
        language_known_share = 0.0
        engagement_bias = {"median_engagement": 0, "mean_engagement": 0,
                           "top_engaged_songs": []}
        country_bias = {"counts": {}, "views": {}, "unknown_count": 0}
        enriched_stats = {"total_songs": int(len(analysis_df)), "sources": {}}

    timeline_df = pd.DataFrame()
    if "published_year" in edf.columns:
        timeline_df = edf[pd.to_numeric(edf["published_year"], errors="coerce").fillna(0) > 0].copy()
    publication_timeline = {
        "years": [],
        "observed_years": [],
        "missing_years": [],
        "song_counts": [],
        "total_views": [],
        "avg_views": [],
        "explicit_rows": 0,
        "inferred_rows": 0,
        "note": "Bars show dated rows only. Missing years stay visible instead of being interpolated into the timeline.",
    }
    publication_year_explicit_share = 0.0
    publication_year_inferred_share = 0.0
    if not timeline_df.empty:
        timeline_df["published_year"] = pd.to_numeric(timeline_df["published_year"], errors="coerce").fillna(0).astype(int)
        timeline_df["published_year_source"] = timeline_df.get(
            "published_year_source",
            pd.Series(["unknown"] * len(timeline_df), index=timeline_df.index),
        ).fillna("unknown").astype(str)
        explicit_rows = int(timeline_df["published_year_source"].eq("explicit_date").sum())
        inferred_rows = int((~timeline_df["published_year_source"].isin(["explicit_date", "unknown"])).sum())
        year_groups = timeline_df.groupby("published_year").agg(
            song_count=("title", "size"),
            total_views=("view_count", "sum"),
            avg_views=("view_count", "mean"),
        ).reset_index().sort_values("published_year")
        observed_years = year_groups["published_year"].astype(int).tolist()
        full_years = list(range(observed_years[0], observed_years[-1] + 1)) if observed_years else []
        year_lookup = {
            int(row["published_year"]): {
                "song_count": int(row["song_count"]),
                "total_views": round(float(row["total_views"])),
                "avg_views": round(float(row["avg_views"])),
            }
            for _, row in year_groups.iterrows()
        }
        publication_timeline = {
            "years": full_years,
            "observed_years": observed_years,
            "missing_years": [year for year in full_years if year not in year_lookup],
            "song_counts": [year_lookup.get(year, {}).get("song_count", 0) for year in full_years],
            "total_views": [year_lookup.get(year, {}).get("total_views", 0) for year in full_years],
            "avg_views": [year_lookup[year]["avg_views"] if year in year_lookup else None for year in full_years],
            "explicit_rows": explicit_rows,
            "inferred_rows": inferred_rows,
            "note": "Bars show dated rows only. Blank line segments mean the current public corpus does not expose a usable year for that point.",
        }
        publication_year_explicit_share = round(float(explicit_rows) / len(edf), 3) if len(edf) else 0.0
        publication_year_inferred_share = round(float(inferred_rows) / len(edf), 3) if len(edf) else 0.0
    publication_year_coverage = round(float(len(timeline_df)) / len(edf), 3) if len(edf) else 0.0

    duration_lookup = {
        "short_under_3min": "< 3 min",
        "medium_3to4min": "3–4 min",
        "long_over_4min": "> 4 min",
    }
    best_duration_key = max(duration_bias, key=lambda k: duration_bias[k]["avg_views"]) if duration_bias else "medium_3to4min"
    best_genre_row = max(classified_genre_breakdown, key=lambda row: row["classified_view_share"], default={})
    best_genre = str(best_genre_row.get("genre", "Unknown"))
    best_duration_label = duration_lookup.get(best_duration_key, "3–4 min")
    latest_year = publication_timeline["years"][-1] if publication_timeline["years"] else None
    earliest_year = publication_timeline["years"][0] if publication_timeline["years"] else None
    coverage_confidence = round(
        (
            gender_known_share
            + classified_genre_share
            + language_known_share
            + publication_year_coverage
        ) / 4.0,
        3,
    )
    language_breadth = round(
        _clamp01(language_bias.get("n_languages", 0) / 8.0) * (1.0 - language_bias.get("english_share", 0)),
        3,
    )
    concentration_relief = round(1.0 - top10_share, 3)
    vp_score = _clamp01(1.0 - abs(1.0 - min(views_parity, 2.0)))
    overall_score = (
        gender_parity * 0.2
        + vp_score * 0.16
        + classified_genre_diversity * 0.18
        + concentration_relief * 0.16
        + language_breadth * 0.1
        + coverage_confidence * 0.2
    )
    overall_bias_grade = letter_grade(overall_score)

    # --- Summary bias scores ---
    bias_scores = {
        "gender_parity": gender_parity,
        "views_parity": views_parity,
        "genre_diversity": classified_genre_diversity,
        "genre_diversity_all": round(1.0 - genre_gini, 3),
        "coverage_confidence": coverage_confidence,
        "known_genre_share": classified_genre_share,
        "language_breadth": language_breadth,
        "collab_rate": round(collab_count / len(analysis_df), 3),
        "concentration_top5": top5_share,
        "publication_year_coverage": publication_year_coverage,
    }

    role_perspectives = {
        "artist": {
            "title": "Artist lens",
            "summary": (
                f"This is a market-shape read, not a songwriting oracle. In the classified slice, {best_genre} carries the strongest "
                f"share of visible attention, the strongest duration pocket is {best_duration_label}, and collaboration helps most when "
                f"it expands reach without making the track anonymous."
            ),
            "question": (
                "Where does the field still leave room for a release to feel distinct instead of merely legible to an existing machine?"
            ),
            "signals": [
                {"label": "Known-genre leader", "value": best_genre},
                {"label": "Collab view share", "value": f"{collab_view_share * 100:.1f}%"},
                {"label": "Known-genre diversity", "value": f"{classified_genre_diversity:.3f}"},
                {"label": "Top duration band", "value": best_duration_label},
            ],
            "next_moves": [
                {
                    "label": "Study release archetypes",
                    "note": "See the distinct ways tracks reached the field before turning one winner into a universal template.",
                    "tab": "music",
                    "target": "mvArchetypes",
                },
                {
                    "label": "Test a hypothetical upload",
                    "note": "Change duration, packaging, tags, and channel size to see what moves the percentile story.",
                    "tab": "music",
                    "target": "mvWhatIf",
                },
                {
                    "label": "Walk the source rows",
                    "note": "Drop back to the songs themselves before borrowing a pattern into a real release decision.",
                    "tab": "music",
                    "target": "mvSongsExplorer",
                },
            ],
            "takeaway": (
                "The practical question is not which genre is supposedly 'best.' It is whether your release shape can still find oxygen once "
                "attention narrows around a few familiar patterns."
            ),
        },
        "consumer": {
            "title": "Consumer lens",
            "summary": (
                f"Listeners are moving through a field that is both concentrated and partially labeled. The visible publication window spans "
                f"{earliest_year} to {latest_year}, but only {publication_year_coverage * 100:.0f}% of rows carry public year data, which "
                f"means breadth has to be read with some caution."
            ),
            "question": (
                "Is this field genuinely broad, or does it only feel broad because the same corridor keeps repainting itself in new colors?"
            ),
            "signals": [
                {"label": "Languages detected", "value": str(language_bias.get("n_languages", 0))},
                {"label": "English share", "value": f"{language_bias.get('english_share', 0) * 100:.1f}%"},
                {"label": "Known-genre coverage", "value": f"{classified_genre_share * 100:.0f}%"},
                {"label": "Publication span", "value": f"{earliest_year or '—'}–{latest_year or '—'}"},
            ],
            "next_moves": [
                {
                    "label": "Trace the tag universe",
                    "note": "See whether discovery is wide or still circling inside a tight tag neighborhood.",
                    "tab": "music",
                    "target": "mvNetwork",
                },
                {
                    "label": "Read the bias surface",
                    "note": "Check who gets the front row once language, genre, and collaboration are counted together.",
                    "tab": "music",
                    "target": "mvBias",
                },
                {
                    "label": "Inspect the public rows",
                    "note": "Stay close to the songs when the discovery story starts sounding too polished.",
                    "tab": "music",
                    "target": "mvSongsExplorer",
                },
            ],
            "takeaway": (
                "A healthy discovery system should feel broader than its hit list. If the surface feels repetitive, the numbers suggest you may not be imagining it."
            ),
        },
        "business": {
            "title": "Business lens",
            "summary": (
                f"Attention remains narrow enough that a small set of channels can still steer the visible market. The top 5 hold "
                f"{top5_share * 100:.1f}% of views and the top 10 hold {top10_share * 100:.1f}%, which is useful if you need to separate repeatable "
                f"distribution logic from one-off mythology."
            ),
            "question": (
                "Which signals still move the market after inherited scale is discounted, and which ones only look strong because the room was preloaded?"
            ),
            "signals": [
                {"label": "Top 5 concentration", "value": f"{top5_share * 100:.1f}%"},
                {"label": "Coverage confidence", "value": f"{coverage_confidence * 100:.0f}%"},
                {"label": "Views parity", "value": f"{views_parity:.2f}x"},
            ],
            "next_moves": [
                {
                    "label": "Pressure-test predictability",
                    "note": "Separate controllable lift from folklore by checking what the ensemble can explain.",
                    "tab": "music",
                    "target": "mvPredictability",
                },
                {
                    "label": "Inspect raw vs partial signals",
                    "note": "See which correlations survive after channel size stops dominating the picture.",
                    "tab": "music",
                    "target": "mvCorrelation",
                },
                {
                    "label": "Read the cultural field",
                    "note": "Move into corridor balance, inheritance pressure, and authenticity posture before productizing the conclusion.",
                    "tab": "music",
                    "target": "mvSongsExplorer",
                },
            ],
            "takeaway": (
                "The value is not 'which song went viral.' It is which conditions keep narrowing or opening the market across multiple cohorts."
            ),
        },
        "research": {
            "title": "Research lens",
            "summary": (
                f"The useful question is not whether a pattern exists somewhere, but whether it survives classification gaps, coverage limits, and cohort changes. "
                f"This lane is strongest when it keeps the leaderboard separate from the broader structural context instead of pretending they are the same thing."
            ),
            "question": (
                "Which claims shrink under coverage pressure, and which ones stay sharp enough to survive disagreement?"
            ),
            "signals": [
                {"label": "Genre Gini", "value": f"{genre_gini:.3f}"},
                {"label": "Coverage confidence", "value": f"{coverage_confidence * 100:.0f}%"},
                {"label": "Observed years", "value": f"{len(publication_timeline.get('observed_years', []))}"},
            ],
            "next_moves": [
                {
                    "label": "Audit the dated field",
                    "note": "Check timeline gaps, known-year share, and whether a temporal story is carrying more certainty than the rows allow.",
                    "tab": "music",
                    "target": "mvBias",
                },
                {
                    "label": "Inspect the row layer",
                    "note": "Keep the conclusion close to the source rows instead of repeating an abstracted summary.",
                    "tab": "music",
                    "target": "mvSongsExplorer",
                },
                {
                    "label": "Open the methods surface",
                    "note": "Cross-check assumptions, quality gates, and contract posture before treating the output as settled.",
                    "tab": "learn",
                    "target": "learnDataSystem",
                },
            ],
            "takeaway": (
                "The method earns trust when the story gets smaller where coverage is weak, and sharper where multiple checks agree."
            ),
        },
    }

    interpretation = (
        f"Analysing {enriched_stats['total_songs']} public songs across multiple datasets. "
        f"Known-gender coverage is {gender_known_share * 100:.0f}% and known-genre coverage is {classified_genre_share * 100:.0f}%, so the equity read should be treated as directional rather than total. "
        f"Within the labeled subset, gender parity is {gender_parity:.2f} and female artists average {f_avg:,.0f} views/song versus {m_avg:,.0f} for male artists (ratio {views_parity:.2f}). "
        f"Genre concentration is high overall (Gini {genre_gini:.3f}), while the classified-only genre diversity reads {classified_genre_diversity:.3f}. "
        f"The top 5 channels still control {top5_share * 100:.1f}% of all views."
    )

    return {
        "gender": {
            "counts": gender_counts,
            "view_share": gender_view_share,
            "avg_views_by_gender": avg_views_by_gender,
            "gender_parity": gender_parity,
            "views_parity": views_parity,
            "female_ratio": round(female_ratio, 3),
            "known_share": gender_known_share,
        },
        "genres": {
            "counts": genre_counts_dict,
            "views": {k: round(v) for k, v in genre_views_dict.items()},
            "gini": genre_gini,
        },
        "genre_breakdown": genre_breakdown,
        "classified_genres": {
            "share_of_songs": classified_genre_share,
            "share_of_views": classified_view_share,
            "gini": classified_genre_gini,
            "diversity": classified_genre_diversity,
            "breakdown": classified_genre_breakdown,
        },
        "collaboration": {
            "collab_count": collab_count,
            "solo_count": int(len(analysis_df) - collab_count),
            "collab_view_share": collab_view_share,
        },
        "duration_bias": duration_bias,
        "official_bias": official_bias,
        "concentration": {
            "top5_share": top5_share,
            "top10_share": top10_share,
            "bottom50_share": bottom50_share,
        },
        "language_bias": language_bias,
        "coverage": {
            "gender_known_share": gender_known_share,
            "genre_known_share": classified_genre_share,
            "language_known_share": language_known_share,
            "publication_year_share": publication_year_coverage,
            "publication_year_explicit_share": publication_year_explicit_share,
            "publication_year_inferred_share": publication_year_inferred_share,
            "confidence": coverage_confidence,
        },
        "engagement_bias": engagement_bias,
        "country_bias": country_bias,
        "publication_timeline": publication_timeline,
        "enriched_stats": enriched_stats,
        "bias_scores": bias_scores,
        "overall_grade": overall_bias_grade,
        "role_perspectives": role_perspectives,
        "interpretation": interpretation,
    }


def _music_tokens(value: object) -> List[str]:
    if value is None:
        return []
    tokens = re.findall(r"[A-Za-z0-9']+", str(value).lower())
    return [t for t in tokens if len(t) > 1]


def resonance_analysis(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """Public proxy for media "resonance" and attention oscillation.

    This is intentionally grounded in observable song metadata rather than any
    hidden hardware claim: title/tag repetition, duration fit, channel reach,
    release timing, and concentration all leave a visible shape that we can
    measure and render.
    """
    analysis_df = load_enriched_dataset().copy() if df is None else df.copy()
    if analysis_df.empty:
        return {
            "scorecard": {
                "oscillation": 0,
                "friction": 0,
                "stability": 0,
                "vitality": 0,
                "communal_carry": 0,
                "novelty_room": 0,
                "wattage_variance_proxy": 0,
                "halt_window_ms": 0,
            },
            "top_tracks": [],
            "genre_pressure": [],
            "year_profile": {"years": [], "oscillation": [], "friction": [], "vitality": [], "song_count": []},
            "interpretation": "No songs are available for resonance analysis.",
        }

    working = analysis_df.copy()
    if "tags" not in working.columns:
        working["tags"] = ""
    if "genre" not in working.columns:
        working["genre"] = "Unknown"
    if "published_year" not in working.columns:
        working["published_year"] = 0
    if "channel_follower_count" not in working.columns:
        working["channel_follower_count"] = 0
    proxy = build_public_music_proxy_table(working)
    genre_share = proxy["genre"].value_counts(normalize=True).to_dict() if "genre" in proxy.columns else {}

    resonance_rows = []
    for _, row in proxy.iterrows():
        duration = float(row.get("duration_min", 0.0) or 0.0)
        duration_fit = float(row.get("duration_fit", 0.0) or 0.0)
        title_repeat = float(row.get("title_echo", 0.0) or 0.0)
        attention_fit = float(row.get("views_norm", 0.0) or 0.0)
        reach_fit = float(row.get("reach_norm", 0.0) or 0.0)
        engagement_fit = float(row.get("engagement_norm", 0.0) or 0.0)
        recency_fit = float(row.get("recency_norm", 0.0) or 0.0)
        somatic_pull = float(row.get("somatic_pull", 0.0) or 0.0)
        communal_carry = float(row.get("communal_carry", 0.0) or 0.0)
        novelty_room = float(row.get("novelty_room", 0.0) or 0.0)
        inheritance_pressure = float(row.get("inheritance_pressure", 0.0) or 0.0)
        vitality_score = float(row.get("vitality_score", 0.0) or 0.0)
        genre = str(row.get("genre", "Unknown"))
        genre_pressure = float(genre_share.get(genre, 0.0))
        published_year = int(row.get("published_year", 0) or 0)
        oscillation = float(np.clip(
            0.28 * somatic_pull +
            0.22 * attention_fit +
            0.18 * title_repeat +
            0.18 * communal_carry +
            0.14 * recency_fit,
            0.0, 1.0
        ))
        friction = float(np.clip(
            0.34 * inheritance_pressure +
            0.24 * (1.0 - novelty_room) +
            0.22 * genre_pressure +
            0.20 * (1.0 - duration_fit),
            0.0, 1.0
        ))
        stability = float(np.clip(
            1.0 - np.std([duration_fit, somatic_pull, communal_carry, novelty_room, title_repeat]),
            0.0, 1.0
        ))
        variance_proxy = float(np.std([duration_fit, attention_fit, reach_fit, title_repeat, vitality_score]))
        resonance_score = float(np.clip(
            0.42 * somatic_pull +
            0.18 * communal_carry +
            0.18 * attention_fit +
            0.12 * (1.0 - friction) +
            0.10 * stability,
            0.0, 1.0
        ))
        signature = vitality_signature_labels(row)
        resonance_rows.append({
            "title": str(row.get("title", "")),
            "channel": str(row.get("channel", "")),
            "genre": genre,
            "language": str(row.get("detected_language", "Unknown")),
            "published_year": published_year,
            "view_count": float(row.get("view_count", 0.0) or 0.0),
            "duration_min": duration,
            "oscillation": round(oscillation, 3),
            "friction": round(friction, 3),
            "stability": round(stability, 3),
            "somatic_pull": round(somatic_pull, 3),
            "communal_carry": round(communal_carry, 3),
            "novelty_room": round(novelty_room, 3),
            "inheritance_pressure": round(inheritance_pressure, 3),
            "vitality_score": round(vitality_score, 3),
            "cultural_corridor": str(row.get("cultural_corridor", "Unlabeled corridor")),
            "wattage_variance_proxy": round(variance_proxy, 3),
            "resonance_score": round(resonance_score, 3),
            "signature": signature,
            "signals": [
                f"duration fit {duration_fit:.2f}",
                f"engagement fit {engagement_fit:.2f}",
                f"novelty room {novelty_room:.2f}",
                f"title/tag echo {title_repeat:.2f}",
            ],
        })

    resonance_rows.sort(key=lambda r: r["resonance_score"], reverse=True)
    top_tracks = resonance_rows[:8]
    genre_pressure = []
    for genre, group in proxy.groupby("genre"):
        local_years = pd.to_numeric(group["published_year"], errors="coerce").fillna(0).astype(int)
        year_density = float((local_years > 0).mean()) if len(group) else 0.0
        resonance_pressure = float(np.mean([r["resonance_score"] for r in resonance_rows if r["genre"] == genre])) if genre else 0.0
        genre_pressure.append({
            "genre": str(genre),
            "song_count": int(len(group)),
            "view_share": round(float(group["view_count"].sum()) / float(proxy["view_count"].sum()), 4) if float(proxy["view_count"].sum()) > 0 else 0.0,
            "avg_resonance": round(resonance_pressure, 3),
            "avg_vitality": round(float(group["vitality_score"].mean()), 3),
            "stability": round(max(0.0, min(1.0, year_density + 0.15 * (1.0 - resonance_pressure))), 3),
        })
    genre_pressure.sort(key=lambda r: r["avg_resonance"], reverse=True)

    years_group = pd.DataFrame(resonance_rows)
    years_group = years_group[years_group["published_year"].astype(int) > 0].copy()
    if not years_group.empty:
        years_group["published_year"] = pd.to_numeric(years_group["published_year"], errors="coerce").fillna(0).astype(int)
        year_stats = years_group.groupby("published_year").agg(
            oscillation=("oscillation", "mean"),
            friction=("friction", "mean"),
            vitality=("vitality_score", "mean"),
            song_count=("title", "count"),
        ).reset_index().sort_values("published_year")
        year_profile = {
            "years": year_stats["published_year"].astype(int).tolist(),
            "oscillation": [round(float(v), 3) for v in year_stats["oscillation"].tolist()],
            "friction": [round(float(v), 3) for v in year_stats["friction"].tolist()],
            "vitality": [round(float(v), 3) for v in year_stats["vitality"].tolist()],
            "song_count": [int(v) for v in year_stats["song_count"].tolist()],
        }
    else:
        year_profile = {"years": [], "oscillation": [], "friction": [], "vitality": [], "song_count": []}

    avg_oscillation = float(np.mean([r["oscillation"] for r in resonance_rows])) if resonance_rows else 0.0
    avg_friction = float(np.mean([r["friction"] for r in resonance_rows])) if resonance_rows else 0.0
    avg_stability = float(np.mean([r["stability"] for r in resonance_rows])) if resonance_rows else 0.0
    avg_vitality = float(np.mean([r["vitality_score"] for r in resonance_rows])) if resonance_rows else 0.0
    avg_communal = float(np.mean([r["communal_carry"] for r in resonance_rows])) if resonance_rows else 0.0
    avg_novelty = float(np.mean([r["novelty_room"] for r in resonance_rows])) if resonance_rows else 0.0
    avg_variance = float(np.mean([r["wattage_variance_proxy"] for r in resonance_rows])) if resonance_rows else 0.0
    halt_window_ms = int(round(4 + (avg_oscillation + avg_friction) * 12))
    strongest = top_tracks[0] if top_tracks else {}
    interpretation = (
        f"Resonance is highest where public bodily pull, communal carry, and attention fit line up without collapsing entirely into inherited scale. "
        f"{strongest.get('title', 'The lead track')} is the clearest proxy for a tight repeat-attention loop, while "
        f"{strongest.get('cultural_corridor', strongest.get('genre', 'the dominant corridor'))} carries the strongest visible pressure."
    )

    return {
        "scorecard": {
            "oscillation": round(avg_oscillation, 3),
            "friction": round(avg_friction, 3),
            "stability": round(avg_stability, 3),
            "vitality": round(avg_vitality, 3),
            "communal_carry": round(avg_communal, 3),
            "novelty_room": round(avg_novelty, 3),
            "wattage_variance_proxy": round(avg_variance, 3),
            "halt_window_ms": halt_window_ms,
        },
        "top_tracks": top_tracks,
        "genre_pressure": genre_pressure,
        "year_profile": year_profile,
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
    # Enriched stats
    try:
        enriched = load_enriched_dataset()
        enriched_count = int(len(enriched))
        enriched_sources = enriched["source"].value_counts().to_dict()
    except Exception:
        enriched_count = int(len(df))
        enriched_sources = {"primary_top100": int(len(df))}
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
        "data_source": "Real YouTube data - top music videos, 2025-2026",
        "enriched_song_count": enriched_count,
        "enriched_sources": enriched_sources,
    }


def songs_table(
    df: Optional[pd.DataFrame] = None, limit: int = 700, sort_by: str = "view_count"
) -> List[Dict[str, object]]:
    df = load_enriched_dataset() if df is None else df
    proxy = build_public_music_proxy_table(df)
    sort_col = sort_by if sort_by in proxy.columns else "view_count"
    ordered = proxy.sort_values(sort_col, ascending=False).head(limit)
    records = []
    for _, r in ordered.iterrows():
        row = r.to_dict()
        records.append(
            {
                "title": str(r["title"]),
                "artist": str(r.get("artist") or r["channel"]),
                "channel": str(r["channel"]),
                "view_count": float(r["view_count"]),
                "duration_min": round(float(r["duration_min"]), 2),
                "channel_follower_count": float(r["channel_follower_count"]),
                "virality_coefficient": round(float(r["virality_coefficient"]), 3),
                "tag_count": int(r["tag_count"]),
                "is_official": int(r["is_official"]),
                "source": str(r.get("source", "primary_top100")),
                "published_year": int(r.get("published_year", 0) or 0),
                "published_year_source": str(r.get("published_year_source", "unknown")),
                "detected_language": str(r.get("detected_language", "Unknown")),
                "genre": str(r.get("genre", "Unknown")),
                "cultural_corridor": str(r.get("cultural_corridor", "Unlabeled corridor")),
                "somatic_pull": round(float(r.get("somatic_pull", 0.0) or 0.0), 4),
                "communal_carry": round(float(r.get("communal_carry", 0.0) or 0.0), 4),
                "novelty_room": round(float(r.get("novelty_room", 0.0) or 0.0), 4),
                "inheritance_pressure": round(float(r.get("inheritance_pressure", 0.0) or 0.0), 4),
                "vitality_score": round(float(r.get("vitality_score", 0.0) or 0.0), 4),
                "distribution_fingerprint": round(float(r.get("distribution_fingerprint", 0.0) or 0.0), 4),
                "organic_signature": round(float(r.get("organic_signature", 0.0) or 0.0), 4),
                "engineered_signature": round(float(r.get("engineered_signature", 0.0) or 0.0), 4),
                "velocity_anomaly": round(float(r.get("velocity_anomaly", 0.0) or 0.0), 4),
                "longevity_potential": round(float(r.get("longevity_potential", 0.0) or 0.0), 4),
                "authenticity_index": round(float(r.get("authenticity_index", 0.0) or 0.0), 4),
                "signature": vitality_signature_labels(row),
            }
        )
    return records


def full_report(df: Optional[pd.DataFrame] = None) -> Dict[str, object]:
    """Everything in one payload - used to bake the static site."""
    df = load_dataset() if df is None else df
    enriched = load_enriched_dataset()
    bias = bias_analysis(enriched)
    resonance = resonance_analysis(enriched)
    decision_lab = build_decision_lab(enriched)
    return {
        "overview": overview(df),
        "power_law": power_law_analysis(df),
        "inequality": inequality_analysis(df),
        "correlations": correlation_analysis(df),
        "archetypes": archetype_analysis(df),
        "network": network_analysis(),
        "predictability": predictability_analysis(df),
        "resonance": resonance,
        "songs": songs_table(enriched, limit=int(len(enriched))),
        "bias": bias,
        "quality": quality_report(df),
        "decision_lab": decision_lab,
        "living_media": build_living_media_surface(enriched, bias=bias, resonance=resonance, decision_lab=decision_lab),
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
