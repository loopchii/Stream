"""Tests for the public enterprise-media research harness."""

from media_liability_lab import (
    analyze_compulsive_usage,
    build_causal_map,
    guard_generated_buffer,
    public_media_lab_snapshot,
    sample_recommendation_events,
)


def test_compulsive_usage_analysis_returns_bounded_score():
    report = analyze_compulsive_usage(sample_recommendation_events())
    assert 0 <= report["risk_score"] <= 1
    assert report["risk_band"] in {"clear", "watch", "elevated", "severe"}
    assert report["recommended_friction_ms"] >= 0


def test_guard_generated_buffer_zeroizes_matches():
    result = guard_generated_buffer(b"hello|copyrighted-castle|world")
    assert result["blocked"] is True
    assert result["zeroized_bytes"] > 0
    assert result["remaining_nonzero_bytes"] == 0


def test_causal_map_has_nodes_and_edges():
    graph = build_causal_map(sample_recommendation_events())
    assert graph["node_count"] > 0
    assert graph["edge_count"] > 0
    assert {"id", "weight", "kind", "label"} <= set(graph["nodes"][0])


def test_public_snapshot_contains_all_sections():
    snapshot = public_media_lab_snapshot()
    assert {"compulsive_usage", "generative_guard", "causal_map", "events"} <= set(snapshot)
