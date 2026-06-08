from __future__ import annotations

from typing import Any

from tool_registry import TOOL_REGISTRY, is_tool_allowed_for_task, validate_tool_args_against_registry


METRIC_ALIASES = {
    None: None,
    "revenue": "revenue_amount",
    "revenue_amount": "revenue_amount",
    "inventory": "inventory_amount",
    "inventory_amount": "inventory_amount",
    "inventory_qty": "inventory_qty",
    "qty": "inventory_qty",
    "revenue_inventory_amount_ratio": "revenue_inventory_amount_ratio",
    "ratio": "revenue_inventory_amount_ratio",
    "health_score": "health_score",
    "risk_score": "risk_score",
}


class PlanValidator:
    def validate(
        self,
        canonical_task_profile: Any,
        llm_plan: Any,
        tool_registry: dict[str, Any] | None = None,
        deterministic_answer_plan: Any | None = None,
    ) -> dict[str, Any]:
        registry = tool_registry or TOOL_REGISTRY
        violations: list[str] = []
        canonical = _canonical_view(canonical_task_profile)
        task_family = canonical["task_family"]
        tools = list(getattr(llm_plan, "tools", []) or [])

        if getattr(llm_plan, "fallback_required", False):
            violations.append("planner_requested_fallback")

        planned_family = str(getattr(llm_plan, "task_family", "") or "")
        if planned_family and task_family and planned_family != task_family:
            violations.append("task_family_mismatch")

        if task_family == "forecast_unsupported":
            if str(getattr(llm_plan, "question_type", "") or "") not in {"", "unsupported"}:
                violations.append("forecast_became_supported")
            if tools:
                violations.append("forecast_tool_violation")
            return _result(violations)

        allowed_by_answer_plan = _allowed_tools_from_answer_plan(deterministic_answer_plan)
        for call in tools:
            tool_name = str(getattr(call, "tool_name", "") or "")
            args = dict(getattr(call, "args", {}) or {})
            contract = registry.get(tool_name)
            if contract is None:
                violations.append(f"unknown_tool:{tool_name}")
                continue
            if not is_tool_allowed_for_task(tool_name, task_family):
                violations.append(f"tool_not_allowed_for_task:{tool_name}")
            if allowed_by_answer_plan and tool_name not in allowed_by_answer_plan:
                violations.append(f"tool_not_in_deterministic_plan:{tool_name}")
            ok, error = validate_tool_args_against_registry(tool_name, args, enforce_required=True)
            if not ok:
                violations.append(error or f"invalid_tool_args:{tool_name}")
                continue
            violations.extend(_validate_time(canonical, tool_name, args))
            violations.extend(_validate_entity(canonical, tool_name, args))
            violations.extend(_validate_metric(canonical, tool_name, args))
            violations.extend(_validate_chart(canonical, tool_name, args))

        if task_family == "entity_month_table_lookup" and not any(getattr(call, "tool_name", None) == "get_entity_month_table" for call in tools):
            violations.append("entity_month_table_tool_missing")
        if task_family == "entity_period_pair_table_lookup" and not any(getattr(call, "tool_name", None) == "get_entity_period_pair_table" for call in tools):
            violations.append("entity_period_pair_table_tool_missing")
        if task_family == "entity_multi_month_table_lookup" and not any(getattr(call, "tool_name", None) == "get_entity_multi_month_table" for call in tools):
            violations.append("entity_multi_month_table_tool_missing")
        if task_family == "entity_period_pair_metric_lookup" and not any(getattr(call, "tool_name", None) == "get_entity_period_pair_value" for call in tools):
            violations.append("entity_period_pair_value_tool_missing")
        if task_family == "metric_lookup" and canonical["target_entity"].get("value") and not any(
            getattr(call, "tool_name", None) == "get_entity_metric_value" for call in tools
        ):
            violations.append("entity_metric_lookup_tool_missing")

        return _result(violations)


def validate_plan(
    canonical_task_profile: Any,
    llm_plan: Any,
    tool_registry: dict[str, Any] | None = None,
    deterministic_answer_plan: Any | None = None,
) -> dict[str, Any]:
    return PlanValidator().validate(canonical_task_profile, llm_plan, tool_registry, deterministic_answer_plan)


def _result(violations: list[str]) -> dict[str, Any]:
    unique = list(dict.fromkeys(violations))
    valid = not unique
    return {
        "valid": valid,
        "fallback_to_deterministic": not valid,
        "reason": "valid" if valid else unique[0],
        "violations": unique,
    }


