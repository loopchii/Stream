"""Tests for the public Stream lens SDK."""

from lens_sdk import (
    LeadBalanceLens,
    StreamRecord,
    build_stream_records,
    default_registry,
    evaluate_stream,
)
from streamlens_processor import DataProcessor


def test_build_stream_records_from_synthetic_data():
    df = DataProcessor().generate_synthetic_data(n_samples=300)
    records = build_stream_records(df, max_groups=12)
    assert len(records) > 0
    first = records[0]
    assert first.record_id
    assert {"diversity", "gender_parity", "male_lead_share", "dialogue_gap", "over_50_share"} <= set(first.metrics)


def test_lead_balance_lens_flags_extreme_skew():
    record = StreamRecord(
        record_id="demo",
        platform="netflix",
        genre="action",
        year=2026,
        sample_size=20,
        metrics={
            "diversity": 0.51,
            "gender_parity": 0.44,
            "male_lead_share": 0.9,
            "female_lead_share": 0.1,
            "dialogue_gap": 0.36,
            "male_dialogue_mean": 520.0,
            "female_dialogue_mean": 140.0,
            "avg_screen_time": 58.0,
            "over_50_share": 0.04,
            "lead_count": 10.0,
            "race_modes": 3.0,
        },
    )
    findings = LeadBalanceLens().evaluate(record)
    assert len(findings) == 1
    assert findings[0].mask.verdict in {"review", "block"}


def test_evaluate_stream_uses_default_registry():
    df = DataProcessor().generate_synthetic_data(n_samples=400)
    results = evaluate_stream(df, registry=default_registry(), max_groups=10)
    assert len(results) > 0
    assert {"record", "finding_count", "findings"} <= set(results[0])
