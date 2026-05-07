from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from config import (
    COL_ANOMALY_SIGNAL,
    COL_ANOMALY_TYPE,
    COL_CORR_VALUE,
    COL_GROUP_CODE,
    COL_INV_AMOUNT,
    COL_INV_QTY,
    COL_MONTH,
    COL_PLATFORM,
    COL_REVENUE,
)
from utils import format_number


class EvidenceRole(str, Enum):
    PRIMARY = "primary"
    SUPPORTING = "supporting"
    BACKGROUND = "background"
    DEBUG = "debug"


@dataclass(frozen=True)
class EvidenceItemWithRole:
    role: str
    evidence_type: str
    source_tool: str
    summary: str
    details: dict[str, Any]
    display_priority: int
    reason: str
    domain: str | None = None


@dataclass(frozen=True)
class RubricResult:
    task_family: str
    rubric_name: str
    evidence: list[EvidenceItemWithRole] = field(default_factory=list)
    primary_count: int = 0
    supporting_count: int = 0
    background_count: int = 0
    debug_count: int = 0


@dataclass(frozen=True)
class Rubric:
    task_family: str
    name: str


def get_rubric(task_profile: Any, answer_plan: Any) -> Rubric:
    task_family = getattr(task_profile, "task_family", "metric_lookup") or "metric_lookup"
    return Rubric(task_family=task_family, name=f"{task_family}_rubric_v1")


def assign_evidence_roles(task_profile: Any, answer_plan: Any, domain_results: list[Any]) -> RubricResult:
    rubric = get_rubric(task_profile, answer_plan)
    task_family = rubric.task_family
    requested_month = (getattr(task_profile, "time_scope", {}) or {}).get("month")
    items: list[EvidenceItemWithRole] = []

    for result in domain_results:
        domain = getattr(result, "domain", None)
        for raw in getattr(result, "evidence", []):
            if not isinstance(raw, dict):
                continue
            evidence_type = _detect_evidence_type(raw, domain)
            source_tool = _infer_source_tool(evidence_type, raw)
            role, priority, reason = _assign_role(
                task_family=task_family,
                evidence_type=evidence_type,
                source_tool=source_tool,
                details=raw,
                requested_month=requested_month,
            )
            items.append(
                EvidenceItemWithRole(
                    role=role.value,
                    evidence_type=evidence_type,
                    source_tool=source_tool,
                    summary=_summarize_evidence(evidence_type, raw, domain),
                    details=raw,
                    display_priority=priority,
                    reason=reason,
                    domain=domain,
                )
            )

    items = sorted(items, key=lambda item: (_role_sort(item.role), item.display_priority, item.summary))
    return RubricResult(
        task_family=task_family,
        rubric_name=rubric.name,
        evidence=items,
        primary_count=sum(1 for item in items if item.role == EvidenceRole.PRIMARY.value),
        supporting_count=sum(1 for item in items if item.role == EvidenceRole.SUPPORTING.value),
        background_count=sum(1 for item in items if item.role == EvidenceRole.BACKGROUND.value),
        debug_count=sum(1 for item in items if item.role == EvidenceRole.DEBUG.value),
    )


