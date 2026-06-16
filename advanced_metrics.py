#!/usr/bin/env python3
"""
StreamLens Analytics - Advanced quantitative metrics.

Pure, dependency-light statistical helpers used by the analysis pipeline:
inequality (Gini / Lorenz / Theil), diversity (Simpson), effect sizes
(Cramer's V for goodness-of-fit chi-square), least-squares trend regression,
bootstrap confidence intervals, and a 0-1 -> letter-grade mapping.

Every function is deterministic given its inputs (bootstraps take an explicit
seed) so the dashboard numbers are reproducible. No models are trained here.

Author: Cazandra Aporbo, MS
"""

from collections import Counter
from typing import Callable, Dict, List, Sequence

import numpy as np


def gini(values: Sequence[float]) -> float:
    """Gini coefficient of a non-negative distribution (0 = perfectly equal).

    Uses the rank-weighted formula G = (2 * sum(i * x_i)) / (n * sum(x)) - (n + 1) / n
    over values sorted ascending. Returns 0.0 for empty input or an all-zero total.
    """
    arr = sorted(float(v) for v in values if v is not None and v >= 0)
    n = len(arr)
    total = sum(arr)
    if n == 0 or total == 0:
        return 0.0
    weighted = sum((i + 1) * x for i, x in enumerate(arr))
    g = (2.0 * weighted) / (n * total) - (n + 1) / n
    # Numerical guard: clamp into the valid [0, 1] range.
    return float(min(1.0, max(0.0, g)))


def lorenz_points(values: Sequence[float], buckets: int = 20) -> List[Dict[str, float]]:
    """Lorenz curve as a list of {p, l} points (cumulative population vs value share).

    Always begins at (0, 0) and ends at (1, 1). The curve is down-sampled to at
    most ``buckets`` interior points so it is cheap to plot on the client.
    """
    arr = sorted(float(v) for v in values if v is not None and v >= 0)
    n = len(arr)
    total = sum(arr)
    points = [{"p": 0.0, "l": 0.0}]
    if n == 0 or total == 0:
        points.append({"p": 1.0, "l": 1.0})
        return points
    cumulative = 0.0
    step = max(1, n // buckets)
    for i, x in enumerate(arr, 1):
        cumulative += x
        if i % step == 0 or i == n:
            points.append({"p": i / n, "l": cumulative / total})
    if points[-1]["p"] != 1.0:
        points.append({"p": 1.0, "l": 1.0})
    return points


def theil_index(values: Sequence[float]) -> float:
    """Theil T inequality index (0 = perfect equality; grows with concentration)."""
    arr = [float(v) for v in values if v is not None and v > 0]
    n = len(arr)
    if n == 0:
        return 0.0
    mean = sum(arr) / n
    if mean == 0:
        return 0.0
    t = sum((x / mean) * np.log(x / mean) for x in arr) / n
    return float(max(0.0, t))


def simpson_index(labels: Sequence[str]) -> float:
    """Gini-Simpson diversity index 1 - sum(p_i^2): probability two picks differ."""
    counts = Counter(labels)
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return float(1.0 - sum((c / total) ** 2 for c in counts.values()))


def cramers_v_goodness_of_fit(observed: Sequence[float]) -> Dict[str, float]:
    """Cramer's V effect size for a one-way chi-square goodness-of-fit vs uniform.

    Returns the chi-square statistic, V in [0, 1], and a plain-language magnitude
    band (Cohen-style: negligible/small/medium/large). V answers "how big is the
    skew", which a raw chi-square (which grows with sample size) cannot.
    """
    obs = [float(o) for o in observed if o is not None and o >= 0]
    k = len(obs)
    n = sum(obs)
    if k < 2 or n == 0:
        return {"chi_square": 0.0, "cramers_v": 0.0, "magnitude": "negligible"}
    expected = n / k
    chi_square = sum(((o - expected) ** 2) / expected for o in obs)
    v = float(np.sqrt(chi_square / (n * (k - 1))))
    v = min(1.0, max(0.0, v))
    if v < 0.1:
        magnitude = "negligible"
    elif v < 0.3:
        magnitude = "small"
    elif v < 0.5:
        magnitude = "medium"
    else:
        magnitude = "large"
    return {"chi_square": float(chi_square), "cramers_v": v, "magnitude": magnitude}


def linear_trend(x: Sequence[float], y: Sequence[float]) -> Dict[str, float]:
    """Ordinary least-squares fit. Returns slope, intercept and R-squared."""
    xs = np.asarray(list(x), dtype=float)
    ys = np.asarray(list(y), dtype=float)
    n = len(xs)
    if n < 2 or np.ptp(xs) == 0:
        return {"slope": 0.0, "intercept": float(ys.mean()) if n else 0.0, "r_squared": 0.0}
    slope, intercept = np.polyfit(xs, ys, 1)
    predicted = slope * xs + intercept
    ss_res = float(np.sum((ys - predicted) ** 2))
    ss_tot = float(np.sum((ys - ys.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(max(0.0, min(1.0, r_squared))),
    }


def bootstrap_ci(
    values: Sequence[float],
    statistic: Callable[[np.ndarray], float],
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> Dict[str, float]:
    """Percentile bootstrap confidence interval for an arbitrary statistic.

    Resamples ``values`` with replacement ``n_boot`` times. Deterministic for a
    given seed so the reported uncertainty band is reproducible.
    """
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    if arr.size == 0:
        return {"point": 0.0, "low": 0.0, "high": 0.0}
    rng = np.random.default_rng(seed)
    point = float(statistic(arr))
    estimates = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        sample = arr[rng.integers(0, arr.size, arr.size)]
        estimates[i] = statistic(sample)
    alpha = (1.0 - ci) / 2.0
    low = float(np.quantile(estimates, alpha))
    high = float(np.quantile(estimates, 1.0 - alpha))
    return {"point": point, "low": low, "high": high}


# Grade thresholds applied to a 0-1 score, highest band first.
_GRADE_BANDS = [
    (0.95, "A+"), (0.90, "A"), (0.85, "A-"),
    (0.80, "B+"), (0.75, "B"), (0.70, "B-"),
    (0.65, "C+"), (0.60, "C"), (0.55, "C-"),
    (0.50, "D+"), (0.45, "D"), (0.40, "D-"),
]


def letter_grade(score: float) -> str:
    """Map a 0-1 quality score to a letter grade (A+ down to F)."""
    s = max(0.0, min(1.0, float(score)))
    for threshold, grade in _GRADE_BANDS:
        if s >= threshold:
            return grade
    return "F"
