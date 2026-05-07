from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from llm_planner import (
    ALLOWED_TOOL_REGISTRY,
    FORECAST_HINTS,
    WHY_HINTS,
    LLMPlanningResult,
    LLMToolPlanner,
)
from multi_agent import MultiAgentAssistant
from ollama_client import OllamaCallResult
from tests.support import build_stubbed_assistant, get_context


BASE_DIR = PROJECT_ROOT / "eval"
ROUTER_FILE = BASE_DIR / "questions_router.jsonl"
ANSWER_FILE = BASE_DIR / "questions_answer.jsonl"
RESULTS_FILE = BASE_DIR / "llm_planner_eval_results.csv"
REPORT_FILE = BASE_DIR / "llm_planner_eval_report.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for source, path in (("router", ROUTER_FILE), ("answer", ANSWER_FILE)):
        for case in load_jsonl(path):
            normalized = dict(case)
            normalized["case_source"] = source
            cases.append(normalized)
    return cases


class MockPlannerLLM:
    def __init__(self, payload: dict[str, Any] | None = None, *, ok: bool = True, error: str | None = None) -> None:
        self.payload = payload
        self.ok = ok
        self.error = error

    def generate_json(self, **kwargs: Any) -> OllamaCallResult:
        return OllamaCallResult(ok=self.ok, text=json.dumps(self.payload, ensure_ascii=False) if self.payload else "", data=self.payload, error=self.error)


def _base_tool_name(tool_name: str) -> str:
    if "(" in tool_name and tool_name.endswith(")"):
        return tool_name.split("(", 1)[0]
    return tool_name


def _materialized_comparable(tool_names: list[str]) -> list[str]:
    return [tool for tool in tool_names if _base_tool_name(tool) in ALLOWED_TOOL_REGISTRY]


def _contains_hint(question: str, hints: list[str]) -> bool:
    lowered = question.lower()
    return any(token in lowered or token in question for token in hints)


def _is_why_question(question: str) -> bool:
    return _contains_hint(question, WHY_HINTS)


def _is_forecast_question(question: str) -> bool:
    return _contains_hint(question, FORECAST_HINTS)


def _infer_dimension(question: str) -> str:
    lowered = question.lower()
    if any(token in question for token in ["平台", "平臺"]) or "platform" in lowered or "gg-" in lowered:
        return "platform"
    if any(token in question for token in ["新事業群", "事業群"]) or "business group" in lowered:
        return "business_group"
    return "overall"


def _infer_chart_key(question: str) -> str:
    lowered = question.lower()
    if "inventory" in lowered or "庫存" in question:
        return "current_month_platform_inventory_amount_bar"
    return "monthly_revenue_trend"


def _normalize_question_type(question_type: str, answer_mode: str) -> str:
    if question_type in {"ranking", "trend", "comparison", "risk", "diagnosis", "chart", "overview", "data_quality", "unsupported"}:
        return question_type
    if question_type in {"query", "metric_query"}:
        return "overview"
    if question_type == "decision":
        return "risk"
    if answer_mode in {"ranking", "trend", "comparison", "risk", "diagnosis", "chart", "overview", "data_quality", "unsupported"}:
        return answer_mode
    return "overview"


def _normalize_answer_mode(answer_mode: str) -> str:
    if answer_mode in {"trend", "diagnosis", "briefing", "chart", "ranking", "unsupported", "comparison", "risk", "overview", "data_quality"}:
        return answer_mode
    if answer_mode == "metric_query":
        return "overview"
    return "overview"


