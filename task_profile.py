from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from entity_labels import resolve_entity_value, text_has_dimension_synonym

# Controlled registry used by semantic coverage validation; update it when a new task family is emitted.
ACTIVE_CANONICAL_TASK_TYPES = frozenset({
    "latest_month_platform_summary", "latest_month_entity_summary", "period_pair_compare",
    "entity_period_pair_table_lookup", "entity_multi_month_table_lookup", "entity_period_pair_metric_lookup",
    "entity_time_series", "overall_trend_analysis", "entity_trend_comparison", "metric_relationship_analysis",
    "contribution_analysis", "forecast_unsupported", "parent_child_drilldown", "entity_month_table_lookup",
    "cross_section_compare", "performance_assessment", "risk_scan", "metric_lookup", "chart_request",
    "entity_ranking", "time_compare", "data_quality", "diagnosis",
})


@dataclass(frozen=True)
class TaskProfile:
    task_family: str
    business_intent: str | None = None
    target_entity: dict[str, Any] = field(default_factory=dict)
    parent_entity: dict[str, Any] = field(default_factory=dict)
    metrics: list[str] = field(default_factory=list)
    time_scope: dict[str, Any] = field(default_factory=dict)
    comparison_axis: dict[str, Any] = field(default_factory=dict)
    polarity: str | None = None
    analysis_depth: str = "basic"
    answer_style: str = "evidence_first"
    requires_table: bool = False
    requires_limitations: bool = True
    question_text: str = ""
    task_requirements: dict[str, Any] = field(default_factory=dict)


OVERALL_TOKENS = ["總體", "整體", "overall", "全部", "全體"]
PLATFORM_TOKENS = ["platform", "平台", "平臺"]
BUSINESS_GROUP_TOKENS = ["business group", "business unit", "BU", "bu", "新事業群", "事業群", "各新事業群", "各事業群"]
PRODUCT_LINE_TOKENS = ["product line", "product_line", "五大產品線", "產品線", "各產品線", "各五大產品線"]

REVENUE_TOKENS = ["revenue", "sales", "營收", "銷售"]
INVENTORY_AMOUNT_TOKENS = ["inventory", "stock", "庫存", "存貨", "庫存金額"]
INVENTORY_QTY_TOKENS = ["qty", "inventory qty", "inventory quantity", "庫存數量", "數量", "QTY"]
RATIO_TOKENS = ["ratio", "efficiency", "營收相對庫存效率", "營收/庫存", "庫存/營收", "效率", "週轉", "周轉", "proxy"]
HEALTH_TOKENS = ["health_score", "health score", "健康", "綜合表現", "表現"]
RISK_TOKENS = ["risk_score", "risk score", "風險", "異常", "警示"]
SUMMARY_TOKENS = ["summary", "summarize", "overview", "整理", "摘要", "重點", "狀況"]
LATEST_TOKENS = ["latest month", "current month", "this month", "最新月份", "最新月", "本月", "當月", "最新"]
COMPARE_TOKENS = ["compare", "comparison", "difference", "versus", " vs ", "比較", "對比", "區別", "差異", "差多少"]
TREND_TOKENS = ["trend", "monthly", "mom", "趨勢", "走勢", "各月", "每月", "變化"]
FORECAST_TOKENS = [
    "forecast",
    "predict",
    "prediction",
    "next month",
    "future",
    "下個月",
    "下月",
    "未來",
    "預測",
    "會不會改善",
    "會不會成長",
]
BEST_TOKENS = ["best", "better", "highest", "top", "最健康", "較佳", "較好", "最好", "最高", "成長最快"]
WORST_TOKENS = ["worst", "weakest", "lowest", "較差", "最差", "較弱", "最弱", "最低", "壓力較高", "壓力最高"]
RELATIONSHIP_TOKENS = ["背離", "divergence", "下降但庫存上升", "營收下降但庫存上升", "效率變差", "效率惡化"]
DEMAND_MOMENTUM_TOKENS = ["需求動能", "動能轉弱", "需求轉弱", "營收動能", "declining revenue momentum", "revenue momentum", "demand momentum"]
STOCK_BUILDUP_TOKENS = ["東西越堆越多", "越堆越多", "越積越高", "庫存堆高", "資金持續沉澱", "資金沉澱", "building up", "stock keeps building", "stock building", "inventory keeps building"]
CONTRIBUTION_TOKENS = ["contribution", "contributed", "contribute", "貢獻", "主要來自", "帶動", "造成"]
YOY_TOKENS = ["yoy", "year over year", "去年同期"]
CHART_TOKENS = ["chart", "plot", "graph", "visual", "圖", "畫", "畫圖", "圖表", "視覺化"]
LOOKUP_TOKENS = ["列出", "顯示", "查詢", "查看", "看一下", "告訴我", "多少", "是多少", "資料", "數據"]
RECOMMENDATION_TOKENS = ["建議", "下一步", "優先確認", "優先檢查", "行動", "action", "next action", "next step", "recommend", "recommendation"]
SELECTION_TOKENS = ["選出", "挑出", "找出", "辨識", "identify", "select", "choose", "which", "top"]


