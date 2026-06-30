"""Tests for the public zero-friction guard surface."""

from loopchii_lite import classify_prompt, public_playground_snapshot, simulate_governance


def test_classify_prompt_detects_pii():
    assert classify_prompt("Use the customer email export and phone list.") == "pii"


def test_classify_prompt_safe_falls_through():
    assert classify_prompt("Summarize the strongest genre shifts and keep the caveats visible.") == "safe"


def test_simulate_governance_blocks_and_zeroizes_publicly():
    result = simulate_governance("Write the full chorus and second verse from a protected pop track.")
    assert result["blocked"] is True
    assert result["category"] == "copyright"
    assert result["blocked_fragment"]
    assert result["governed_risky_tokens_rendered"] == 0


def test_simulate_governance_allows_safe_prompt():
    result = simulate_governance("Summarize the strongest genre shifts in the public music data.")
    assert result["blocked"] is False
    assert result["category"] == "safe"
    assert result["standard_response"] == result["governed_recovery"]


def test_public_playground_snapshot_has_package_surface():
    snapshot = public_playground_snapshot()
    assert snapshot["package"]["entry"] == "packages/loopchii-lite/src/index.js"
    assert len(snapshot["presets"]) >= 5
