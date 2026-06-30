"""Public enterprise-media research harness for Stream.

This module keeps the work honest: it does not claim hardware enforcement or
private Loopchii internals. It does provide a reproducible public lab for three
high-stakes media questions:

1. How repetitive and compulsive does a recommendation stream look?
2. Can a generated output buffer be screened and zeroized before release?
3. Can we export a readable causal map of recommendation flow?
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class RecommendationEvent:
    event_id: str
    creator_id: str
    title: str
    category: str
    dwell_ms: int
    watch_ratio: float


def sample_recommendation_events() -> list[RecommendationEvent]:
    """Deterministic public sample representing a recommendation stream."""
    return [
        RecommendationEvent("evt-001", "creator-alpha", "Midnight Hook", "music", 3400, 0.91),
        RecommendationEvent("evt-002", "creator-alpha", "Midnight Hook Remix", "music", 3200, 0.94),
        RecommendationEvent("evt-003", "creator-alpha", "Midnight Hook Live", "music", 3100, 0.92),
        RecommendationEvent("evt-004", "creator-beta", "Tiny Laughs 01", "shorts", 1800, 0.88),
        RecommendationEvent("evt-005", "creator-beta", "Tiny Laughs 02", "shorts", 1700, 0.9),
        RecommendationEvent("evt-006", "creator-beta", "Tiny Laughs 03", "shorts", 1600, 0.89),
        RecommendationEvent("evt-007", "creator-gamma", "Family Game Night", "family", 5200, 0.63),
        RecommendationEvent("evt-008", "creator-alpha", "Midnight Hook Acoustic", "music", 3300, 0.93),
        RecommendationEvent("evt-009", "creator-delta", "Makeup Loop 01", "beauty", 1500, 0.96),
        RecommendationEvent("evt-010", "creator-delta", "Makeup Loop 02", "beauty", 1500, 0.97),
        RecommendationEvent("evt-011", "creator-delta", "Makeup Loop 03", "beauty", 1400, 0.95),
        RecommendationEvent("evt-012", "creator-epsilon", "Long Interview", "news", 11800, 0.42),
    ]


def analyze_compulsive_usage(events: Iterable[RecommendationEvent]) -> dict:
    """Score how repetitive and compulsive a recommendation stream appears."""

    events = list(events)
    if not events:
        return {
            "risk_score": 0.0,
            "risk_band": "clear",
            "recommended_friction_ms": 0,
            "signals": {},
            "explanation": "No events provided.",
        }

    creators = [event.creator_id for event in events]
    categories = [event.category for event in events]
    watch_ratios = [event.watch_ratio for event in events]
    dwell = [event.dwell_ms for event in events]

    unique_creator_ratio = len(set(creators)) / len(creators)
    creator_entropy = _normalized_entropy(creators)
    category_entropy = _normalized_entropy(categories)
    max_creator_streak = _max_streak(creators)
    max_category_streak = _max_streak(categories)
    repeat_ratio = 1 - unique_creator_ratio
    high_completion_rate = sum(1 for ratio in watch_ratios if ratio >= 0.9) / len(watch_ratios)
    short_dwell_ratio = sum(1 for ms in dwell if ms <= 3500) / len(dwell)

    risk_score = (
        repeat_ratio * 0.28
        + (1 - creator_entropy) * 0.22
        + (1 - category_entropy) * 0.16
        + min(1.0, max_creator_streak / 5) * 0.12
        + min(1.0, max_category_streak / 5) * 0.08
        + high_completion_rate * 0.09
        + short_dwell_ratio * 0.05
    )
    risk_score = round(min(0.99, risk_score), 4)

    if risk_score >= 0.72:
        risk_band = "severe"
        recommended_friction_ms = 180
    elif risk_score >= 0.52:
        risk_band = "elevated"
        recommended_friction_ms = 90
    elif risk_score >= 0.34:
        risk_band = "watch"
        recommended_friction_ms = 35
    else:
        risk_band = "clear"
        recommended_friction_ms = 0

    return {
        "risk_score": risk_score,
        "risk_band": risk_band,
        "recommended_friction_ms": recommended_friction_ms,
        "signals": {
            "unique_creator_ratio": round(unique_creator_ratio, 4),
            "creator_entropy": round(creator_entropy, 4),
            "category_entropy": round(category_entropy, 4),
            "max_creator_streak": max_creator_streak,
            "max_category_streak": max_category_streak,
            "high_completion_rate": round(high_completion_rate, 4),
            "short_dwell_ratio": round(short_dwell_ratio, 4),
        },
        "explanation": (
            "Higher scores indicate a recommendation flow dominated by short-cycle repetition, "
            "low variety, and unusually sticky completion patterns."
        ),
    }


def guard_generated_buffer(
    payload: bytes,
    *,
    protected_signatures: Iterable[bytes] | None = None,
    toxic_signatures: Iterable[bytes] | None = None,
) -> dict:
    """Inspect and zeroize a generated output buffer if it matches public guard signatures."""

    protected_signatures = list(protected_signatures or [b"copyrighted-castle", b"signature-character"])
    toxic_signatures = list(toxic_signatures or [b"target-minor-loop", b"graphic-self-harm"])

    working = bytearray(payload)
    reasons: list[str] = []

    for signature in protected_signatures:
        if signature in working:
            reasons.append(f"protected_signature:{signature.decode('utf-8', errors='ignore')}")

    for signature in toxic_signatures:
        if signature in working:
            reasons.append(f"toxic_signature:{signature.decode('utf-8', errors='ignore')}")

    blocked = bool(reasons)
    if blocked:
        for index in range(len(working)):
            working[index] = 0

    return {
        "blocked": blocked,
        "reason_count": len(reasons),
        "reasons": reasons,
        "zeroized_bytes": len(working) if blocked else 0,
        "remaining_nonzero_bytes": sum(1 for byte in working if byte != 0),
        "preview": working[:24].hex(),
    }


def build_causal_map(events: Iterable[RecommendationEvent]) -> dict:
    """Create a readable topological map of recommendation flow."""

    events = list(events)
    node_weights: dict[str, int] = defaultdict(int)
    edge_weights: dict[tuple[str, str], int] = defaultdict(int)

    def creator_node(event: RecommendationEvent) -> str:
        return f"creator::{event.creator_id}"

    def category_node(event: RecommendationEvent) -> str:
        return f"category::{event.category}"

    for event in events:
        for node_id in (creator_node(event), category_node(event)):
            node_weights[node_id] += 1

    for current, nxt in zip(events, events[1:]):
        edge_weights[(creator_node(current), creator_node(nxt))] += 1
        edge_weights[(category_node(current), category_node(nxt))] += 1

    nodes = [
        {
            "id": node_id,
            "weight": weight,
            "kind": node_id.split("::", 1)[0],
            "label": node_id.split("::", 1)[1],
        }
        for node_id, weight in sorted(node_weights.items())
    ]
    edges = [
        {
            "source": source,
            "target": target,
            "weight": weight,
            "risk_edge": weight >= 2,
        }
        for (source, target), weight in sorted(edge_weights.items())
    ]

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "summary": "Repeated creator or category transitions are marked as risk edges.",
    }


def public_media_lab_snapshot() -> dict:
    """Return the full public research snapshot for the media lab."""

    events = sample_recommendation_events()
    compulsive = analyze_compulsive_usage(events)
    generative = guard_generated_buffer(
        b"safe-frame|copyrighted-castle|soundtrack-stem",
    )
    causal_map = build_causal_map(events)
    return {
        "compulsive_usage": compulsive,
        "generative_guard": generative,
        "causal_map": causal_map,
        "events": [asdict(event) for event in events],
    }


def _normalized_entropy(values: list[str]) -> float:
    counts = Counter(values)
    total = sum(counts.values())
    if total == 0 or len(counts) <= 1:
        return 0.0
    probs = [count / total for count in counts.values()]
    entropy = -sum(prob * math.log(prob) for prob in probs if prob > 0)
    return entropy / math.log(len(counts))


def _max_streak(values: list[str]) -> int:
    if not values:
        return 0
    best = 1
    current = 1
    for left, right in zip(values, values[1:]):
        if left == right:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best
