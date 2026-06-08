from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any

from logging_utils import get_logger
from tool_registry import (
    build_allowed_tool_names_for_task_family,
    build_llm_allowed_tools_from_registry,
    validate_tool_args_against_registry,
)


ALLOWED_QUESTION_TYPES = {
    "ranking",
    "trend",
    "comparison",
    "risk",
    "diagnosis",
    "chart",
    "overview",
    "data_quality",
    "unsupported",
}

ALLOWED_ANSWER_MODES = {
    "trend",
    "diagnosis",
    "briefing",
    "chart",
    "ranking",
    "unsupported",
    "comparison",
    "risk",
    "overview",
    "data_quality",
}

ALLOWED_DOMAINS = {"sales", "inventory", "financial", "chart", "association"}

TASK_FAMILY_ALIASES = {
    "table_lookup": "entity_month_table_lookup",
    "period_pair_table_lookup": "entity_period_pair_table_lookup",
    "date_range_table_lookup": "entity_multi_month_table_lookup",
    "multi_month_table_lookup": "entity_multi_month_table_lookup",
    "value": "metric_lookup",
    "forecast": "forecast_unsupported",
}

QUESTION_TYPE_ALIASES = {
    "entity_month_table_lookup": "overview",
    "entity_period_pair_table_lookup": "overview",
    "entity_multi_month_table_lookup": "overview",
    "entity_period_pair_metric_lookup": "comparison",
    "table_lookup": "overview",
    "metric_lookup": "overview",
    "value": "overview",
    "cross_section_compare": "comparison",
    "period_pair_compare": "comparison",
    "entity_time_series": "trend",
    "overall_trend_analysis": "trend",
    "chart_request": "chart",
    "forecast_unsupported": "unsupported",
    "forecast": "unsupported",
}

ANSWER_MODE_ALIASES = {
    **QUESTION_TYPE_ALIASES,
    "overview": "overview",
    "comparison": "comparison",
    "trend": "trend",
    "chart": "chart",
    "unsupported": "unsupported",
    "ranking": "ranking",
    "risk": "risk",
    "diagnosis": "diagnosis",
    "data_quality": "data_quality",
    "briefing": "briefing",
}

ENTITY_DIMENSION_ALIASES = {
    "overall": "overall",
    "總體": "overall",
    "整體": "overall",
    "all": "overall",
    "business_group": "business_group",
    "business group": "business_group",
    "group": "business_group",
    "bu": "business_group",
    "BU": "business_group",
    "事業群": "business_group",
    "各事業群": "business_group",
    "新事業群": "business_group",
    "各新事業群": "business_group",
    "product_line_5": "product_line_5",
    "product_line": "product_line_5",
    "product line": "product_line_5",
    "產品線": "product_line_5",
    "各產品線": "product_line_5",
    "五大產品線": "product_line_5",
}

METRIC_ALIASES = {
    "revenue": "revenue_amount",
    "營收": "revenue_amount",
    "revenue_amount": "revenue_amount",
    "inventory": "inventory_amount",
    "庫存": "inventory_amount",
    "庫存金額": "inventory_amount",
    "inventory_amount": "inventory_amount",
    "qty": "inventory_qty",
    "庫存qty": "inventory_qty",
    "庫存數量": "inventory_qty",
    "inventory_qty": "inventory_qty",
    "revenue_inventory_amount_ratio": "revenue_inventory_amount_ratio",
    "health_score": "health_score",
    "risk_score": "risk_score",
}

WHY_HINTS = ["why", "cause", "root cause", "為什麼", "原因"]
FORECAST_HINTS = ["forecast", "predict", "prediction", "預測", "下個月", "next month"]
SAFE_FORECAST_TOOLS = {"get_data_coverage", "get_mapping_summary", "get_tool_capability_matrix"}
CHART_HINTS = ["chart", "plot", "graph", "畫", "圖", "趨勢圖", "長條圖"]
DATA_QUALITY_HINTS = ["data quality", "coverage", "mapping", "quality", "資料涵蓋", "資料品質", "mapping"]
RANKING_HINTS = ["highest", "top", "rank", "排名", "最高", "最多", "最低", "who is"]

