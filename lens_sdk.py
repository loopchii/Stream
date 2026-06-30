"""Public lens SDK for Stream.

This file intentionally exposes a lightweight, inspectable extension surface:
contributors can define a ``KineticLens`` that evaluates grouped stream records
and emits typed findings without touching any proprietary Loopchii systems.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Iterable, Protocol

import pandas as pd


@dataclass(frozen=True)
class GeometricMask:
    """Typed output of a public lens evaluation."""

    verdict: str
    confidence: float
    rationale: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StreamRecord:
    """Grouped public stream record used by the lens SDK."""

    record_id: str
    platform: str
    genre: str
    year: int
    sample_size: int
    metrics: dict[str, float]


@dataclass(frozen=True)
class LensFinding:
    """A finding produced by a ``KineticLens``."""

    lens_id: str
    display_name: str
    mask: GeometricMask

    def to_dict(self) -> dict[str, Any]:
        return {
            "lens_id": self.lens_id,
            "display_name": self.display_name,
            "mask": asdict(self.mask),
        }


class KineticLens(Protocol):
    """Public protocol for writing a stream lens."""

    lens_id: str
    display_name: str
    description: str

    def evaluate(self, record: StreamRecord) -> list[LensFinding]:
        """Evaluate a grouped stream record and return any findings."""


@dataclass
class LensRegistry:
    """Simple public registry for pluggable lenses."""

    lenses: list[KineticLens] = field(default_factory=list)

    def register(self, lens: KineticLens) -> None:
        self.lenses.append(lens)

    def catalog(self) -> list[dict[str, str]]:
        return [
            {
                "lens_id": lens.lens_id,
                "display_name": lens.display_name,
                "description": lens.description,
            }
            for lens in self.lenses
        ]

    def evaluate_record(self, record: StreamRecord) -> list[LensFinding]:
        findings: list[LensFinding] = []
        for lens in self.lenses:
            findings.extend(lens.evaluate(record))
        return findings


class LeadBalanceLens:
    lens_id = "lead_balance"
    display_name = "Lead Balance Lens"
    description = "Flags platform-genre-year groups where lead roles skew too heavily toward one gender."

    def evaluate(self, record: StreamRecord) -> list[LensFinding]:
        share = record.metrics["male_lead_share"]
        if 0.35 <= share <= 0.65:
            return []
        severity = abs(share - 0.5) * 2
        verdict = "block" if share >= 0.82 or share <= 0.18 else "review"
        rationale = (
            f"Lead-role distribution is materially skewed in {record.platform} / {record.genre} / {record.year}."
        )
        return [
            LensFinding(
                lens_id=self.lens_id,
                display_name=self.display_name,
                mask=GeometricMask(
                    verdict=verdict,
                    confidence=round(min(0.99, 0.55 + severity * 0.4), 3),
                    rationale=rationale,
                    evidence={
                        "male_lead_share": round(share, 4),
                        "female_lead_share": round(record.metrics["female_lead_share"], 4),
                        "sample_size": record.sample_size,
                    },
                ),
            )
        ]


class DialogueSkewLens:
    lens_id = "dialogue_skew"
    display_name = "Dialogue Skew Lens"
    description = "Flags groups where average dialogue allocation skews sharply by gender."

    def evaluate(self, record: StreamRecord) -> list[LensFinding]:
        gap = record.metrics["dialogue_gap"]
        if gap < 0.22:
            return []
        verdict = "block" if gap >= 0.42 else "review"
        return [
            LensFinding(
                lens_id=self.lens_id,
                display_name=self.display_name,
                mask=GeometricMask(
                    verdict=verdict,
                    confidence=round(min(0.99, 0.58 + gap * 0.5), 3),
                    rationale="Average dialogue share materially diverges between men and women in this grouped record.",
                    evidence={
                        "dialogue_gap": round(gap, 4),
                        "female_dialogue_mean": round(record.metrics["female_dialogue_mean"], 2),
                        "male_dialogue_mean": round(record.metrics["male_dialogue_mean"], 2),
                    },
                ),
            )
        ]


class AgeVisibilityLens:
    lens_id = "age_visibility"
    display_name = "Age Visibility Lens"
    description = "Flags groups where older characters become structurally scarce."

    def evaluate(self, record: StreamRecord) -> list[LensFinding]:
        share = record.metrics["over_50_share"]
        if share >= 0.12:
            return []
        deficit = max(0.0, 0.12 - share)
        verdict = "block" if share <= 0.05 else "review"
        return [
            LensFinding(
                lens_id=self.lens_id,
                display_name=self.display_name,
                mask=GeometricMask(
                    verdict=verdict,
                    confidence=round(min(0.99, 0.56 + deficit * 2.5), 3),
                    rationale="Characters over 50 are sparsely represented in this slice of the stream.",
                    evidence={
                        "over_50_share": round(share, 4),
                        "sample_size": record.sample_size,
                    },
                ),
            )
        ]


class DiversityFloorLens:
    lens_id = "diversity_floor"
    display_name = "Diversity Floor Lens"
    description = "Flags groups whose racial diversity score falls under a public floor."

    def evaluate(self, record: StreamRecord) -> list[LensFinding]:
        score = record.metrics["diversity"]
        if score >= 0.62:
            return []
        deficit = max(0.0, 0.62 - score)
        verdict = "block" if score <= 0.48 else "review"
        return [
            LensFinding(
                lens_id=self.lens_id,
                display_name=self.display_name,
                mask=GeometricMask(
                    verdict=verdict,
                    confidence=round(min(0.99, 0.55 + deficit * 1.2), 3),
                    rationale="Diversity falls below the public floor for this grouped record.",
                    evidence={
                        "diversity": round(score, 4),
                        "gender_parity": round(record.metrics["gender_parity"], 4),
                    },
                ),
            )
        ]


def default_registry() -> LensRegistry:
    registry = LensRegistry()
    registry.register(LeadBalanceLens())
    registry.register(DialogueSkewLens())
    registry.register(AgeVisibilityLens())
    registry.register(DiversityFloorLens())
    return registry


def build_stream_records(df: pd.DataFrame, *, max_groups: int | None = None) -> list[StreamRecord]:
    """Build grouped public stream records from the character-level dataframe."""

    required = {"platform", "genre", "year", "gender", "age_group", "role_type", "dialogue_words", "screen_time", "race"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    grouped = []
    for (platform, genre, year), group in (
        df.groupby(["platform", "genre", "year"], sort=True)
    ):
        sample_size = int(len(group))
        if sample_size == 0:
            continue

        leads = group[group["role_type"] == "lead"]
        lead_count = int(len(leads))
        male_leads = int((leads["gender"] == "male").sum())
        female_leads = int((leads["gender"] == "female").sum())

        dialogue_by_gender = group.groupby("gender")["dialogue_words"].mean()
        male_dialogue = float(dialogue_by_gender.get("male", 0.0))
        female_dialogue = float(dialogue_by_gender.get("female", 0.0))
        dialogue_gap = float(1 - female_dialogue / male_dialogue) if male_dialogue > 0 else 0.0

        race_counts = group["race"].value_counts().to_dict()
        analyzer = _AnalyzerShim()

        grouped.append(
            StreamRecord(
                record_id=f"{platform}:{genre}:{year}",
                platform=str(platform),
                genre=str(genre),
                year=int(year),
                sample_size=sample_size,
                metrics={
                    "diversity": analyzer.diversity_index(group["race"].tolist()),
                    "gender_parity": analyzer.gender_parity(group["gender"].value_counts().to_dict()),
                    "male_lead_share": float(male_leads / lead_count) if lead_count else 0.0,
                    "female_lead_share": float(female_leads / lead_count) if lead_count else 0.0,
                    "dialogue_gap": max(0.0, dialogue_gap),
                    "male_dialogue_mean": male_dialogue,
                    "female_dialogue_mean": female_dialogue,
                    "avg_screen_time": float(group["screen_time"].mean()),
                    "over_50_share": float((group["age_group"] == ">50").mean()),
                    "lead_count": float(lead_count),
                    "race_modes": float(len(race_counts)),
                },
            )
        )

    records = sorted(grouped, key=lambda record: (record.year, record.platform, record.genre))
    return records[:max_groups] if max_groups is not None else records


def evaluate_stream(
    df: pd.DataFrame,
    *,
    registry: LensRegistry | None = None,
    max_groups: int | None = None,
) -> list[dict[str, Any]]:
    """Evaluate the grouped public stream with the active lens registry."""

    registry = registry or default_registry()
    records = build_stream_records(df, max_groups=max_groups)
    evaluations = []
    for record in records:
        findings = registry.evaluate_record(record)
        evaluations.append(
            {
                "record": asdict(record),
                "finding_count": len(findings),
                "findings": [finding.to_dict() for finding in findings],
            }
        )
    return evaluations


class _AnalyzerShim:
    """Small local metric shim to avoid a heavy import cycle."""

    @staticmethod
    def diversity_index(values: Iterable[str]) -> float:
        series = pd.Series(list(values))
        counts = series.value_counts()
        if counts.empty or len(counts) <= 1:
            return 0.0
        probs = counts / counts.sum()
        score = float(-(probs * probs.map(lambda p: 0 if p <= 0 else math.log(p))).sum())
        return score / math.log(len(counts))

    @staticmethod
    def gender_parity(counts: dict[str, int]) -> float:
        total = sum(counts.values())
        if total <= 0:
            return 0.0
        female_ratio = counts.get("female", 0) / total
        return 1 - abs(0.5 - female_ratio) * 2