def _canonical_view(profile: Any) -> dict[str, Any]:
    time_scope = dict(getattr(profile, "time_scope", {}) or {})
    target_entity = dict(getattr(profile, "target_entity", {}) or {})
    parent_entity = dict(getattr(profile, "parent_entity", {}) or {})
    metrics = list(getattr(profile, "metrics", []) or [])
    metric = getattr(profile, "metric", None) or (metrics[0] if metrics else None)
    return {
        "task_family": str(getattr(profile, "task_family", "") or ""),
        "time_scope": time_scope,
        "target_entity": target_entity,
        "parent_entity": parent_entity,
        "metric": _canonical_metric(metric),
        "chart_type": getattr(profile, "chart_type", None),
    }


def _allowed_tools_from_answer_plan(answer_plan: Any | None) -> set[str]:
    if answer_plan is None:
        return set()
    names: list[str] = []
    for attr in ["primary_tools", "supporting_tools"]:
        names.extend(list(getattr(answer_plan, attr, []) or []))
    return {_base_tool_name(name) for name in names}


def _base_tool_name(name: str) -> str:
    return str(name).split("(", 1)[0]


def _validate_time(canonical: dict[str, Any], tool_name: str, args: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    time_scope = canonical["time_scope"]
    contract = TOOL_REGISTRY.get(tool_name)
    allowed_args = set(getattr(contract, "allowed_args", ()) if contract else ())
    expected_month = time_scope.get("month") or time_scope.get("single_month")
    if expected_month and ("month" in allowed_args or "month" in args):
        if args.get("month") != expected_month:
            violations.append("date_mismatch:month")
    for field in ["period_a", "period_b"]:
        expected = time_scope.get(field)
        if expected and (field in allowed_args or field in args):
            if args.get(field) != expected:
                violations.append(f"date_mismatch:{field}")
    for field in ["start_month", "end_month"]:
        expected = time_scope.get(field)
        if expected and (field in allowed_args or field in args):
            if args.get(field) != expected:
                violations.append(f"date_mismatch:{field}")
    expected_recent_n = time_scope.get("recent_n")
    if expected_recent_n is not None and ("recent_n" in allowed_args or "recent_n" in args):
        if args.get("recent_n") != expected_recent_n:
            violations.append("date_mismatch:recent_n")
    if time_scope.get("mode") == "period_pair" and tool_name in {"get_entity_month_table", "get_entity_time_series", "get_overall_time_series"}:
        violations.append("period_pair_fallback_tool_violation")
    return violations


def _validate_entity(canonical: dict[str, Any], tool_name: str, args: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    target = canonical["target_entity"]
    parent = canonical["parent_entity"]
    contract = TOOL_REGISTRY.get(tool_name)
    allowed_args = set(getattr(contract, "allowed_args", ()) if contract else ())
    expected_dimension = target.get("dimension")
    if expected_dimension in {"overall", "business_group", "product_line_5"} and (
        "entity_dimension" in allowed_args or "dimension" in allowed_args or "entity_dimension" in args or "dimension" in args
    ):
        actual_dimension = args.get("entity_dimension") or args.get("dimension")
        if actual_dimension != expected_dimension:
            violations.append("entity_dimension_mismatch")
    expected_value = target.get("value")
    if expected_value:
        if "entity_value" in allowed_args or "entity_value" in args:
            if args.get("entity_value") != expected_value:
                violations.append("entity_value_mismatch")
        else:
            violations.append("entity_value_missing")
    elif target.get("scope") == "all" and args.get("entity_value") not in {None, "", "all"}:
        violations.append("unexpected_entity_value_for_all_scope")

    expected_parent = parent.get("value")
    if expected_parent:
        parent_filter = args.get("parent_filter")
        if not isinstance(parent_filter, dict) or parent_filter.get("business_group") != expected_parent:
            violations.append("parent_filter_missing")
    return violations


def _validate_metric(canonical: dict[str, Any], tool_name: str, args: dict[str, Any]) -> list[str]:
    expected = canonical["metric"]
    if expected is None:
        return []
    contract = TOOL_REGISTRY.get(tool_name)
    allowed_args = set(getattr(contract, "allowed_args", ()) if contract else ())
    if "metric" not in allowed_args and "metric" not in args:
        return []
    actual = _canonical_metric(args.get("metric"))
    if actual != expected:
        return ["metric_mismatch"]
    return []


def _validate_chart(canonical: dict[str, Any], tool_name: str, args: dict[str, Any]) -> list[str]:
    expected = canonical.get("chart_type")
    if canonical["task_family"] != "chart_request" or not expected or tool_name not in {"get_chart_payload", "get_chart_table"}:
        return []
    actual = args.get("chart_type") or _chart_type_from_key(args.get("chart_key"))
    if actual != expected:
        return ["chart_type_mismatch"]
    return []


def _chart_type_from_key(chart_key: Any) -> str | None:
    key = str(chart_key or "")
    for chart_type in ["pie", "bar", "line", "area"]:
        if chart_type in key:
            return chart_type
    return None


def _canonical_metric(metric: Any) -> str | None:
    if metric in METRIC_ALIASES:
        return METRIC_ALIASES[metric]
    return str(metric) if metric is not None else None