PROMPT_MODE_SLIM = "slim"
PROMPT_MODE_FULL = "full"


@dataclass(frozen=True)
class PlannedToolCall:
    tool_name: str
    args: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass(frozen=True)
class ToolPlan:
    task_family: str
    question_type: str
    domains: list[str]
    tools: list[PlannedToolCall]
    answer_mode: str
    requires_limitations: bool
    unsupported_reason: str | None = None
    planner_intent: str = ""
    needs_table: bool = False
    needs_chart: bool = False
    fallback_required: bool = False


@dataclass(frozen=True)
class LLMPlanningResult:
    ok: bool
    planning_failed: bool
    plan: ToolPlan | None = None
    error: str | None = None
    fallback_reason: str | None = None
    raw_response: dict[str, Any] | None = None
    rejection_category: str | None = None
    trace: dict[str, Any] | None = None


@dataclass(frozen=True)
class AllowedToolSpec:
    description: str
    allowed_args: tuple[str, ...] = ()
    allowed_metrics: tuple[str, ...] = ()
    allowed_dimensions: tuple[str, ...] = ()


def _allowed_tool_registry_from_tool_registry() -> dict[str, AllowedToolSpec]:
    contracts = build_llm_allowed_tools_from_registry()
    return {
        name: AllowedToolSpec(
            description=contract.description,
            allowed_args=contract.allowed_args,
            allowed_metrics=contract.supported_metrics,
            allowed_dimensions=contract.supported_entity_dimensions,
        )
        for name, contract in contracts.items()
    }


ALLOWED_TOOL_REGISTRY: dict[str, AllowedToolSpec] = _allowed_tool_registry_from_tool_registry()


TOOL_SUBSET_PRESETS: dict[str, tuple[str, ...]] = {
    "chart": ("get_chart_payload", "get_chart_table", "get_data_coverage"),
    "diagnosis": (
        "get_yoy_mom_breakdown",
        "get_contribution_analysis",
        "get_inventory_turnover_proxy",
        "get_root_cause_candidates",
        "get_anomalies",
        "get_platform_ratios",
    ),
    "ranking": ("get_entity_metric_ranking", "get_entity_performance_snapshot", "get_data_coverage"),
    "data_quality": ("get_data_coverage", "get_mapping_summary", "get_tool_capability_matrix"),
    "overview": (
        "get_yoy_mom_breakdown",
        "get_contribution_analysis",
        "get_inventory_turnover_proxy",
        "get_root_cause_candidates",
        "get_data_coverage",
    ),
    "forecast": tuple(SAFE_FORECAST_TOOLS),
}


def _contains_hint(question: str, hints: list[str]) -> bool:
    lowered = question.lower()
    return any(token in lowered or token in question for token in hints)


def infer_prompt_profile(question: str) -> str:
    if _contains_hint(question, FORECAST_HINTS):
        return "forecast"
    if _contains_hint(question, DATA_QUALITY_HINTS):
        return "data_quality"
    if _contains_hint(question, CHART_HINTS):
        return "chart"
    if _contains_hint(question, WHY_HINTS):
        return "diagnosis"
    if _contains_hint(question, RANKING_HINTS):
        return "ranking"
    return "overview"


def select_planner_tool_subset(question: str) -> list[str]:
    profile = infer_prompt_profile(question)
    return list(TOOL_SUBSET_PRESETS[profile])


def build_compact_tool_registry(question: str, allowed_tool_names: list[str] | None = None) -> list[str]:
    lines: list[str] = []
    tool_names = allowed_tool_names or select_planner_tool_subset(question)
    for tool_name in tool_names:
        spec = ALLOWED_TOOL_REGISTRY[tool_name]
        args: list[str] = []
        if spec.allowed_metrics:
            args.append("metric:" + "|".join(spec.allowed_metrics))
        if spec.allowed_dimensions and ("entity_dimension" in spec.allowed_args or "dimension" in spec.allowed_args):
            dimension_arg = "entity_dimension" if "entity_dimension" in spec.allowed_args else "dimension"
            args.append(f"{dimension_arg}:" + "|".join(spec.allowed_dimensions))
        if spec.allowed_args and not args:
            args.extend(spec.allowed_args)
        arg_text = f"({', '.join(args)})" if args else "()"
        lines.append(f"{tool_name}{arg_text}")
    return lines


