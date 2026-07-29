from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnswerPlan:
    primary_tools: list[str] = field(default_factory=list)
    supporting_tools: list[str] = field(default_factory=list)
    background_tools: list[str] = field(default_factory=list)
    forbidden_primary_tools: list[str] = field(default_factory=list)
    max_key_observations: int = 3
    requires_table: bool = False
    display_debug_findings: bool = False
    conclusion_policy: dict[str, Any] = field(default_factory=dict)
    semantic_requirement_id: str | None = None
    required_primary_evidence: list[str] = field(default_factory=list)
    required_supporting_evidence: list[str] = field(default_factory=list)
    optional_counter_evidence: list[str] = field(default_factory=list)
    required_limitations: list[str] = field(default_factory=list)
    partial_completion_rule: dict[str, Any] = field(default_factory=dict)


def build_answer_plan(task_profile: Any, routing: Any) -> AnswerPlan:
    task_family = getattr(task_profile, "task_family", None)

    if task_family in {"latest_month_platform_summary", "latest_month_entity_summary"}:
        return AnswerPlan(
            primary_tools=["get_entity_performance_snapshot"],
            supporting_tools=["get_entity_cross_section_comparison", "get_inventory_turnover_proxy"],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_metric_table", "get_platform_ranking(inventory_amount)"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={
                "mode": "heuristic_display_projection",
                "headline_source": "latest_month_entity_scorecard",
                "must_not_use": ["metric_table_as_headline", "raw_platform_ranking_as_headline"],
            },
        )

    if task_family == "period_pair_compare":
        return AnswerPlan(
            primary_tools=["get_entity_period_pair_comparison"],
            supporting_tools=["get_period_pair_metric_comparison"],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_metric_table(platform_monthly)", "get_platform_ranking(inventory_amount)"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={
                "mode": "heuristic_display_projection",
                "headline_source": "explicit_period_pair_difference",
            },
        )

    if task_family == "entity_period_pair_table_lookup":
        requested = getattr(task_profile, "task_requirements", {}) or {}
        supporting = ["get_entity_performance_snapshot"] if len(requested.get("requested_metrics") or []) > 1 or "rank" in (requested.get("requested_operations") or []) else []
        return AnswerPlan(
            primary_tools=["get_entity_period_pair_table"],
            supporting_tools=supporting,
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_entity_period_pair_comparison", "get_period_pair_metric_comparison", "get_entity_month_table"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "entity_period_pair_table"},
        )

    if task_family == "entity_multi_month_table_lookup":
        return AnswerPlan(
            primary_tools=["get_entity_multi_month_table"],
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_entity_period_pair_comparison", "get_period_pair_metric_comparison", "get_entity_month_table"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "entity_multi_month_table"},
        )

    if task_family == "entity_period_pair_metric_lookup":
        return AnswerPlan(
            primary_tools=["get_entity_period_pair_value"],
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_entity_period_pair_comparison", "get_period_pair_metric_comparison", "get_entity_month_table"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "entity_period_pair_value"},
        )

    if task_family == "entity_time_series":
        return AnswerPlan(
            primary_tools=["get_entity_time_series"],
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_yoy_mom_breakdown", "get_contribution_analysis(revenue)"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "entity_time_series"},
        )

    if task_family == "overall_trend_analysis":
        return AnswerPlan(
            primary_tools=["get_overall_time_series"],
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_entity_period_pair_comparison", "get_contribution_analysis(revenue)"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "overall_time_series"},
        )

    if task_family == "entity_trend_comparison":
        requested = getattr(task_profile, "task_requirements", {}) or {}
        operations = set(requested.get("requested_operations") or [])
        supporting = []
        if "anomaly" in operations or "risk_score" in (requested.get("requested_metrics") or []):
            supporting.append("get_anomalies")
        if len(requested.get("requested_metrics") or []) > 1:
            supporting.append("get_entity_performance_snapshot")
        management_selection = bool(requested.get("requires_named_selection") or requested.get("requires_counter_evidence") or requested.get("requires_recommendation"))
        return AnswerPlan(
            primary_tools=["get_entity_trend_comparison"],
            supporting_tools=list(dict.fromkeys(supporting)),
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_entity_period_pair_comparison", "get_yoy_mom_breakdown"],
            max_key_observations=6 if management_selection else 3,
            requires_table=True,
            display_debug_findings=False,
            required_supporting_evidence=["counter_evidence", "next_action"] if management_selection else [],
            optional_counter_evidence=["revenue_growth", "inventory_decline", "no_anomaly"] if management_selection else [],
            required_limitations=["多指標管理風險排序為歷史資料 proxy，不代表因果或預測。"] if management_selection else [],
            conclusion_policy={"mode": "management_risk_selection" if management_selection else "heuristic_display_projection", "headline_source": "management_risk_rank" if management_selection else "entity_trend_comparison"},
        )

    if task_family == "metric_relationship_analysis":
        relationship_tools = ["get_revenue_inventory_relationship"]
        supporting_tools = ["get_entity_performance_snapshot"]
        requested = getattr(task_profile, "task_requirements", {}) or {}
        operations = set(requested.get("requested_operations") or [])
        requested_metrics = set(requested.get("requested_metrics") or [])
        if getattr(task_profile, "time_scope", {}).get("mode") in {"recent_n_months", "date_range", "multi_month_series"} or "trend" in operations or "cross_check" in operations:
            relationship_tools.append("get_entity_trend_comparison")
            supporting_tools.insert(0, "get_entity_trend_comparison")
        if "anomaly" in operations or "risk_score" in requested_metrics:
            supporting_tools.append("get_anomalies")
        if "cross_check" in operations or "inventory_qty" in requested_metrics or "revenue_inventory_amount_ratio" in requested_metrics:
            supporting_tools.append("get_inventory_turnover_proxy")
        return AnswerPlan(
            primary_tools=relationship_tools,
            supporting_tools=list(dict.fromkeys(supporting_tools)),
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_root_cause_candidates", "get_contribution_analysis(revenue)"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "metric_relationship_analysis"},
        )

    if task_family == "contribution_analysis":
        return AnswerPlan(
            primary_tools=["get_entity_contribution_analysis"],
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_yoy_mom_breakdown", "get_overall_time_series"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "entity_contribution_analysis"},
        )

    if task_family == "forecast_unsupported":
        return AnswerPlan(
            primary_tools=[],
            supporting_tools=[],
            background_tools=[],
            forbidden_primary_tools=["get_metric_table", "get_metric_table(revenue_trend)", "get_metric_table(inventory_amount_trend)"],
            max_key_observations=2,
            requires_table=False,
            display_debug_findings=False,
            conclusion_policy={
                "mode": "unsupported",
                "headline_source": "forecast_not_available",
            },
        )

    if task_family == "parent_child_drilldown":
        return AnswerPlan(
            primary_tools=["get_entity_performance_snapshot"],
            supporting_tools=["get_inventory_turnover_proxy"],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_contribution_analysis(revenue)", "get_yoy_mom_breakdown"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "parent_child_drilldown"},
        )

    if task_family == "entity_month_table_lookup":
        return AnswerPlan(
            primary_tools=["get_entity_month_table"],
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_entity_period_pair_comparison", "get_overall_time_series", "get_entity_time_series"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "entity_month_table"},
        )

    if task_family == "cross_section_compare":
        metrics = list(getattr(task_profile, "metrics", []) or [])
        requirements = getattr(task_profile, "task_requirements", {}) or {}
        operations = set(requirements.get("requested_operations") or [])
        time_scope = getattr(task_profile, "time_scope", {}) or {}
        single_metric = len(metrics) == 1 and time_scope.get("mode") in {"single_month", "latest_month"}
        supporting_tools = [] if single_metric else ["get_anomalies"]
        if "proxy" in operations:
            supporting_tools.append("get_inventory_turnover_proxy")
        return AnswerPlan(
            primary_tools=["get_entity_month_table"] if single_metric else ["get_entity_cross_section_comparison", "get_entity_performance_snapshot"],
            supporting_tools=list(dict.fromkeys(supporting_tools)),
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_contribution_analysis(revenue)", "get_entity_period_pair_comparison", "get_overall_time_series"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={
                "mode": "heuristic_display_projection",
                "headline_source": "same_month_entity_comparison",
                "must_not_use": ["mom_contribution_as_headline", "latest_month_if_explicit_month"],
            },
        )

    if task_family == "performance_assessment":
        return AnswerPlan(
            primary_tools=["get_entity_performance_snapshot"],
            supporting_tools=["get_inventory_turnover_proxy", "get_entity_cross_section_comparison", "get_anomalies"],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_platform_ranking(inventory_amount)"],
            max_key_observations=3,
            requires_table=False,
            display_debug_findings=False,
            conclusion_policy={
                "mode": "heuristic_display_projection",
                "headline_source": "performance_proxy_not_inventory_amount_rank",
                "tie_policy": "state_tradeoff",
            },
        )

    if task_family == "risk_scan":
        requested = getattr(task_profile, "task_requirements", {}) or {}
        supporting = ["get_anomalies", "get_inventory_turnover_proxy"]
        if len(requested.get("requested_metrics") or []) > 2 or "trend" in (requested.get("requested_operations") or []):
            supporting.append("get_entity_trend_comparison")
        supporting.append("get_entity_performance_snapshot")
        return AnswerPlan(
            primary_tools=["get_revenue_inventory_relationship"],
            supporting_tools=list(dict.fromkeys(supporting)),
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_root_cause_candidates"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "risk_scan"},
        )

    if task_family == "metric_lookup":
        target_entity = getattr(task_profile, "target_entity", {}) or {}
        primary_tools = ["get_entity_metric_value"] if target_entity.get("value") else ["get_metric_table"]
        return AnswerPlan(
            primary_tools=primary_tools,
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=[],
            max_key_observations=3,
            requires_table=False,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "metric_lookup"},
        )

    if task_family == "chart_request":
        return AnswerPlan(
            primary_tools=["get_chart_payload"],
            supporting_tools=["get_chart_table"],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=[],
            max_key_observations=3,
            requires_table=False,
            display_debug_findings=False,
            conclusion_policy={"mode": "heuristic_display_projection", "headline_source": "chart_request"},
        )

    if task_family == "entity_ranking":
        target_dimension = (getattr(task_profile, "target_entity", {}) or {}).get("dimension")
        if target_dimension in {"business_group", "product_line_5", "platform"}:
            return AnswerPlan(
                primary_tools=["get_entity_metric_ranking"],
                supporting_tools=["get_entity_performance_snapshot"],
                background_tools=["get_data_coverage"],
                forbidden_primary_tools=["get_top_groups", "get_platform_ranking"],
                max_key_observations=3,
                requires_table=True,
                display_debug_findings=False,
                conclusion_policy={
                    "mode": "heuristic_display_projection",
                    "headline_source": "entity_metric_ranking",
                    "must_not_use": ["empty_primary_evidence_fallback"],
                },
            )

    if task_family == "time_compare":
        return AnswerPlan(
            primary_tools=["get_yoy_mom_breakdown", "get_contribution_analysis"],
            supporting_tools=[],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=[],
            max_key_observations=3,
            requires_table=False,
            display_debug_findings=False,
            conclusion_policy={
                "mode": "heuristic_display_projection",
                "headline_source": "period_change_and_contribution",
            },
        )

    answer_strategy = getattr(routing, "answer_strategy", None) or getattr(routing, "question_type", "query")
    return AnswerPlan(
        primary_tools=_default_primary_tools(answer_strategy),
        supporting_tools=_default_supporting_tools(answer_strategy),
        background_tools=["get_data_coverage"],
        forbidden_primary_tools=[],
        max_key_observations=3,
        requires_table=bool(getattr(task_profile, "requires_table", False)),
        display_debug_findings=False,
        conclusion_policy={"mode": "legacy_answer_contract", "headline_source": answer_strategy},
    )


def _default_primary_tools(answer_strategy: str) -> list[str]:
    mapping = {
        "ranking": ["get_entity_metric_ranking"],
        "trend": ["get_yoy_mom_breakdown"],
        "risk": ["get_anomalies"],
        "diagnosis": ["get_root_cause_candidates", "get_contribution_analysis"],
        "performance_weakness": ["get_entity_performance_snapshot", "get_inventory_turnover_proxy"],
        "comparison": ["get_entity_performance_snapshot", "get_entity_cross_section_comparison"],
        "chart": ["get_chart_payload"],
        "data_quality": ["get_data_coverage", "get_mapping_summary"],
    }
    return mapping.get(answer_strategy, ["get_metric_table"])


def _default_supporting_tools(answer_strategy: str) -> list[str]:
    mapping = {
        "risk": ["get_inventory_turnover_proxy", "get_platform_ratios"],
        "diagnosis": ["get_anomalies", "get_inventory_turnover_proxy"],
        "performance_weakness": ["get_anomalies"],
        "trend": ["get_contribution_analysis"],
    }
    return mapping.get(answer_strategy, [])
