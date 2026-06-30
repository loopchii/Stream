from __future__ import annotations

from typing import Any, Iterable, Mapping


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _avg(values: Iterable[float], default: float = 0.0) -> float:
    items = [value for value in values]
    if not items:
        return default
    return sum(items) / len(items)


def _letter(score: float) -> str:
    bands = [
        (0.95, "A+"),
        (0.90, "A"),
        (0.85, "A-"),
        (0.80, "B+"),
        (0.75, "B"),
        (0.70, "B-"),
        (0.65, "C+"),
        (0.60, "C"),
        (0.55, "C-"),
        (0.50, "D+"),
        (0.45, "D"),
        (0.40, "D-"),
    ]
    for threshold, label in bands:
        if score >= threshold:
            return label
    return "F"


def _status(score: float) -> str:
    if score >= 0.8:
        return "pass"
    if score >= 0.65:
        return "watch"
    return "caution"


def _evidence(label: str, value: Any, note: str) -> dict[str, Any]:
    return {"label": label, "value": value, "note": note}


def _count_risky_fields(contracts: Iterable[Mapping[str, Any]]) -> int:
    risky_tokens = ("email", "phone", "address", "ssn", "dob", "birth", "lat", "lon", "gps")
    count = 0
    for contract in contracts:
        for row in contract.get("schema", []) or []:
            name = str(row.get("name", "")).lower()
            if any(token in name for token in risky_tokens):
                count += 1
    return count


