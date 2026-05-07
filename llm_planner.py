from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any

from logging_utils import get_logger


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
    question_type: str
    domains: list[str]
    tools: list[PlannedToolCall]
    answer_mode: str
    requires_limitations: bool
    unsupported_reason: str | None = None


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


ALLOWED_TOOL_REGISTRY: dict[str, AllowedToolSpec] = {
    "get_metric_table": AllowedToolSpec(
        description="Load deterministic metric rows.",
        allowed_args=("metric",),
        allowed_metrics=("revenue_trend", "inventory_amount_trend", "inventory_qty_trend", "platform_monthly", "anomalies"),
    ),
    "get_top_groups": AllowedToolSpec(
        description="Rank business groups.",
        allowed_args=("metric",),
        allowed_metrics=("revenue", "inventory"),
    ),
    "get_platform_ranking": AllowedToolSpec(
        description="Rank platforms.",
        allowed_args=("metric",),
        allowed_metrics=("revenue", "inventory_amount", "inventory_qty"),
    ),
    "get_platform_ratios": AllowedToolSpec(description="Revenue/inventory proxy ratios."),
    "get_anomalies": AllowedToolSpec(description="Deterministic anomalies."),
    "get_yoy_mom_breakdown": AllowedToolSpec(
        description="MoM and YoY change rows.",
        allowed_args=("metric", "dimension"),
        allowed_metrics=("revenue", "inventory_amount", "inventory_qty"),
        allowed_dimensions=("platform", "business_group", "overall"),
    ),
    "get_contribution_analysis": AllowedToolSpec(
        description="Current vs previous month contribution.",
        allowed_args=("metric", "dimension"),
        allowed_metrics=("revenue", "inventory_amount", "inventory_qty"),
        allowed_dimensions=("platform", "business_group"),
    ),
    "get_inventory_turnover_proxy": AllowedToolSpec(description="Inventory efficiency proxy."),
    "get_root_cause_candidates": AllowedToolSpec(
        description="Candidate observations without causal claim.",
        allowed_args=("metric",),
        allowed_metrics=("revenue",),
    ),
    "get_chart_payload": AllowedToolSpec(
        description="Chart payload.",
        allowed_args=("chart_key",),
    ),
    "get_chart_table": AllowedToolSpec(
        description="Chart preview table.",
        allowed_args=("chart_key",),
    ),
    "get_data_coverage": AllowedToolSpec(description="Available months and row counts."),
    "get_mapping_summary": AllowedToolSpec(description="Mapping summary."),
    "get_tool_capability_matrix": AllowedToolSpec(description="Tool capability matrix."),
}


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
    "ranking": ("get_top_groups", "get_platform_ranking", "get_data_coverage"),
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


def build_compact_tool_registry(question: str) -> list[str]:
    lines: list[str] = []
    for tool_name in select_planner_tool_subset(question):
        spec = ALLOWED_TOOL_REGISTRY[tool_name]
        args: list[str] = []
        if spec.allowed_metrics:
            args.append("metric:" + "|".join(spec.allowed_metrics))
        if spec.allowed_dimensions:
            args.append("dimension:" + "|".join(spec.allowed_dimensions))
        if spec.allowed_args and not args:
            args.extend(spec.allowed_args)
        arg_text = f"({', '.join(args)})" if args else "()"
        lines.append(f"{tool_name}{arg_text}")
    return lines


