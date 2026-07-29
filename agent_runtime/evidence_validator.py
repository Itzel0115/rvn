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

        if metric and not _evidence_covers_metric(evidence, str(metric)):
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
        missing.extend(_missing_task_requirement_coverage(canonical, evidence))
        if any(str(item).startswith("metric:") for item in missing):
            issues.append("missing_requested_metric_evidence")
        if any(str(item).startswith("operation:") for item in missing):
            issues.append("missing_requested_operation_evidence")

        if task_family == "metric_relationship_analysis":
            relationship_evidence = [item for item in evidence if item.get("source_tool") == "get_revenue_inventory_relationship"]
            if not relationship_evidence:
                issues.append("missing_relationship_evidence")
                missing.append("paired_revenue_inventory_evidence")
            elif not any(_has_relationship_pair(item) for item in relationship_evidence):
                issues.append("incomplete_relationship_evidence")
                missing.append("paired_revenue_inventory_evidence")
            if time_scope.get("mode") in {"recent_n_months", "date_range", "multi_month_series"}:
                trend_metrics = _trend_metrics(evidence)
                for required_metric in ("revenue_amount", "inventory_amount", "inventory_qty"):
                    if required_metric not in trend_metrics:
                        issues.append("missing_multimetric_trend_evidence")
                        missing.append(f"trend_metric:{required_metric}")
                if not any(_has_limitation(item, "proxy") or _has_limitation(item, "反證") or _has_limitation(item, "counter") for item in evidence):
                    issues.append("missing_proxy_or_counter_limitation")
                    missing.append("proxy_and_counter_limitation")

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



def _missing_task_requirement_coverage(canonical: dict[str, Any], evidence: list[dict[str, Any]]) -> list[str]:
    requirements = canonical.get("task_requirements") or {}
    requested_metrics = [str(item) for item in (requirements.get("requested_metrics") or []) if item]
    requested_operations = {str(item) for item in (requirements.get("requested_operations") or []) if item}
    missing: list[str] = []
    for metric in requested_metrics:
        if not _evidence_covers_metric(evidence, metric):
            missing.append(f"metric:{metric}")
    if "anomaly" in requested_operations and not any(item.get("source_tool") == "get_anomalies" or item.get("evidence_type") == "anomaly" for item in evidence):
        missing.append("operation:anomaly")
    if "proxy" in requested_operations and not any(item.get("source_tool") == "get_inventory_turnover_proxy" for item in evidence):
        missing.append("operation:proxy")
    if "cross_check" in requested_operations:
        covered = {metric for metric in requested_metrics if _evidence_covers_metric(evidence, metric)}
        if len(covered) < min(2, len(set(requested_metrics))):
            missing.append("operation:cross_check")
    if "counter_evidence" in requested_operations and "inventory_qty" in requested_metrics and not _evidence_covers_metric(evidence, "inventory_qty"):
        missing.append("operation:counter_evidence")
    missing.extend(_missing_management_risk_selection_coverage(requirements, evidence))
    return missing


def _missing_management_risk_selection_coverage(requirements: dict[str, Any], evidence: list[dict[str, Any]]) -> list[str]:
    if not requirements.get("requires_named_selection"):
        return []
    top_n = int(requirements.get("requested_top_n") or requirements.get("top_n") or 0)
    if top_n <= 0:
        return ["selection:missing_requested_top_n"]
    missing: list[str] = []
    requested_metrics = set(str(item) for item in requirements.get("requested_metrics") or [])
    trend_metrics = _management_trend_summaries(evidence)
    peer_entities = set().union(*(set(value) for value in trend_metrics.values())) if trend_metrics else set()
    peer_entities = {entity for entity in peer_entities if entity and entity not in {"未對應", "N/A", "None", "null"}}
    if len(peer_entities) < max(top_n + 1, 3):
        missing.append("selection:complete_peer_group_comparison")
    required_core = {"revenue_amount", "inventory_amount", "inventory_qty"} & requested_metrics
    for metric in required_core:
        if len(set(trend_metrics.get(metric, {})) & peer_entities) < max(top_n + 1, 3):
            missing.append(f"selection:complete_metric_peer_comparison:{metric}")
    candidates = _management_risk_candidates(evidence)
    selected = candidates[:top_n]
    if len(selected) != top_n or any(not item.get("entity_value") for item in selected):
        missing.append(f"selection:named_selected_entities:{top_n}")
    if len(candidates) < top_n or all(float(item.get("score") or 0) == 0 for item in candidates[:top_n]):
        missing.append("selection:composite_risk_ranking")
    for item in selected:
        if int(item.get("evidence_metric_count") or 0) < 3:
            missing.append(f"selection:min_three_metric_evidence:{item.get('entity_value')}")
    if requirements.get("requires_counter_evidence") and any(not item.get("counter_evidence") for item in selected):
        missing.append("selection:counter_evidence")
    if requirements.get("requires_recommendation") and any(not item.get("next_action") for item in selected):
        missing.append("selection:next_action")
    return list(dict.fromkeys(missing))