def rubric_result_to_dict(result: RubricResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["evidence"] = [asdict(item) for item in result.evidence]
    return payload


def _assign_role(
    *,
    task_family: str,
    evidence_type: str,
    source_tool: str,
    details: dict[str, Any],
    requested_month: str | None,
) -> tuple[EvidenceRole, int, str]:
    same_month = _is_same_month(details, requested_month)

    if task_family == "cross_section_compare":
        if evidence_type in {"platform_performance_snapshot", "platform_performance_row"}:
            return EvidenceRole.PRIMARY, 1, "platform performance scorecard can drive same-month cross-section comparison"
        if evidence_type in {"platform_ratio", "inventory_turnover_proxy", "platform_metric_snapshot"} and same_month:
            return EvidenceRole.PRIMARY, 5, "same-month platform revenue/inventory comparison evidence"
        if evidence_type == "anomaly" and same_month:
            return EvidenceRole.SUPPORTING, 20, "same-month anomaly can support the comparison"
        if evidence_type in {"contribution_analysis", "yoy_mom_breakdown", "correlation", "platform_ranking", "group_ranking"}:
            return EvidenceRole.BACKGROUND, 80, "not primary for same-month cross-section comparison"
        return EvidenceRole.BACKGROUND, 90, "not part of cross-section primary rubric"

    if task_family == "performance_assessment":
        if evidence_type in {"platform_performance_snapshot", "platform_performance_row"}:
            return EvidenceRole.PRIMARY, 1, "performance assessment uses deterministic platform scorecard evidence"
        if evidence_type in {"inventory_turnover_proxy", "platform_ratio"}:
            return EvidenceRole.SUPPORTING, 20, "revenue-to-inventory proxy supports the platform scorecard"
        if evidence_type in {"anomaly", "yoy_mom_breakdown"}:
            return EvidenceRole.SUPPORTING, 30, "risk or momentum can support platform performance assessment"
        if source_tool == "get_platform_ranking(inventory_amount)" or evidence_type in {"platform_ranking", "group_ranking", "correlation"}:
            return EvidenceRole.BACKGROUND, 80, "single metric inventory ranking cannot determine performance"
        return EvidenceRole.BACKGROUND, 90, "not part of performance primary rubric"

    if task_family == "time_compare":
        if evidence_type == "contribution_analysis":
            return EvidenceRole.PRIMARY, 1, "period-over-period contribution evidence answers who drove the change"
        if evidence_type == "yoy_mom_breakdown":
            return EvidenceRole.PRIMARY, 2, "period-over-period comparison requires change evidence"
        if evidence_type == "anomaly" and same_month:
            return EvidenceRole.SUPPORTING, 20, "same-period anomaly can support time comparison"
        return EvidenceRole.BACKGROUND, 80, "not primary for period comparison"

    if task_family == "diagnosis":
        if evidence_type in {"root_cause_candidate", "contribution_analysis"}:
            return EvidenceRole.PRIMARY, 1, "diagnosis uses deterministic candidate observations and contribution evidence"
        if evidence_type in {"anomaly", "inventory_turnover_proxy", "platform_ratio", "yoy_mom_breakdown"}:
            return EvidenceRole.SUPPORTING, 20, "supporting signal for diagnosis"
        return EvidenceRole.BACKGROUND, 80, "background only for diagnosis"

    if task_family == "ranking":
        if evidence_type in {"platform_ranking", "group_ranking"}:
            return EvidenceRole.PRIMARY, 1, "explicit ranking evidence"
        if evidence_type == "inventory_turnover_proxy" and "get_inventory_turnover_proxy" in source_tool:
            return EvidenceRole.PRIMARY, 2, "explicit efficiency ranking evidence"
        return EvidenceRole.BACKGROUND, 80, "unrelated to explicit ranking"

    if task_family == "risk_scan":
        if evidence_type in {"anomaly", "inventory_turnover_proxy"}:
            return EvidenceRole.PRIMARY, 1, "risk scan primary signal"
        if evidence_type == "platform_ratio":
            return EvidenceRole.SUPPORTING, 20, "platform ratio supports risk scan"
        return EvidenceRole.BACKGROUND, 80, "background only for risk scan"

    if task_family == "trend_analysis":
        if evidence_type == "yoy_mom_breakdown":
            return EvidenceRole.PRIMARY, 1, "trend analysis uses MoM/YoY evidence"
        if evidence_type == "contribution_analysis":
            return EvidenceRole.SUPPORTING, 20, "contribution can explain trend movement"
        return EvidenceRole.BACKGROUND, 80, "background only for trend analysis"

    if evidence_type in {"debug", "chart_payload", "chart_image"}:
        return EvidenceRole.DEBUG, 100, "debug or presentation artifact"
    return EvidenceRole.PRIMARY, 50, "legacy fallback evidence"


def _detect_evidence_type(item: dict[str, Any], domain: str | None) -> str:
    if item.get("dimension") == "platform" and isinstance(item.get("rows"), list) and item.get("summary") is not None:
        return "platform_performance_snapshot"
    if item.get("platform") and item.get("health_score") is not None and item.get("performance_label"):
        return "platform_performance_row"
    if item.get("root_cause_available") is False and isinstance(item.get("candidates"), list):
        return "root_cause_candidate"
    if isinstance(item.get("contributors"), list):
        return "contribution_analysis"
    if item.get("mom_change") is not None and item.get("metric"):
        return "yoy_mom_breakdown"
    if item.get("efficiency_level") and item.get("revenue_inventory_amount_ratio") is not None:
        return "inventory_turnover_proxy"
    if item.get(COL_ANOMALY_TYPE) or item.get(COL_ANOMALY_SIGNAL) is not None:
        return "anomaly"
    if item.get("dimension") == "platform" and item.get("value_text") is not None:
        return "platform_ranking"
    if item.get(COL_GROUP_CODE) is not None and item.get("value_text") is not None:
        return "group_ranking"
    if item.get("platform") and item.get("revenue_inventory_amount_ratio") is not None:
        return "platform_ratio"
    if item.get(COL_PLATFORM) and (item.get(COL_REVENUE) is not None or item.get(COL_INV_AMOUNT) is not None):
        return "platform_metric_snapshot"
    if item.get(COL_CORR_VALUE) is not None or item.get("correlation") is not None:
        return "correlation"
    if item.get("chart_key") and item.get("chart_type"):
        return "chart_payload"
    if item.get("output_path"):
        return "chart_image"
    if item.get(COL_MONTH):
        return "metric_table"
    return "debug"


def _infer_source_tool(evidence_type: str, item: dict[str, Any]) -> str:
    if evidence_type == "root_cause_candidate":
        return "get_root_cause_candidates"
    if evidence_type == "contribution_analysis":
        metric = item.get("metric") or "metric"
        return f"get_contribution_analysis({metric})"
    if evidence_type == "yoy_mom_breakdown":
        metric = item.get("metric") or "metric"
        return f"get_yoy_mom_breakdown({metric})"
    if evidence_type == "inventory_turnover_proxy":
        return "get_inventory_turnover_proxy"
    if evidence_type in {"platform_performance_snapshot", "platform_performance_row"}:
        return "get_platform_performance_snapshot"
    if evidence_type == "platform_ratio":
        return "get_platform_ratios"
    if evidence_type == "anomaly":
        return "get_anomalies"
    if evidence_type == "platform_ranking":
        metric = item.get("metric") or "metric"
        return f"get_platform_ranking({metric})"
    if evidence_type == "group_ranking":
        metric = item.get("metric") or "metric"
        return f"get_top_groups({metric})"
    if evidence_type == "correlation":
        return "get_correlations"
    if evidence_type == "chart_payload":
        return "get_chart_payload"
    if evidence_type == "chart_image":
        return "create_chart_image"
    return "unknown"


def _summarize_evidence(evidence_type: str, item: dict[str, Any], domain: str | None) -> str:
    if evidence_type in {"platform_ratio", "inventory_turnover_proxy"}:
        return (
            f"{item.get('month')} / {item.get('platform')} revenue/inventory proxy "
            f"{format_number(item.get('revenue_inventory_amount_ratio'))}"
        )
    if evidence_type == "anomaly":
        return (
            f"{item.get(COL_MONTH, 'N/A')} / {item.get(COL_PLATFORM, 'N/A')} anomaly "
            f"{item.get(COL_ANOMALY_TYPE, 'N/A')}"
        )
    if evidence_type == "contribution_analysis":
        first = (item.get("contributors") or [{}])[0]
        return (
            f"{item.get('month')} vs {item.get('previous_month')} top contributor "
            f"{first.get('name')} change {format_number(first.get('change'))}"
        )
    if evidence_type == "yoy_mom_breakdown":
        return (
            f"{item.get('month')} vs {item.get('previous_month')} "
            f"{item.get('metric')} change {format_number(item.get('mom_change'))}"
        )
    if evidence_type == "root_cause_candidate":
        first = (item.get("candidates") or [{}])[0]
        return f"candidate observation: {first.get('title') or first.get('candidate_type')}"
    if evidence_type == "platform_performance_snapshot":
        summary = item.get("summary") or {}
        return (
            f"platform scorecard best={summary.get('best_platform')} "
            f"weakest={summary.get('weakest_platform')}"
        )
    if evidence_type == "platform_performance_row":
        return (
            f"{item.get('month')} / {item.get('platform')} health_score "
            f"{format_number(item.get('health_score'))}"
        )
    if evidence_type in {"platform_ranking", "group_ranking"}:
        subject = item.get("platform") or item.get(COL_GROUP_CODE) or item.get("group_code")
        return f"{evidence_type}: {subject} value {item.get('value_text')}"
    if evidence_type == "platform_metric_snapshot":
        return (
            f"{item.get(COL_MONTH)} / {item.get(COL_PLATFORM)} revenue {format_number(item.get(COL_REVENUE))}, "
            f"inventory {format_number(item.get(COL_INV_AMOUNT))}"
        )
    return f"{domain or 'unknown'}: {evidence_type}"


def _is_same_month(item: dict[str, Any], requested_month: str | None) -> bool:
    if not requested_month:
        return True
    month = item.get("month") or item.get(COL_MONTH)
    return str(month) == str(requested_month)


def _role_sort(role: str) -> int:
    order = {
        EvidenceRole.PRIMARY.value: 0,
        EvidenceRole.SUPPORTING.value: 1,
        EvidenceRole.BACKGROUND.value: 2,
        EvidenceRole.DEBUG.value: 3,
    }
    return order.get(role, 9)
