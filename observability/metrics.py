from __future__ import annotations
from statistics import median
from typing import Any

def summarize_metrics(traces: list[dict[str, Any]]) -> dict[str, Any]:
    durations=[float(t["duration_ms"]) for t in traces if t.get("duration_ms") is not None]
    def pct(p: float): return sorted(durations)[max(0, min(len(durations)-1, int((len(durations)-1)*p)))] if durations else None
    statuses=[t.get("final_status") or t.get("status") for t in traces]
    return {"agent_runs_total":len(traces),"agent_completed_total":statuses.count("completed"),"agent_partial_total":statuses.count("partial"),"agent_failed_total":statuses.count("failed"),"capability_gap_total":sum(t.get("stop_reason")=="capability_gap" for t in traces),"tool_calls_total":sum(int(t.get("tool_call_count") or 0) for t in traces),"replans_total":sum(int(t.get("replan_count") or 0) for t in traces),"agent_run_duration_ms":{"count":len(durations),"mean":sum(durations)/len(durations) if durations else None,"p50":median(durations) if durations else None,"p90":pct(.9),"p95":pct(.95),"max":max(durations) if durations else None}}
