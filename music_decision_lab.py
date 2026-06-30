#!/usr/bin/env python3
"""
Decision-grade analysis for the public music lane.

This module answers the next layer of questions after the summary charts:

- Which shifts are actually moving over time?
- Which release-shape differences still matter once the rows are split?
- How much of the resulting story is supported by the public data we have?

It stays inside the repo's public boundary: no hidden infrastructure claims,
only calculations that can be rerun from the committed public corpus.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from advanced_metrics import gini, letter_grade
from music_field_proxies import build_public_music_proxy_table, vitality_signature_labels


CURRENT_YEAR = date.today().year


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_mean(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(pd.to_numeric(series, errors="coerce").dropna().mean() or 0.0)


def _safe_median(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.median())


def _pct(series: pd.Series, predicate) -> float:
    if series.empty:
        return 0.0
    truth = predicate(series)
    return float(np.mean(np.asarray(truth, dtype=float)))


def _detect_collab(title: object) -> bool:
    low = str(title or "").lower()
    indicators = [" ft.", " feat.", " ft ", " feat ", " x ", " & ", " with ", " featuring "]
    return any(indicator in low for indicator in indicators)


def _clean_language(series: pd.Series) -> pd.Series:
    return (
        series.fillna("Unknown")
        .astype(str)
        .replace({"": "Unknown"})
    )


def _top_channel_share(df: pd.DataFrame, k: int = 10) -> float:
    if df.empty or "view_count" not in df.columns or "channel" not in df.columns:
        return 0.0
    total_views = float(pd.to_numeric(df["view_count"], errors="coerce").fillna(0).sum())
    if total_views <= 0:
        return 0.0
    shares = (
        df.assign(_views=pd.to_numeric(df["view_count"], errors="coerce").fillna(0))
        .groupby("channel")["_views"]
        .sum()
        .sort_values(ascending=False)
    )
    return float(shares.head(k).sum() / total_views)


def _year_windows(df: pd.DataFrame) -> Tuple[str, pd.DataFrame, str, pd.DataFrame]:
    dated = df.copy()
    dated["published_year"] = pd.to_numeric(dated.get("published_year"), errors="coerce").fillna(0).astype(int)
    dated = dated[dated["published_year"] > 0].copy()
    if dated.empty:
        return "Undated field", df.iloc[0:0].copy(), "Undated field", df.iloc[0:0].copy()

    years = sorted(dated["published_year"].unique().tolist())
    midpoint = len(years) // 2
    early_years = years[: midpoint or 1]
    late_years = years[midpoint:] if midpoint else years
    if not late_years:
        late_years = years[-1:]

    early = dated[dated["published_year"].isin(early_years)].copy()
    late = dated[dated["published_year"].isin(late_years)].copy()
    return (
        f"{early_years[0]}–{early_years[-1]}",
        early,
        f"{late_years[0]}–{late_years[-1]}",
        late,
    )


def _metric_snapshot(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return {
            "official_share": 0.0,
            "collab_share": 0.0,
            "english_share": 0.0,
            "median_duration": 0.0,
            "median_virality": 0.0,
            "top10_channel_share": 0.0,
            "median_tag_count": 0.0,
        }

    languages = _clean_language(df.get("detected_language", pd.Series(["Unknown"] * len(df), index=df.index)))
    known_languages = languages[~languages.isin(["Unknown"])]
    english_share = float((known_languages == "English").mean()) if len(known_languages) else 0.0

    return {
        "official_share": _safe_mean(df.get("is_official", pd.Series([], dtype=float))),
        "collab_share": float(df["title"].map(_detect_collab).mean()) if "title" in df.columns and len(df) else 0.0,
        "english_share": english_share,
        "median_duration": _safe_median(df.get("duration_min", pd.Series([], dtype=float))),
        "median_virality": _safe_median(df.get("virality_coefficient", pd.Series([], dtype=float))),
        "top10_channel_share": _top_channel_share(df, k=10),
        "median_tag_count": _safe_median(df.get("tag_count", pd.Series([], dtype=float))),
    }


def _relative_delta(before: float, after: float) -> float:
    if abs(before) < 1e-9:
        return after
    return (after - before) / abs(before)


def _drift_highlights(df: pd.DataFrame) -> Dict[str, object]:
    early_label, early_df, late_label, late_df = _year_windows(df)
    early = _metric_snapshot(early_df)
    late = _metric_snapshot(late_df)

    metric_docs = {
        "official_share": {
            "label": "Official-video share",
            "unit": "pct",
            "why": "Useful for separating label-backed distribution from field-native breakout behavior.",
        },
        "collab_share": {
            "label": "Collaboration share",
            "unit": "pct",
            "why": "Shows whether the field is opening through partnerships or closing around solo incumbency.",
        },
        "english_share": {
            "label": "English-language share",
            "unit": "pct",
            "why": "A rising English share usually means discovery is narrowing around one language corridor.",
        },
        "median_duration": {
            "label": "Median duration",
            "unit": "minutes",
            "why": "Track length often reveals whether releases are being tuned for attention windows.",
        },
        "median_virality": {
            "label": "Median virality",
            "unit": "ratio",
            "why": "Views-per-subscriber indicates how far songs travel beyond their built-in audience.",
        },
        "top10_channel_share": {
            "label": "Top-10 channel concentration",
            "unit": "pct",
            "why": "A narrower winner ring can make the market feel active while staying structurally closed.",
        },
        "median_tag_count": {
            "label": "Median tag count",
            "unit": "count",
            "why": "This helps show whether packaging discipline is getting more aggressive as competition tightens.",
        },
    }

    rows: List[dict] = []
    for key, meta in metric_docs.items():
        before = float(early.get(key, 0.0))
        after = float(late.get(key, 0.0))
        delta = after - before
        relative = _relative_delta(before, after)
        if meta["unit"] == "pct":
            before_label = f"{before * 100:.1f}%"
            after_label = f"{after * 100:.1f}%"
            delta_label = f"{delta * 100:+.1f} pts"
            salience = abs(delta) * 100
        elif meta["unit"] == "minutes":
            before_label = f"{before:.2f} min"
            after_label = f"{after:.2f} min"
            delta_label = f"{delta:+.2f} min"
            salience = abs(delta)
        elif meta["unit"] == "ratio":
            before_label = f"{before:.2f}x"
            after_label = f"{after:.2f}x"
            delta_label = f"{delta:+.2f}x"
            salience = abs(relative)
        else:
            before_label = f"{before:.1f}"
            after_label = f"{after:.1f}"
            delta_label = f"{delta:+.1f}"
            salience = abs(relative)

        rows.append(
            {
                "metric": key,
                "label": meta["label"],
                "before": round(before, 4),
                "after": round(after, 4),
                "before_label": before_label,
                "after_label": after_label,
                "delta": round(delta, 4),
                "delta_label": delta_label,
                "relative_change": round(relative, 4),
                "why_it_matters": meta["why"],
                "salience": round(float(salience), 4),
            }
        )

    rows.sort(key=lambda row: row["salience"], reverse=True)
    top = rows[0] if rows else None
    narrative = (
        f"The sharpest visible shift from {early_label} to {late_label} is {top['label'].lower()} "
        f"moving from {top['before_label']} to {top['after_label']}."
        if top
        else "There is not enough dated public data yet to describe a meaningful cohort shift."
    )

    return {
        "windows": {
            "earlier": {"label": early_label, "rows": int(len(early_df))},
            "later": {"label": late_label, "rows": int(len(late_df))},
        },
        "highlights": rows[:6],
        "narrative": narrative,
    }


def _cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    comparisons = np.subtract.outer(a, b)
    positive = float((comparisons > 0).sum())
    negative = float((comparisons < 0).sum())
    return (positive - negative) / float(a.size * b.size)


def _bootstrap_ratio_ci(a: np.ndarray, b: np.ndarray, seed: int = 42, n_boot: int = 300) -> Tuple[float, float]:
    if a.size == 0 or b.size == 0:
        return 1.0, 1.0
    rng = np.random.default_rng(seed)
    ratios = []
    for _ in range(n_boot):
        sa = a[rng.integers(0, a.size, a.size)]
        sb = b[rng.integers(0, b.size, b.size)]
        med_a = float(np.median(sa))
        med_b = float(np.median(sb))
        ratios.append(med_a / med_b if med_b else 1.0)
    low, high = np.quantile(np.asarray(ratios, dtype=float), [0.025, 0.975])
    return float(low), float(high)


def _experiment_card(label: str, left_name: str, right_name: str, left_df: pd.DataFrame, right_df: pd.DataFrame, why: str) -> dict:
    left_views = pd.to_numeric(left_df.get("view_count"), errors="coerce").dropna().to_numpy(dtype=float)
    right_views = pd.to_numeric(right_df.get("view_count"), errors="coerce").dropna().to_numpy(dtype=float)
    left_median = float(np.median(left_views)) if left_views.size else 0.0
    right_median = float(np.median(right_views)) if right_views.size else 0.0
    ratio = left_median / right_median if right_median else 1.0
    ci_low, ci_high = _bootstrap_ratio_ci(left_views, right_views)
    cliffs = _cliffs_delta(left_views, right_views)
    support = min(left_views.size, right_views.size)
    confidence = _clamp01((min(support, 120) / 120.0) * (1.0 - min(abs(cliffs), 1.0) * 0.15 + 0.15))
    return {
        "label": label,
        "left": left_name,
        "right": right_name,
        "left_count": int(left_views.size),
        "right_count": int(right_views.size),
        "left_median_views": round(left_median),
        "right_median_views": round(right_median),
        "median_uplift_ratio": round(ratio, 3),
        "median_uplift_label": f"{ratio:.2f}x",
        "ratio_ci": {"low": round(ci_low, 3), "high": round(ci_high, 3)},
        "cliffs_delta": round(float(cliffs), 3),
        "confidence": round(confidence, 3),
        "why_it_matters": why,
        "takeaway": (
            f"{left_name} currently outperforms {right_name} at the median by {ratio:.2f}x."
            if ratio >= 1.0
            else f"{right_name} currently outperforms {left_name} at the median by {1.0 / max(ratio, 1e-9):.2f}x."
        ),
    }


def _experiment_suite(df: pd.DataFrame) -> Dict[str, object]:
    title_words = pd.to_numeric(df.get("title_word_count"), errors="coerce").fillna(0)
    tag_count = pd.to_numeric(df.get("tag_count"), errors="coerce").fillna(0)
    followers = pd.to_numeric(df.get("channel_follower_count"), errors="coerce").fillna(0)
    duration = pd.to_numeric(df.get("duration_min"), errors="coerce").fillna(0)
    collab_mask = df["title"].map(_detect_collab) if "title" in df.columns else pd.Series(False, index=df.index)
    official_mask = pd.to_numeric(df.get("is_official"), errors="coerce").fillna(0).astype(int).eq(1)

    experiments = [
        _experiment_card(
            "Official release advantage",
            "Official uploads",
            "Unofficial uploads",
            df[official_mask],
            df[~official_mask],
            "Useful for separating raw song demand from packaging and distribution leverage.",
        ),
        _experiment_card(
            "Collaboration opening",
            "Collaborations",
            "Solo-billed releases",
            df[collab_mask],
            df[~collab_mask],
            "Shows whether partnership is still acting as a reach multiplier in the public field.",
        ),
        _experiment_card(
            "Radio-window duration fit",
            "2.5–4.0 minute tracks",
            "Outside the radio window",
            df[(duration >= 2.5) & (duration <= 4.0)],
            df[(duration < 2.5) | (duration > 4.0)],
            "Tracks whether the market is rewarding familiar attention windows over everything else.",
        ),
        _experiment_card(
            "Concise title efficiency",
            "Titles with 4 words or fewer",
            "Titles with more than 4 words",
            df[title_words <= 4],
            df[title_words > 4],
            "A packaging test for whether brevity is still being rewarded more than detail.",
        ),
        _experiment_card(
            "Tag-density packaging",
            "Top-quartile tag density",
            "Lower tag-density uploads",
            df[tag_count >= float(tag_count.quantile(0.75))],
            df[tag_count < float(tag_count.quantile(0.75))],
            "Helps show whether metadata discipline is simply descriptive or materially changing reach.",
        ),
        _experiment_card(
            "Reach-base amplification",
            "Top-quartile channel reach",
            "Lower-reach channels",
            df[followers >= float(followers.quantile(0.75))],
            df[followers < float(followers.quantile(0.75))],
            "Useful because a high-visibility field can still be mostly inherited rather than newly earned.",
        ),
    ]

    experiments.sort(
        key=lambda card: (abs(np.log(max(card["median_uplift_ratio"], 1e-9))), card["confidence"]),
        reverse=True,
    )

    return {
        "cards": experiments,
        "strongest": experiments[0] if experiments else None,
    }


def _trust_surface(df: pd.DataFrame) -> Dict[str, object]:
    total = len(df)
    if total == 0:
        return {
            "score": 0.0,
            "grade": "F",
            "summary": "No public music rows are available, so no trust posture can be calculated.",
            "signals": [],
        }

    year_share = float(pd.to_numeric(df.get("published_year"), errors="coerce").fillna(0).astype(int).gt(0).mean())
    known_language_share = float((~_clean_language(df.get("detected_language", pd.Series(["Unknown"] * total))).isin(["Unknown"])).mean()) if total else 0.0
    follower_share = float(pd.to_numeric(df.get("channel_follower_count"), errors="coerce").notna().mean())
    likes_share = float(pd.to_numeric(df.get("likes"), errors="coerce").notna().mean()) if "likes" in df.columns else 0.0
    source_distribution = df.get("source", pd.Series([], dtype=str)).astype(str).value_counts(normalize=True)
    source_balance = 1.0 - float(gini(source_distribution.tolist())) if len(source_distribution) else 0.0
    recency = 0.0
    if "published_year" in df.columns:
        years = pd.to_numeric(df["published_year"], errors="coerce").fillna(0).astype(int)
        latest = int(years.max()) if len(years) else 0
        if latest > 0:
            recency = _clamp01(1.0 - max(CURRENT_YEAR - latest, 0) / 8.0)

    score = round(
        (
            year_share * 0.26
            + known_language_share * 0.18
            + follower_share * 0.18
            + likes_share * 0.12
            + source_balance * 0.14
            + recency * 0.12
        ),
        3,
    )

    return {
        "score": score,
        "grade": letter_grade(score),
        "summary": (
            f"This public field is strongest when read as a multi-source attention study, not as a complete census. "
            f"Year coverage is {year_share * 100:.0f}%, source balance reads {source_balance:.2f}, and the freshest visible year is weighted into the trust score."
        ),
        "signals": [
            {"label": "Year coverage", "value": f"{year_share * 100:.0f}%", "note": "How much of the corpus can support time-based claims."},
            {"label": "Language labels", "value": f"{known_language_share * 100:.0f}%", "note": "How much of the corpus can support language-bias claims."},
            {"label": "Subscriber coverage", "value": f"{follower_share * 100:.0f}%", "note": "How much of the corpus can support reach-adjusted comparisons."},
            {"label": "Source balance", "value": f"{source_balance:.2f}", "note": "Higher means the public corpus is less dominated by one cohort source."},
            {"label": "Freshness posture", "value": f"{recency:.2f}", "note": "A light recency signal derived from the newest visible publication year."},
        ],
        "questions": [
            "Would this claim still hold if the unlabeled rows were removed?",
            "Are we looking at a platform effect, a packaging effect, or only a scale effect?",
            "Is the visible shift durable across time, or just concentrated in one recent slice?",
        ],
    }


def _embodied_track_reading(row: dict) -> str:
    somatic_pull = float(row.get("somatic_pull", 0.0) or 0.0)
    novelty_room = float(row.get("novelty_room", 0.0) or 0.0)
    communal_carry = float(row.get("communal_carry", 0.0) or 0.0)
    inheritance_pressure = float(row.get("inheritance_pressure", 0.0) or 0.0)

    body_read = (
        "a strong bodily invitation"
        if somatic_pull >= 0.68
        else "a measured bodily pull"
        if somatic_pull >= 0.52
        else "a cooler bodily profile"
    )
    novelty_read = (
        "room beyond inherited formulas"
        if novelty_room >= 0.6
        else "some open room"
        if novelty_room >= 0.46
        else "a familiar corridor bias"
    )
    community_read = (
        "community-led carry"
        if communal_carry >= 0.58
        else "mixed social carry"
        if communal_carry >= 0.42
        else "less visible community lift"
    )
    inheritance_read = (
        "The song still leans heavily on inherited scale."
        if inheritance_pressure >= 0.66
        else "The song is not relying entirely on inherited scale."
    )
    return (
        f"{row.get('title', 'This track')} shows {body_read}, {novelty_read}, and {community_read}. "
        f"{inheritance_read}"
    )


def _corridor_reading(row: pd.Series) -> str:
    view_share = float(row.get("view_share", 0.0) or 0.0)
    vitality = float(row.get("avg_vitality", 0.0) or 0.0)
    novelty = float(row.get("avg_novelty_room", 0.0) or 0.0)
    communal = float(row.get("avg_communal_carry", 0.0) or 0.0)

    if view_share >= 0.18 and novelty < 0.45:
        return "This corridor holds a large share of attention while staying structurally familiar."
    if vitality >= 0.56 and novelty >= 0.52:
        return "This corridor is still generating live pull without depending only on familiar scale."
    if communal >= 0.56:
        return "This corridor reads as community-carried rather than purely distribution-carried."
    return "This corridor is present, but its current reach still looks more mixed than settled."


def _embodied_surface(df: pd.DataFrame) -> Dict[str, object]:
    proxy = build_public_music_proxy_table(df)
    if proxy.empty:
        return {
            "boundary_note": "No public music rows are available, so no embodied proxy surface can be calculated.",
            "headline": "There is not enough public material yet to describe bodily pull, cultural corridors, or vitality proxies.",
            "summary_cards": [],
            "summary_index": {},
            "top_signatures": [],
            "cultural_corridors": [],
            "provocations": [],
        }

    corridor_stats = (
        proxy.groupby("cultural_corridor", dropna=False)
        .agg(
            song_count=("title", "count"),
            total_views=("view_count", "sum"),
            avg_vitality=("vitality_score", "mean"),
            avg_somatic_pull=("somatic_pull", "mean"),
            avg_novelty_room=("novelty_room", "mean"),
            avg_communal_carry=("communal_carry", "mean"),
            avg_inheritance_pressure=("inheritance_pressure", "mean"),
            collab_share=("collaboration_flag", "mean"),
            median_duration=("duration_min", "median"),
        )
        .reset_index()
    )
    total_views = float(proxy["view_count"].sum()) or 1.0
    corridor_stats["view_share"] = corridor_stats["total_views"] / total_views
    corridor_stats["corridor_score"] = (
        corridor_stats["avg_vitality"] * 0.46
        + corridor_stats["avg_novelty_room"] * 0.24
        + corridor_stats["avg_communal_carry"] * 0.18
        + corridor_stats["view_share"] * 0.12
    )
    corridor_stats = corridor_stats.sort_values(["corridor_score", "view_share"], ascending=False)

    corridor_balance = 1.0 - float(gini(corridor_stats["view_share"].tolist())) if len(corridor_stats) else 0.0
    dominant_corridor_share = float(corridor_stats["view_share"].iloc[0]) if len(corridor_stats) else 0.0

    summary_cards = [
        {
            "key": "somatic_pull",
            "label": "Somatic invitation",
            "value": round(float(proxy["somatic_pull"].mean()), 3),
            "value_label": f"{round(float(proxy['somatic_pull'].mean()) * 100):d}/100",
            "note": "Public proxy for repeat-pull built from duration fit, engagement, virality, and title/tag echo.",
        },
        {
            "key": "communal_carry",
            "label": "Communal carry",
            "value": round(float(proxy["communal_carry"].mean()), 3),
            "value_label": f"{round(float(proxy['communal_carry'].mean()) * 100):d}/100",
            "note": "How much the field is being carried by collaboration, engagement, recency, and cross-language circulation.",
        },
        {
            "key": "novelty_room",
            "label": "Novelty room",
            "value": round(float(proxy["novelty_room"].mean()), 3),
            "value_label": f"{round(float(proxy['novelty_room'].mean()) * 100):d}/100",
            "note": "How much room the field leaves for less inherited, less familiar corridors to break through.",
        },
        {
            "key": "inheritance_pressure",
            "label": "Inheritance pressure",
            "value": round(float(proxy["inheritance_pressure"].mean()), 3),
            "value_label": f"{round(float(proxy['inheritance_pressure'].mean()) * 100):d}/100",
            "note": "How heavily the visible market still leans on channel scale, official packaging, and familiar corridors.",
        },
        {
            "key": "vitality_score",
            "label": "Vitality score",
            "value": round(float(proxy["vitality_score"].mean()), 3),
            "value_label": f"{round(float(proxy['vitality_score'].mean()) * 100):d}/100",
            "note": "Composite public proxy for aliveness: bodily pull, novelty room, communal carry, and reduced inheritance pressure.",
        },
        {
            "key": "corridor_balance",
            "label": "Corridor balance",
            "value": round(corridor_balance, 3),
            "value_label": f"{round(corridor_balance * 100):d}/100",
            "note": "Higher means attention is less trapped inside one cultural corridor.",
        },
    ]
    summary_index = {card["key"]: card["value"] for card in summary_cards}

    top_signatures = []
    top_proxy = proxy.sort_values(
        ["vitality_score", "novelty_room", "communal_carry", "view_count"],
        ascending=False,
    ).head(8)
    for _, row in top_proxy.iterrows():
        row_dict = {
            "title": str(row.get("title", "")),
            "channel": str(row.get("channel", "")),
            "genre": str(row.get("genre", "Unknown")),
            "language": str(row.get("detected_language", "Unknown")),
            "published_year": int(row.get("published_year", 0) or 0),
            "cultural_corridor": str(row.get("cultural_corridor", "Unlabeled corridor")),
            "view_count": round(float(row.get("view_count", 0.0) or 0.0)),
            "somatic_pull": round(float(row.get("somatic_pull", 0.0) or 0.0), 3),
            "communal_carry": round(float(row.get("communal_carry", 0.0) or 0.0), 3),
            "novelty_room": round(float(row.get("novelty_room", 0.0) or 0.0), 3),
            "inheritance_pressure": round(float(row.get("inheritance_pressure", 0.0) or 0.0), 3),
            "vitality_score": round(float(row.get("vitality_score", 0.0) or 0.0), 3),
        }
        row_dict["signature"] = vitality_signature_labels(row_dict)
        row_dict["reading"] = _embodied_track_reading(row_dict)
        top_signatures.append(row_dict)

    cultural_corridors = []
    for _, row in corridor_stats.head(6).iterrows():
        corridor = {
            "corridor": str(row.get("cultural_corridor", "Unlabeled corridor")),
            "song_count": int(row.get("song_count", 0) or 0),
            "view_share": round(float(row.get("view_share", 0.0) or 0.0), 4),
            "avg_vitality": round(float(row.get("avg_vitality", 0.0) or 0.0), 3),
            "avg_somatic_pull": round(float(row.get("avg_somatic_pull", 0.0) or 0.0), 3),
            "avg_novelty_room": round(float(row.get("avg_novelty_room", 0.0) or 0.0), 3),
            "avg_communal_carry": round(float(row.get("avg_communal_carry", 0.0) or 0.0), 3),
            "avg_inheritance_pressure": round(float(row.get("avg_inheritance_pressure", 0.0) or 0.0), 3),
            "collab_share": round(float(row.get("collab_share", 0.0) or 0.0), 3),
            "median_duration": round(float(row.get("median_duration", 0.0) or 0.0), 2),
        }
        corridor["reading"] = _corridor_reading(pd.Series(corridor))
        cultural_corridors.append(corridor)

    top_signature = top_signatures[0] if top_signatures else {}
    headline = (
        f"The public field currently rewards {top_signature.get('cultural_corridor', 'its dominant corridor')} "
        f"through a vitality score of {top_signature.get('vitality_score', 0):.2f}, while the largest single corridor still holds "
        f"{dominant_corridor_share * 100:.1f}% of visible views."
    )

    provocations = [
        {
            "title": "Bodily pull is not the same thing as market freedom.",
            "body": (
                f"The field-level somatic invitation proxy sits at {summary_index.get('somatic_pull', 0) * 100:.0f}/100, "
                f"but novelty room is only {summary_index.get('novelty_room', 0) * 100:.0f}/100. Repetition may be rewarded more than exploration."
            ),
        },
        {
            "title": "Cultural circulation should not be mistaken for universality.",
            "body": (
                f"The top corridor still captures {dominant_corridor_share * 100:.1f}% of visible views. "
                "A dominant language or genre lane can look universal while still being structurally narrow."
            ),
        },
        {
            "title": "Community carry matters when scale does not explain the lift.",
            "body": (
                f"Communal carry currently reads {summary_index.get('communal_carry', 0) * 100:.0f}/100. "
                "That is the proxy to watch when a release seems to travel beyond what channel size alone should explain."
            ),
        },
        {
            "title": "The repo still refuses to overclaim.",
            "body": (
                "These are public proxies. They do not claim waveform physics, biometrics, or universal cross-cultural meaning. "
                "They are here to make the next question sharper, not to close the question too early."
            ),
        },
    ]

    return {
        "boundary_note": (
            "This layer uses public structure only: duration, engagement, virality, packaging, language spread, "
            "and release timing. It does not claim direct biometric measurement, waveform physics, or universal cultural truth."
        ),
        "headline": headline,
        "summary_cards": summary_cards,
        "summary_index": summary_index,
        "top_signatures": top_signatures,
        "cultural_corridors": cultural_corridors,
        "provocations": provocations,
    }


def build_decision_lab(df: pd.DataFrame) -> Dict[str, object]:
    """Build the higher-rigor comparative surface for the public music lane."""
    working = df.copy()
    working["view_count"] = pd.to_numeric(working.get("view_count"), errors="coerce").fillna(0)
    working["duration_min"] = pd.to_numeric(working.get("duration_min"), errors="coerce").fillna(0)
    working["channel_follower_count"] = pd.to_numeric(working.get("channel_follower_count"), errors="coerce").fillna(0)
    working["virality_coefficient"] = pd.to_numeric(working.get("virality_coefficient"), errors="coerce").fillna(0)
    working["tag_count"] = pd.to_numeric(working.get("tag_count"), errors="coerce").fillna(0)
    working["title_word_count"] = pd.to_numeric(working.get("title_word_count"), errors="coerce").fillna(0)
    working["is_official"] = pd.to_numeric(working.get("is_official"), errors="coerce").fillna(0)

    drift = _drift_highlights(working)
    experiments = _experiment_suite(working)
    trust = _trust_surface(working)
    embodied = _embodied_surface(working)
    strongest = experiments.get("strongest") or {}
    top_drift = (drift.get("highlights") or [{}])[0]

    return {
        "generated_at": date.today().isoformat(),
        "drift": drift,
        "experiments": experiments,
        "trust": trust,
        "embodied": embodied,
        "summary": {
            "headline": (
                f"The strongest current structural gap is {strongest.get('label', 'not yet available').lower()}, "
                f"while the sharpest dated shift is {top_drift.get('label', 'not yet available').lower()}."
            ),
            "embodied_headline": embodied.get("headline", ""),
            "recommended_next_question": (
                "Ask whether the same uplift still holds once you split by year, reach tier, official packaging, and cultural corridor."
            ),
        },
    }
