from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class ProactivePolicy:
    version: str = "proactive-policy.v1"; minimum_relative_change: float = 0.10; minimum_absolute_change: float = 0.0
    minimum_periods: int = 3; candidate_limit_per_scan: int = 5; candidate_limit_per_detector: int = 3
    minimum_confidence: float = 0.45; publication_risk_threshold: str = "medium"
    weights: tuple[int, int, int] = (45, 30, 25)

def load_policy() -> ProactivePolicy:
    def number(name: str, default: float) -> float:
        raw=os.getenv(name); return default if raw is None else float(raw)
    try:
        return ProactivePolicy(minimum_relative_change=number("PROACTIVE_MIN_RELATIVE_CHANGE", .10), minimum_absolute_change=number("PROACTIVE_MIN_ABSOLUTE_CHANGE", 0.0), minimum_periods=int(number("PROACTIVE_MIN_PERIODS", 3)), candidate_limit_per_scan=int(number("PROACTIVE_CANDIDATE_LIMIT", 5)), candidate_limit_per_detector=int(number("PROACTIVE_CANDIDATE_LIMIT_PER_DETECTOR", 3)))
    except ValueError as exc: raise ValueError("Invalid proactive policy environment value") from exc
