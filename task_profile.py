from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskProfile:
    task_family: str
    business_intent: str | None = None
    target_entity: dict[str, Any] = field(default_factory=dict)
    metrics: list[str] = field(default_factory=list)
    time_scope: dict[str, Any] = field(default_factory=dict)
    comparison_axis: dict[str, Any] = field(default_factory=dict)
    polarity: str | None = None
    analysis_depth: str = "basic"
    answer_style: str = "evidence_first"
    requires_table: bool = False
    requires_limitations: bool = True


PLATFORM_TOKENS = ["platform", "\u5e73\u53f0", "\u5e73\u81fa"]
REVENUE_TOKENS = ["revenue", "sales", "\u71df\u6536", "\u92b7\u552e"]
INVENTORY_TOKENS = ["inventory", "stock", "qty", "\u5eab\u5b58", "\u5b58\u8ca8", "\u91d1\u984d"]
COMPARE_TOKENS = ["compare", "comparison", "versus", " vs ", "\u6bd4\u8f03", "\u5c0d\u6bd4", "\u76f8\u8f03"]
CONTRIBUTION_TOKENS = ["contribution", "contributed", "contribute", "\u8ca2\u737b"]
CHANGE_TOKENS = ["change", "mom", "monthly", "\u8b8a\u5316", "\u6708\u589e", "\u76f8\u8f03"]
PERFORMANCE_TOKENS = ["performance", "performing", "health", "healthy", "stable", "\u8868\u73fe", "\u7e3e\u6548", "\u5065\u5eb7", "\u7a69", "\u512a\u5148\u6ce8\u610f"]
BEST_TOKENS = ["best", "better", "stronger", "highest", "healthiest", "stable", "\u8f03\u4f73", "\u6700\u4f73", "\u8f03\u597d", "\u6700\u597d", "\u6700\u5065\u5eb7", "\u6700\u7a69", "\u6bd4\u8f03\u7a69"]
WORST_TOKENS = ["worst", "weaker", "weakest", "poor", "lowest", "attention", "\u8f03\u5dee", "\u6700\u5dee", "\u8f03\u5f31", "\u9700\u8981\u512a\u5148\u6ce8\u610f", "\u512a\u5148\u6ce8\u610f"]