class LLMToolPlanner:
    def __init__(self, request_id: str, prompt_mode: str | None = None) -> None:
        self.request_id = request_id
        self.logger = get_logger("llm_planner", request_id, domain="planner")
        self.prompt_mode = (prompt_mode or os.getenv("LLM_PLANNER_PROMPT_MODE", PROMPT_MODE_SLIM)).strip().lower()
        if self.prompt_mode not in {PROMPT_MODE_SLIM, PROMPT_MODE_FULL}:
            self.prompt_mode = PROMPT_MODE_SLIM

    def plan_question(self, question: str, llm_client: Any) -> LLMPlanningResult:
        system_prompt, prompt_meta = self._build_system_prompt(question)
        user_prompt = self._build_user_prompt(question)
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
            plan = self._validate_plan(question, result.data)
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
        if tool_name in {"get_metric_table", "get_top_groups", "get_platform_ranking", "get_yoy_mom_breakdown", "get_contribution_analysis"} and metric:
            return f"{tool_name}({metric})"
        return tool_name

    @staticmethod
    def _suggest_object_dimension(plan: ToolPlan) -> str | None:
        for call in plan.tools:
            dimension = call.args.get("dimension")
            if dimension in {"platform", "business_group"}:
                return dimension
            if call.tool_name == "get_platform_ranking":
                return "platform"
            if call.tool_name == "get_top_groups":
                return "business_group"
        return None

    def _build_system_prompt(self, question: str) -> tuple[str, dict[str, Any]]:
        tool_lines = build_compact_tool_registry(question)
        registry_block = "\n".join(f"- {line}" for line in tool_lines)
        example = (
            '{"question_type":"trend","domains":["sales"],'
            '"tools":[{"tool_name":"get_yoy_mom_breakdown","args":{"metric":"revenue","dimension":"overall"},"reason":"MoM"}],'
            '"answer_mode":"trend","requires_limitations":false,"unsupported_reason":null}'
        )
        slim_prompt = (
            "Return JSON only. Never answer the user question.\n"
            "Rules: use only listed tools; max 5 tools; no forecast; no root cause claim; "
            "why/cause -> requires_limitations=true; forecast -> unsupported or safe coverage tools only.\n"
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
            "9. Output a single JSON object matching the ToolPlan schema.\n"
            f"Allowed tools registry: {json.dumps(full_registry, ensure_ascii=False)}"
        )
        prompt = slim_prompt if self.prompt_mode == PROMPT_MODE_SLIM else full_prompt
        prompt_meta = {
            "planner_prompt_mode": self.prompt_mode,
            "compact_registry_tool_count": len(tool_lines),
            "prompt_char_count": len(prompt),
        }
        return prompt, prompt_meta

    @staticmethod
    def _build_user_prompt(question: str) -> str:
        return (
            "JSON keys only: question_type, domains, tools, answer_mode, requires_limitations, unsupported_reason.\n"
            "Each tool: tool_name, args, reason.\n"
            f"Question: {question}"
        )

    def _validate_plan(self, question: str, payload: dict[str, Any]) -> ToolPlan:
        question_type = str(payload.get("question_type") or "").strip()
        answer_mode = str(payload.get("answer_mode") or "").strip()
        requires_limitations = bool(payload.get("requires_limitations"))
        unsupported_reason = payload.get("unsupported_reason")
        domains = payload.get("domains") or []
        tools = payload.get("tools") or []

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
        is_forecast = any(token in lowered or token in question for token in FORECAST_HINTS)
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
            if not isinstance(args, dict):
                raise ValueError(f"Tool args must be an object for tool {tool_name}")
            self._validate_tool_args(tool_name, args)
            planned_calls.append(PlannedToolCall(tool_name=tool_name, args=args, reason=reason))

        if is_forecast:
            disallowed = [call.tool_name for call in planned_calls if call.tool_name not in SAFE_FORECAST_TOOLS]
            if question_type != "unsupported" or disallowed:
                raise ValueError("Forecast questions must return unsupported or only use safe coverage tools.")

        return ToolPlan(
            question_type=question_type,
            domains=list(domains),
            tools=planned_calls,
            answer_mode=answer_mode,
            requires_limitations=requires_limitations,
            unsupported_reason=str(unsupported_reason) if unsupported_reason else None,
        )

    @staticmethod
    def _validate_tool_args(tool_name: str, args: dict[str, Any]) -> None:
        spec = ALLOWED_TOOL_REGISTRY[tool_name]
        unexpected = set(args.keys()) - set(spec.allowed_args)
        if unexpected:
            raise ValueError(f"Planner returned unsupported args for {tool_name}: {sorted(unexpected)}")

        metric = args.get("metric")
        if metric is not None and spec.allowed_metrics and metric not in spec.allowed_metrics:
            raise ValueError(f"Planner returned unsupported metric for {tool_name}: {metric}")

        dimension = args.get("dimension")
        if dimension is not None and spec.allowed_dimensions and dimension not in spec.allowed_dimensions:
            raise ValueError(f"Planner returned unsupported dimension for {tool_name}: {dimension}")

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
