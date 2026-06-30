from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping


def build_streaming_readiness_snapshot(
    *,
    music_quality: Mapping[str, object],
    data_engineering: Mapping[str, object],
) -> dict:
    coverage = (music_quality or {}).get("coverage", {}) if isinstance(music_quality, Mapping) else {}
    genre_known_share = float((coverage or {}).get("genre_known_share", 0.0) or 0.0)
    publication_year_share = float(
        (coverage or {}).get("publication_year_explicit_share", 0.0) or 0.0
    ) + float((coverage or {}).get("publication_year_inferred_share", 0.0) or 0.0)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "positioning": {
            "problem": (
                "Stream helps people inspect how attention, representation, bias, and release shape move through "
                "public media datasets without requiring private platform access."
            ),
            "thirty_second_test": {
                "status": "partial_pass",
                "verdict": (
                    "The public value is visible quickly once the dashboard loads, but a streaming-infrastructure "
                    "reader still has to work too hard to separate research surfaces from production claims."
                ),
            },
            "maturity_label": "research_foundation_with_operational_signals",
            "why_not_production_yet": (
                "The repo has real APIs, contracts, static exports, and a runtime doctor, but it does not yet implement "
                "the core guarantees a production streaming system is judged on."
            ),
        },
        "discovery_call_questions": [
            "What is the core user job: explain media systems, benchmark fairness, or operate a real-time event product?",
            "Which workflows must be low-latency and interactive, and which can remain batch-oriented?",
            "What event schema is stable enough to support replay, partitioning, and versioned consumers?",
            "What is the canonical source of truth for updates: local CSV refreshes, APIs, or a streaming ingest layer?",
            "Which decisions would an artist, label, platform analyst, or governance team actually take from these outputs?",
            "What latency, scale, and correctness guarantees are required before a buyer would trust this in production?",
        ],
        "architecture_concerns": [
            "The system is still batch-first. It serves JSON cleanly, but it does not yet behave like a durable event-processing architecture.",
            "In-process caching is useful for a public demo, but it is not a substitute for replayable state, checkpoint recovery, or distributed execution.",
            "The data contracts are clearer than many open repos, but there is no event envelope, schema registry, or explicit version-compatibility policy.",
            "Static exports are a strength for distribution, yet they can blur freshness expectations unless every consumer understands the rebuild boundary.",
        ],
        "production_expectations_missing": {
            "runtime_guarantees": [
                "Exactly-once semantics",
                "Checkpointing and recoverable state snapshots",
                "Backpressure management",
                "Replayable event logs",
                "Explicit event ordering guarantees",
                "Partitioning strategy and shard-local routing",
                "Schema evolution policy with compatibility checks",
            ],
            "operations": [
                "Structured metrics with time-series export",
                "Distributed tracing",
                "Alerting thresholds",
                "Failure budgets and SLOs",
                "Runbooks and incident posture",
                "Persistent state recovery drills",
            ],
            "security_and_governance": [
                "Role-based API boundaries",
                "Authn/authz on non-public endpoints",
                "Rate limiting and abuse posture",
                "Signed artifact provenance for exports",
                "Data retention and deletion policy",
                "Explicit compliance mapping for public-source ingestion",
            ],
        },
        "credibility_gaps": [
            "No end-to-end streaming benchmark demonstrating throughput, latency, or memory posture across increasing event volumes.",
            "No replayability demo showing a deterministic rebuild from an append-only event log.",
            "No schema-evolution example proving old and new consumers can coexist safely.",
            "No observability reference dashboard with metrics, traces, and error budgets.",
            "No fault-injection story covering malformed events, partial writes, or interrupted materialization.",
        ],
        "streaming_engineer_expectations": {
            "would_expect": [
                "Explicit ingest -> normalize -> enrich -> serve topology",
                "Serializable event schemas",
                "Offset or watermark management",
                "Progressive materializations",
                "Stateful windowing semantics",
                "Benchmark evidence at 10K, 100K, and 1M+ records",
            ],
            "currently_present": [
                "Clear batch contracts",
                "Static export parity",
                "A runtime doctor",
                "Public quality reporting",
                "Deterministic synthetic-data reproducibility",
            ],
        },
        "trust_and_rejection": {
            "engineering_manager_would_trust_if": [
                "The repo clearly labels batch versus streaming surfaces and stops implying guarantees it has not implemented.",
                "Benchmarks, replay drills, and schema tests exist beside the UI.",
                "Observability and failure behavior are visible without reading the entire codebase.",
            ],
            "enterprise_architect_would_reject_if": [
                "The repo continues to market itself as infrastructure without durable state, replay, compatibility, and operational controls.",
                "Freshness and provenance boundaries remain implicit.",
                "The event model stays undefined while the UI grows more ambitious than the backend.",
            ],
        },
        "interview_and_investor_pressure": {
            "senior_data_engineering_questions": [
                "Where is the event contract and how do consumers evolve safely?",
                "How would you reprocess one year of events after a bug fix?",
                "What breaks first under backpressure?",
                "How do you prove that static exports and live endpoints cannot drift?",
                "Which state is authoritative when materialization and API cache disagree?",
            ],
            "investor_weaknesses": [
                "The moat is clearer in taste and analysis quality than in infrastructure defensibility.",
                "The current architecture demonstrates craft, but not yet large-scale operational inevitability.",
                "The repo signals intelligence well; it still needs stronger proof of repeatable system leverage.",
            ],
        },
        "benchmarks_to_add": [
            "1M-row groupby and aggregation benchmark with pandas baseline and optional Polars or DuckDB acceleration",
            "Progressive materialization benchmark showing time-to-first-result and full-build completion",
            "Replay benchmark from persisted artifacts into regenerated gold outputs",
            "Cold-start versus warm-cache API latency profile",
        ],
        "ai_systems_differentiators": [
            "Public fairness and propagation surfaces that connect analysis to governance questions instead of generic stream plumbing alone",
            "Static/live parity that lets a browser experience run from the same Python outputs",
            "Deterministic synthetic lanes paired with real public music evidence so claims can be taught, challenged, and reproduced",
        ],
        "repo_grade": {
            "verdict": "promising_but_not_yet_streaming_infrastructure",
            "genre_signal_strength": round(genre_known_share, 3),
            "publication_year_coverage": round(publication_year_share, 3),
            "system_count": int((data_engineering.get("operating_model") or {}).get("dataset_count", 0))
            if isinstance(data_engineering, Mapping)
            else 0,
        },
        "roadmap": {
            "quick_wins": [
                "Make the batch-first posture explicit in README, API docs, and system surfaces.",
                "Publish a benchmark harness and baseline timings for 10K, 100K, and 1M records.",
                "Add genre-coverage, freshness, and artifact-parity checks to the doctor output.",
                "Document the public source boundary and rebuild workflow in one operational page.",
            ],
            "medium_improvements": [
                "Introduce versioned event envelopes and compatibility tests.",
                "Add append-only artifact logs plus deterministic replay commands.",
                "Split heavy analysis steps into progressive materialization stages with visible timing.",
                "Add structured metrics, traces, and benchmark result exports.",
            ],
            "major_architecture": [
                "Add a real ingest log with replay and checkpoint semantics.",
                "Introduce partition-aware processing and ordering rules.",
                "Move state materialization from in-process cache to durable, inspectable storage layers.",
                "Prove fault tolerance with interrupted-run recovery, schema migration, and backpressure exercises.",
            ],
        },
    }