def _management_trend_summaries(evidence: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    by_metric: dict[str, dict[str, dict[str, Any]]] = {}
    for item in evidence:
        if item.get("source_tool") != "get_entity_trend_comparison":
            continue
        metric = str(item.get("metric") or "")
        if not metric:
            continue
        for row in item.get("entity_summaries") or []:
            if not isinstance(row, dict):
                continue
            entity = str(row.get("entity_value") or "").strip()
            if entity:
                by_metric.setdefault(metric, {})[entity] = row
    return by_metric


def _management_risk_candidates(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = _management_trend_summaries(evidence)
    entities = set().union(*(set(value) for value in summaries.values())) if summaries else set()
    anomaly_entities: set[str] = set()
    for item in evidence:
        if item.get("source_tool") == "get_anomalies" and isinstance(item.get("rows"), list):
            rows = item.get("rows") or []
        else:
            rows = [item]
        for row in rows:
            if not isinstance(row, dict):
                continue
            if row.get("異常類型") is None and row.get("訊號") is None and row.get("anomaly_type") is None and row.get("anomaly_signal") is None:
                continue
            entity = str(row.get("entity_value") or row.get("事業群") or row.get("group_code") or row.get("平台") or row.get("platform") or "").strip()
            if entity:
                anomaly_entities.add(entity)
                entities.add(entity)
    candidates: list[dict[str, Any]] = []
    for entity in sorted(entities):
        if entity in {"未對應", "N/A", "None", "null", ""}:
            continue
        metric_count = sum(1 for metric in ["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"] if entity in summaries.get(metric, {}))
        if entity in anomaly_entities:
            metric_count += 1
        score = 0.0
        counter: list[str] = []
        for metric, risk_when in [("revenue_amount", "down"), ("inventory_amount", "up"), ("inventory_qty", "up"), ("revenue_inventory_amount_ratio", "down")]:
            row = summaries.get(metric, {}).get(entity) or {}
            value = _safe_float(row.get("overall_change_pct"))
            if value is None:
                continue
            if (risk_when == "down" and value < 0) or (risk_when == "up" and value > 0):
                score += abs(value)
            else:
                counter.append(metric)
        if entity in anomaly_entities:
            score += 1.0
        elif "risk_score" in (str(metric) for metric in summaries.keys()) or anomaly_entities:
            counter.append("no_primary_anomaly")
        candidates.append({"entity_value": entity, "score": score, "evidence_metric_count": metric_count, "counter_evidence": counter, "next_action": bool(metric_count >= 3)})
    candidates.sort(key=lambda item: (float(item.get("score") or 0), int(item.get("evidence_metric_count") or 0)), reverse=True)
    return candidates


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _evidence_covers_metric(evidence: list[dict[str, Any]], metric: str) -> bool:
    if metric == "risk_score":
        return any(item.get("source_tool") in {"get_anomalies", "get_entity_performance_snapshot"} or item.get("evidence_type") == "anomaly" for item in evidence)
    if metric == "health_score":
        return any(item.get("source_tool") == "get_entity_performance_snapshot" for item in evidence)
    for item in evidence:
        source_tool = item.get("source_tool")
        if _contains_metric(item, metric):
            return True
        if source_tool == "get_revenue_inventory_relationship" and metric in {"revenue_amount", "inventory_amount", "revenue_inventory_amount_ratio"}:
            return True
        if source_tool == "get_entity_performance_snapshot" and metric in {"revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio", "health_score", "risk_score"}:
            return True
        if source_tool == "get_inventory_turnover_proxy" and metric in {"inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"}:
            return True
    return False

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


def _trend_metrics(evidence: list[dict[str, Any]]) -> set[str]:
    metrics: set[str] = set()
    for item in evidence:
        if item.get("source_tool") != "get_entity_trend_comparison":
            continue
        metric = str(item.get("metric") or "")
        if metric:
            metrics.add(metric)
    return metrics


def _has_limitation(item: dict[str, Any], token: str) -> bool:
    lowered = token.lower()
    return any(lowered in str(value).lower() for value in item.get("limitations") or [])


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