def _planned_tool_from_expected(tool_name: str, question: str) -> dict[str, Any] | None:
    if tool_name == "create_chart_image":
        return None

    if tool_name.startswith("get_metric_table("):
        metric = tool_name[len("get_metric_table("):-1]
        return {"tool_name": "get_metric_table", "args": {"metric": metric}, "reason": f"Need deterministic table for {metric}."}
    if tool_name.startswith("get_top_groups("):
        metric = tool_name[len("get_top_groups("):-1]
        return {"tool_name": "get_top_groups", "args": {"metric": metric}, "reason": f"Need ranking for {metric}."}
    if tool_name.startswith("get_platform_ranking("):
        metric = tool_name[len("get_platform_ranking("):-1]
        return {"tool_name": "get_platform_ranking", "args": {"metric": metric}, "reason": f"Need platform ranking for {metric}."}
    if tool_name.startswith("get_yoy_mom_breakdown("):
        metric = tool_name[len("get_yoy_mom_breakdown("):-1]
        return {
            "tool_name": "get_yoy_mom_breakdown",
            "args": {"metric": metric, "dimension": _infer_dimension(question)},
            "reason": f"Need MoM and YoY breakdown for {metric}.",
        }
    if tool_name.startswith("get_contribution_analysis("):
        metric = tool_name[len("get_contribution_analysis("):-1]
        dimension = "platform" if _infer_dimension(question) == "platform" else "business_group"
        return {
            "tool_name": "get_contribution_analysis",
            "args": {"metric": metric, "dimension": dimension},
            "reason": f"Need contribution view for {metric}.",
        }
    if tool_name == "get_root_cause_candidates":
        return {
            "tool_name": "get_root_cause_candidates",
            "args": {"metric": "revenue"},
            "reason": "Need deterministic candidate observations without claiming root cause.",
        }
    if tool_name in {"get_chart_payload", "get_chart_table"}:
        return {
            "tool_name": tool_name,
            "args": {"chart_key": _infer_chart_key(question)},
            "reason": "Need chart payload for rendering.",
        }
    return {"tool_name": tool_name, "args": {}, "reason": f"Need {tool_name} for deterministic evidence."}


def build_mock_planner_payload(
    case: dict[str, Any],
    deterministic_routing: dict[str, Any],
    deterministic_tools: list[str],
) -> dict[str, Any]:
    question = case["question"]
    raw_question_type = case.get("expected_question_type") or deterministic_routing.get("question_type") or "query"
    domains = case.get("expected_domains")
    if domains is None:
        expected_domain = case.get("expected_domain")
        domains = [expected_domain] if expected_domain else deterministic_routing.get("domains", [])
    answer_mode = _normalize_answer_mode(case.get("expected_answer_type") or deterministic_routing.get("question_type") or "overview")
    question_type = _normalize_question_type(raw_question_type, answer_mode)
    expected_tools = list(case.get("expected_tools") or deterministic_tools)

    if _is_forecast_question(question):
        return {
            "question_type": "unsupported",
            "domains": [],
            "tools": [
                {
                    "tool_name": "get_data_coverage",
                    "args": {},
                    "reason": "Can only inspect current loaded data coverage for forecast questions.",
                }
            ],
            "answer_mode": "unsupported",
            "requires_limitations": True,
            "unsupported_reason": "Forecasting is out of scope for this planner.",
        }

    planned_tools = [
        item
        for item in (_planned_tool_from_expected(tool_name, question) for tool_name in expected_tools)
        if item is not None
    ][:5]

    return {
        "question_type": question_type,
        "domains": domains or [],
        "tools": planned_tools,
        "answer_mode": answer_mode,
        "requires_limitations": _is_why_question(question) or question_type == "diagnosis",
        "unsupported_reason": "Data is unsupported for this question." if question_type == "unsupported" or case.get("expected_answer_type") == "unsupported" else None,
    }


def _tool_overlap_ratio(expected_tools: list[str], planned_tools: list[str]) -> float:
    if not expected_tools:
        return 1.0 if not planned_tools else 0.0
    overlap_count = len(set(expected_tools) & set(planned_tools))
    return overlap_count / len(set(expected_tools))


def _why_requires_limitation_pass(question: str, planning: LLMPlanningResult) -> bool | None:
    if not _is_why_question(question):
        return None
    if planning.ok and planning.plan is not None:
        return planning.plan.requires_limitations
    return planning.rejection_category == "missing_limitations"


def _forecast_safety_pass(question: str, planning: LLMPlanningResult) -> bool | None:
    if not _is_forecast_question(question):
        return None
    if planning.ok and planning.plan is not None:
        return planning.plan.question_type == "unsupported" and all(
            tool.tool_name in {"get_data_coverage", "get_mapping_summary", "get_tool_capability_matrix"}
            for tool in planning.plan.tools
        )
    return planning.rejection_category == "forecast_safety"