def normalize_task_family(value: Any, canonical_task_family: str | None = None) -> str:
    raw = str(value or canonical_task_family or "").strip()
    if not raw:
        return str(canonical_task_family or "")
    return TASK_FAMILY_ALIASES.get(raw, raw)


def normalize_question_type(value: Any, task_family: str) -> str:
    raw = str(value or "").strip()
    if raw in ALLOWED_QUESTION_TYPES:
        return raw
    if raw in QUESTION_TYPE_ALIASES:
        return QUESTION_TYPE_ALIASES[raw]
    return _question_type_for_task_family(task_family)


def normalize_answer_mode(value: Any, task_family: str) -> str:
    raw = str(value or "").strip()
    if raw in ALLOWED_ANSWER_MODES:
        return raw
    if raw in ANSWER_MODE_ALIASES:
        return ANSWER_MODE_ALIASES[raw]
    return _answer_mode_for_task_family(task_family)


def normalize_entity_dimension(value: Any) -> Any:
    if value is None:
        return None
    raw = str(value).strip()
    return ENTITY_DIMENSION_ALIASES.get(raw, ENTITY_DIMENSION_ALIASES.get(raw.lower(), value))


def normalize_metric(value: Any) -> Any:
    if value is None:
        return None
    raw = str(value).strip()
    return METRIC_ALIASES.get(raw, METRIC_ALIASES.get(raw.lower(), value))


def normalize_tool_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(args)
    spec = ALLOWED_TOOL_REGISTRY.get(tool_name)
    allowed_args = set(spec.allowed_args if spec else ())
    if "dimension" in normalized:
        normalized["dimension"] = normalize_entity_dimension(normalized.get("dimension"))
        if "entity_dimension" in allowed_args and "entity_dimension" not in normalized:
            normalized["entity_dimension"] = normalized["dimension"]
        if "dimension" not in allowed_args and "entity_dimension" in normalized:
            normalized.pop("dimension", None)
    if "entity_dimension" in normalized:
        normalized["entity_dimension"] = normalize_entity_dimension(normalized.get("entity_dimension"))
    if "metric" in normalized:
        metric = normalize_metric(normalized.get("metric"))
        if tool_name in {"get_entity_period_pair_comparison", "get_period_pair_metric_comparison"} and metric == "revenue_amount":
            metric = "revenue"
        if spec and spec.allowed_metrics and metric not in spec.allowed_metrics and normalized.get("metric") in spec.allowed_metrics:
            metric = normalized.get("metric")
        normalized["metric"] = metric
    return normalized


