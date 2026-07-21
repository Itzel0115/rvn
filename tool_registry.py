from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolContract:
    tool_name: str
    description: str
    allowed_task_families: tuple[str, ...] = ()
    required_args: tuple[str, ...] = ()
    optional_args: tuple[str, ...] = ()
    supported_entity_dimensions: tuple[str, ...] = ()
    supported_metrics: tuple[str, ...] = ()
    supports_month: bool = False
    supports_period_pair: bool = False
    supports_parent_filter: bool = False
    output_evidence_type: str | None = None
    is_legacy: bool = False
    replacement_tool: str | None = None
    read_only: bool = True
    risk_level: str = "low"
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_evidence_types: tuple[str, ...] = ()
    supported_metric_ids: tuple[str, ...] = ()
    supported_dimension_ids: tuple[str, ...] = ()
    evidence_roles: tuple[str, ...] = ("primary",)
    max_output_rows: int = 50
    mcp_exposable: bool = False
    mcp_name: str | None = None
    requires_context: bool = True
    known_limitations: tuple[str, ...] = ()

    @property
    def allowed_args(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*self.required_args, *self.optional_args)))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


COMMON_ENTITY_DIMENSIONS = ("business_group", "product_line_5")
COMMON_METRICS = ("revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio")


TOOL_REGISTRY: dict[str, ToolContract] = {
    "get_entity_month_table": ToolContract(
        tool_name="get_entity_month_table",
        description="List all entities for one explicit month and metric.",
        allowed_task_families=("entity_month_table_lookup", "cross_section_compare"),
        required_args=("entity_dimension", "metric", "month"),
        optional_args=("dimension", "parent_filter", "include_qty"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=("revenue_amount", "inventory_amount", "inventory_qty"),
        supports_month=True,
        supports_parent_filter=True,
        output_evidence_type="entity_month_table",
        mcp_exposable=True, mcp_name="get_entity_month_table", evidence_roles=("primary",),
    ),
    "get_entity_metric_value": ToolContract(
        tool_name="get_entity_metric_value",
        description="Lookup one real-data entity metric for one explicit month.",
        allowed_task_families=("metric_lookup",),
        required_args=("entity_dimension", "entity_value", "metric", "month"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=COMMON_METRICS,
        supports_month=True,
        output_evidence_type="entity_metric_lookup",
    ),
    "get_entity_period_pair_table": ToolContract(
        tool_name="get_entity_period_pair_table",
        description="List all entities for two explicit periods and one metric without latest fallback.",
        allowed_task_families=("entity_period_pair_table_lookup",),
        required_args=("entity_dimension", "metric", "period_a", "period_b"),
        optional_args=("parent_filter", "include_change"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=("revenue_amount", "inventory_amount", "inventory_qty"),
        supports_period_pair=True,
        supports_parent_filter=True,
        output_evidence_type="entity_period_pair_table",
    ),
    "get_entity_multi_month_table": ToolContract(
        tool_name="get_entity_multi_month_table",
        description="List all entities by month for an explicit date range and one metric.",
        allowed_task_families=("entity_multi_month_table_lookup",),
        required_args=("entity_dimension", "metric", "start_month", "end_month"),
        optional_args=("parent_filter",),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=("revenue_amount", "inventory_amount", "inventory_qty"),
        supports_parent_filter=True,
        output_evidence_type="entity_multi_month_table",
    ),
    "get_entity_period_pair_value": ToolContract(
        tool_name="get_entity_period_pair_value",
        description="Lookup one named entity for two explicit periods and one metric without latest fallback.",
        allowed_task_families=("entity_period_pair_metric_lookup",),
        required_args=("entity_dimension", "entity_value", "metric", "period_a", "period_b"),
        optional_args=("parent_filter",),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=COMMON_METRICS,
        supports_period_pair=True,
        supports_parent_filter=True,
        output_evidence_type="entity_period_pair_value",
    ),
    "get_entity_metric_ranking": ToolContract(
        tool_name="get_entity_metric_ranking",
        description="Rank real-data entities by a single metric.",
        allowed_task_families=("entity_ranking",),
        required_args=("entity_dimension", "metric"),
        optional_args=("dimension", "month", "top_n", "parent_filter", "sort_direction"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=(*COMMON_METRICS, "health_score", "risk_score"),
        supports_month=True,
        supports_parent_filter=True,
        output_evidence_type="entity_metric_ranking",
        mcp_exposable=True, mcp_name="get_entity_metric_ranking", evidence_roles=("primary",),
    ),
    "get_entity_performance_snapshot": ToolContract(
        tool_name="get_entity_performance_snapshot",
        description="Return deterministic entity performance scorecard; relationship analyses may use it only as supporting context.",
        allowed_task_families=("latest_month_entity_summary", "cross_section_compare", "performance_assessment", "parent_child_drilldown", "metric_relationship_analysis"),
        required_args=("entity_dimension",),
        optional_args=("dimension", "month", "parent_filter", "top_n"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supports_month=True,
        supports_parent_filter=True,
        output_evidence_type="entity_performance_snapshot",
        mcp_exposable=True, mcp_name="get_entity_performance_snapshot", evidence_roles=("supporting", "diagnostic"),
    ),
    "get_entity_cross_section_comparison": ToolContract(
        tool_name="get_entity_cross_section_comparison",
        description="Return same-month entity comparison.",
        allowed_task_families=("cross_section_compare",),
        required_args=("entity_dimension",),
        optional_args=("month", "parent_filter"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supports_month=True,
        supports_parent_filter=True,
        output_evidence_type="entity_cross_section_comparison",
    ),
    "get_entity_period_pair_comparison": ToolContract(
        tool_name="get_entity_period_pair_comparison",
        description="Compare one explicit period pair by real-data entity.",
        allowed_task_families=("period_pair_compare",),
        required_args=("entity_dimension", "metric", "period_a", "period_b"),
        optional_args=("parent_filter",),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=("revenue", "inventory_amount", "inventory_qty"),
        supports_period_pair=True,
        supports_parent_filter=True,
        output_evidence_type="entity_period_pair_comparison",
    ),
    "get_period_pair_metric_comparison": ToolContract(
        tool_name="get_period_pair_metric_comparison",
        description="Compare one explicit period pair at overall or supported aggregate dimension.",
        allowed_task_families=("period_pair_compare",),
        required_args=("metric", "period_a", "period_b"),
        optional_args=("dimension", "top_n"),
        supported_entity_dimensions=("overall", "business_group", "platform"),
        supported_metrics=("revenue", "inventory_amount", "inventory_qty"),
        supports_period_pair=True,
        output_evidence_type="period_pair_metric_comparison",
    ),
    "get_entity_time_series": ToolContract(
        tool_name="get_entity_time_series",
        description="Return one named entity's monthly time series.",
        allowed_task_families=("entity_time_series",),
        required_args=("entity_dimension", "entity_value", "metric"),
        optional_args=("recent_n", "start_month", "end_month", "parent_filter"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=COMMON_METRICS,
        supports_parent_filter=True,
        output_evidence_type="entity_time_series",
    ),
    "get_overall_time_series": ToolContract(
        tool_name="get_overall_time_series",
        description="Return overall monthly trend for one metric.",
        allowed_task_families=("overall_trend_analysis",),
        required_args=("metric",),
        optional_args=("recent_n", "start_month", "end_month"),
        supported_entity_dimensions=("overall",),
        supported_metrics=("revenue_amount", "inventory_amount", "inventory_qty"),
        output_evidence_type="overall_time_series",
        mcp_exposable=True, mcp_name="get_overall_time_series", evidence_roles=("primary",),
    ),
    "get_entity_trend_comparison": ToolContract(
        tool_name="get_entity_trend_comparison",
        description="Return monthly trend comparison across entities.",
        allowed_task_families=("entity_trend_comparison",),
        required_args=("entity_dimension", "metric"),
        optional_args=("recent_n", "start_month", "end_month", "parent_filter"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=COMMON_METRICS,
        supports_parent_filter=True,
        output_evidence_type="entity_trend_comparison",
    ),
    "get_revenue_inventory_relationship": ToolContract(
        tool_name="get_revenue_inventory_relationship",
        description="Return deterministic revenue/inventory relationship labels.",
        allowed_task_families=("metric_relationship_analysis", "risk_scan"),
        required_args=("entity_dimension",),
        optional_args=("recent_n", "month", "parent_filter"),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supports_month=True,
        supports_parent_filter=True,
        output_evidence_type="metric_relationship",
        mcp_exposable=True, mcp_name="get_revenue_inventory_relationship", evidence_roles=("primary",),
    ),
    "get_entity_contribution_analysis": ToolContract(
        tool_name="get_entity_contribution_analysis",
        description="Return deterministic entity contribution between two explicit periods.",
        allowed_task_families=("contribution_analysis",),
        required_args=("entity_dimension", "metric", "period_a", "period_b"),
        optional_args=("parent_filter",),
        supported_entity_dimensions=COMMON_ENTITY_DIMENSIONS,
        supported_metrics=COMMON_METRICS,
        supports_period_pair=True,
        supports_parent_filter=True,
        output_evidence_type="entity_contribution_analysis",
    ),
    "get_chart_payload": ToolContract(
        tool_name="get_chart_payload",
        description="Return chart-ready payload for frontend rendering.",
        allowed_task_families=("chart_request",),
        required_args=(),
        optional_args=("chart_key", "chart_type", "month", "entity_dimension", "entity_value", "metric", "parent_filter"),
        supports_month=True,
        output_evidence_type="chart_payload",
    ),
    "get_chart_table": ToolContract(
        tool_name="get_chart_table",
        description="Return table rows aligned with a chart payload.",
        allowed_task_families=("chart_request",),
        required_args=(),
        optional_args=("chart_key", "chart_type", "month", "entity_dimension", "entity_value", "metric", "parent_filter"),
        supports_month=True,
        output_evidence_type="chart_table",
    ),
    "get_data_coverage": ToolContract(
        tool_name="get_data_coverage",
        description="Return available months, row counts, and supported domains.",
        allowed_task_families=("data_quality", "forecast_unsupported"),
        output_evidence_type="data_coverage",
        mcp_exposable=True, mcp_name="get_data_coverage", evidence_roles=("diagnostic",), requires_context=True,
    ),
    "get_mapping_summary": ToolContract(
        tool_name="get_mapping_summary",
        description="Return mapping summary and data alignment coverage.",
        allowed_task_families=("data_quality", "forecast_unsupported"),
        output_evidence_type="mapping_summary",
    ),
    "get_tool_capability_matrix": ToolContract(
        tool_name="get_tool_capability_matrix",
        description="Return tool capability metadata.",
        allowed_task_families=("data_quality", "forecast_unsupported"),
        output_evidence_type="tool_capability_matrix",
    ),
    "get_anomalies": ToolContract(
        tool_name="get_anomalies",
        description="Return deterministic anomaly records.",
        allowed_task_families=("risk_scan", "diagnosis", "cross_section_compare"),
        optional_args=("month",),
        supports_month=True,
        output_evidence_type="anomaly",
    ),
    "get_yoy_mom_breakdown": ToolContract(
        tool_name="get_yoy_mom_breakdown",
        description="Return MoM and YoY change rows.",
        allowed_task_families=("trend_analysis", "diagnosis"),
        required_args=("metric",),
        optional_args=("dimension",),
        supported_entity_dimensions=("platform", "business_group", "overall"),
        supported_metrics=("revenue", "inventory_amount", "inventory_qty"),
        output_evidence_type="yoy_mom_breakdown",
    ),
    "get_contribution_analysis": ToolContract(
        tool_name="get_contribution_analysis",
        description="Return current-vs-previous contribution analysis.",
        allowed_task_families=("time_compare", "diagnosis"),
        required_args=("metric",),
        optional_args=("dimension",),
        supported_entity_dimensions=("platform", "business_group"),
        supported_metrics=("revenue", "inventory_amount", "inventory_qty"),
        output_evidence_type="contribution_analysis",
    ),
    "get_inventory_turnover_proxy": ToolContract(
        tool_name="get_inventory_turnover_proxy",
        description="Return inventory efficiency proxy rows.",
        allowed_task_families=("performance_assessment", "risk_scan", "diagnosis"),
        output_evidence_type="inventory_turnover_proxy",
    ),
    "get_root_cause_candidates": ToolContract(
        tool_name="get_root_cause_candidates",
        description="Return candidate observations without claiming root cause.",
        allowed_task_families=("diagnosis",),
        optional_args=("metric",),
        supported_metrics=("revenue",),
        output_evidence_type="root_cause_candidate",
    ),
    "get_platform_ratios": ToolContract(
        tool_name="get_platform_ratios",
        description="Legacy wrapper for business-group revenue/inventory proxy ratios.",
        allowed_task_families=("risk_scan", "diagnosis", "performance_assessment"),
        output_evidence_type="platform_ratio",
        is_legacy=True,
        replacement_tool="get_revenue_inventory_relationship or get_entity_performance_snapshot",
    ),
    "get_platform_ranking": ToolContract(
        tool_name="get_platform_ranking",
        description="Legacy platform ranking wrapper; business_group entity ranking is preferred.",
        allowed_task_families=("entity_ranking",),
        optional_args=("metric",),
        supported_metrics=("revenue", "inventory_amount", "inventory_qty"),
        output_evidence_type="platform_ranking",
        is_legacy=True,
        replacement_tool="get_entity_metric_ranking",
    ),
    "get_platform_performance_snapshot": ToolContract(
        tool_name="get_platform_performance_snapshot",
        description="Legacy platform scorecard wrapper; entity performance snapshot is preferred.",
        allowed_task_families=("performance_assessment", "latest_month_entity_summary"),
        output_evidence_type="platform_performance_snapshot",
        is_legacy=True,
        replacement_tool="get_entity_performance_snapshot",
    ),
    "get_top_groups": ToolContract(
        tool_name="get_top_groups",
        description="Legacy business-group ranking helper.",
        allowed_task_families=("entity_ranking",),
        optional_args=("metric",),
        supported_metrics=("revenue", "inventory"),
        output_evidence_type="group_ranking",
        is_legacy=True,
        replacement_tool="get_entity_metric_ranking",
    ),
    "get_metric_table": ToolContract(
        tool_name="get_metric_table",
        description="Legacy raw metric table loader.",
        allowed_task_families=("metric_lookup", "trend_analysis", "diagnosis"),
        optional_args=("metric",),
        supported_metrics=("revenue_trend", "inventory_amount_trend", "inventory_qty_trend", "platform_monthly", "anomalies"),
        output_evidence_type="metric_table",
        is_legacy=True,
        replacement_tool="task-specific entity or time-series tools",
    ),
}


def get_tool_contract(tool_name: str) -> ToolContract:
    return TOOL_REGISTRY[tool_name]


def tool_registry_payload() -> dict[str, Any]:
    return {name: contract.to_dict() for name, contract in TOOL_REGISTRY.items()}


def is_tool_allowed_for_task(tool_name: str, task_family: str) -> bool:
    contract = TOOL_REGISTRY.get(tool_name)
    if contract is None:
        return False
    return not contract.allowed_task_families or task_family in contract.allowed_task_families


def build_allowed_tool_names_for_task_family(task_family: str, *, include_legacy: bool = False) -> list[str]:
    if task_family == "forecast_unsupported":
        return []
    names: list[str] = []
    for name, contract in TOOL_REGISTRY.items():
        if contract.is_legacy and not include_legacy:
            continue
        if is_tool_allowed_for_task(name, task_family):
            names.append(name)
    return names


def build_llm_allowed_tools_from_registry(tool_names: list[str] | None = None) -> dict[str, ToolContract]:
    names = tool_names or list(TOOL_REGISTRY)
    return {name: TOOL_REGISTRY[name] for name in names if name in TOOL_REGISTRY}


def validate_tool_args_against_registry(
    tool_name: str,
    args: dict[str, Any],
    *,
    enforce_required: bool = False,
) -> tuple[bool, str | None]:
    contract = TOOL_REGISTRY.get(tool_name)
    if contract is None:
        return False, f"Unknown tool requested by planner: {tool_name}"
    unexpected = set(args.keys()) - set(contract.allowed_args)
    if unexpected:
        return False, f"Planner returned unsupported args for {tool_name}: {sorted(unexpected)}"
    if enforce_required:
        missing = [name for name in contract.required_args if name not in args]
        if missing:
            return False, f"Planner omitted required args for {tool_name}: {missing}"
    metric = args.get("metric")
    if metric is not None and contract.supported_metrics and metric not in contract.supported_metrics:
        return False, f"Planner returned unsupported metric for {tool_name}: {metric}"
    dimension = args.get("dimension")
    if dimension is not None and contract.supported_entity_dimensions and dimension not in contract.supported_entity_dimensions:
        return False, f"Planner returned unsupported dimension for {tool_name}: {dimension}"
    entity_dimension = args.get("entity_dimension")
    if (
        entity_dimension is not None
        and contract.supported_entity_dimensions
        and entity_dimension not in contract.supported_entity_dimensions
    ):
        return False, f"Planner returned unsupported dimension for {tool_name}: {entity_dimension}"
    return True, None
