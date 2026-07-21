from __future__ import annotations
from typing import Iterable
from .models import InvestigationCandidate
from .policies import ProactivePolicy

def prioritize(candidates: Iterable[InvestigationCandidate], policy: ProactivePolicy, quality_blocked: bool = False) -> list[InvestigationCandidate]:
    severity={"info":10,"low":25,"medium":50,"high":75,"critical":95}
    for item in candidates:
        score=float(severity[item.severity.value])
        if item.candidate_type == "revenue_inventory_divergence": score += 10
        if item.counter_signals: score -= 20
        if item.candidate_type == "performance_risk": score=min(score, 70)
        if quality_blocked and item.candidate_type != "data_quality_issue": score=0; item.confidence="low"
        item.priority_score=max(0,min(100,score)); item.prioritization_explanation=[f"severity={item.severity.value}", f"quality_blocked={quality_blocked}", "counter evidence lowers score"]
    return sorted(candidates, key=lambda item: (-item.priority_score,item.candidate_type,item.candidate_id))[:policy.candidate_limit_per_scan]