def build_task_profile(question: str, routing: Any) -> TaskProfile:
    text = question or ""
    lowered = text.lower()
    filters = getattr(routing, "filters", None)
    routed_question_type = getattr(routing, "question_type", "query") or "query"
    routed_answer_strategy = getattr(routing, "answer_strategy", None) or routed_question_type
    target_dimension = getattr(routing, "object_dimension", None) or _infer_target_dimension(text, lowered)
    month = getattr(filters, "month", None) or _extract_month(text)

    if _is_time_compare(text, lowered):
        return TaskProfile(
            task_family="time_compare",
            business_intent="explain_period_change_contribution",
            target_entity={"dimension": target_dimension or "platform", "ids": [], "scope": "all"},
            metrics=_unique(["revenue"] if _has_any(text, lowered, REVENUE_TOKENS) else ["revenue", "inventory_amount"]),
            time_scope={
                "mode": "period_compare",
                "month": month,
                "baseline": _extract_baseline_month(text, month),
                "requires_previous_period": True,
            },
            comparison_axis={"axis": "time", "dimension": "month", "baseline": "previous_period"},
            polarity=None,
            analysis_depth="standard",
            answer_style="evidence_first",
            requires_table=False,
            requires_limitations=True,
        )

    if _is_cross_section_compare(text, lowered, routed_answer_strategy):
        return TaskProfile(
            task_family="cross_section_compare",
            business_intent="compare_platform_metrics_same_month",
            target_entity={"dimension": "platform", "ids": [], "scope": "all"},
            metrics=["revenue", "inventory_amount", "inventory_qty", "revenue_inventory_ratio"],
            time_scope={
                "mode": "single_month",
                "month": month,
                "baseline": None,
                "requires_previous_period": False,
            },
            comparison_axis={"axis": "entity", "dimension": "platform", "baseline": "same_month_peers"},
            polarity=None,
            analysis_depth="standard",
            answer_style="table_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_performance_assessment(text, lowered, routed_answer_strategy):
        polarity = _infer_polarity(text, lowered)
        return TaskProfile(
            task_family="performance_assessment",
            business_intent=f"assess_platform_performance_{polarity or 'neutral'}",
            target_entity={"dimension": "platform", "ids": [], "scope": "all"},
            metrics=["revenue", "inventory_amount", "inventory_turnover_proxy", "anomaly"],
            time_scope={
                "mode": "single_month" if month else "latest_or_overall",
                "month": month,
                "baseline": None,
                "requires_previous_period": False,
            },
            comparison_axis={"axis": "entity", "dimension": "platform", "baseline": "peer_performance"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=False,
            requires_limitations=True,
        )

    return TaskProfile(
        task_family=_fallback_task_family(routed_answer_strategy),
        business_intent=routed_answer_strategy,
        target_entity={"dimension": target_dimension, "ids": [], "scope": "all"},
        metrics=_fallback_metrics(text, lowered, routed_answer_strategy),
        time_scope={
            "mode": "single_month" if month else "unspecified",
            "month": month,
            "baseline": None,
            "requires_previous_period": routed_answer_strategy in {"trend", "diagnosis"},
        },
        comparison_axis=_fallback_comparison_axis(routed_answer_strategy, target_dimension),
        polarity=_infer_polarity(text, lowered),
        analysis_depth="basic",
        answer_style=_fallback_answer_style(routed_answer_strategy),
        requires_table=False,
        requires_limitations=bool(getattr(routing, "requires_limitations", False)) or routed_answer_strategy in {"diagnosis", "risk", "unsupported"},
    )


def _is_cross_section_compare(text: str, lowered: str, answer_strategy: str) -> bool:
    has_compare = _has_any(text, lowered, COMPARE_TOKENS) or answer_strategy == "comparison"
    has_platform = _has_any(text, lowered, PLATFORM_TOKENS)
    has_revenue_inventory = _has_any(text, lowered, REVENUE_TOKENS) and _has_any(text, lowered, INVENTORY_TOKENS)
    return has_compare and has_platform and has_revenue_inventory and not _is_time_compare(text, lowered)


def _is_performance_assessment(text: str, lowered: str, answer_strategy: str) -> bool:
    has_platform = _has_any(text, lowered, PLATFORM_TOKENS)
    has_performance = _has_any(text, lowered, PERFORMANCE_TOKENS)
    has_best_or_worst = _has_any(text, lowered, BEST_TOKENS + WORST_TOKENS)
    return has_platform and has_performance and (has_best_or_worst or answer_strategy == "performance_weakness")


def _is_time_compare(text: str, lowered: str) -> bool:
    explicit_two_months = len(re.findall(r"(?<!\d)(1[0-2]|0?[1-9])\s*\u6708", text)) >= 2
    has_change = _has_any(text, lowered, CHANGE_TOKENS)
    asks_contribution = _has_any(text, lowered, CONTRIBUTION_TOKENS)
    return (explicit_two_months or _has_any(text, lowered, [" vs ", "versus", "\u76f8\u8f03"])) and (has_change or asks_contribution)


def _infer_target_dimension(text: str, lowered: str) -> str | None:
    if _has_any(text, lowered, PLATFORM_TOKENS):
        return "platform"
    if _has_any(text, lowered, ["business group", "group", "\u4e8b\u696d\u7fa4", "\u65b0\u4e8b\u696d\u7fa4"]):
        return "business_group"
    if _has_any(text, lowered, ["month", "\u6708\u4efd", "\u672c\u6708", "\u6700\u65b0\u6708"]):
        return "month"
    return None


def _infer_polarity(text: str, lowered: str) -> str | None:
    if _has_any(text, lowered, WORST_TOKENS):
        return "worst"
    if _has_any(text, lowered, BEST_TOKENS):
        return "best"
    return None


def _fallback_task_family(answer_strategy: str) -> str:
    mapping = {
        "comparison": "cross_section_compare",
        "performance_weakness": "performance_assessment",
        "ranking": "ranking",
        "trend": "trend_analysis",
        "risk": "risk_scan",
        "diagnosis": "diagnosis",
        "overview": "executive_summary",
        "chart": "chart_request",
        "data_quality": "data_quality",
        "unsupported": "unsupported",
        "metric_query": "metric_lookup",
        "query": "metric_lookup",
    }
    return mapping.get(answer_strategy, answer_strategy or "metric_lookup")


def _fallback_metrics(text: str, lowered: str, answer_strategy: str) -> list[str]:
    metrics: list[str] = []
    if _has_any(text, lowered, REVENUE_TOKENS):
        metrics.append("revenue")
    if _has_any(text, lowered, INVENTORY_TOKENS):
        metrics.extend(["inventory_amount", "inventory_qty"])
    if answer_strategy in {"risk", "diagnosis", "performance_weakness"}:
        metrics.append("anomaly")
    return _unique(metrics or ["revenue"])


def _fallback_comparison_axis(answer_strategy: str, target_dimension: str | None) -> dict[str, Any]:
    if answer_strategy in {"ranking", "comparison", "performance_weakness"}:
        return {"axis": "entity", "dimension": target_dimension, "baseline": "peers"}
    if answer_strategy in {"trend", "diagnosis"}:
        return {"axis": "time", "dimension": "month", "baseline": "previous_period"}
    return {"axis": "none", "dimension": None, "baseline": None}


def _fallback_answer_style(answer_strategy: str) -> str:
    if answer_strategy in {"ranking", "risk", "diagnosis", "performance_weakness"}:
        return "conclusion_first"
    if answer_strategy == "chart":
        return "chart_only"
    if answer_strategy == "data_quality":
        return "coverage_summary"
    return "evidence_first"


def _extract_month(text: str) -> str | None:
    match = re.search(r"(20\d{2})[-/]?(0[1-9]|1[0-2])", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    month_only = re.search(r"(?<!\d)(1[0-2]|0?[1-9])\s*\u6708", text)
    if month_only:
        return f"2024-{int(month_only.group(1)):02d}"
    chinese_months = {
        "\u4e00\u6708": "2024-01",
        "\u4e8c\u6708": "2024-02",
        "\u4e09\u6708": "2024-03",
        "\u56db\u6708": "2024-04",
        "\u4e94\u6708": "2024-05",
        "\u516d\u6708": "2024-06",
        "\u4e03\u6708": "2024-07",
        "\u516b\u6708": "2024-08",
        "\u4e5d\u6708": "2024-09",
        "\u5341\u6708": "2024-10",
        "\u5341\u4e00\u6708": "2024-11",
        "\u5341\u4e8c\u6708": "2024-12",
    }
    for token, month in chinese_months.items():
        if token in text:
            return month
    return None


def _extract_baseline_month(text: str, current_month: str | None) -> str | None:
    month_numbers = [int(item) for item in re.findall(r"(?<!\d)(1[0-2]|0?[1-9])\s*\u6708", text)]
    if len(month_numbers) >= 2:
        return f"2024-{month_numbers[1]:02d}" if current_month == f"2024-{month_numbers[0]:02d}" else f"2024-{month_numbers[0]:02d}"
    return None


def _has_any(text: str, lowered: str, tokens: list[str]) -> bool:
    return any(token.lower() in lowered or token in text for token in tokens)


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