class LLMToolPlanner:
    def __init__(self, request_id: str, prompt_mode: str | None = None) -> None:
        self.request_id = request_id
        self.logger = get_logger("llm_planner", request_id, domain="planner")
        self.prompt_mode = (prompt_mode or os.getenv("LLM_PLANNER_PROMPT_MODE", PROMPT_MODE_SLIM)).strip().lower()
        if self.prompt_mode not in {PROMPT_MODE_SLIM, PROMPT_MODE_FULL}:
            self.prompt_mode = PROMPT_MODE_SLIM

    def plan_question(
        self,
        question: str,
        llm_client: Any,
        *,
        allowed_tool_names: list[str] | None = None,
        canonical_task_family: str | None = None,
        canonical_task_profile: Any | None = None,
        deterministic_answer_plan: Any | None = None,
    ) -> LLMPlanningResult:
        canonical_task_family = canonical_task_family or str(getattr(canonical_task_profile, "task_family", "") or "") or None
        if canonical_task_family and allowed_tool_names is None:
            allowed_tool_names = build_allowed_tool_names_for_task_family(canonical_task_family)
        system_prompt, prompt_meta = self._build_system_prompt(
            question,
            allowed_tool_names,
            canonical_task_family,
            canonical_task_profile=canonical_task_profile,
            deterministic_answer_plan=deterministic_answer_plan,
        )
        user_prompt = self._build_user_prompt(
            question,
            canonical_task_family,
            canonical_task_profile=canonical_task_profile,
            deterministic_answer_plan=deterministic_answer_plan,
            allowed_tool_names=allowed_tool_names,
        )
        result = llm_client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.0)
        if not result.ok or not result.data:
            error = result.error or "planner_call_failed"
            self.logger.info("planner.failed reason=%s", error)
            trace = {
                "question": question,
                "raw_planner_response": result.data or (result.text or None),
                "validated_plan": None,
                "rejected_reason": error,
                "materialized_tools": [],
                "fallback_reason": "llm_planner_unavailable",
                **prompt_meta,
            }
            return LLMPlanningResult(
                ok=False,
                planning_failed=True,
                error=error,
                fallback_reason="llm_planner_unavailable",
                rejection_category=self._categorize_error(error),
                trace=trace,
            )

        try:
            plan = self._validate_plan(
                question,
                result.data,
                allowed_tool_names=allowed_tool_names,
                canonical_task_family=canonical_task_family,
                canonical_task_profile=canonical_task_profile,
                deterministic_answer_plan=deterministic_answer_plan,
            )
        except ValueError as exc:
            error = str(exc)
            self.logger.info("planner.failed reason=%s", error)
            trace = {
                "question": question,
                "raw_planner_response": result.data,
                "validated_plan": None,
                "rejected_reason": error,
                "materialized_tools": [],
                "fallback_reason": "llm_planner_invalid_output",
                **prompt_meta,
            }
            return LLMPlanningResult(
                ok=False,
                planning_failed=True,
                error=error,
                fallback_reason="llm_planner_invalid_output",
                raw_response=result.data,
                rejection_category=self._categorize_error(error),
                trace=trace,
            )

        materialized_tools = self.materialize_tools(plan)
        trace = {
            "question": question,
            "raw_planner_response": result.data,
            "validated_plan": asdict(plan),
            "rejected_reason": None,
            "materialized_tools": materialized_tools,
            "fallback_reason": None,
            "planned_tool_count": len(plan.tools),
            **prompt_meta,
        }
        self.logger.info(
            "planner.done question_type=%s domains=%s tools=%s prompt_mode=%s prompt_chars=%s",
            plan.question_type,
            plan.domains,
            [tool.tool_name for tool in plan.tools],
            prompt_meta["planner_prompt_mode"],
            prompt_meta["prompt_char_count"],
        )
        return LLMPlanningResult(
            ok=True,
            planning_failed=False,
            plan=plan,
            raw_response=result.data,
            trace=trace,
        )

    def materialize_tools(self, plan: ToolPlan) -> list[str]:
        return [self._materialize_tool_name(call) for call in plan.tools]

    @staticmethod
    def _materialize_tool_name(call: PlannedToolCall) -> str:
        tool_name = call.tool_name
        metric = call.args.get("metric")
        if tool_name in {
            "get_metric_table",
            "get_top_groups",
            "get_platform_ranking",
            "get_yoy_mom_breakdown",
            "get_contribution_analysis",
            "get_entity_period_pair_comparison",
            "get_period_pair_metric_comparison",
        } and metric:
            return f"{tool_name}({metric})"
        return tool_name

    @staticmethod
    def _suggest_object_dimension(plan: ToolPlan) -> str | None:
        for call in plan.tools:
            dimension = call.args.get("dimension")
            if dimension in {"platform", "business_group"}:
                return dimension
            if dimension == "product_line_5":
                return dimension
            if call.tool_name in {"get_entity_metric_ranking", "get_entity_performance_snapshot"}:
                entity_dimension = call.args.get("entity_dimension")
                if entity_dimension in {"business_group", "product_line_5"}:
                    return entity_dimension
            if call.tool_name == "get_platform_ranking":
                return "platform"
            if call.tool_name == "get_top_groups":
                return "business_group"
        return None

    def _build_system_prompt(
        self,
        question: str,
        allowed_tool_names: list[str] | None = None,
        canonical_task_family: str | None = None,
        *,
        canonical_task_profile: Any | None = None,
        deterministic_answer_plan: Any | None = None,
    ) -> tuple[str, dict[str, Any]]:
        tool_lines = build_compact_tool_registry(question, allowed_tool_names)
        registry_block = "\n".join(f"- {line}" for line in tool_lines)
        if canonical_task_profile is not None:
            allowed_contracts = build_llm_allowed_tools_from_registry(allowed_tool_names or [])
            allowed_tools_payload = {
                name: {
                    "description": contract.description,
                    "required_args": list(contract.required_args),
                    "optional_args": list(contract.optional_args),
                    "supported_entity_dimensions": list(contract.supported_entity_dimensions),
                    "supported_metrics": list(contract.supported_metrics),
                    "supports_month": contract.supports_month,
                    "supports_period_pair": contract.supports_period_pair,
                    "supports_parent_filter": contract.supports_parent_filter,
                    "output_evidence_type": contract.output_evidence_type,
                    "is_legacy": contract.is_legacy,
                    "replacement_tool": contract.replacement_tool,
                }
                for name, contract in allowed_contracts.items()
            }
            canonical_payload = _to_plain_dict(canonical_task_profile)
            answer_plan_payload = _to_plain_dict(deterministic_answer_plan) if deterministic_answer_plan is not None else {}
            output_schema = {
                "planner_intent": "short reason for the candidate plan",
                "tool_calls": [{"tool_name": "...", "args": {}, "reason": "..."}],
                "answer_mode": "comparison|trend|chart|ranking|overview|risk|diagnosis|unsupported|data_quality|briefing",
                "needs_table": False,
                "needs_chart": False,
                "fallback_required": False,
            }
            prompt = (
                "Return JSON only. You are a candidate tool planner, not the source of truth.\n"
                "Use the deterministic CanonicalTaskProfile exactly as given.\n"
                "Rules:\n"
                "1. You must return canonical task_family exactly. Do not use table_lookup/value/forecast aliases unless unavoidable.\n"
                "2. You must not change month, period_a, period_b, or recent_n.\n"
                "3. You must not change entity_dimension, entity_value, scope, or parent_filter.\n"
                "4. entity_dimension must be one of: overall, business_group, product_line_5.\n"
                "5. metric must be one of: revenue_amount, inventory_amount, inventory_qty, revenue_inventory_amount_ratio, health_score, risk_score.\n"
                "6. You must not change metric or chart_type.\n"
                "7. You may only select tools from allowed_tools.\n"
                "8. Aliases table_lookup/value/forecast, group/BU/新事業群, and product line/五大產品線 will be normalized, but canonical values are preferred.\n"
                "9. forecast_unsupported must not use data tools; return tool_calls=[] and fallback_required=true if needed.\n"
                "10. If no valid tool is suitable, return tool_calls=[] and fallback_required=true.\n"
                "11. Do not forecast and do not claim root cause.\n"
                "12. Output must match this schema: "
                f"{json.dumps(output_schema, ensure_ascii=False)}\n"
                "canonical_task_profile:\n"
                f"{json.dumps(canonical_payload, ensure_ascii=False, sort_keys=True)}\n"
                "allowed_tools:\n"
                f"{json.dumps(allowed_tools_payload, ensure_ascii=False, sort_keys=True)}\n"
                "deterministic_answer_plan:\n"
                f"{json.dumps(answer_plan_payload, ensure_ascii=False, sort_keys=True)}"
            )
            prompt_meta = {
                "planner_prompt_mode": self.prompt_mode,
                "compact_registry_tool_count": len(tool_lines),
                "prompt_char_count": len(prompt),
                "canonical_task_family": canonical_task_family,
            }
            return prompt, prompt_meta

        example = (
            '{"task_family":"overall_trend_analysis","question_type":"trend","domains":["sales"],'
            '"tools":[{"tool_name":"get_yoy_mom_breakdown","args":{"metric":"revenue","dimension":"overall"},"reason":"MoM"}],'
            '"answer_mode":"trend","requires_limitations":false,"unsupported_reason":null}'
        )
        slim_prompt = (
            "Return JSON only. Never answer the user question.\n"
            "Rules: use only listed tools; max 5 tools; no forecast; no root cause claim; "
            "why/cause -> requires_limitations=true; forecast -> unsupported or safe coverage tools only; "
            "preserve explicit months exactly; preserve named business_group or product_line_5 exactly; "
            "normalize BU/事業群/新事業群 to business_group and 產品線/五大產品線 to product_line_5; "
            "preserve chart_type exactly, including pie for 圓餅圖; "
            "do not invent dates, entities, or metrics; do not convert metric_lookup into query; "
            "do not convert period_pair_compare into trend; do not convert entity_time_series into generic trend.\n"
            "Tools:\n"
            f"{registry_block}\n"
            f"Example:\n{example}"
        )
        full_registry = {
            name: {
                "description": spec.description,
                "allowed_args": list(spec.allowed_args),
                "allowed_metrics": list(spec.allowed_metrics),
                "allowed_dimensions": list(spec.allowed_dimensions),
            }
            for name, spec in ALLOWED_TOOL_REGISTRY.items()
        }
        full_prompt = (
            "You are an experimental planning module for a deterministic business analysis assistant. "
            "You must only return JSON and never answer the user's question directly.\n"
            "Rules:\n"
            "1. Only choose tools from the provided registry.\n"
            "2. Do not invent tools.\n"
            "3. Select at most 5 tools.\n"
            "4. Do not forecast.\n"
            "5. Do not claim root cause.\n"
            "6. If the question is about why/cause, requires_limitations must be true.\n"
            "7. If the question is forecast-oriented, return unsupported or only use data coverage style tools.\n"
            "8. If the question asks for a chart, use chart tools.\n"
            "9. Preserve explicit months, metrics, chart type, and entity names exactly as asked.\n"
            "10. Normalize BU/事業群/新事業群 to business_group and 產品線/五大產品線 to product_line_5.\n"
            "11. Never downgrade metric_lookup, entity_month_table_lookup, or chart_request to generic query.\n"
            "12. For single-month all-entity table questions, preserve the explicit month, entity_dimension, scope=all, and metric; use get_entity_month_table.\n"
            "13. Output a single JSON object matching the ToolPlan schema.\n"
            f"Allowed tools registry: {json.dumps(full_registry, ensure_ascii=False)}"
        )
        if canonical_task_family:
            slim_prompt += f"\nCanonical task family to preserve: {canonical_task_family}"
            full_prompt += f"\nCanonical task family to preserve: {canonical_task_family}"
        prompt = slim_prompt if self.prompt_mode == PROMPT_MODE_SLIM else full_prompt
        prompt_meta = {
            "planner_prompt_mode": self.prompt_mode,
            "compact_registry_tool_count": len(tool_lines),
            "prompt_char_count": len(prompt),
        }
        return prompt, prompt_meta

    @staticmethod
    def _build_user_prompt(
        question: str,
        canonical_task_family: str | None = None,
        *,
        canonical_task_profile: Any | None = None,
        deterministic_answer_plan: Any | None = None,
        allowed_tool_names: list[str] | None = None,
    ) -> str:
        if canonical_task_profile is not None:
            payload = {
                "original_question": question,
                "canonical_task_profile": _to_plain_dict(canonical_task_profile),
                "allowed_tools": allowed_tool_names or [],
                "constraints": (_to_plain_dict(canonical_task_profile).get("constraints") or {}),
                "deterministic_answer_plan": _to_plain_dict(deterministic_answer_plan) if deterministic_answer_plan is not None else {},
            }
            return "Plan candidate tools from this canonical input only:\n" + json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return (
            "JSON keys only: task_family, question_type, domains, tools, answer_mode, requires_limitations, unsupported_reason.\n"
            "Each tool: tool_name, args, reason.\n"
            f"Canonical task family: {canonical_task_family or 'unknown'}\n"
            f"Question: {question}"
        )

    def _validate_plan(
        self,
        question: str,
        payload: dict[str, Any],
        *,
        allowed_tool_names: list[str] | None = None,
        canonical_task_family: str | None = None,
        canonical_task_profile: Any | None = None,
        deterministic_answer_plan: Any | None = None,
    ) -> ToolPlan:
        task_family = normalize_task_family(payload.get("task_family"), canonical_task_family)
        question_type = normalize_question_type(payload.get("question_type"), task_family)
        answer_mode = normalize_answer_mode(payload.get("answer_mode"), task_family)
        requires_limitations = bool(payload.get("requires_limitations", True))
        unsupported_reason = payload.get("unsupported_reason")
        domains = payload.get("domains")
        if domains is None:
            domains = _domains_for_task_family(task_family)
        tools = payload.get("tool_calls") if "tool_calls" in payload else payload.get("tools")
        tools = tools or []
        fallback_required = bool(payload.get("fallback_required", False))
        planner_intent = str(payload.get("planner_intent") or "").strip()
        needs_table = bool(payload.get("needs_table", getattr(deterministic_answer_plan, "requires_table", False)))
        needs_chart = bool(payload.get("needs_chart", task_family == "chart_request"))

        if canonical_task_family and task_family and task_family != canonical_task_family:
            raise ValueError(f"Planner changed task_family: {task_family} != {canonical_task_family}")
        if question_type not in ALLOWED_QUESTION_TYPES:
            raise ValueError(f"Unsupported question_type: {question_type}")
        if answer_mode not in ALLOWED_ANSWER_MODES:
            raise ValueError(f"Unsupported answer_mode: {answer_mode}")
        if not isinstance(domains, list) or any(domain not in ALLOWED_DOMAINS for domain in domains):
            raise ValueError("Planner returned unsupported domains.")
        if not isinstance(tools, list) or len(tools) > 5:
            raise ValueError("Planner returned invalid tools list.")

        lowered = question.lower()
        is_why = any(token in lowered or token in question for token in WHY_HINTS)
        is_forecast = any(token in lowered or token in question for token in FORECAST_HINTS) or task_family == "forecast_unsupported"
        if is_why and not requires_limitations:
            raise ValueError("Why/cause questions must set requires_limitations=true.")

        planned_calls: list[PlannedToolCall] = []
        for tool_payload in tools:
            if not isinstance(tool_payload, dict):
                raise ValueError("Each planned tool must be an object.")
            tool_name = str(tool_payload.get("tool_name") or "").strip()
            args = tool_payload.get("args") or {}
            reason = str(tool_payload.get("reason") or "").strip()
            if tool_name not in ALLOWED_TOOL_REGISTRY:
                raise ValueError(f"Unknown tool requested by planner: {tool_name}")
            if allowed_tool_names is not None and tool_name not in set(allowed_tool_names):
                raise ValueError(f"Planner returned tool outside allowed baseline: {tool_name}")
            if not isinstance(args, dict):
                raise ValueError(f"Tool args must be an object for tool {tool_name}")
            args = normalize_tool_args(tool_name, args)
            self._validate_tool_args(tool_name, args)
            planned_calls.append(PlannedToolCall(tool_name=tool_name, args=args, reason=reason))

        if is_forecast and planned_calls:
            raise ValueError("Forecast questions must return unsupported with no tools.")

        return ToolPlan(
            task_family=task_family,
            question_type=question_type,
            domains=list(domains),
            tools=planned_calls,
            answer_mode=answer_mode,
            requires_limitations=requires_limitations,
            unsupported_reason=str(unsupported_reason) if unsupported_reason else None,
            planner_intent=planner_intent,
            needs_table=needs_table,
            needs_chart=needs_chart,
            fallback_required=fallback_required,
        )

    @staticmethod
    def _validate_tool_args(tool_name: str, args: dict[str, Any]) -> None:
        ok, error = validate_tool_args_against_registry(tool_name, args)
        if not ok:
            raise ValueError(error or f"Planner returned invalid args for {tool_name}")

    @staticmethod
    def _categorize_error(error: str | None) -> str | None:
        if not error:
            return None
        lowered = error.lower()
        if "timed out" in lowered or "read timeout" in lowered:
            return "llm_unavailable"
        if "unknown tool" in lowered:
            return "unknown_tool"
        if "unsupported args" in lowered:
            return "invalid_args"
        if "unsupported metric" in lowered:
            return "invalid_metric"
        if "unsupported dimension" in lowered:
            return "invalid_dimension"
        if "failed to parse json" in lowered or "invalid json" in lowered:
            return "invalid_json"
        if "requires_limitations=true" in lowered:
            return "missing_limitations"
        if "forecast questions must" in lowered:
            return "forecast_safety"
        if "planner_call_failed" in lowered or "unavailable" in lowered or "stub" in lowered:
            return "llm_unavailable"
        return "invalid_plan"


