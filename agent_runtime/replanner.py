from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tool_registry import TOOL_REGISTRY
from semantic_layer import get_catalog

from .models import AgentRunState, PlanStep


@dataclass(frozen=True)
class ReplanProposal:
    steps: list[PlanStep] = field(default_factory=list)
    source: str = "deterministic_repair"
    reason: str = ""


class DeterministicReplanner:
    """Conservative repair: use only planned, registry-approved, non-duplicate tools."""

    def propose(self, state: AgentRunState, missing_requirements: list[str]) -> ReplanProposal:
        if state.replan_count >= state.max_replans:
            return ReplanProposal(reason="max_replans_reached")
        previous = {(step.tool_name, _args_key(step.tool_args)) for step in state.steps}
        candidates = list(state.answer_plan_summary.get("supporting_tools", []))
        try:
            requirement = get_catalog().get_task_requirement(str(state.canonical_task.get("task_family") or ""))
        except (ValueError, KeyError):
            requirement = None
        if requirement and state.canonical_task.get("semantic_task_requirement_id"):
            failed_primary = any(step.tool_name in requirement.allowed_primary_tools and step.status.value in {"empty", "failed"} for step in state.steps)
            candidates = list(requirement.allowed_primary_tools if failed_primary else requirement.allowed_supporting_tools)
        steps: list[PlanStep] = []
        for missing in missing_requirements:
            repair = _repair_for_missing_requirement(str(missing), state.canonical_task)
            if repair is None:
                continue
            tool_name, args = repair
            if tool_name not in TOOL_REGISTRY or (tool_name, _args_key(args)) in previous:
                continue
            sequence = len(state.steps) + len(steps) + 1
            steps.append(PlanStep(
                step_id=f"p{state.current_plan_version + 1}-s{sequence}",
                plan_version=state.current_plan_version + 1,
                sequence=sequence,
                tool_name=tool_name,
                tool_args=args,
                purpose=f"replan evidence repair: {missing}",
            ))
        if steps:
            reason = "missing_multimetric_trend_evidence" if any(str(item).startswith("trend_metric:") for item in missing_requirements) else "missing_evidence"
            return ReplanProposal(steps=steps, reason=reason)
        for raw_name in candidates:
            tool_name = str(raw_name).split("(", 1)[0]
            if tool_name not in TOOL_REGISTRY:
                continue
            args = _args_for_tool(tool_name, state.canonical_task)
            if (tool_name, _args_key(args)) in previous:
                continue
            sequence = len(state.steps) + len(steps) + 1
            steps.append(PlanStep(
                step_id=f"p{state.current_plan_version + 1}-s{sequence}",
                plan_version=state.current_plan_version + 1,
                sequence=sequence,
                tool_name=tool_name,
                tool_args=args,
                purpose="replan evidence repair: " + ", ".join(missing_requirements[:2]),
            ))
        return ReplanProposal(steps=steps, reason="missing_evidence" if steps else "no_legal_non_duplicate_repair")



def _repair_for_missing_requirement(missing: str, canonical: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    task_family = str(canonical.get("task_family") or "")
    if missing.startswith("trend_metric:"):
        metric = missing.split(":", 1)[1]
        return _metric_repair_tool(task_family, metric, canonical, prefer_trend=True)
    if missing.startswith("metric:"):
        metric = missing.split(":", 1)[1]
        return _metric_repair_tool(task_family, metric, canonical, prefer_trend=False)
    if missing.startswith("operation:anomaly"):
        return "get_anomalies", _args_for_tool("get_anomalies", canonical)
    if missing.startswith("operation:proxy"):
        return "get_inventory_turnover_proxy", _args_for_tool("get_inventory_turnover_proxy", canonical)
    if missing.startswith("operation:counter_evidence") and "inventory_qty" in (canonical.get("task_requirements") or {}).get("requested_metrics", []):
        return _metric_repair_tool(task_family, "inventory_qty", canonical, prefer_trend=True)
    return None


def _metric_repair_tool(task_family: str, metric: str, canonical: dict[str, Any], *, prefer_trend: bool) -> tuple[str, dict[str, Any]] | None:
    if metric in {"risk_score"}:
        return "get_anomalies", _args_for_tool("get_anomalies", canonical)
    if metric in {"health_score"}:
        return "get_entity_performance_snapshot", _args_for_tool("get_entity_performance_snapshot", canonical)
    if task_family == "entity_period_pair_table_lookup":
        tool_name = "get_entity_period_pair_table"
    elif task_family == "period_pair_compare":
        tool_name = "get_period_pair_metric_comparison"
    elif task_family == "overall_trend_analysis":
        tool_name = "get_overall_time_series"
    elif prefer_trend or task_family in {"entity_trend_comparison", "metric_relationship_analysis", "risk_scan"}:
        tool_name = "get_entity_trend_comparison"
    elif task_family in {"risk_scan", "performance_assessment"} and metric in {"inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"}:
        tool_name = "get_inventory_turnover_proxy"
    else:
        tool_name = "get_entity_trend_comparison"
    if tool_name not in TOOL_REGISTRY:
        return None
    args = _args_for_tool(tool_name, canonical)
    if "metric" in TOOL_REGISTRY[tool_name].allowed_args:
        args["metric"] = "revenue" if tool_name in {"get_entity_period_pair_comparison", "get_period_pair_metric_comparison"} and metric == "revenue_amount" else metric
    return tool_name, args

def _args_key(args: dict[str, Any]) -> str:
    return repr(sorted(args.items()))


def _args_for_tool(tool_name: str, canonical: dict[str, Any]) -> dict[str, Any]:
    contract = TOOL_REGISTRY[tool_name]
    time_scope = canonical.get("time_scope") or {}
    target = canonical.get("target_entity") or {}
    parent = canonical.get("parent_entity") or {}
    args: dict[str, Any] = {}
    allowed = set(contract.allowed_args)
    if "metric" in allowed and canonical.get("metric"):
        metric = canonical["metric"]
        if tool_name in {"get_entity_period_pair_comparison", "get_period_pair_metric_comparison"} and metric == "revenue_amount":
            metric = "revenue"
        args["metric"] = metric
    selected_dimension = target.get("dimension") if target.get("dimension") not in {None, "overall"} else "business_group"
    if "entity_dimension" in allowed:
        args["entity_dimension"] = selected_dimension
    if "dimension" in allowed and "entity_dimension" not in allowed:
        args["dimension"] = selected_dimension
    if "entity_value" in allowed and target.get("value"):
        args["entity_value"] = target["value"]
    for key in ("month", "period_a", "period_b", "start_month", "end_month", "recent_n"):
        if key in allowed and time_scope.get(key) is not None:
            args[key] = time_scope[key]
    requirements = canonical.get("task_requirements") or {}
    if "top_n" in allowed and requirements.get("top_n") is not None:
        args["top_n"] = requirements.get("top_n")
    if "parent_filter" in allowed and parent.get("value"):
        args["parent_filter"] = {str(parent.get("dimension") or "business_group"): parent["value"]}
    return args
