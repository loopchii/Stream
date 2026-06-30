#!/usr/bin/env python3
"""Terminal-first demo for the public Stream lens SDK."""

from __future__ import annotations

import argparse
import itertools
import sys
import time

import numpy as np

from lens_sdk import default_registry, evaluate_stream
from streamlens_processor import DataProcessor


RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
RED = "\033[91m"
AMBER = "\033[93m"
MINT = "\033[96m"
PINK = "\033[95m"


def _bar(value: float, width: int = 18, fill: str = "█") -> str:
    value = max(0.0, min(1.0, value))
    filled = int(round(value * width))
    return fill * filled + "·" * (width - filled)


def _headline() -> None:
    print()
    print(f"{BOLD}{MINT}STREAM LENS VISUALIZER{RESET}")
    print(f"{DIM}Public terminal hologram for grouped media-stream findings{RESET}")
    print()


def _print_record(evaluation: dict) -> None:
    record = evaluation["record"]
    metrics = record["metrics"]
    findings = evaluation["findings"]

    print(
        f"{BOLD}{record['platform'].replace('_', ' ').title():<14}{RESET}"
        f" {record['genre']:<12} {record['year']}  "
        f"size={record['sample_size']:<3}"
    )
    print(
        f"  diversity   {PINK}{_bar(metrics['diversity'])}{RESET} {metrics['diversity']:.2f}    "
        f"parity   {MINT}{_bar(metrics['gender_parity'])}{RESET} {metrics['gender_parity']:.2f}"
    )
    print(
        f"  lead skew   {AMBER}{_bar(metrics['male_lead_share'])}{RESET} {metrics['male_lead_share']:.2f}    "
        f"dialogue gap {RED}{_bar(metrics['dialogue_gap'])}{RESET} {metrics['dialogue_gap']:.2f}"
    )
    if not findings:
        print(f"  {DIM}[CLEAR] no active public-lens findings{RESET}")
        print()
        return

    for finding in findings:
        verdict = finding["mask"]["verdict"].upper()
        color = RED if verdict == "BLOCK" else AMBER
        print(
            f"  {color}[{verdict}] {finding['display_name']}{RESET} "
            f"{DIM}{finding['mask']['rationale']}{RESET}"
        )
    hottest = findings[0]
    print(
        f"  {RED}[APOPTOSIS]{RESET} stream record stressed at "
        f"{record['record_id']}  confidence={hottest['mask']['confidence']:.2f}"
    )
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the public Stream lens demo in the terminal.")
    parser.add_argument("--samples", type=int, default=400, help="Synthetic sample size for the stream demo.")
    parser.add_argument("--limit", type=int, default=16, help="Maximum grouped records to display.")
    parser.add_argument("--sleep", type=float, default=0.04, help="Delay between records in seconds.")
    args = parser.parse_args()

    np.random.seed(42)
    processor = DataProcessor()
    df = processor.generate_synthetic_data(n_samples=args.samples)
    evaluations = evaluate_stream(df, registry=default_registry(), max_groups=args.limit)

    _headline()
    print(
        f"{DIM}Run time-to-wow path:{RESET} "
        f"{BOLD}python lens_visualizer.py --samples {args.samples} --limit {args.limit}{RESET}"
    )
    print()

    for evaluation in evaluations:
        _print_record(evaluation)
        sys.stdout.flush()
        time.sleep(max(0.0, args.sleep))

    total_findings = sum(item["finding_count"] for item in evaluations)
    blocked = sum(
        1 for item in evaluations for finding in item["findings"]
        if finding["mask"]["verdict"] == "block"
    )
    print(
        f"{BOLD}summary{RESET}  "
        f"records={len(evaluations)}  findings={total_findings}  "
        f"blocked={blocked}  registry={len(default_registry().catalog())} lenses"
    )
    print(f"{DIM}Public lens SDK is meant to be extended, tested, and challenged.{RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