def build_governance_surface(
    data_engineering: Mapping[str, Any],
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
) -> dict[str, Any]:
    synthetic = data_engineering.get("synthetic_contract", {})
    music = data_engineering.get("music_contract", {})
    contracts = [synthetic, music]
    quality_checks = synthetic.get("quality_checks", []) + music.get("quality_checks", [])
    pass_count = sum(1 for check in quality_checks if check.get("status") == "pass")
    warn_count = sum(1 for check in quality_checks if check.get("status") == "warn")
    fail_count = sum(1 for check in quality_checks if check.get("status") == "fail")
    total_checks = len(quality_checks)
    pass_rate = pass_count / total_checks if total_checks else 0.0

    advanced = representation.get("advanced_metrics", {}) if isinstance(representation, Mapping) else {}
    scorecard = advanced.get("scorecard", {}) if isinstance(advanced, Mapping) else {}
    industry = scorecard.get("industry", {}) if isinstance(scorecard, Mapping) else {}
    confidence = advanced.get("confidence", {}) if isinstance(advanced, Mapping) else {}
    effect_sizes = advanced.get("effect_sizes", {}) if isinstance(advanced, Mapping) else {}

    parity_point = _as_float(
        ((confidence.get("gender_parity") or {}).get("point")),
        _as_float((representation.get("overall_metrics") or {}).get("gender_parity")),
    )
    diversity_point = _as_float(
        ((confidence.get("diversity") or {}).get("point")),
        _as_float((representation.get("overall_metrics") or {}).get("diversity_index")),
    )
    parity_width = _as_float(((confidence.get("gender_parity") or {}).get("high"))) - _as_float(
        ((confidence.get("gender_parity") or {}).get("low"))
    )
    diversity_width = _as_float(((confidence.get("diversity") or {}).get("high"))) - _as_float(
        ((confidence.get("diversity") or {}).get("low"))
    )
    confidence_tightness = _clamp(1 - (_avg([parity_width, diversity_width], 0.2) / 0.2))

    industry_score = _as_float(
        industry.get("overall"),
        _avg(
            [
                _as_float(industry.get("diversity")),
                _as_float(industry.get("parity")),
                _as_float(industry.get("dialogue_equity")),
                _as_float(industry.get("screen_equity")),
            ],
            0.0,
        ),
    )
    industry_grade = str(industry.get("grade") or _letter(industry_score))

    effect_values = [
        _as_float((effect_sizes.get("gender_dialogue") or {}).get("cramers_v")),
        _as_float((effect_sizes.get("age_dialogue") or {}).get("cramers_v")),
        _as_float((effect_sizes.get("racial_dialogue") or {}).get("cramers_v")),
    ]
    effect_pressure = _avg([value for value in effect_values if value > 0], 0.0)
    discrimination_readiness = _clamp(1 - effect_pressure)
    strongest_effect = max(
        (
            {
                "label": key.replace("_", " "),
                "cramers_v": _as_float((payload or {}).get("cramers_v")),
                "magnitude": str((payload or {}).get("magnitude", "unknown")),
            }
            for key, payload in effect_sizes.items()
        ),
        key=lambda item: item["cramers_v"],
        default={"label": "none", "cramers_v": 0.0, "magnitude": "unknown"},
    )

    decision_lab = music_report.get("decision_lab", {}) if isinstance(music_report, Mapping) else {}
    trust = decision_lab.get("trust", {}) if isinstance(decision_lab, Mapping) else {}
    music_quality = music_report.get("quality", {}) if isinstance(music_report, Mapping) else {}
    music_coverage = music_quality.get("coverage", {}) if isinstance(music_quality, Mapping) else {}
    year_explicit_share = _as_float(music_coverage.get("publication_year_explicit_share"))
    year_inferred_share = _as_float(music_coverage.get("publication_year_inferred_share"))
    time_support = _clamp(year_explicit_share + (year_inferred_share * 0.35))
    trust_score = _as_float(trust.get("score"), 0.0)

    risky_fields = _count_risky_fields(contracts)
    lane_separation = any(
        "stay separated" in str(item.get("detail", "")).lower()
        for item in data_engineering.get("quality_highlights", []) or []
    )
    data_scope_discipline = _clamp(
        0.72 + (0.16 if lane_separation else 0.0) + (0.12 if risky_fields == 0 else 0.0) - min(risky_fields * 0.1, 0.3)
    )
    gdpr_boundary = _clamp(0.38 + (0.17 if risky_fields == 0 else 0.0) + (0.12 if lane_separation else 0.0) + (0.08 if total_checks else 0.0))
    decision_readiness = _clamp(_avg([trust_score, confidence_tightness, pass_rate, time_support], 0.0))
    human_review_required = strongest_effect["cramers_v"] >= 0.3 or decision_readiness < 0.78

    domains = [
        {
            "id": "fairness_controls",
            "label": "Algorithmic fairness",
            "score": round(industry_score, 3),
            "grade": industry_grade,
            "status": _status(industry_score),
            "headline": "The fairness lane is usable, but it is not self-certifying.",
            "note": (
                f"Industry-level readiness is {industry_grade}. Diversity ({diversity_point:.3f}), parity ({parity_point:.3f}), "
                f"dialogue equity ({_as_float(industry.get('dialogue_equity')):.3f}), and screen equity "
                f"({_as_float(industry.get('screen_equity')):.3f}) all need to travel together before this repo should present a calm fairness story."
            ),
            "evidence": [
                _evidence("Industry grade", industry_grade, "Compressed read across the four representation dimensions."),
                _evidence("Parity point", f"{parity_point:.3f}", "Centered closer to 1.0 means less headline imbalance."),
                _evidence("Diversity point", f"{diversity_point:.3f}", "Breadth matters, but it is not the whole fairness picture."),
                _evidence("Average confidence spread", f"{_avg([parity_width, diversity_width], 0.0):.3f}", "Wider bands mean the fairness claim should stay softer."),
            ],
            "route": {"tab": "scorecard", "target": "scorecardVerdict", "label": "Open decision grade"},
        },
        {
            "id": "discrimination_pressure",
            "label": "Discrimination pressure",
            "score": round(discrimination_readiness, 3),
            "grade": _letter(discrimination_readiness),
            "status": _status(discrimination_readiness),
            "headline": "The effect sizes are too large to wave away as presentation noise.",
            "note": (
                f"Dialogue-related group differences stay material. The strongest current effect is {strongest_effect['label']} at "
                f"Cramér's V {strongest_effect['cramers_v']:.3f} ({strongest_effect['magnitude']}). "
                "That means this surface should raise structural-risk questions, not only summarize distribution."
            ),
            "evidence": [
                _evidence("Mean effect pressure", f"{effect_pressure:.3f}", "Average Cramér's V across the measured dialogue disparity tests."),
                _evidence("Gender dialogue", f"{_as_float((effect_sizes.get('gender_dialogue') or {}).get('cramers_v')):.3f}", "If this stays high, role voice is still stratified."),
                _evidence("Racial dialogue", f"{_as_float((effect_sizes.get('racial_dialogue') or {}).get('cramers_v')):.3f}", "High values mean speaking share is not distributing neutrally."),
                _evidence("Age dialogue", f"{_as_float((effect_sizes.get('age_dialogue') or {}).get('cramers_v')):.3f}", "Generational visibility can flatten long before it is obvious in the UI."),
            ],
            "route": {"tab": "library", "target": "libraryPropagationStudio", "label": "Trace propagation"},
        },
        {
            "id": "data_scope",
            "label": "Data-scope discipline",
            "score": round(data_scope_discipline, 3),
            "grade": _letter(data_scope_discipline),
            "status": _status(data_scope_discipline),
            "headline": "The public scope is tight enough to inspect without pretending to be a private trust platform.",
            "note": (
                "The repo keeps synthetic representation data and public music rows in separate lanes, exposes the contract for both, "
                "and avoids direct contact or location fields in the current contracted schemas. That is strong public-scope discipline."
            ),
            "evidence": [
                _evidence("Contracted datasets", str(len([contract for contract in contracts if contract])), "Separate lanes help keep methods and claims honest."),
                _evidence("Risky fields detected", str(risky_fields), "Count of direct-identifier style field names in the public schemas."),
                _evidence("Lane separation", "yes" if lane_separation else "partial", "Synthetic and public lanes should remain visibly distinct."),
                _evidence("Manual refresh disclosure", "yes", "The music lane does not pretend to be a hidden live ingestion firehose."),
            ],
            "route": {"tab": "learn", "target": "learnDataSystem", "label": "Inspect contracts"},
        },
        {
            "id": "gdpr_boundary",
            "label": "GDPR and consent boundary",
            "score": round(gdpr_boundary, 3),
            "grade": _letter(gdpr_boundary),
            "status": _status(gdpr_boundary),
            "headline": "Useful for public research, not sufficient for subject-rights automation.",
            "note": (
                "This repository is an open-source analysis repo. It does not implement lawful-basis routing, DSAR handling, deletion receipts, "
                "or per-subject consent tracking. That is the right boundary for open work, and it should stay visible."
            ),
            "evidence": [
                _evidence("Personal contact fields", str(risky_fields), "The current public schemas avoid obvious personal-contact columns."),
                _evidence("Subject-rights flows", "not implemented", "There is no DSAR or deletion orchestration in this repo today."),
                _evidence("Refresh posture", "manual + declared", "Public-source refreshes are explicit instead of silently continuous."),
                _evidence("Public-source lane", "yes", "The music module is built from committed public datasets."),
            ],
            "route": {"tab": "learn", "target": "learnDataSystem", "label": "Read the boundary"},
        },
        {
            "id": "human_review",
            "label": "Decision and human review",
            "score": round(decision_readiness, 3),
            "grade": _letter(decision_readiness),
            "status": _status(decision_readiness),
            "headline": "The repo should route decisions, not finalize them alone.",
            "note": (
                f"Trust posture is {str(trust.get('grade', 'n/a'))}, year support lands at {time_support:.3f}, and the average confidence spread "
                f"is {_avg([parity_width, diversity_width], 0.0):.3f}. That is enough to guide review and prioritization, but high-stakes calls still need a human."
            ),
            "evidence": [
                _evidence("Trust score", f"{trust_score:.3f}", "Public music trust surface: coverage, source balance, and freshness."),
                _evidence("Time support", f"{time_support:.3f}", "Explicit years count more than inferred ones when the question is trend."),
                _evidence("Pass rate", f"{pass_rate:.0%}", "Visible quality gates that passed in the current contracted datasets."),
                _evidence("Human review", "required" if human_review_required else "recommended", "A visible guard against auto-escalating soft evidence."),
            ],
            "route": {"tab": "music", "target": "mvAuditPanel", "label": "Open audit"},
        },
    ]
    readiness_score = _avg([domain["score"] for domain in domains], 0.0)

    return {
        "summary": {
            "title": "Public governance contract",
            "repository_mode": "independent_open_source_surface",
            "independence_note": (
                "This repository runs on its own public Python, static-export, and browser stack. "
                "It is not a thin shell over a private LOOPCHii platform service."
            ),
            "claim_boundary": (
                "Governance here means public evidence, visible controls, and explicit human-review thresholds. "
                "It does not mean private-platform enforcement has been open-sourced."
            ),
            "quality_check_count": total_checks,
            "pass_rate": round(pass_rate, 3),
            "readiness_score": round(readiness_score, 3),
            "readiness_grade": _letter(readiness_score),
            "human_review_required": human_review_required,
        },
        "quality_check_count": total_checks,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "contracts": {
            "synthetic_dataset": synthetic.get("dataset_id"),
            "music_dataset": music.get("dataset_id"),
        },
        "insight_count": (
            len(representation.get("insights", []))
            if isinstance(representation.get("insights"), list)
            else 0
        ),
        "domains": domains,
        "questions": [
            "Would this claim still hold if the inferred-year rows were removed?",
            "Are we describing a fairness gap, or flattening a genre or platform confounder into one story?",
            "Is this surface helping a human review better, or is it being asked to make the decision by itself?",
            "What extra metadata would turn the weakest governance grade into something more defensible?",
        ],
        "contribution_paths": [
            {
                "title": "Strengthen fairness tests",
                "detail": "Add deeper subgroup checks, counterfactual analysis, or stronger uncertainty explanations where current effect sizes stay large.",
                "lane": "backend",
            },
            {
                "title": "Improve public-data rights posture",
                "detail": "Document what a future consent, deletion, or lawful-basis workflow would need before this surface could handle private user data.",
                "lane": "docs",
            },
            {
                "title": "Expand year and source coverage carefully",
                "detail": "The trust surface improves when more rows carry explicit time and language labels without pretending certainty where the source is thin.",
                "lane": "data",
            },
            {
                "title": "Keep the boundary legible in the UI",
                "detail": "Refine the browser flow so readers can see when a result is strong enough to act on and when it still needs a person in the loop.",
                "lane": "ui",
            },
        ],
    }
