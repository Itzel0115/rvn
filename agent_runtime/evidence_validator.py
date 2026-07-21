from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import AgentRunState, PlanStepStatus
from semantic_layer import get_catalog


@dataclass(frozen=True)
class EvidenceValidationResult:
    sufficient: bool
    needs_replan: bool
    issues: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    suggested_tools: list[str] = field(default_factory=list)
    confidence: str = "low"
    stop_recommended: bool = False


class EvidenceValidator:
    """Post-execution coverage checks; this intentionally complements PlanValidator."""

    def validate(self, state: AgentRunState) -> EvidenceValidationResult:
        issues: list[str] = []
        missing: list[str] = []
        successful = [step for step in state.steps if step.status == PlanStepStatus.SUCCEEDED]
        empty_or_failed = [step for step in state.steps if step.status in {PlanStepStatus.EMPTY, PlanStepStatus.FAILED}]
        evidence = list(state.evidence)
        if not successful:
            issues.append("no_successful_tool_execution")
            missing.append("successful_tool_result")
        if state.steps and len(empty_or_failed) == len(state.steps):
            issues.append("all_tool_results_empty_or_failed")

        canonical = state.canonical_task or {}
        task_family = str(canonical.get("task_family") or "")
        time_scope = canonical.get("time_scope") or {}
        target = canonical.get("target_entity") or {}
        metric = canonical.get("metric")
        source_tools = {str(item.get("source_tool") or item.get("tool_name") or "") for item in evidence}
        try:
            semantic_requirement = get_catalog().get_task_requirement(task_family)
        except (ValueError, KeyError):
            semantic_requirement = None
        if semantic_requirement and canonical.get("semantic_task_requirement_id"):
            if not any(tool in source_tools for tool in semantic_requirement.allowed_primary_tools):
                issues.append("missing_semantic_primary_evidence")
                missing.append(semantic_requirement.requirement_id)

        primary_steps = [step for step in state.steps if step.purpose.startswith("primary")]
        for step in primary_steps:
            if step.status not in {PlanStepStatus.SUCCEEDED, PlanStepStatus.SKIPPED} and not evidence:
                missing.append(f"primary_evidence:{step.tool_name}")

        metric_tools = {"revenue_amount": {"get_revenue_inventory_relationship"}, "inventory_amount": {"get_revenue_inventory_relationship"}}
        if metric and not any(_contains_metric(item, str(metric)) or item.get("source_tool") in metric_tools.get(str(metric), set()) for item in evidence):
            issues.append("missing_metric_evidence")
            missing.append(f"metric:{metric}")
        month = time_scope.get("month") or time_scope.get("single_month")
        if month and not any(_contains_value(item, str(month)) for item in evidence):
            issues.append("missing_requested_month")
            missing.append(f"month:{month}")
        if time_scope.get("mode") == "period_pair":
            for period in (time_scope.get("period_a"), time_scope.get("period_b")):
                if period and not any(_contains_value(item, str(period)) for item in evidence):
                    issues.append("missing_period_pair_evidence")
                    missing.append(f"period:{period}")
        entity = target.get("value")
        if entity and not any(_contains_value(item, str(entity)) for item in evidence):
            issues.append("missing_target_entity")
            missing.append(f"entity:{entity}")
        if task_family in {"entity_ranking", "metric_relationship_analysis", "contribution_analysis"}:
            required_key = "contributors" if task_family == "contribution_analysis" else "rows"
            if not any(_has_rows(item, required_key) for item in evidence):
                issues.append(f"missing_{task_family}_rows")
                missing.append(required_key)
        if "trend" in task_family and not any(_row_count(item) >= 2 for item in evidence):
            issues.append("insufficient_trend_points")
            missing.append("at_least_two_time_points")
        if task_family == "diagnosis" and len(evidence) < 2:
            issues.append("diagnosis_missing_supporting_evidence")
            missing.append("supporting_evidence")
        if task_family == "metric_relationship_analysis":
            relationship_evidence = [item for item in evidence if item.get("source_tool") == "get_revenue_inventory_relationship"]
            if not relationship_evidence:
                issues.append("missing_relationship_evidence")
                missing.append("paired_revenue_inventory_evidence")
            elif not any(_has_relationship_pair(item) for item in relationship_evidence):
                issues.append("incomplete_relationship_evidence")
                missing.append("paired_revenue_inventory_evidence")

        duplicate = _has_duplicate_exhaustion(state)
        if duplicate:
            issues.append("duplicate_tool_call_without_new_evidence")

        # Pipeline warnings are evidence of limitations, never standalone proof.
        if evidence and all(not _meaningful(item) for item in evidence):
            issues.append("warnings_without_data")
            missing.append("meaningful_data")

        unique_missing = list(dict.fromkeys(missing))
        unique_issues = list(dict.fromkeys(issues))
        sufficient = bool(successful) and not unique_missing and not any(issue in unique_issues for issue in {"warnings_without_data", "duplicate_tool_call_without_new_evidence"})
        can_replan = not sufficient and state.replan_count < state.max_replans and state.step_count < state.max_steps and not duplicate
        return EvidenceValidationResult(
            sufficient=sufficient,
            needs_replan=can_replan,
            issues=unique_issues,
            missing_requirements=unique_missing,
            suggested_tools=_suggested_tools(state, unique_missing),
            confidence="high" if sufficient and len(evidence) >= 2 else "medium" if sufficient else "low",
            stop_recommended=not sufficient and not can_replan,
        )