def allowed_tools_registry_payload() -> dict[str, Any]:
    return {name: asdict(spec) for name, spec in ALLOWED_TOOL_REGISTRY.items()}


def validate_llm_plan_against_canonical_task_profile(
    plan: ToolPlan,
    canonical_task_profile: Any,
    canonical_answer_plan: Any,
) -> tuple[bool, str | None]:
    from plan_validator import PlanValidator

    result = PlanValidator().validate(canonical_task_profile, plan, deterministic_answer_plan=canonical_answer_plan)
    return bool(result["valid"]), None if result["valid"] else str(result["reason"])


def _to_plain_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    try:
        return asdict(value)
    except TypeError:
        if isinstance(value, dict):
            return dict(value)
        return {}


def _question_type_for_task_family(task_family: str) -> str:
    mapping = {
        "entity_ranking": "ranking",
        "latest_month_entity_summary": "overview",
        "cross_section_compare": "comparison",
        "period_pair_compare": "comparison",
        "entity_period_pair_table_lookup": "overview",
        "entity_multi_month_table_lookup": "overview",
        "entity_period_pair_metric_lookup": "comparison",
        "entity_time_series": "trend",
        "overall_trend_analysis": "trend",
        "entity_trend_comparison": "trend",
        "performance_assessment": "overview",
        "risk_scan": "risk",
        "metric_relationship_analysis": "risk",
        "contribution_analysis": "comparison",
        "parent_child_drilldown": "comparison",
        "data_quality": "data_quality",
        "chart_request": "chart",
        "forecast_unsupported": "unsupported",
        "metric_lookup": "overview",
        "entity_month_table_lookup": "overview",
    }
    return mapping.get(task_family, "overview")


def _answer_mode_for_task_family(task_family: str) -> str:
    mapping = {
        "entity_ranking": "ranking",
        "latest_month_entity_summary": "briefing",
        "cross_section_compare": "comparison",
        "period_pair_compare": "comparison",
        "entity_period_pair_table_lookup": "overview",
        "entity_multi_month_table_lookup": "overview",
        "entity_period_pair_metric_lookup": "comparison",
        "entity_time_series": "trend",
        "overall_trend_analysis": "trend",
        "entity_trend_comparison": "trend",
        "performance_assessment": "briefing",
        "risk_scan": "risk",
        "metric_relationship_analysis": "risk",
        "contribution_analysis": "comparison",
        "parent_child_drilldown": "comparison",
        "data_quality": "data_quality",
        "chart_request": "chart",
        "forecast_unsupported": "unsupported",
        "metric_lookup": "overview",
        "entity_month_table_lookup": "overview",
    }
    return mapping.get(task_family, "overview")


def _domains_for_task_family(task_family: str) -> list[str]:
    if task_family == "chart_request":
        return ["chart"]
    if task_family == "forecast_unsupported":
        return []
    if task_family == "data_quality":
        return []
    return ["financial"]