def evaluate_cases(
    cases: list[dict[str, Any]],
    *,
    mock_mode: bool = False,
    mock_overrides: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    assistant = build_stubbed_assistant("llm-planner-eval")
    planner = LLMToolPlanner("llm-planner-eval")
    rows: list[dict[str, Any]] = []

    real_planner_client = None
    if not mock_mode:
        real_assistant = MultiAgentAssistant(get_context(), "llm-planner-eval-real", use_llm_planner=True)
        real_planner_client = real_assistant.llm_client

    for case in cases:
        response = assistant.answer(case["question"])
        deterministic_routing = response["routing"]
        deterministic_tools = list(response["answer_contract"].get("tools_used", []))
        expected_tools = list(case.get("expected_tools") or deterministic_tools)
        comparable_expected_tools = _materialized_comparable(expected_tools)

        if mock_mode:
            payload = (mock_overrides or {}).get(case["id"])
            if payload is None:
                payload = build_mock_planner_payload(case, deterministic_routing, deterministic_tools)
            llm_client = MockPlannerLLM(payload=payload)
        else:
            llm_client = real_planner_client

        planning = planner.plan_question(case["question"], llm_client)
        planned_tools = planner.materialize_tools(planning.plan) if planning.ok and planning.plan is not None else []
        overlap_tools = sorted(set(comparable_expected_tools) & set(planned_tools))
        extra_tools = sorted(set(planned_tools) - set(comparable_expected_tools))
        missing_tools = sorted(set(comparable_expected_tools) - set(planned_tools))
        why_pass = _why_requires_limitation_pass(case["question"], planning)
        forecast_pass = _forecast_safety_pass(case["question"], planning)

        rows.append(
            {
                "case_source": case["case_source"],
                "id": case["id"],
                "question": case["question"],
                "deterministic_question_type": deterministic_routing.get("question_type"),
                "deterministic_domains": deterministic_routing.get("domains", []),
                "deterministic_tools": deterministic_tools,
                "expected_tools": expected_tools,
                "planner_success": planning.ok,
                "planning_failed": planning.planning_failed,
                "planned_question_type": planning.plan.question_type if planning.plan else None,
                "planned_domains": planning.plan.domains if planning.plan else [],
                "planned_tools": planned_tools,
                "tool_count": len(planned_tools),
                "comparable_expected_tools": comparable_expected_tools,
                "overlap_tools": overlap_tools,
                "extra_tools": extra_tools,
                "missing_tools": missing_tools,
                "overlap_ratio": _tool_overlap_ratio(comparable_expected_tools, planned_tools),
                "fallback_reason": planning.fallback_reason,
                "rejection_category": planning.rejection_category,
                "why_requires_limitation_pass": why_pass,
                "forecast_safety_pass": forecast_pass,
                "raw_planner_response": planning.trace.get("raw_planner_response") if planning.trace else planning.raw_response,
                "validated_plan": planning.trace.get("validated_plan") if planning.trace else None,
                "materialized_tools": planning.trace.get("materialized_tools") if planning.trace else planned_tools,
                "debug_trace": planning.trace or {},
            }
        )

    return rows


def summarize_metrics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    total = len(rows) or 1
    success_count = sum(1 for row in rows if row["planner_success"])
    fallback_count = sum(1 for row in rows if row["planning_failed"])
    invalid_count = sum(
        1
        for row in rows
        if row["planning_failed"] and row.get("rejection_category") not in {None, "llm_unavailable"}
    )
    avg_tool_count = (
        sum(int(row["tool_count"]) for row in rows if row["planner_success"]) / success_count
        if success_count
        else 0.0
    )
    overlap_values = [float(row["overlap_ratio"]) for row in rows]
    why_values = [row["why_requires_limitation_pass"] for row in rows if row["why_requires_limitation_pass"] is not None]
    forecast_values = [row["forecast_safety_pass"] for row in rows if row["forecast_safety_pass"] is not None]

    return {
        "planner_success_rate": success_count / total,
        "planner_fallback_rate": fallback_count / total,
        "invalid_plan_rate": invalid_count / total,
        "avg_tool_count": avg_tool_count,
        "tool_overlap_rate": (sum(overlap_values) / len(overlap_values)) if overlap_values else 0.0,
        "unknown_tool_rejection_count": sum(1 for row in rows if row.get("rejection_category") == "unknown_tool"),
        "invalid_args_rejection_count": sum(
            1 for row in rows if row.get("rejection_category") in {"invalid_args", "invalid_metric", "invalid_dimension"}
        ),
        "why_requires_limitation_pass_rate": (
            sum(1 for value in why_values if value) / len(why_values) if why_values else 0.0
        ),
        "forecast_safety_pass_rate": (
            sum(1 for value in forecast_values if value) / len(forecast_values) if forecast_values else 0.0
        ),
    }


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    fieldnames = [
        "case_source",
        "id",
        "question",
        "deterministic_question_type",
        "deterministic_domains",
        "deterministic_tools",
        "expected_tools",
        "planner_success",
        "planning_failed",
        "planned_question_type",
        "planned_domains",
        "planned_tools",
        "tool_count",
        "comparable_expected_tools",
        "overlap_tools",
        "extra_tools",
        "missing_tools",
        "overlap_ratio",
        "fallback_reason",
        "rejection_category",
        "why_requires_limitation_pass",
        "forecast_safety_pass",
        "raw_planner_response",
        "validated_plan",
        "materialized_tools",
        "debug_trace",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            for key, value in serialized.items():
                if isinstance(value, (list, dict)):
                    serialized[key] = json.dumps(value, ensure_ascii=False)
            writer.writerow(serialized)


def write_report(rows: list[dict[str, Any]], metrics: dict[str, float | int], output_path: Path, *, mock_mode: bool) -> None:
    failure_rows = [row for row in rows if row["planning_failed"]]
    fallback_counts: dict[str, int] = {}
    for row in failure_rows:
        reason = str(row.get("rejection_category") or row.get("fallback_reason") or "unknown")
        fallback_counts[reason] = fallback_counts.get(reason, 0) + 1

    report_lines = [
        "# LLM Planner Eval Report",
        "",
        f"- mode: {'mock' if mock_mode else 'live'}",
        f"- cases: {len(rows)}",
        "",
        "## Metrics",
        "",
        f"- planner_success_rate: {metrics['planner_success_rate']:.2%}",
        f"- planner_fallback_rate: {metrics['planner_fallback_rate']:.2%}",
        f"- invalid_plan_rate: {metrics['invalid_plan_rate']:.2%}",
        f"- avg_tool_count: {metrics['avg_tool_count']:.2f}",
        f"- tool_overlap_rate: {metrics['tool_overlap_rate']:.2%}",
        f"- unknown_tool_rejection_count: {metrics['unknown_tool_rejection_count']}",
        f"- invalid_args_rejection_count: {metrics['invalid_args_rejection_count']}",
        f"- why_requires_limitation_pass_rate: {metrics['why_requires_limitation_pass_rate']:.2%}",
        f"- forecast_safety_pass_rate: {metrics['forecast_safety_pass_rate']:.2%}",
        "",
        "## Fallback Summary",
        "",
    ]
    if fallback_counts:
        report_lines.extend([f"- {reason}: {count}" for reason, count in sorted(fallback_counts.items())])
    else:
        report_lines.append("- No planner fallbacks were recorded.")

    sample_failures = failure_rows[:5]
    report_lines.extend(["", "## Sample Cases", ""])
    if sample_failures:
        for row in sample_failures:
            report_lines.append(f"- `{row['id']}`: {row['question']}")
            report_lines.append(f"  fallback={row.get('fallback_reason')} rejection={row.get('rejection_category')}")
    else:
        report_lines.append("- All planner cases succeeded in this run.")

    report_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Phase 7A.5 evaluates planner quality only; final answers still come from deterministic answer_contract assembly.",
            "- Tool overlap compares planner output against deterministic expected tools filtered to the planner allowlist.",
            "- Why and forecast metrics count both compliant plans and safely rejected invalid plans as rule enforcement passes.",
        ]
    )
    output_path.write_text("\n".join(report_lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate experimental LLM planner quality.")
    parser.add_argument("--mock", action="store_true", help="Run evaluation with generated mock planner responses.")
    args = parser.parse_args(argv)

    rows = evaluate_cases(load_cases(), mock_mode=args.mock)
    metrics = summarize_metrics(rows)
    write_csv(rows, RESULTS_FILE)
    write_report(rows, metrics, REPORT_FILE, mock_mode=args.mock)
    print(f"Wrote {RESULTS_FILE}")
    print(f"Wrote {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
