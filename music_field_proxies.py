#!/usr/bin/env python3
"""Shared public proxy features for the Stream music lane.

These proxies stay inside public evidence. They use public catalog structure
rather than hidden waveform, biometric, or private platform traces. The goal is
to produce richer, auditable questions about embodied pull, cultural corridors,
and vitality without making unverifiable claims.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Mapping

import numpy as np
import pandas as pd


CURRENT_YEAR = date.today().year
_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def music_tokens(value: object) -> List[str]:
    if value is None:
        return []
    return [token for token in _TOKEN_RE.findall(str(value).lower()) if len(token) > 1]


def detect_collab(value: object) -> bool:
    low = str(value or "").lower()
    indicators = [" ft.", " feat.", " ft ", " feat ", " x ", " & ", " with ", " featuring "]
    return any(indicator in low for indicator in indicators)


def corridor_label(genre: object, language: object) -> str:
    genre_value = str(genre or "").strip() or "Unknown"
    language_value = str(language or "").strip() or "Unknown"
    genre_known = genre_value.lower() not in {"unknown", "other/unclassified"}
    language_known = language_value.lower() not in {"unknown", ""}

    if genre_known and language_known:
        return f"{language_value} · {genre_value}"
    if genre_known:
        return f"{genre_value} corridor"
    if language_known:
        return f"{language_value} corridor"
    return "Unlabeled corridor"


def vitality_signature_labels(row: Mapping[str, object]) -> List[str]:
    somatic_pull = float(row.get("somatic_pull", 0.0) or 0.0)
    novelty_room = float(row.get("novelty_room", 0.0) or 0.0)
    communal_carry = float(row.get("communal_carry", 0.0) or 0.0)
    inheritance_pressure = float(row.get("inheritance_pressure", 0.0) or 0.0)

    labels: List[str] = []
    if somatic_pull >= 0.72:
        labels.append("strong bodily invitation")
    elif somatic_pull >= 0.58:
        labels.append("steady bodily invitation")
    else:
        labels.append("cooler bodily pull")

    if novelty_room >= 0.62:
        labels.append("room beyond inherited formulas")
    elif novelty_room >= 0.48:
        labels.append("moderate novelty room")
    else:
        labels.append("familiar corridor pressure")

    if communal_carry >= 0.58:
        labels.append("community-led carry")
    elif inheritance_pressure >= 0.66:
        labels.append("scale-heavy distribution")
    else:
        labels.append("mixed route to attention")
    return labels


def _rank_normalize(series: pd.Series, default: float = 0.5) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    out = pd.Series(default, index=series.index, dtype=float)
    mask = numeric.notna()
    if not mask.any():
        return out
    if int(mask.sum()) == 1:
        out.loc[mask] = default
        return out
    out.loc[mask] = numeric.loc[mask].rank(method="average", pct=True).astype(float)
    return out.fillna(default)


def build_public_music_proxy_table(df: pd.DataFrame) -> pd.DataFrame:
    """Attach explainable embodied/cultural proxy features to a public music frame."""
    working = df.copy()
    if working.empty:
        return working

    working["title"] = working.get("title", pd.Series([""] * len(working), index=working.index)).fillna("").astype(str)
    working["tags"] = working.get("tags", pd.Series([""] * len(working), index=working.index)).fillna("").astype(str)
    working["genre"] = working.get("genre", pd.Series(["Unknown"] * len(working), index=working.index)).fillna("Unknown").astype(str)
    working["detected_language"] = (
        working.get("detected_language", pd.Series(["Unknown"] * len(working), index=working.index))
        .fillna("Unknown")
        .replace({"": "Unknown"})
        .astype(str)
    )
    working["duration_min"] = pd.to_numeric(working.get("duration_min"), errors="coerce").fillna(0.0)
    working["view_count"] = pd.to_numeric(working.get("view_count"), errors="coerce").fillna(0.0)
    working["virality_coefficient"] = pd.to_numeric(working.get("virality_coefficient"), errors="coerce").fillna(0.0)
    working["channel_follower_count"] = pd.to_numeric(working.get("channel_follower_count"), errors="coerce").fillna(0.0)
    working["engagement_ratio"] = pd.to_numeric(
        working.get("engagement_ratio", pd.Series([0.0] * len(working), index=working.index)),
        errors="coerce",
    ).fillna(0.0)
    working["is_official"] = pd.to_numeric(
        working.get("is_official", pd.Series([0.0] * len(working), index=working.index)),
        errors="coerce",
    ).fillna(0.0)
    working["published_year"] = pd.to_numeric(working.get("published_year"), errors="coerce").fillna(0).astype(int)

    title_words = pd.to_numeric(working.get("title_word_count"), errors="coerce")
    if title_words.isna().all():
        title_words = working["title"].map(lambda value: len(music_tokens(value)))
    else:
        title_words = title_words.fillna(working["title"].map(lambda value: len(music_tokens(value))))
    working["title_word_count"] = title_words.astype(float)

    years = working["published_year"].copy()
    known_years = years[years > 0]
    year_min = int(known_years.min()) if not known_years.empty else CURRENT_YEAR - 8
    year_max = int(known_years.max()) if not known_years.empty else CURRENT_YEAR
    year_span = max(year_max - year_min, 1)

    def _title_echo(row: pd.Series) -> float:
        title_tokens = set(music_tokens(row.get("title", "")))
        tag_tokens = set(music_tokens(row.get("tags", "")))
        if not title_tokens:
            return 0.0
        return float(len(title_tokens & tag_tokens) / max(len(title_tokens), 1))

    working["title_echo"] = working.apply(_title_echo, axis=1)
    working["duration_fit"] = np.exp(-((working["duration_min"] - 3.25) / 1.15) ** 2).astype(float)
    working["brevity_fit"] = np.exp(-((working["title_word_count"] - 4.0) / 2.25) ** 2).astype(float)
    working["views_norm"] = _rank_normalize(np.log1p(working["view_count"]))
    working["virality_norm"] = _rank_normalize(np.log1p(working["virality_coefficient"].clip(lower=0.0)))
    working["reach_norm"] = _rank_normalize(np.log1p(working["channel_follower_count"].clip(lower=0.0)))
    working["engagement_norm"] = _rank_normalize(np.log1p((working["engagement_ratio"].clip(lower=0.0) * 10_000.0) + 1.0))
    working["recency_norm"] = years.map(
        lambda value: 0.42 if value <= 0 else clamp01(1.0 - max(year_max - int(value), 0) / max(year_span + 1, 2))
    )

    genre_counts = working["genre"].replace({"": "Unknown"}).value_counts(normalize=True)
    known_language_counts = (
        working["detected_language"]
        .loc[lambda values: ~values.str.lower().isin(["unknown", ""])]
        .value_counts(normalize=True)
    )
    working["genre_share"] = working["genre"].map(lambda value: float(genre_counts.get(value, 0.0)))
    working["language_share"] = working["detected_language"].map(
        lambda value: float(known_language_counts.get(value, 0.0)) if str(value).lower() not in {"unknown", ""} else 0.0
    )
    working["genre_rarity"] = working["genre_share"].map(lambda value: clamp01(1.0 - value))
    working["language_rarity"] = working["detected_language"].map(
        lambda value: 0.35 if str(value).lower() in {"unknown", ""} else clamp01(1.0 - float(known_language_counts.get(value, 0.0)))
    )
    working["collaboration_flag"] = working["title"].map(detect_collab).astype(float)
    working["cultural_corridor"] = [
        corridor_label(genre, language)
        for genre, language in zip(working["genre"], working["detected_language"])
    ]

    working["inheritance_pressure"] = (
        0.52 * working["reach_norm"]
        + 0.23 * working["is_official"].clip(lower=0.0, upper=1.0)
        + 0.15 * (1.0 - working["genre_rarity"])
        + 0.10 * (1.0 - working["language_rarity"])
    ).map(clamp01)

    working["somatic_pull"] = (
        0.30 * working["duration_fit"]
        + 0.24 * working["engagement_norm"]
        + 0.18 * working["virality_norm"]
        + 0.16 * working["title_echo"]
        + 0.12 * working["brevity_fit"]
    ).map(clamp01)

    working["communal_carry"] = (
        0.34 * working["collaboration_flag"]
        + 0.26 * working["engagement_norm"]
        + 0.20 * working["language_rarity"]
        + 0.20 * working["recency_norm"]
    ).map(clamp01)

    working["novelty_room"] = (
        0.38 * (1.0 - working["reach_norm"])
        + 0.34 * working["genre_rarity"]
        + 0.18 * working["language_rarity"]
        + 0.10 * (1.0 - working["is_official"].clip(lower=0.0, upper=1.0))
    ).map(clamp01)

    working["vitality_score"] = (
        0.34 * working["somatic_pull"]
        + 0.24 * working["novelty_room"]
        + 0.22 * working["communal_carry"]
        + 0.20 * (1.0 - working["inheritance_pressure"])
    ).map(clamp01)

    return working


def _mean_or_default(series: pd.Series, default: float = 0.0) -> float:
    if series is None or series.empty:
        return default
    return float(pd.to_numeric(series, errors="coerce").fillna(default).mean())


def _metric_value_label(value: float) -> str:
    return f"{round(clamp01(value) * 100):d}/100"


def living_media_profile_text(row: Mapping[str, object]) -> str:
    corridor = str(row.get("cultural_corridor") or row.get("genre") or "this corridor")
    labels = vitality_signature_labels(row)
    vitality = round(float(row.get("vitality_index", row.get("vitality_score", 0.0)) or 0.0) * 100)
    kinetic = round(float(row.get("kinetic_energy", 0.0) or 0.0) * 100)
    resistance = round(float(row.get("bias_resistance", 0.0) or 0.0) * 100)
    return (
        f"{row.get('title', 'This track')} holds {corridor} with {labels[0]}, "
        f"{labels[1]}, and {labels[2]}. The current kinetic read is {kinetic}/100, "
        f"bias resistance is {resistance}/100, and the composite vitality surface reads {vitality}/100."
    )


def build_living_media_surface(
    df: pd.DataFrame,
    bias: Mapping[str, object] | None = None,
    resonance: Mapping[str, object] | None = None,
    decision_lab: Mapping[str, object] | None = None,
) -> Dict[str, object]:
    """Summarize the public music field as a living media surface.

    The output is intentionally limited to public, inspectable signals. It does
    not claim direct biometric sensing, waveform physiology, or universal
    psychological truth.
    """

    bias = bias or {}
    resonance = resonance or {}
    decision_lab = decision_lab or {}
    proxy = df.copy()
    required = {"somatic_pull", "communal_carry", "novelty_room", "inheritance_pressure", "vitality_score"}
    if proxy.empty:
        proxy = build_public_music_proxy_table(proxy)
    elif not required.issubset(proxy.columns):
        proxy = build_public_music_proxy_table(proxy)

    if proxy.empty:
        return {
            "boundary_note": "No public music rows are available, so the living media field cannot be estimated yet.",
            "headline": "The living media surface needs a real public cohort before it can speak.",
            "metrics": [],
            "summary_index": {},
            "somatic_profiles": [],
            "cultural_ecology": [],
            "bias_field": [],
            "cross_media_routes": [],
            "provocations": [],
        }

    working = proxy.copy()
    total_views = float(pd.to_numeric(working.get("view_count"), errors="coerce").fillna(0.0).sum()) or 1.0
    working["kinetic_energy"] = (
        0.34 * working["virality_norm"]
        + 0.24 * working["engagement_norm"]
        + 0.18 * working["duration_fit"]
        + 0.14 * working["title_echo"]
        + 0.10 * working["brevity_fit"]
    ).map(clamp01)
    working["resonance_depth"] = (
        0.42 * working["somatic_pull"]
        + 0.30 * working["communal_carry"]
        + 0.18 * working["engagement_norm"]
        + 0.10 * working["title_echo"]
    ).map(clamp01)
    working["cultural_gravity"] = (
        0.42 * working["reach_norm"]
        + 0.20 * working["views_norm"]
        + 0.18 * (1.0 - working["genre_rarity"])
        + 0.10 * working["is_official"].clip(lower=0.0, upper=1.0)
        + 0.10 * (1.0 - working["language_rarity"])
    ).map(clamp01)
    working["distribution_fingerprint"] = (
        0.34 * working["reach_norm"]
        + 0.24 * working["is_official"].clip(lower=0.0, upper=1.0)
        + 0.18 * working["views_norm"]
        + 0.14 * working["title_echo"]
        + 0.10 * working["duration_fit"]
    ).map(clamp01)
    working["organic_signature"] = (
        0.32 * working["communal_carry"]
        + 0.26 * working["novelty_room"]
        + 0.18 * working["language_rarity"]
        + 0.14 * working["genre_rarity"]
        + 0.10 * (1.0 - working["reach_norm"])
    ).map(clamp01)
    working["engineered_signature"] = (
        0.32 * working["distribution_fingerprint"]
        + 0.26 * working["inheritance_pressure"]
        + 0.18 * working["is_official"].clip(lower=0.0, upper=1.0)
        + 0.14 * working["views_norm"]
        + 0.10 * (1.0 - working["novelty_room"])
    ).map(clamp01)
    working["velocity_anomaly"] = (
        0.55 * (working["virality_norm"] - working["communal_carry"]).abs()
        + 0.25 * (working["views_norm"] - working["recency_norm"]).abs()
        + 0.20 * (working["distribution_fingerprint"] - working["organic_signature"]).abs()
    ).map(clamp01)
    working["longevity_potential"] = (
        0.38 * working["resonance_depth"]
        + 0.24 * working["communal_carry"]
        + 0.18 * working["novelty_room"]
        + 0.20 * (1.0 - working["velocity_anomaly"])
    ).map(clamp01)
    working["authenticity_index"] = (
        0.42 * working["organic_signature"]
        + 0.24 * working["longevity_potential"]
        + 0.18 * working["resonance_depth"]
        + 0.16 * (1.0 - working["engineered_signature"])
    ).map(clamp01)

    genre_diversity = clamp01(
        float(
            ((bias.get("classified_genres") or {}).get("diversity"))
            or ((bias.get("bias_scores") or {}).get("genre_diversity"))
            or 0.0
        )
    )
    gender_parity = clamp01(float(((bias.get("gender") or {}).get("gender_parity")) or 0.0))
    coverage_confidence = clamp01(
        float(
            ((bias.get("coverage") or {}).get("confidence"))
            or ((bias.get("bias_scores") or {}).get("coverage_confidence"))
            or 0.0
        )
    )
    top10_concentration = clamp01(float(((bias.get("concentration") or {}).get("top10_share")) or 0.0))
    trust_score_raw = float(((decision_lab.get("trust") or {}).get("score")) or 0.0)
    trust_score = clamp01(trust_score_raw / 100.0 if trust_score_raw > 1.0 else trust_score_raw)

    corridor_stats = (
        working.groupby("cultural_corridor", dropna=False)
        .agg(
            song_count=("title", "size"),
            total_views=("view_count", "sum"),
            avg_vitality=("vitality_score", "mean"),
            avg_kinetic=("kinetic_energy", "mean"),
            avg_resonance=("resonance_depth", "mean"),
            avg_resistance=("novelty_room", "mean"),
            avg_authenticity=("authenticity_index", "mean"),
            avg_engineered=("engineered_signature", "mean"),
            collab_share=("collaboration_flag", "mean"),
            language_variety=("detected_language", pd.Series.nunique),
            genre_variety=("genre", pd.Series.nunique),
        )
        .reset_index()
    )
    corridor_stats["view_share"] = corridor_stats["total_views"].map(lambda value: clamp01(float(value) / total_views))
    corridor_stats["inheritance_bias"] = corridor_stats["avg_resistance"].map(lambda value: clamp01(1.0 - float(value)))
    top_corridor_share = float(corridor_stats["view_share"].max()) if not corridor_stats.empty else 1.0
    corridor_balance = clamp01(1.0 - top_corridor_share)

    mean_kinetic = _mean_or_default(working["kinetic_energy"])
    mean_resonance = _mean_or_default(working["resonance_depth"])
    mean_gravity = _mean_or_default(working["cultural_gravity"])
    mean_vitality = _mean_or_default(working["vitality_score"])
    mean_novelty = _mean_or_default(working["novelty_room"])
    mean_inheritance = _mean_or_default(working["inheritance_pressure"])
    mean_distribution = _mean_or_default(working["distribution_fingerprint"])
    mean_organic = _mean_or_default(working["organic_signature"])
    mean_engineered = _mean_or_default(working["engineered_signature"])
    mean_velocity_anomaly = _mean_or_default(working["velocity_anomaly"])
    mean_longevity = _mean_or_default(working["longevity_potential"])
    mean_authenticity = _mean_or_default(working["authenticity_index"])
    bias_resistance = clamp01(
        0.30 * mean_novelty
        + 0.22 * corridor_balance
        + 0.18 * genre_diversity
        + 0.14 * gender_parity
        + 0.08 * coverage_confidence
        + 0.08 * trust_score
    )
    vitality_index = clamp01(
        0.26 * mean_kinetic
        + 0.24 * mean_resonance
        + 0.18 * mean_vitality
        + 0.18 * bias_resistance
        + 0.14 * (1.0 - mean_inheritance)
    )

    metrics = [
        {
            "label": "Kinetic energy",
            "value": round(mean_kinetic, 4),
            "value_label": f"{round(mean_kinetic * 100):d}/100",
            "note": "A public proxy for pace, drive, and release pressure built from virality, engagement, and duration fit.",
        },
        {
            "label": "Resonance depth",
            "value": round(mean_resonance, 4),
            "value_label": f"{round(mean_resonance * 100):d}/100",
            "note": "How deeply the field appears to land through repeated pull, communal carry, and engagement structure.",
        },
        {
            "label": "Cultural gravity",
            "value": round(mean_gravity, 4),
            "value_label": f"{round(mean_gravity * 100):d}/100",
            "note": "How heavily scale, official packaging, and familiar corridors are still organizing the visible market.",
        },
        {
            "label": "Bias resistance",
            "value": round(bias_resistance, 4),
            "value_label": f"{round(bias_resistance * 100):d}/100",
            "note": "A public-evidence resistance score built from corridor spread, genre breadth, parity, coverage confidence, and novelty room.",
        },
        {
            "label": "Vitality index",
            "value": round(vitality_index, 4),
            "value_label": f"{round(vitality_index * 100):d}/100",
            "note": "The composite read: aliveness through motion, depth, resistance, and reduced inheritance pressure.",
        },
    ]
    origin_detector = [
        {
            "label": "Authenticity index",
            "value": round(mean_authenticity, 4),
            "value_label": _metric_value_label(mean_authenticity),
            "note": "A public proxy for how strongly the field reads as community-carried and novelty-bearing rather than centrally over-shaped.",
        },
        {
            "label": "Organic signature",
            "value": round(mean_organic, 4),
            "value_label": _metric_value_label(mean_organic),
            "note": "Higher when communal carry, novelty room, and language or genre spread are doing more of the work than inherited reach.",
        },
        {
            "label": "Engineered pressure",
            "value": round(mean_engineered, 4),
            "value_label": _metric_value_label(mean_engineered),
            "note": "Higher when official packaging, reach concentration, repeat titling, and inherited scale keep organizing the visible field.",
        },
        {
            "label": "Velocity anomaly",
            "value": round(mean_velocity_anomaly, 4),
            "value_label": _metric_value_label(mean_velocity_anomaly),
            "note": "Flags songs moving faster than community carry and recency context alone would suggest.",
        },
        {
            "label": "Distribution fingerprint",
            "value": round(mean_distribution, 4),
            "value_label": _metric_value_label(mean_distribution),
            "note": "A public proxy for how optimized the distribution layer looks before anyone makes a claim about 'natural' breakout.",
        },
        {
            "label": "Longevity potential",
            "value": round(mean_longevity, 4),
            "value_label": _metric_value_label(mean_longevity),
            "note": "Higher when resonance depth, communal carry, and lower anomaly suggest the field can survive beyond a first spike.",
        },
    ]

    ranked_profiles = (
        working.assign(
            vitality_index=lambda frame: (
                0.30 * frame["vitality_score"]
                + 0.24 * frame["kinetic_energy"]
                + 0.18 * frame["resonance_depth"]
                + 0.14 * frame["novelty_room"]
                + 0.14 * (1.0 - frame["inheritance_pressure"])
            ).map(clamp01),
            bias_resistance=lambda frame: (
                0.42 * frame["novelty_room"]
                + 0.26 * frame["genre_rarity"]
                + 0.18 * frame["language_rarity"]
                + 0.14 * (1.0 - frame["inheritance_pressure"])
            ).map(clamp01),
        )
        .sort_values(["vitality_index", "resonance_depth", "view_count"], ascending=[False, False, False])
        .head(6)
    )

    somatic_profiles = []
    for _, row in ranked_profiles.iterrows():
        item = row.to_dict()
        somatic_profiles.append(
            {
                "title": str(item.get("title", "")),
                "channel": str(item.get("channel", "")),
                "cultural_corridor": str(item.get("cultural_corridor", "Unlabeled corridor")),
                "kinetic_energy": round(float(item.get("kinetic_energy", 0.0)), 4),
                "resonance_depth": round(float(item.get("resonance_depth", 0.0)), 4),
                "bias_resistance": round(float(item.get("bias_resistance", 0.0)), 4),
                "vitality_index": round(float(item.get("vitality_index", 0.0)), 4),
                "signature": vitality_signature_labels(item),
                "reading": living_media_profile_text(item),
            }
        )

    authenticity_profiles = []
    authenticity_rows = pd.concat(
        [
            working.sort_values(
                ["authenticity_index", "organic_signature", "view_count"],
                ascending=[False, False, False],
            ).head(3).assign(_posture="Organic-leaning"),
            working.sort_values(
                ["engineered_signature", "distribution_fingerprint", "view_count"],
                ascending=[False, False, False],
            ).head(3).assign(_posture="Engineered-leaning"),
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["title", "channel"], keep="first")

    for _, row in authenticity_rows.iterrows():
        posture = str(row.get("_posture", "Mixed signal"))
        authenticity_profiles.append(
            {
                "title": str(row.get("title", "")),
                "channel": str(row.get("channel", "")),
                "posture": posture,
                "cultural_corridor": str(row.get("cultural_corridor", "Unlabeled corridor")),
                "authenticity_index": round(float(row.get("authenticity_index", 0.0) or 0.0), 4),
                "organic_signature": round(float(row.get("organic_signature", 0.0) or 0.0), 4),
                "engineered_signature": round(float(row.get("engineered_signature", 0.0) or 0.0), 4),
                "velocity_anomaly": round(float(row.get("velocity_anomaly", 0.0) or 0.0), 4),
                "reading": (
                    f"{row.get('title', 'This track')} reads {posture.lower()} in the current public field. "
                    f"It sits in {row.get('cultural_corridor', 'an unlabeled corridor')} with authenticity "
                    f"{_metric_value_label(float(row.get('authenticity_index', 0.0) or 0.0))}, engineered pressure "
                    f"{_metric_value_label(float(row.get('engineered_signature', 0.0) or 0.0))}, and anomaly "
                    f"{_metric_value_label(float(row.get('velocity_anomaly', 0.0) or 0.0))}."
                ),
            }
        )

    cultural_ecology = []
    ordered_corridors = corridor_stats.sort_values(
        ["view_share", "avg_vitality", "song_count"], ascending=[False, False, False]
    ).head(6)
    for _, row in ordered_corridors.iterrows():
        corridor = str(row["cultural_corridor"])
        reading = (
            f"{corridor} currently carries {round(float(row['view_share']) * 100):d}% of visible views "
            f"with vitality {round(float(row['avg_vitality']) * 100):d}/100 and kinetic pull "
            f"{round(float(row['avg_kinetic']) * 100):d}/100."
        )
        if float(row["avg_resistance"]) >= 0.5:
            reading += " It keeps more room open for counter-patterns than the median corridor."
        else:
            reading += " It still leans on inherited market shape more than on open novelty."
        cultural_ecology.append(
            {
                "corridor": corridor,
                "song_count": int(row["song_count"]),
                "view_share": round(float(row["view_share"]), 4),
                "avg_vitality": round(float(row["avg_vitality"]), 4),
                "avg_kinetic": round(float(row["avg_kinetic"]), 4),
                "avg_resonance": round(float(row["avg_resonance"]), 4),
                "collab_share": round(float(row["collab_share"]), 4),
                "reading": reading,
            }
        )

    bias_field = [
        {
            "label": "Centering pressure",
            "value": round(1.0 - corridor_balance, 4),
            "value_label": f"{round((1.0 - corridor_balance) * 100):d}/100",
            "note": "How strongly one dominant corridor is still centering the field.",
        },
        {
            "label": "Representation lift",
            "value": round((genre_diversity + gender_parity) / 2.0, 4),
            "value_label": f"{round(((genre_diversity + gender_parity) / 2.0) * 100):d}/100",
            "note": "A public representation read built from genre diversity and gender parity rather than subjective taste claims.",
        },
        {
            "label": "Narrative entropy",
            "value": round(mean_novelty, 4),
            "value_label": f"{round(mean_novelty * 100):d}/100",
            "note": "How much room remains for less inherited release shapes to register as more than noise.",
        },
        {
            "label": "Documentation honesty",
            "value": round((coverage_confidence + trust_score) / 2.0, 4),
            "value_label": f"{round(((coverage_confidence + trust_score) / 2.0) * 100):d}/100",
            "note": "How much the repository can prove about this field before the interpretation outruns the evidence.",
        },
    ]
    bias_spectrum = [
        {
            "label": "Temporal bias",
            "value": round(1.0 - coverage_confidence, 4),
            "value_label": _metric_value_label(1.0 - coverage_confidence),
            "note": "Higher when year coverage is thin enough to let one moment masquerade as a durable market truth.",
        },
        {
            "label": "Corridor bias",
            "value": round(1.0 - corridor_balance, 4),
            "value_label": _metric_value_label(1.0 - corridor_balance),
            "note": "Higher when one cultural corridor keeps centering the field and shrinking what counts as visible success.",
        },
        {
            "label": "Aesthetic bias",
            "value": round(clamp01((0.58 * _mean_or_default(working["duration_fit"])) + (0.42 * _mean_or_default(working["brevity_fit"]))), 4),
            "value_label": _metric_value_label((0.58 * _mean_or_default(working["duration_fit"])) + (0.42 * _mean_or_default(working["brevity_fit"]))),
            "note": "Captures how strongly the field rewards a narrow duration and titling aesthetic rather than broader formal variation.",
        },
        {
            "label": "Cognitive bias",
            "value": round(clamp01((0.42 * _mean_or_default(working["title_echo"])) + (0.28 * top10_concentration) + (0.30 * mean_distribution)), 4),
            "value_label": _metric_value_label((0.42 * _mean_or_default(working["title_echo"])) + (0.28 * top10_concentration) + (0.30 * mean_distribution)),
            "note": "A public proxy for how much repeated packaging and winner concentration may be exploiting familiar attention heuristics.",
        },
        {
            "label": "Social bias",
            "value": round(clamp01((0.52 * (1.0 - _mean_or_default(working["collaboration_flag"]))) + (0.48 * mean_inheritance)), 4),
            "value_label": _metric_value_label((0.52 * (1.0 - _mean_or_default(working["collaboration_flag"]))) + (0.48 * mean_inheritance)),
            "note": "Higher when the field remains closed around inherited scale instead of circulating through broader collaborative routes.",
        },
        {
            "label": "Technological bias",
            "value": round(clamp01((0.60 * _mean_or_default(working["is_official"])) + (0.40 * mean_distribution)), 4),
            "value_label": _metric_value_label((0.60 * _mean_or_default(working["is_official"])) + (0.40 * mean_distribution)),
            "note": "Higher when platform-optimized packaging and official upload pathways dominate what becomes visible.",
        },
        {
            "label": "Somatic bias",
            "value": round(clamp01((0.56 * _mean_or_default(working["somatic_pull"])) + (0.44 * (1.0 - genre_diversity))), 4),
            "value_label": _metric_value_label((0.56 * _mean_or_default(working["somatic_pull"])) + (0.44 * (1.0 - genre_diversity))),
            "note": "Higher when one bodily invitation pattern keeps winning across a field that otherwise claims stylistic variety.",
        },
        {
            "label": "Epistemic bias",
            "value": round(1.0 - ((coverage_confidence + trust_score) / 2.0), 4),
            "value_label": _metric_value_label(1.0 - ((coverage_confidence + trust_score) / 2.0)),
            "note": "Higher when the explanation layer is tempted to outrun what the public rows, dates, and labels can honestly support.",
        },
    ]
    propagation_chain = [
        {
            "stage": "Packaging",
            "value": round(clamp01((0.46 * _mean_or_default(working["is_official"])) + (0.54 * _mean_or_default(working["title_echo"]))), 4),
            "value_label": _metric_value_label((0.46 * _mean_or_default(working["is_official"])) + (0.54 * _mean_or_default(working["title_echo"]))),
            "note": "Where titling discipline, official upload cues, and repeat-ready framing first shape expectation.",
        },
        {
            "stage": "Distribution",
            "value": round(mean_distribution, 4),
            "value_label": _metric_value_label(mean_distribution),
            "note": "How heavily reach, packaging, and inherited scale organize circulation before reception is visible.",
        },
        {
            "stage": "Attention",
            "value": round(top10_concentration, 4),
            "value_label": _metric_value_label(top10_concentration),
            "note": "How much of the public field collapses into the winner ring once the song is in circulation.",
        },
        {
            "stage": "Corridor",
            "value": round(1.0 - corridor_balance, 4),
            "value_label": _metric_value_label(1.0 - corridor_balance),
            "note": "How strongly one language or genre corridor keeps organising what attention means.",
        },
        {
            "stage": "Interpretation",
            "value": round(1.0 - ((coverage_confidence + trust_score) / 2.0), 4),
            "value_label": _metric_value_label(1.0 - ((coverage_confidence + trust_score) / 2.0)),
            "note": "Where explanation becomes fragile because coverage, dates, or labels are thinner than the story being told.",
        },
    ]

    headline = (
        f"The living media read gives the field {round(vitality_index * 100):d}/100 vitality, "
        f"with {round(mean_resonance * 100):d}/100 resonance depth and {round((1.0 - corridor_balance) * 100):d}/100 centering pressure."
    )
    boundary_note = (
        "This layer stays inside public evidence: metadata, duration, engagement, virality, release timing, "
        "corridor spread, and documented bias surfaces. It does not claim direct waveform physiology, biometric sensing, "
        "or universal emotional truth."
    )

    top_profile_title = somatic_profiles[0]["title"] if somatic_profiles else "the strongest visible profile"
    dominant_corridor = cultural_ecology[0]["corridor"] if cultural_ecology else "the dominant corridor"
    provocations = [
        {
            "title": "What looks alive because it truly moves people, and what looks alive because distribution keeps shoving it forward?",
            "body": f"Right now {top_profile_title} sits near the front of the vitality field, but {dominant_corridor} still carries the heaviest structural gravity. The interesting question is not who won — it is what kind of life the system keeps rewarding.",
        },
        {
            "title": "Where does community carry become more important than inherited scale?",
            "body": "Tracks with stronger communal carry often travel differently from scale-heavy releases. That difference is worth following because it reveals whether social movement is opening the market or simply decorating the same concentration curve.",
        },
        {
            "title": "What kind of bias remains even after the explicit labels look better?",
            "body": "Representation can improve while corridor balance stays narrow. That is why the field map tracks centering pressure separately from genre and parity scores.",
        },
        {
            "title": "How much of the field is interpretable, and how much still needs more score, scene, or cultural context?",
            "body": "A living archive should admit its blind spots. The documentation honesty score is there to keep the repository curious instead of overconfident.",
        },
    ]

    cross_media_routes = [
        {
            "title": "Visual rhythm and narrative pressure",
            "tab": "dashboard",
            "target": "dashTimeline",
            "note": "Jump back into the synthetic screen field to compare how pacing, attention, and imbalance behave outside the real-music lane.",
        },
        {
            "title": "Bias as field, not slogan",
            "tab": "library",
            "target": "libraryCards",
            "note": "Use the pattern library when you want names for the structures the music field only hints at.",
        },
        {
            "title": "Methods before mythology",
            "tab": "learn",
            "target": "learnMethods",
            "note": "Return to the methods lane when the living-media read needs its assumptions surfaced before it travels any further.",
        },
        {
            "title": "Real rows, real pressure",
            "tab": "music",
            "target": "mvSongsExplorer",
            "note": "Drop back into the full songs explorer to see whether the vitality story still feels earned at row level.",
        },
    ]

    return {
        "boundary_note": boundary_note,
        "headline": headline,
        "metrics": metrics,
        "summary_index": {
            "kinetic_energy": round(mean_kinetic, 4),
            "resonance_depth": round(mean_resonance, 4),
            "cultural_gravity": round(mean_gravity, 4),
            "bias_resistance": round(bias_resistance, 4),
            "vitality_index": round(vitality_index, 4),
            "corridor_balance": round(corridor_balance, 4),
            "authenticity_index": round(mean_authenticity, 4),
            "engineered_pressure": round(mean_engineered, 4),
            "velocity_anomaly": round(mean_velocity_anomaly, 4),
        },
        "somatic_profiles": somatic_profiles,
        "cultural_ecology": cultural_ecology,
        "bias_field": bias_field,
        "bias_spectrum": bias_spectrum,
        "origin_detector": origin_detector,
        "authenticity_profiles": authenticity_profiles,
        "propagation_chain": propagation_chain,
        "cross_media_routes": cross_media_routes,
        "provocations": provocations,
    }