def _contains_value(value: Any, expected: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_value(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains_value(item, expected) for item in value)
    return str(value) == expected


def _contains_metric(value: Any, metric: str) -> bool:
    aliases = {metric, {"revenue_amount": "revenue", "inventory_amount": "inventory", "inventory_qty": "qty"}.get(metric, metric)}
    if isinstance(value, dict):
        return any(str(value.get(key)) in aliases for key in ("metric", "metric_key", "metric_label")) or any(_contains_metric(v, metric) for v in value.values())
    if isinstance(value, list):
        return any(_contains_metric(item, metric) for item in value)
    return False


def _row_count(item: dict[str, Any]) -> int:
    for key in ("rows", "breakdown", "contributors", "candidates"):
        value = item.get(key)
        if isinstance(value, list):
            return len(value)
    return int(item.get("row_count") or (item.get("summary") or {}).get("row_count") or 0)


def _has_rows(item: dict[str, Any], key: str) -> bool:
    if key == "contributors":
        return bool(item.get("contributors") or item.get("rows"))
    return _row_count(item) > 0


def _meaningful(item: dict[str, Any]) -> bool:
    return _row_count(item) > 0 or item.get("value") is not None or item.get("overall") or item.get("summary")


def _has_relationship_pair(item: dict[str, Any]) -> bool:
    rows = item.get("rows") or []
    return any(
        isinstance(row, dict) and row.get("revenue_change") is not None and row.get("inventory_change") is not None
        for row in rows
    )


def _has_duplicate_exhaustion(state: AgentRunState) -> bool:
    fingerprints: dict[tuple[str, str], list[PlanStepStatus]] = {}
    for step in state.steps:
        key = (step.tool_name, repr(sorted(step.tool_args.items())))
        fingerprints.setdefault(key, []).append(step.status)
    return any(len(statuses) > 1 and all(s in {PlanStepStatus.EMPTY, PlanStepStatus.FAILED} for s in statuses) for statuses in fingerprints.values())


def _suggested_tools(state: AgentRunState, missing: list[str]) -> list[str]:
    supporting = list(state.answer_plan_summary.get("supporting_tools") or [])
    primary = list(state.answer_plan_summary.get("primary_tools") or [])
    completed = {step.tool_name for step in state.steps if step.status == PlanStepStatus.SUCCEEDED}
    candidates = [str(tool).split("(", 1)[0] for tool in [*supporting, *primary]]
    return list(dict.fromkeys(tool for tool in candidates if tool not in completed))
