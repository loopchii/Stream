from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    try:
        denominator = float(denominator)
        if denominator == 0:
            return default
        return float(numerator) / denominator
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def pct(value: float, digits: int = 1) -> float:
    return round(float(value) * 100.0, digits)