def build_task_profile(question: str, routing: Any) -> TaskProfile:
    text = (question or "").strip()
    lowered = text.lower()
    answer_strategy = getattr(routing, "answer_strategy", None) or getattr(routing, "question_type", "query")

    def make_profile(**kwargs: Any) -> TaskProfile:
        if "task_requirements" not in kwargs:
            kwargs["task_requirements"] = _build_task_requirement_manifest(
                text=text,
                lowered=lowered,
                task_family=str(kwargs.get("task_family") or ""),
                metrics=_unique([*(metrics or []), *(kwargs.get("metrics") or [])]),
                target_entity=dict(kwargs.get("target_entity") or target_entity or {}),
                time_scope=dict(kwargs.get("time_scope") or time_scope or {}),
                comparison_axis=dict(kwargs.get("comparison_axis") or {}),
            )
        return TaskProfile(question_text=text, **kwargs)

    time_scope = _infer_time_scope(text, lowered)
    target_entity, parent_entity = _infer_entity_scope(text, lowered, getattr(routing, "object_dimension", None))
    metrics = _infer_metrics(text, lowered, answer_strategy)
    explicit_metric = _has_explicit_metric(text, lowered)
    primary_metric = metrics[0] if metrics else "revenue_amount"
    polarity = _infer_polarity(text, lowered)

    if _is_forecast_unsupported(text, lowered) or _is_capability_boundary_unsupported(text, lowered):
        return make_profile(
            task_family="forecast_unsupported",
            business_intent="forecast_unsupported" if _is_forecast_unsupported(text, lowered) else "capability_boundary_unsupported",
            target_entity=target_entity,
            parent_entity=parent_entity,
            metrics=metrics or ["revenue_amount"],
            time_scope=time_scope,
            comparison_axis={"axis": "none", "dimension": None, "baseline": None},
            polarity=polarity,
            answer_style="unsupported_with_limitations",
            requires_table=False,
            requires_limitations=True,
        )

    if answer_strategy == "data_quality":
        return make_profile(
            task_family="data_quality",
            business_intent="data_quality",
            target_entity=target_entity,
            parent_entity=parent_entity,
            metrics=[],
            time_scope=time_scope,
            comparison_axis={"axis": "none", "dimension": None, "baseline": None},
            answer_style="coverage_summary",
            requires_table=False,
            requires_limitations=True,
        )

    if _is_chart_request(text, lowered, answer_strategy):
        return make_profile(
            task_family="chart_request",
            business_intent="chart_request",
            target_entity=target_entity,
            parent_entity=parent_entity,
            metrics=metrics or [primary_metric],
            time_scope=time_scope,
            comparison_axis=_comparison_axis_for(target_entity, time_scope),
            polarity=polarity,
            answer_style="chart_only",
            requires_table=False,
            requires_limitations=True,
        )

    if _is_entity_period_pair_table_lookup(text, lowered, target_entity, time_scope):
        entity_dimension = _peer_dimension(target_entity)
        return make_profile(
            task_family="entity_period_pair_table_lookup",
            business_intent="entity_period_pair_table_lookup",
            target_entity={"dimension": entity_dimension, "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=[primary_metric],
            time_scope=time_scope,
            comparison_axis={"axis": "entity_and_time", "dimension": entity_dimension, "baseline": "explicit_period_pair_table"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="table_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_entity_multi_month_table_lookup(text, lowered, target_entity, time_scope):
        entity_dimension = _peer_dimension(target_entity)
        return make_profile(
            task_family="entity_multi_month_table_lookup",
            business_intent="entity_multi_month_table_lookup",
            target_entity={"dimension": entity_dimension, "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=[primary_metric],
            time_scope=time_scope,
            comparison_axis={"axis": "entity_and_time", "dimension": entity_dimension, "baseline": "date_range_table"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="table_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_entity_period_pair_metric_lookup(text, lowered, target_entity, time_scope):
        return make_profile(
            task_family="entity_period_pair_metric_lookup",
            business_intent="entity_period_pair_metric_lookup",
            target_entity=target_entity,
            parent_entity=parent_entity,
            metrics=[primary_metric],
            time_scope=time_scope,
            comparison_axis={"axis": "time", "dimension": "month", "baseline": "explicit_period_pair"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="table_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_single_month_all_entity_cross_section(text, lowered, target_entity, time_scope):
        entity_dimension = _peer_dimension(target_entity)
        return make_profile(
            task_family="cross_section_compare",
            business_intent="single_month_entity_cross_section",
            target_entity={"dimension": entity_dimension, "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=metrics if len(metrics) > 1 else ([primary_metric] if explicit_metric else _default_data_metrics()),
            time_scope=_default_single_or_latest_lookup_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": entity_dimension, "baseline": "same_month_single_metric"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="single_month_entity_comparison",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_entity_month_table_lookup(text, lowered, target_entity, time_scope):
        entity_dimension = _peer_dimension(target_entity)
        return make_profile(
            task_family="entity_month_table_lookup",
            business_intent="entity_month_table_lookup",
            target_entity={"dimension": entity_dimension, "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=[primary_metric] if explicit_metric else _default_data_metrics(),
            time_scope=_default_single_or_latest_lookup_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": entity_dimension, "baseline": "single_month_table"},
            polarity=polarity,
            answer_style="entity_month_table",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_entity_month_metric_lookup(text, lowered, target_entity, time_scope):
        return make_profile(
            task_family="metric_lookup",
            business_intent="entity_month_metric_lookup",
            target_entity=target_entity,
            parent_entity=parent_entity,
            metrics=[primary_metric],
            time_scope=_default_single_or_latest_lookup_scope(time_scope),
            comparison_axis={"axis": "none", "dimension": None, "baseline": None},
            polarity=polarity,
            answer_style="entity_month_metric_lookup",
            requires_table=False,
            requires_limitations=True,
        )

    if _is_parent_child_drilldown(text, target_entity, parent_entity):
        return make_profile(
            task_family="parent_child_drilldown",
            business_intent="parent_child_drilldown",
            target_entity={"dimension": "product_line_5", "value": None, "scope": "children"},
            parent_entity=parent_entity,
            metrics=_performance_metrics(metrics),
            time_scope=_default_latest_month_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": "product_line_5", "baseline": "siblings_under_parent"},
            polarity=polarity or "worst",
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_contribution_question(text, lowered):
        metric = primary_metric if primary_metric not in {"health_score", "risk_score"} else "revenue_amount"
        return make_profile(
            task_family="contribution_analysis",
            business_intent="contribution_analysis",
            target_entity=_normalize_peer_target(target_entity),
            parent_entity=parent_entity,
            metrics=[metric],
            time_scope=time_scope,
            comparison_axis={"axis": "entity", "dimension": _peer_dimension(target_entity), "baseline": "period_change_contribution"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_metric_relationship_question(text, lowered):
        relationship_time_scope = _default_relationship_scope(time_scope)
        return make_profile(
            task_family="metric_relationship_analysis",
            business_intent="metric_relationship_analysis",
            target_entity=_normalize_peer_target(target_entity),
            parent_entity=parent_entity,
            metrics=["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"],
            time_scope=relationship_time_scope,
            comparison_axis={"axis": "entity", "dimension": _peer_dimension(target_entity), "baseline": relationship_time_scope.get("mode") or "latest_vs_previous"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=True,
            requires_limitations=True,
        )

    if time_scope.get("period_a") and time_scope.get("period_b") and _looks_like_period_pair_question(text):
        metric = primary_metric if primary_metric not in {"health_score", "risk_score"} else "revenue_amount"
        return make_profile(
            task_family="period_pair_compare",
            business_intent="period_pair_compare",
            target_entity=_normalize_peer_target(target_entity),
            parent_entity=parent_entity,
            metrics=[metric],
            time_scope=time_scope,
            comparison_axis={"axis": "time", "dimension": "month", "baseline": "explicit_period_pair"},
            analysis_depth="standard",
            answer_style="period_difference_summary",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_latest_month_entity_summary(text, lowered, answer_strategy, target_entity):
        entity_dimension = _peer_dimension(target_entity)
        return make_profile(
            task_family="latest_month_entity_summary",
            business_intent="latest_month_entity_summary",
            target_entity={"dimension": entity_dimension, "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio", "health_score", "risk_score"],
            time_scope=_default_latest_month_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": entity_dimension, "baseline": "latest_month_peers"},
            analysis_depth="standard",
            answer_style="executive_summary_with_table",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_entity_trend_comparison(text, lowered, target_entity):
        metric = primary_metric if primary_metric not in {"health_score", "risk_score"} else "revenue_amount"
        return make_profile(
            task_family="entity_trend_comparison",
            business_intent="entity_trend_comparison",
            target_entity={"dimension": _peer_dimension(target_entity), "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=[metric],
            time_scope=_default_series_scope(time_scope),
            comparison_axis={"axis": "entity_and_time", "dimension": _peer_dimension(target_entity), "baseline": "multi_entity_series"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_entity_time_series(text, lowered, target_entity):
        metric = primary_metric if primary_metric not in {"health_score", "risk_score"} else "revenue_amount"
        return make_profile(
            task_family="entity_time_series",
            business_intent="entity_time_series",
            target_entity=target_entity,
            parent_entity=parent_entity,
            metrics=[metric],
            time_scope=_default_series_scope(time_scope),
            comparison_axis={"axis": "time", "dimension": "month", "baseline": "monthly_series"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_overall_trend(text, lowered, target_entity, answer_strategy):
        metric = primary_metric if primary_metric not in {"health_score", "risk_score"} else "revenue_amount"
        return make_profile(
            task_family="overall_trend_analysis",
            business_intent="overall_trend_analysis",
            target_entity={"dimension": "overall", "value": None, "scope": "overall"},
            parent_entity={},
            metrics=[metric],
            time_scope=_default_series_scope(time_scope),
            comparison_axis={"axis": "time", "dimension": "month", "baseline": "monthly_series"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_cross_section_compare(text, lowered, answer_strategy, target_entity):
        entity_dimension = _peer_dimension(target_entity)
        return make_profile(
            task_family="cross_section_compare",
            business_intent="cross_section_compare",
            target_entity={"dimension": entity_dimension, "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=metrics if len(metrics) > 1 else ([primary_metric] if explicit_metric else ["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"]),
            time_scope=_default_latest_or_single_month_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": entity_dimension, "baseline": "same_month_peers"},
            analysis_depth="standard",
            answer_style="table_first",
            requires_table=True,
            requires_limitations=True,
        )

    if _is_performance_assessment(text, lowered, answer_strategy, target_entity):
        return make_profile(
            task_family="performance_assessment",
            business_intent="performance_assessment",
            target_entity=_normalize_peer_target(target_entity),
            parent_entity=parent_entity,
            metrics=_performance_metrics(metrics),
            time_scope=_default_latest_or_single_month_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": _peer_dimension(target_entity), "baseline": "peer_performance"},
            polarity=polarity,
            analysis_depth="standard",
            answer_style="conclusion_first",
            requires_table=False,
            requires_limitations=True,
        )

    if answer_strategy == "ranking" or _is_ranking_question(text, lowered):
        return make_profile(
            task_family="entity_ranking",
            business_intent="entity_metric_ranking",
            target_entity={"dimension": _peer_dimension(target_entity), "value": None, "scope": "all"},
            parent_entity=parent_entity,
            metrics=[_ranking_metric(text, lowered)],
            time_scope=_default_latest_or_single_month_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": _peer_dimension(target_entity), "baseline": "peer_ranking"},
            polarity=polarity or "best",
            analysis_depth="basic",
            answer_style="conclusion_first",
            requires_table=True,
            requires_limitations=True,
        )

    if answer_strategy == "risk":
        return make_profile(
            task_family="risk_scan",
            business_intent="risk_scan",
            target_entity=_normalize_peer_target(target_entity),
            parent_entity=parent_entity,
            metrics=metrics or ["risk_score"],
            time_scope=_default_latest_or_single_month_scope(time_scope),
            comparison_axis={"axis": "entity", "dimension": _peer_dimension(target_entity), "baseline": "risk_scan"},
            answer_style="conclusion_first",
            requires_table=False,
            requires_limitations=True,
        )

    if answer_strategy == "diagnosis":
        return make_profile(
            task_family="diagnosis",
            business_intent="diagnosis",
            target_entity=_normalize_peer_target(target_entity),
            parent_entity=parent_entity,
            metrics=metrics or ["revenue_amount"],
            time_scope=_default_latest_or_single_month_scope(time_scope),
            comparison_axis={"axis": "evidence", "dimension": None, "baseline": "deterministic_candidates"},
            polarity=polarity,
            answer_style="conclusion_first",
            requires_table=False,
            requires_limitations=True,
        )

    return make_profile(
        task_family=_fallback_task_family(answer_strategy, target_entity, time_scope),
        business_intent=answer_strategy,
        target_entity=target_entity,
        parent_entity=parent_entity,
        metrics=metrics or ["revenue_amount"],
        time_scope=time_scope,
        comparison_axis=_comparison_axis_for(target_entity, time_scope),
        polarity=polarity,
        answer_style=_fallback_answer_style(answer_strategy),
        requires_table=False,
        requires_limitations=answer_strategy in {"diagnosis", "risk", "unsupported"},
    )


def _is_forecast_unsupported(text: str, lowered: str) -> bool:
    return _has_any(text, lowered, FORECAST_TOKENS)


def _is_capability_boundary_unsupported(text: str, lowered: str) -> bool:
    formal_turnover = any(token in text or token in lowered for token in ["正式庫存週轉率", "正式庫存週轉", "庫存週轉天數", "inventory turnover days", "formal inventory turnover", "formal turnover"])
    forbids_proxy = any(token in text or token in lowered for token in ["不允許", "不要改用", "不得", "不准", "do not use", "not use", "no proxy", "proxy is not allowed"])
    unsupported_financial = any(token in text or token in lowered for token in ["毛利率", "毛利", "gross margin", "營業利益率", "營業利益", "operating margin", "operating profit", "庫存週轉天數", "inventory turnover days"])
    return unsupported_financial or (formal_turnover and forbids_proxy)


def _is_chart_request(text: str, lowered: str, answer_strategy: str) -> bool:
    return answer_strategy == "chart" or _has_any(text, lowered, CHART_TOKENS)


def _is_single_month_all_entity_request(
    text: str,
    lowered: str,
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
) -> bool:
    return (
        time_scope.get("mode") == "single_month"
        and target_entity.get("dimension") in {"business_group", "product_line_5"}
        and target_entity.get("scope") in {"all", "children"}
        and not target_entity.get("value")
        and _has_any_entity_dimension_request(text, lowered, target_entity.get("dimension"))
        and (
            _has_any(text, lowered, REVENUE_TOKENS + INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
            or any(token in text for token in ["資料", "數據"])
        )
    )


def _is_single_month_all_entity_cross_section(
    text: str,
    lowered: str,
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
) -> bool:
    return (
        _is_single_month_all_entity_request(text, lowered, target_entity, time_scope)
        and _has_any(text, lowered, COMPARE_TOKENS)
        and not _looks_like_period_pair_question(text)
    )


def _is_entity_month_table_lookup(
    text: str,
    lowered: str,
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
) -> bool:
    return (
        _is_single_month_all_entity_request(text, lowered, target_entity, time_scope)
        and _has_any(text, lowered, LOOKUP_TOKENS)
        and not _has_any(text, lowered, COMPARE_TOKENS)
    )


def _is_entity_month_metric_lookup(
    text: str,
    lowered: str,
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
) -> bool:
    return (
        _has_any(text, lowered, LOOKUP_TOKENS)
        and target_entity.get("dimension") in {"business_group", "product_line_5"}
        and bool(target_entity.get("value"))
        and time_scope.get("mode") in {"single_month", "latest_month"}
        and _has_any(text, lowered, REVENUE_TOKENS + INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
    )


def _is_entity_period_pair_table_lookup(
    text: str,
    lowered: str,
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
) -> bool:
    return (
        time_scope.get("mode") == "period_pair"
        and target_entity.get("dimension") in {"business_group", "product_line_5"}
        and target_entity.get("scope") in {"all", "children"}
        and not target_entity.get("value")
        and _has_any_entity_dimension_request(text, lowered, target_entity.get("dimension"))
        and _has_any(text, lowered, LOOKUP_TOKENS + COMPARE_TOKENS + ["變化", "挑出", "選出", "找出", "對照"])
        and _has_any(text, lowered, REVENUE_TOKENS + INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
    )


def _is_entity_multi_month_table_lookup(
    text: str,
    lowered: str,
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
) -> bool:
    return (
        time_scope.get("mode") in {"date_range", "multi_month_series"}
        and bool(time_scope.get("start_month"))
        and bool(time_scope.get("end_month"))
        and target_entity.get("dimension") in {"business_group", "product_line_5"}
        and target_entity.get("scope") in {"all", "children"}
        and not target_entity.get("value")
        and _has_any_entity_dimension_request(text, lowered, target_entity.get("dimension"))
        and _has_any(text, lowered, LOOKUP_TOKENS + ["各月", "每月", "趨勢"])
        and _has_any(text, lowered, REVENUE_TOKENS + INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
    )


def _is_entity_period_pair_metric_lookup(
    text: str,
    lowered: str,
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
) -> bool:
    return (
        time_scope.get("mode") == "period_pair"
        and target_entity.get("dimension") in {"business_group", "product_line_5"}
        and bool(target_entity.get("value"))
        and _has_any(text, lowered, LOOKUP_TOKENS + COMPARE_TOKENS + ["變化"])
        and _has_any(text, lowered, REVENUE_TOKENS + INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
    )


def _is_latest_month_entity_summary(text: str, lowered: str, answer_strategy: str, target_entity: dict[str, Any]) -> bool:
    return (
        _has_any(text, lowered, LATEST_TOKENS)
        and (_has_any(text, lowered, SUMMARY_TOKENS) or answer_strategy in {"summary", "latest_month_entity_summary"})
        and target_entity.get("dimension") in {"business_group", "product_line_5"}
        and _has_any(text, lowered, REVENUE_TOKENS)
        and _has_any(text, lowered, INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
    )


def _is_cross_section_compare(text: str, lowered: str, answer_strategy: str, target_entity: dict[str, Any]) -> bool:
    has_entity_compare = (
        target_entity.get("dimension") in {"business_group", "product_line_5"}
        and not target_entity.get("value")
        and _has_any(text, lowered, REVENUE_TOKENS + INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
    )
    has_multi_metric_compare = _has_any(text, lowered, REVENUE_TOKENS) and _has_any(text, lowered, INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)
    return (
        (_has_any(text, lowered, COMPARE_TOKENS) or answer_strategy == "comparison")
        and target_entity.get("dimension") in {"business_group", "product_line_5"}
        and (has_multi_metric_compare or has_entity_compare)
        and not _looks_like_period_pair_question(text)
    )


def _is_performance_assessment(text: str, lowered: str, answer_strategy: str, target_entity: dict[str, Any]) -> bool:
    return (
        target_entity.get("dimension") in {"business_group", "product_line_5"}
        and _has_any(text, lowered, HEALTH_TOKENS + RISK_TOKENS + RATIO_TOKENS + ["壓力", "較佳", "較差", "表現"])
        and (answer_strategy == "performance_weakness" or _has_any(text, lowered, RATIO_TOKENS) or (_infer_polarity(text, lowered) is not None and not _has_any(text, lowered, REVENUE_TOKENS) and not _has_any(text, lowered, INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS)))
    )


def _is_ranking_question(text: str, lowered: str) -> bool:
    return _has_any(text, lowered, ["ranking", "rank", "top", "bottom", "排名", "排行", "最高", "最低"])


def _is_metric_relationship_question(text: str, lowered: str) -> bool:
    revenue_semantics = _has_any(text, lowered, REVENUE_TOKENS + DEMAND_MOMENTUM_TOKENS) or any(token in text or token in lowered for token in ["營收卻一直往下", "營收一路變弱", "營收仍在成長", "declining revenue", "revenue decline"])
    inventory_semantics = _has_any(text, lowered, INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS + STOCK_BUILDUP_TOKENS)
    relationship_semantics = (
        _has_any(text, lowered, RELATIONSHIP_TOKENS + STOCK_BUILDUP_TOKENS)
        or ("下降" in text and ("上升" in text or "增加" in text or "堆" in text or "積" in text))
        or any(token in lowered for token in ["declining revenue momentum", "revenue keeps dropping", "inventory risk", "stock keeps building", "worsening inventory"])
        or any(token in text for token in ["惡化", "風險可能惡化", "庫存風險"])
    )
    return revenue_semantics and inventory_semantics and relationship_semantics


def _is_contribution_question(text: str, lowered: str) -> bool:
    return _has_any(text, lowered, CONTRIBUTION_TOKENS)


def _is_parent_child_drilldown(text: str, target_entity: dict[str, Any], parent_entity: dict[str, Any]) -> bool:
    return (
        target_entity.get("dimension") == "product_line_5"
        and parent_entity.get("dimension") == "business_group"
        and any(token in text for token in ["底下", "下面"])
    )


def _is_entity_time_series(text: str, lowered: str, target_entity: dict[str, Any]) -> bool:
    return (
        target_entity.get("dimension") in {"business_group", "product_line_5"}
        and bool(target_entity.get("value"))
        and _has_any(text, lowered, ["各月", "每月", "trend", "趨勢", "變化"])
    )


def _is_entity_trend_comparison(text: str, lowered: str, target_entity: dict[str, Any]) -> bool:
    return (
        target_entity.get("dimension") in {"business_group", "product_line_5"}
        and not target_entity.get("value")
        and (_extract_recent_n(text) is not None or _has_any(text, lowered, ["各月", "每月", "trend", "趨勢", "變化"]))
    )


def _is_overall_trend(text: str, lowered: str, target_entity: dict[str, Any], answer_strategy: str) -> bool:
    return target_entity.get("dimension") == "overall" and (answer_strategy == "trend" or _has_any(text, lowered, TREND_TOKENS))


def _infer_time_scope(text: str, lowered: str) -> dict[str, Any]:
    period_pair = _extract_period_pair(text)
    single_month = None if period_pair else _extract_single_month(text)
    month_range = None if period_pair else _extract_month_range(text)
    recent_n = _extract_recent_n(text)
    latest = _has_any(text, lowered, LATEST_TOKENS)
    yoy = _has_any(text, lowered, YOY_TOKENS)
    if _is_forecast_unsupported(text, lowered):
        mode = "future_period"
    elif period_pair:
        mode = "period_pair"
    elif month_range:
        mode = "date_range"
    elif recent_n is not None:
        mode = "recent_n_months"
    elif single_month:
        mode = "year_over_year" if yoy else "single_month"
    elif latest:
        mode = "latest_month"
    elif _has_any(text, lowered, TREND_TOKENS):
        mode = "multi_month_series"
    else:
        mode = "unspecified"
    return {
        "mode": mode,
        "month": period_pair[1] if period_pair else single_month,
        "single_month": single_month,
        "period_a": period_pair[0] if period_pair else None,
        "period_b": period_pair[1] if period_pair else None,
        "start_month": month_range[0] if month_range else None,
        "end_month": month_range[1] if month_range else None,
        "recent_n": recent_n,
        "yoy": yoy,
    }


def _infer_entity_scope(text: str, lowered: str, routed_dimension: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    parent_entity = _infer_parent_entity(text)
    if parent_entity.get("value"):
        resolved_parent = resolve_entity_value(str(parent_entity["value"]), "business_group") or parent_entity["value"]
        parent_entity = {**parent_entity, "value": resolved_parent}
    explicit_dimension = _infer_target_dimension(text, lowered, routed_dimension)
    if explicit_dimension == "overall":
        return {"dimension": "overall", "value": None, "scope": "overall"}, parent_entity
    if parent_entity.get("dimension") == "business_group":
        return {"dimension": "product_line_5", "value": None, "scope": "children"}, parent_entity
    if explicit_dimension in {"business_group", "product_line_5"} and _has_all_entity_phrase(text, explicit_dimension):
        return {"dimension": explicit_dimension, "value": None, "scope": "all"}, parent_entity
    product_line = _extract_named_product_line(text)
    if product_line:
        return {"dimension": "product_line_5", "value": product_line, "scope": "single"}, parent_entity
    business_group = _extract_named_business_group(text)
    if business_group:
        return {"dimension": "business_group", "value": business_group, "scope": "single"}, parent_entity
    dimension = explicit_dimension or "overall"
    scope = "all" if dimension in {"business_group", "product_line_5"} else ("overall" if dimension == "overall" else "unspecified")
    return {"dimension": dimension, "value": None, "scope": scope}, parent_entity


def _infer_target_dimension(text: str, lowered: str, routed_dimension: str | None) -> str | None:
    if _has_any(text, lowered, OVERALL_TOKENS):
        return "overall"
    if _has_any(text, lowered, PRODUCT_LINE_TOKENS) or text_has_dimension_synonym(text, "product_line_5"):
        return "product_line_5"
    if _has_any(text, lowered, BUSINESS_GROUP_TOKENS + PLATFORM_TOKENS) or text_has_dimension_synonym(text, "business_group"):
        return "business_group"
    if routed_dimension in {"platform", "business_group"}:
        return "business_group"
    if routed_dimension in {"product_line_5", "overall"}:
        return routed_dimension
    return None


def _has_all_entity_phrase(text: str, dimension: str) -> bool:
    if dimension == "business_group":
        return any(token in text for token in ["各事業群", "各新事業群", "各BU", "各 BU", "各business unit", "各Business Unit", "各平台"])
    if dimension == "product_line_5":
        return any(token in text for token in ["各產品線", "各五大產品線", "各product line", "各Product Line"])
    return False


def _has_any_entity_plural(text: str, lowered: str) -> bool:
    return _has_all_entity_phrase(text, "business_group") or _has_all_entity_phrase(text, "product_line_5")


def _has_any_entity_dimension_request(text: str, lowered: str, dimension: str | None) -> bool:
    if dimension == "business_group":
        return _has_all_entity_phrase(text, "business_group") or _has_any(text, lowered, BUSINESS_GROUP_TOKENS + PLATFORM_TOKENS)
    if dimension == "product_line_5":
        return _has_all_entity_phrase(text, "product_line_5") or _has_any(text, lowered, PRODUCT_LINE_TOKENS)
    return _has_any_entity_plural(text, lowered)


def _infer_parent_entity(text: str) -> dict[str, Any]:
    if not any(token in text for token in ["底下", "下面"]) or not any(token in text for token in ["產品線", "五大產品線"]):
        return {}
    match = re.search(r"(?P<value>[\w\u4e00-\u9fff+\-/]+?)\s*(?:底下|下面)", text)
    value = match.group("value").strip() if match else None
    if value in {"某", "某新事業群", "某事業群"}:
        value = None
    return {"dimension": "business_group", "value": value}


def _infer_metrics(text: str, lowered: str, answer_strategy: str) -> list[str]:
    metrics: list[str] = []
    if _has_any(text, lowered, DEMAND_MOMENTUM_TOKENS):
        metrics.append("revenue_amount")
    if _has_any(text, lowered, STOCK_BUILDUP_TOKENS):
        metrics.append("inventory_amount")
    if _has_any(text, lowered, RATIO_TOKENS):
        metrics.append("revenue_inventory_amount_ratio")
    if _has_any(text, lowered, HEALTH_TOKENS) and "營收" not in text and "庫存" not in text:
        metrics.append("health_score")
    if _has_any(text, lowered, RISK_TOKENS) and "risk_score" not in metrics:
        metrics.append("risk_score")
    if _has_any(text, lowered, REVENUE_TOKENS):
        metrics.append("revenue_amount")
    has_inventory_qty = _has_any(text, lowered, INVENTORY_QTY_TOKENS) or ("inventory" in lowered and "quantity" in lowered)
    has_inventory_amount = _has_inventory_amount_metric_request(text, lowered, has_inventory_qty=has_inventory_qty)
    if has_inventory_qty:
        metrics.append("inventory_qty")
    if has_inventory_amount:
        metrics.append("inventory_amount")
    if any(token in text or token in lowered for token in ["異常訊號", "異常信號", "anomaly signal", "anomaly signals"]):
        if "risk_score" not in metrics:
            metrics.append("risk_score")
    if any(token in text or token in lowered for token in ["庫存風險", "inventory risk"]):
        for metric in ["inventory_amount", "inventory_qty"]:
            if metric not in metrics:
                metrics.append(metric)
    if answer_strategy in {"risk", "performance_weakness"} and "risk_score" not in metrics:
        metrics.append("risk_score")
    return _unique(metrics or ["revenue_amount"])


def _build_task_requirement_manifest(
    *,
    text: str,
    lowered: str,
    task_family: str,
    metrics: list[str],
    target_entity: dict[str, Any],
    time_scope: dict[str, Any],
    comparison_axis: dict[str, Any],
) -> dict[str, Any]:
    requested_metrics = _unique(metrics or ["revenue_amount"])
    if _asks_for_multiple_inventory_indicators(text, lowered):
        for metric in ["inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"]:
            if metric not in requested_metrics:
                requested_metrics.append(metric)
    if _has_any(text, lowered, STOCK_BUILDUP_TOKENS) or any(token in text or token in lowered for token in ["庫存風險", "inventory risk", "庫存價值", "inventory value"]):
        for metric in ["inventory_amount", "inventory_qty"]:
            if metric not in requested_metrics:
                requested_metrics.append(metric)
    if _has_any(text, lowered, DEMAND_MOMENTUM_TOKENS) and "revenue_amount" not in requested_metrics:
        requested_metrics.insert(0, "revenue_amount")
    if _has_any(text, lowered, INVENTORY_QTY_TOKENS) and "inventory_qty" not in requested_metrics:
        requested_metrics.append("inventory_qty")
    if task_family in {"risk_scan", "performance_assessment"} and _has_any(text, lowered, REVENUE_TOKENS) and "revenue_amount" not in requested_metrics:
        requested_metrics.insert(0, "revenue_amount")

    operations = _infer_requested_operations(text, lowered, task_family, time_scope)
    if "anomaly" in operations and "risk_score" not in requested_metrics:
        requested_metrics.append("risk_score")
    top_n = _extract_top_n(text)
    requires_recommendation = _requires_recommendation(text, lowered)
    requires_named_selection = _requires_named_selection(text, lowered, top_n, operations)
    if requires_recommendation and "next_action" not in operations:
        operations.append("next_action")
    if requires_named_selection and "select" not in operations:
        operations.append("select")
    dimensions = [target_entity.get("dimension") or comparison_axis.get("dimension") or "overall"]
    dimensions = [dimension for dimension in dimensions if dimension]
    return {
        "requested_metrics": requested_metrics,
        "requested_dimensions": _unique([str(item) for item in dimensions]),
        "time_scope": dict(time_scope),
        "top_n": top_n,
        "requested_top_n": top_n,
        "requested_operations": operations,
        "requires_counter_evidence": "counter_evidence" in operations,
        "requires_recommendation": requires_recommendation,
        "requires_named_selection": requires_named_selection,
        "required_selected_entity_count": top_n if requires_named_selection and top_n is not None else None,
    }


def _requires_recommendation(text: str, lowered: str) -> bool:
    return _has_any(text, lowered, RECOMMENDATION_TOKENS)


def _requires_named_selection(text: str, lowered: str, top_n: int | None, operations: list[str]) -> bool:
    if top_n is None:
        return False
    has_select_language = _has_any(text, lowered, SELECTION_TOKENS) or any(token in text or token in lowered for token in ["最需要", "最值得", "關注", "management attention", "management risk"])
    return has_select_language and ("rank" in operations or "filter" in operations or "select" in operations)


def _asks_for_multiple_inventory_indicators(text: str, lowered: str) -> bool:
    return (
        ("庫存" in text and any(token in text for token in ["兩個", "2個", "二個", "至少兩", "至少 2", "多個", "交叉"]))
        or ("inventory" in lowered and any(token in lowered for token in ["two", "multiple", "cross"]))
    )


def _has_inventory_amount_metric_request(text: str, lowered: str, *, has_inventory_qty: bool) -> bool:
    explicit_amount_tokens = ["inventory amount", "stock amount", "庫存金額", "存貨金額", "庫存額", "金額"]
    if _has_any(text, lowered, explicit_amount_tokens):
        return True
    return _has_any(text, lowered, INVENTORY_AMOUNT_TOKENS) and not has_inventory_qty


def _infer_requested_operations(text: str, lowered: str, task_family: str, time_scope: dict[str, Any]) -> list[str]:
    operations: list[str] = []
    top_n = _extract_top_n(text)
    if _has_any(text, lowered, COMPARE_TOKENS + ["對照"]) or time_scope.get("mode") == "period_pair":
        operations.append("compare")
    if _has_any(text, lowered, TREND_TOKENS + DEMAND_MOMENTUM_TOKENS + STOCK_BUILDUP_TOKENS) or time_scope.get("mode") in {"multi_month_series", "recent_n_months", "date_range"} or any(token in text or token in lowered for token in ["一直", "一路", "持續", "連續", "最近", "momentum", "declining", "growing", "growth", "成長"]):
        operations.append("trend")
    if any(token in text or token in lowered for token in ["找出", "篩選", "符合", "哪些", "挑出", "辨識", "有沒有", "identify", "find", "which", "where"]):
        operations.append("filter")
    if any(token in text or token in lowered for token in ["選出", "挑出", "select", "choose"]):
        operations.append("select")
    if any(token in text or token in lowered for token in ["檢查", "交叉", "一致", "同時", "以及", "也", "分辨", "區分", "只有其中", "只有一邊", "兩個指標", "多指標", "庫存金額與庫存數量", "庫存金額和庫存數量", "cross-check", "cross check", "support", "both", "only one", "only those", "same groups", "evaluate", "all considered", "considered", "direction"]):
        operations.append("cross_check")
    if top_n is not None or _is_ranking_question(text, lowered) or any(token in text or token in lowered for token in ["排序", "最異常", "最需要", "最明顯", "關注", "選出", "挑出", "rank", "management risk", "highest risk"]):
        operations.append("rank")
    if any(token in text or token in lowered for token in ["反證", "相反證據", "降低其風險", "降低風險", "可能降低", "確定答案", "因為", "造成", "counter", "counter-evidence", "counter evidence"]):
        operations.append("counter_evidence")
    if any(token in text or token in lowered for token in ["異常", "異常指標", "異常訊號", "異常信號", "警示", "anomaly", "anomalies", "signals"]):
        operations.append("anomaly")
    if any(token in text or token in lowered for token in ["排除", "分開呈現", "分開列", "不可比較", "不具可比", "non-comparable", "not comparable", "exclude", "excluded"]):
        operations.append("exclude")
    if _is_metric_relationship_question(text, lowered):
        operations.append("relationship")
    if _has_any(text, lowered, RATIO_TOKENS):
        operations.append("proxy")
    if any(token in text or token in lowered for token in ["限制", "代理指標", "不能", "不要直接停止", "不允許", "不要改用", "資料不足", "缺少", "避免只依", "避免只用", "單一指標", "limitation", "limitations", "limits"]):
        operations.append("limitations")
    return _unique(operations or [task_family or "lookup"])


def _extract_top_n(text: str) -> int | None:
    patterns = [
        r"(?:top|前|最)\s*(?P<n>\d+|[一二三四五六七八九十兩]+)\s*(?:名|個|項|筆|條)?",
        r"(?P<n>\d+|[一二三四五六七八九十兩]+)\s*(?:個|名|條)\s*(?:可比較)?\s*(?:事業群|產品線|business groups?|product lines?)",
        r"(?P<n>\d+|[一二三四五六七八九十兩]+)\s*個\s*最",
        r"(?:跌最多的|下降最多的|衰退最大的)\s*(?P<n>\d+|[一二三四五六七八九十兩]+)\s*個",
        r"(?P<n>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:business groups?|product lines?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        raw = match.group("n")
        parsed = _parse_small_number(raw)
        if parsed is not None:
            return parsed
    return None


def _has_explicit_metric(text: str, lowered: str) -> bool:
    return _has_any(
        text,
        lowered,
        REVENUE_TOKENS + INVENTORY_AMOUNT_TOKENS + INVENTORY_QTY_TOKENS + RATIO_TOKENS + HEALTH_TOKENS + RISK_TOKENS,
    )


def _default_data_metrics() -> list[str]:
    return ["revenue_amount", "inventory_amount", "inventory_qty"]


def _performance_metrics(metrics: list[str]) -> list[str]:
    values = list(metrics)
    for metric in ["health_score", "risk_score", "revenue_amount", "inventory_amount", "revenue_inventory_amount_ratio"]:
        if metric not in values:
            values.append(metric)
    return values


def _infer_polarity(text: str, lowered: str) -> str | None:
    if _has_any(text, lowered, WORST_TOKENS):
        return "worst"
    if _has_any(text, lowered, BEST_TOKENS):
        return "best"
    return None


def _ranking_metric(text: str, lowered: str) -> str:
    if "health_score" in lowered or "health score" in lowered:
        return "health_score"
    if "risk_score" in lowered or "risk score" in lowered:
        return "risk_score"
    if _has_any(text, lowered, RATIO_TOKENS):
        return "revenue_inventory_amount_ratio"
    if _has_any(text, lowered, INVENTORY_QTY_TOKENS):
        return "inventory_qty"
    if _has_any(text, lowered, INVENTORY_AMOUNT_TOKENS) and not _has_any(text, lowered, REVENUE_TOKENS):
        return "inventory_amount"
    return "revenue_amount"


def _fallback_task_family(answer_strategy: str, target_entity: dict[str, Any], time_scope: dict[str, Any]) -> str:
    mapping = {
        "comparison": "cross_section_compare",
        "performance_weakness": "performance_assessment",
        "ranking": "entity_ranking",
        "trend": "overall_trend_analysis" if target_entity.get("dimension") == "overall" else "entity_trend_comparison",
        "risk": "risk_scan",
        "diagnosis": "diagnosis",
        "overview": "metric_lookup",
        "chart": "chart_request",
        "data_quality": "data_quality",
        "unsupported": "unsupported",
        "metric_query": "metric_lookup",
        "query": "metric_lookup",
    }
    if time_scope.get("mode") == "period_pair":
        return "period_pair_compare"
    return mapping.get(answer_strategy, answer_strategy or "metric_lookup")


def _comparison_axis_for(target_entity: dict[str, Any], time_scope: dict[str, Any]) -> dict[str, Any]:
    if time_scope.get("mode") in {"period_pair", "multi_month_series", "recent_n_months", "year_over_year"}:
        return {"axis": "time", "dimension": "month", "baseline": time_scope.get("mode")}
    if target_entity.get("dimension") in {"business_group", "product_line_5"} and target_entity.get("value") is None:
        return {"axis": "entity", "dimension": target_entity.get("dimension"), "baseline": "peers"}
    return {"axis": "none", "dimension": None, "baseline": None}


def _fallback_answer_style(answer_strategy: str) -> str:
    if answer_strategy in {"ranking", "risk", "diagnosis", "performance_weakness"}:
        return "conclusion_first"
    if answer_strategy == "chart":
        return "chart_only"
    if answer_strategy == "data_quality":
        return "coverage_summary"
    return "evidence_first"


def _normalize_peer_target(target_entity: dict[str, Any]) -> dict[str, Any]:
    if target_entity.get("dimension") == "overall":
        return {"dimension": "business_group", "value": None, "scope": "all"}
    return target_entity


def _peer_dimension(target_entity: dict[str, Any]) -> str:
    return "business_group" if target_entity.get("dimension") == "overall" else str(target_entity.get("dimension") or "business_group")


def _default_latest_month_scope(time_scope: dict[str, Any]) -> dict[str, Any]:
    return time_scope if time_scope.get("mode") == "latest_month" else {**time_scope, "mode": "latest_month"}


def _default_latest_or_single_month_scope(time_scope: dict[str, Any]) -> dict[str, Any]:
    return time_scope if time_scope.get("mode") in {"single_month", "latest_month"} else _default_latest_month_scope(time_scope)


def _default_relationship_scope(time_scope: dict[str, Any]) -> dict[str, Any]:
    if time_scope.get("mode") in {"recent_n_months", "date_range", "multi_month_series"}:
        return time_scope
    return _default_latest_month_scope(time_scope)


def _default_series_scope(time_scope: dict[str, Any]) -> dict[str, Any]:
    if time_scope.get("mode") in {"date_range", "multi_month_series", "recent_n_months", "year_over_year"}:
        return time_scope
    if time_scope.get("period_a") and time_scope.get("period_b"):
        return {**time_scope, "mode": "multi_month_series", "start_month": time_scope.get("period_a"), "end_month": time_scope.get("period_b")}
    return {**time_scope, "mode": "multi_month_series"}


def _default_single_or_latest_lookup_scope(time_scope: dict[str, Any]) -> dict[str, Any]:
    if time_scope.get("mode") == "single_month":
        return time_scope
    if time_scope.get("single_month") or time_scope.get("month"):
        month = time_scope.get("single_month") or time_scope.get("month")
        return {**time_scope, "mode": "single_month", "single_month": month, "month": month}
    return _default_latest_month_scope(time_scope)


def _extract_single_month(text: str) -> str | None:
    months = _extract_all_months(text)
    return months[0] if months else None


def _extract_period_pair(text: str) -> tuple[str, str] | None:
    matches = _extract_all_month_matches(text)
    unique_matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in matches:
        if item["month"] not in seen:
            unique_matches.append(item)
            seen.add(str(item["month"]))
    if len(unique_matches) >= 2 and _looks_like_period_pair_question(text):
        first = unique_matches[0]
        second = unique_matches[1]
        connector = text[first["span"][1] : second["span"][0]]
        if "比" in connector and not any(token in connector for token in ["與", "和", "以及", "跟"]):
            return str(second["month"]), str(first["month"])
        return str(first["month"]), str(second["month"])
    return None


def _extract_month_range(text: str) -> tuple[str, str] | None:
    quarter = _extract_quarter_range(text)
    if quarter:
        return quarter
    months = list(dict.fromkeys(_extract_all_months(text)))
    if len(months) >= 2 and any(token in text for token in ["到", "至", "~", "期間"]):
        return months[0], months[1]
    return None


def _extract_all_months(text: str) -> list[str]:
    return [item["month"] for item in _extract_all_month_matches(text)]


def _extract_all_month_matches(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(r"(20\d{2})\s*[-/\u5e74]?\s*(1[0-2]|0?[1-9])\s*(?:\u6708)?")
    matches = [
        {
            "month": f"{match.group(1)}-{int(match.group(2)):02d}",
            "span": match.span(),
            "year": match.group(1),
        }
        for match in pattern.finditer(text)
    ]
    matches.extend(_extract_english_month_matches(text))
    if matches:
        first_year = str(matches[0]["year"])
        occupied = [item["span"] for item in matches]
        for match in re.finditer(r"(?<!\d)(1[0-2]|0?[1-9])\s*\u6708", text):
            span = match.span()
            if any(not (span[1] <= used[0] or span[0] >= used[1]) for used in occupied):
                continue
            matches.append(
                {
                    "month": f"{first_year}-{int(match.group(1)):02d}",
                    "span": span,
                    "year": first_year,
                }
            )
    return sorted(matches, key=lambda item: item["span"][0])




def _extract_english_month_matches(text: str) -> list[dict[str, Any]]:
    month_map = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12,
    }
    month_pattern = "|".join(sorted(month_map, key=len, reverse=True))
    matches: list[dict[str, Any]] = []
    pair = re.search(rf"(?P<m1>{month_pattern})\s+(?:versus|vs\.?|and|to|-)\s+(?P<m2>{month_pattern})\s+(?P<year>20\d{{2}})", text, flags=re.IGNORECASE)
    if pair:
        year = pair.group("year")
        for key in ["m1", "m2"]:
            month = month_map[pair.group(key).lower()]
            span = pair.span(key)
            matches.append({"month": f"{year}-{month:02d}", "span": span, "year": year})
    for match in re.finditer(rf"(?P<mon>{month_pattern})\s+(?P<year>20\d{{2}})", text, flags=re.IGNORECASE):
        month = month_map[match.group("mon").lower()]
        matches.append({"month": f"{match.group('year')}-{month:02d}", "span": match.span(), "year": match.group("year")})
    return matches


def _extract_quarter_range(text: str) -> tuple[str, str] | None:
    match = re.search(r"(20\d{2})\s*Q([1-4])", text, flags=re.IGNORECASE)
    if not match:
        match = re.search(r"(20\d{2})\s*第?\s*([1-4])\s*季", text)
    if not match:
        return None
    year = match.group(1)
    quarter = int(match.group(2))
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2
    return f"{year}-{start_month:02d}", f"{year}-{end_month:02d}"


def _extract_recent_n(text: str) -> int | None:
    match = re.search(r"(?:近|最近)\s*(\d+|[一二三四五六七八九十兩]+)\s*個?月", text)
    if match:
        return _parse_small_number(match.group(1))
    lowered = text.lower()
    match = re.search(r"(?:latest|recent|last)\s+(?P<n>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+months", lowered)
    if match:
        return _parse_small_number(match.group("n"))
    if any(token in text or token in lowered for token in ["最近幾個月", "近幾個月", "recent months", "last few months"]):
        return 3
    return None


def _parse_small_number(raw: str) -> int | None:
    raw = str(raw).strip().lower()
    if raw.isdigit():
        return int(raw)
    english = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    if raw in english:
        return english[raw]
    return _parse_small_chinese_number(raw)


def _parse_small_chinese_number(raw: str) -> int | None:
    digits = {"一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if raw in digits:
        return digits[raw]
    if raw == "十":
        return 10
    if raw.startswith("十") and len(raw) == 2 and raw[1] in digits:
        return 10 + digits[raw[1]]
    if raw.endswith("十") and len(raw) == 2 and raw[0] in digits:
        return digits[raw[0]] * 10
    if "十" in raw:
        left, right = raw.split("十", 1)
        if left in digits and right in digits:
            return digits[left] * 10 + digits[right]
    return None


def _looks_like_period_pair_question(text: str) -> bool:
    if len(_extract_all_months(text)) < 2:
        return False
    lowered = text.lower()
    if any(token in text or token in lowered for token in COMPARE_TOKENS + ["以及", "與", "和", "比"]):
        return True
    return "變化" in text and any(token in text for token in ["到", "至", "~"])


def _extract_named_business_group(text: str) -> str | None:
    resolved = resolve_entity_value(text, "business_group")
    if resolved:
        return resolved
    patterns = [
        r"比較\s*(?P<value>[\w\u4e00-\u9fff+\-/]+)\s*(?:各月|每月|近\s*\d+\s*個?月)",
        r"(?P<value>[\w\u4e00-\u9fff+\-/]+)\s*(?:各月|每月|近\s*\d+\s*個?月).*(?:營收|庫存)",
        r"(?P<value>[\w\u4e00-\u9fff+\-/]+)\s*(?:底下|下面)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group("value").strip()
            if value and not _looks_like_non_entity_token(value):
                return resolve_entity_value(value, "business_group") or value
    if any(token in text for token in ["方案", "+"]):
        match = re.search(r"(?P<value>[\w\u4e00-\u9fff+\-/]*(?:方案|[\u4e00-\u9fff]+?\+[\u4e00-\u9fff\w]+))", text)
        if match:
            value = match.group("value").strip()
            if value and not _looks_like_non_entity_token(value):
                return resolve_entity_value(value, "business_group") or value
    return None


def _extract_named_product_line(text: str) -> str | None:
    resolved = resolve_entity_value(text, "product_line_5")
    if resolved:
        return resolved
    match = re.search(r"(?P<value>[\w\u4e00-\u9fff+\-/]+)\s*產品線", text)
    if not match:
        return None
    value = match.group("value").strip()
    if value in {"五大", "各", "哪個", "哪一個", "用"} or "五大" in value or _looks_like_non_entity_token(value):
        return None
    return resolve_entity_value(value, "product_line_5") or value


def _looks_like_non_entity_token(value: str) -> bool:
    cleaned = value.strip()
    if not cleaned:
        return True
    if re.search(r"20\d{2}", cleaned):
        return True
    if "產品線" in cleaned:
        return True
    if "各" in cleaned and any(token in cleaned for token in ["列出", "比較", "顯示", "查詢", "查看", "看一下"]):
        return True
    if any(cleaned.startswith(token) for token in ["列出", "比較", "顯示", "查詢", "查看", "看一下", "告訴我", "請以", "請用", "請"]):
        return True
    return cleaned in {
        "比較",
        "各月",
        "每月",
        "近",
        "營收",
        "庫存",
        "總體",
        "整體",
        "新事業群",
        "各新事業群",
        "事業群",
        "各事業群",
        "產品線",
        "各產品線",
        "各五大產品線",
        "哪個",
        "哪一個",
        "最新月份",
    }


def _has_any(text: str, lowered: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in lowered or keyword in text for keyword in keywords)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered
