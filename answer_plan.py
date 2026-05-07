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


def build_answer_plan(task_profile: Any, routing: Any) -> AnswerPlan:
    task_family = getattr(task_profile, "task_family", None)

    if task_family == "cross_section_compare":
        return AnswerPlan(
            primary_tools=["get_platform_performance_snapshot", "get_platform_ratios", "get_metric_table(platform_monthly)"],
            supporting_tools=["get_anomalies"],
            background_tools=["get_data_coverage"],
            forbidden_primary_tools=["get_contribution_analysis(revenue)"],
            max_key_observations=3,
            requires_table=True,
            display_debug_findings=False,
            conclusion_policy={
                "mode": "heuristic_display_projection",
                "headline_source": "same_month_entity_comparison",
                "must_not_use": ["mom_contribution_as_headline"],
            },
        )

    if task_family == "performance_assessment":
        return AnswerPlan(
            primary_tools=["get_platform_performance_snapshot", "get_inventory_turnover_proxy", "get_platform_ratios"],
            supporting_tools=["get_anomalies"],
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
        "ranking": ["get_top_groups", "get_platform_ranking"],
        "trend": ["get_yoy_mom_breakdown"],
        "risk": ["get_anomalies"],
        "diagnosis": ["get_root_cause_candidates", "get_contribution_analysis"],
        "performance_weakness": ["get_platform_performance_snapshot", "get_inventory_turnover_proxy", "get_platform_ratios"],
        "comparison": ["get_platform_performance_snapshot", "get_platform_ratios"],
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
