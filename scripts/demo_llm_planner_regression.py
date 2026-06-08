from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from answer_plan import build_answer_plan
from business_question_classifier import classify_business_question
from canonical_task import CanonicalTaskProfile
from llm_planner import LLMToolPlanner
from ollama_client import OllamaCallResult
from plan_validator import PlanValidator
from task_profile import build_task_profile
from tool_registry import TOOL_REGISTRY, build_allowed_tool_names_for_task_family
from tests.support import build_stubbed_assistant


CASE_FILE = PROJECT_ROOT / "eval" / "questions_answer.jsonl"
REPORT_DIR = PROJECT_ROOT / "eval"
CSV_FILE = REPORT_DIR / "demo_llm_planner_regression_results.csv"
MD_FILE = REPORT_DIR / "demo_llm_planner_regression.md"


def load_cases() -> list[dict[str, Any]]:
    return [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


class ScriptedPlannerLLM:
    def generate(self, **kwargs):
        return self.generate_json(**kwargs)

    def generate_json(self, **kwargs):
        question = _extract_question(str(kwargs.get("user_prompt") or ""))
        data = _build_planner_payload(question)
        return OllamaCallResult(ok=True, text="", data=data, error=None)


def _extract_question(user_prompt: str) -> str:
    match = re.search(r"Question:\s*(.+)$", user_prompt, re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(r"\"original_question\"\s*:\s*\"([^\"]+)\"", user_prompt)
    return match.group(1).strip() if match else ""


def _build_planner_payload(question: str) -> dict[str, Any]:
    if question == "列出2025年3月各產品線庫存資料":
        return {
            "task_family": "table_lookup",
            "question_type": "table_lookup",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_entity_month_table",
                    "args": {"entity_dimension": "product line", "metric": "inventory_amount", "month": "2025-03"},
                    "reason": "legacy alias should normalize",
                }
            ],
            "answer_mode": "table_lookup",
            "requires_limitations": True,
            "unsupported_reason": None,
        }
    if question == "列出通路方案 2026/2 最新營收":
        return {
            "task_family": "value",
            "question_type": "value",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_entity_metric_value",
                    "args": {"entity_dimension": "BU", "entity_value": "通路方案", "metric": "revenue", "month": "2026-02"},
                    "reason": "legacy value alias should normalize",
                }
            ],
            "answer_mode": "value",
            "requires_limitations": True,
            "unsupported_reason": None,
        }
    if question == "下個月營收會不會改善？":
        return {
            "task_family": "forecast",
            "question_type": "forecast",
            "domains": [],
            "tools": [],
            "answer_mode": "forecast",
            "requires_limitations": True,
            "unsupported_reason": "forecast unsupported",
        }
    if question == "比較 2025 年 12 月與 2026 年 1 月營收差別":
        return {
            "task_family": "period_pair_compare",
            "question_type": "comparison",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_entity_period_pair_comparison",
                    "args": {"entity_dimension": "business_group", "metric": "revenue", "period_a": "2025-01", "period_b": "2026-01"},
                    "reason": "intentionally bad date pair",
                }
            ],
            "answer_mode": "comparison",
            "requires_limitations": True,
            "unsupported_reason": None,
        }
    if question == "比較 3通路方案 各月營收":
        return {
            "task_family": "overall_trend_analysis",
            "question_type": "trend",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_overall_time_series",
                    "args": {"metric": "revenue_amount"},
                    "reason": "intentionally bad task downgrade",
                }
            ],
            "answer_mode": "trend",
            "requires_limitations": True,
            "unsupported_reason": None,
        }
    if question == "各新事業群近 6 個月營收趨勢":
        return {
            "task_family": "overall_trend_analysis",
            "question_type": "trend",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_overall_time_series",
                    "args": {"metric": "revenue_amount"},
                    "reason": "intentionally bad trend downgrade",
                }
            ],
            "answer_mode": "trend",
            "requires_limitations": True,
            "unsupported_reason": None,
        }
    if question == "2026 年 1 月比 2025 年 1 月營收差多少？":
        return {
            "task_family": "period_pair_compare",
            "question_type": "comparison",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_entity_period_pair_comparison",
                    "args": {"entity_dimension": "business_group", "metric": "revenue", "period_a": "2026-01", "period_b": "2026-02"},
                    "reason": "intentionally wrong month pair",
                }
            ],
            "answer_mode": "comparison",
            "requires_limitations": True,
            "unsupported_reason": None,
        }
    if question == "2026-01 比 2025-12 成長主要來自哪個新事業群？":
        return {
            "task_family": "overall_trend_analysis",
            "question_type": "trend",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_overall_time_series",
                    "args": {"metric": "revenue_amount"},
                    "reason": "intentionally bad contribution downgrade",
                }
            ],
            "answer_mode": "trend",
            "requires_limitations": True,
            "unsupported_reason": None,
        }
    if question == "下個月營收會不會改善？":
        return {
            "task_family": "forecast_unsupported",
            "question_type": "comparison",
            "domains": ["financial"],
            "tools": [
                {
                    "tool_name": "get_entity_time_series",
                    "args": {"entity_dimension": "business_group", "metric": "revenue_amount"},
                    "reason": "intentionally unsupported",
                }
            ],
            "answer_mode": "comparison",
            "requires_limitations": True,
            "unsupported_reason": None,
        }

    routing = classify_business_question(question)
    profile = build_task_profile(question, routing)
    plan = build_answer_plan(profile, routing)
    primary_tool = (plan.primary_tools or [None])[0]
    tool_payload = _planner_tool_payload(primary_tool, profile)
    domains = ["chart"] if profile.task_family == "chart_request" else ([] if profile.task_family == "forecast_unsupported" else ["financial"])
    question_type, answer_mode = _question_type_for(profile.task_family)
    return {
        "task_family": profile.task_family,
        "question_type": question_type,
        "domains": domains,
        "tools": [tool_payload] if tool_payload else [],
        "answer_mode": answer_mode,
        "requires_limitations": bool(profile.requires_limitations),
        "unsupported_reason": "forecast unsupported" if profile.task_family == "forecast_unsupported" else None,
    }


def _question_type_for(task_family: str) -> tuple[str, str]:
    mapping = {
        "entity_ranking": ("ranking", "ranking"),
        "latest_month_entity_summary": ("overview", "briefing"),
        "cross_section_compare": ("comparison", "comparison"),
        "period_pair_compare": ("comparison", "comparison"),
        "entity_period_pair_table_lookup": ("overview", "overview"),
        "entity_multi_month_table_lookup": ("overview", "overview"),
        "entity_period_pair_metric_lookup": ("comparison", "comparison"),
        "entity_time_series": ("trend", "trend"),
        "overall_trend_analysis": ("trend", "trend"),
        "entity_trend_comparison": ("trend", "trend"),
        "performance_assessment": ("overview", "briefing"),
        "risk_scan": ("risk", "risk"),
        "metric_relationship_analysis": ("risk", "risk"),
        "contribution_analysis": ("comparison", "comparison"),
        "parent_child_drilldown": ("comparison", "comparison"),
        "data_quality": ("data_quality", "data_quality"),
        "chart_request": ("chart", "chart"),
        "forecast_unsupported": ("unsupported", "unsupported"),
        "metric_lookup": ("overview", "overview"),
        "entity_month_table_lookup": ("overview", "overview"),
    }
    return mapping.get(task_family, ("overview", "overview"))


def _planner_tool_payload(tool_name: str | None, profile: Any) -> dict[str, Any] | None:
    if not tool_name:
        return None
    target = getattr(profile, "target_entity", {}) or {}
    parent = getattr(profile, "parent_entity", {}) or {}
    time_scope = getattr(profile, "time_scope", {}) or {}
    metric = (getattr(profile, "metrics", []) or [None])[0]
    parent_filter = {"business_group": parent["value"]} if parent.get("dimension") == "business_group" and parent.get("value") else None
    if tool_name == "get_entity_metric_ranking":
        return {"tool_name": tool_name, "args": {"entity_dimension": target.get("dimension"), "metric": metric}, "reason": "canonical ranking"}
    if tool_name == "get_entity_performance_snapshot":
        args: dict[str, Any] = {"entity_dimension": target.get("dimension")}
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical snapshot"}
    if tool_name == "get_entity_cross_section_comparison":
        return {"tool_name": tool_name, "args": {"entity_dimension": target.get("dimension")}, "reason": "canonical comparison"}
    if tool_name == "get_entity_period_pair_comparison":
        metric_value = "revenue" if metric == "revenue_amount" else metric
        args = {"entity_dimension": target.get("dimension"), "metric": metric_value, "period_a": time_scope.get("period_a"), "period_b": time_scope.get("period_b")}
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical period pair"}
    if tool_name == "get_entity_time_series":
        args = {"entity_dimension": target.get("dimension"), "entity_value": target.get("value"), "metric": metric}
        if time_scope.get("recent_n") is not None:
            args["recent_n"] = time_scope.get("recent_n")
        if time_scope.get("start_month"):
            args["start_month"] = time_scope.get("start_month")
        if time_scope.get("end_month"):
            args["end_month"] = time_scope.get("end_month")
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical entity series"}
    if tool_name == "get_overall_time_series":
        args = {"metric": metric}
        if time_scope.get("recent_n") is not None:
            args["recent_n"] = time_scope.get("recent_n")
        if time_scope.get("start_month"):
            args["start_month"] = time_scope.get("start_month")
        if time_scope.get("end_month"):
            args["end_month"] = time_scope.get("end_month")
        return {"tool_name": tool_name, "args": args, "reason": "canonical overall series"}
    if tool_name == "get_entity_trend_comparison":
        args = {"entity_dimension": target.get("dimension"), "metric": metric}
        if time_scope.get("recent_n") is not None:
            args["recent_n"] = time_scope.get("recent_n")
        if time_scope.get("start_month"):
            args["start_month"] = time_scope.get("start_month")
        if time_scope.get("end_month"):
            args["end_month"] = time_scope.get("end_month")
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical trend comparison"}
    if tool_name == "get_revenue_inventory_relationship":
        args = {"entity_dimension": target.get("dimension")}
        if time_scope.get("single_month"):
            args["month"] = time_scope.get("single_month")
        if time_scope.get("recent_n") is not None:
            args["recent_n"] = time_scope.get("recent_n")
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical relationship"}
    if tool_name == "get_entity_contribution_analysis":
        args = {
            "entity_dimension": target.get("dimension"),
            "metric": metric,
            "period_a": time_scope.get("period_a"),
            "period_b": time_scope.get("period_b"),
        }
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical contribution"}
    if tool_name == "get_entity_period_pair_table":
        args = {"entity_dimension": target.get("dimension"), "metric": metric, "period_a": time_scope.get("period_a"), "period_b": time_scope.get("period_b")}
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical entity period pair table"}
    if tool_name == "get_entity_multi_month_table":
        args = {"entity_dimension": target.get("dimension"), "metric": metric, "start_month": time_scope.get("start_month"), "end_month": time_scope.get("end_month")}
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical entity multi-month table"}
    if tool_name == "get_entity_period_pair_value":
        args = {"entity_dimension": target.get("dimension"), "entity_value": target.get("value"), "metric": metric, "period_a": time_scope.get("period_a"), "period_b": time_scope.get("period_b")}
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical entity period pair value"}
    if tool_name == "get_entity_metric_value":
        month = time_scope.get("single_month") or time_scope.get("month")
        return {
            "tool_name": tool_name,
            "args": {
                "entity_dimension": target.get("dimension"),
                "entity_value": target.get("value"),
                "metric": metric,
                "month": month,
            },
            "reason": "canonical entity metric lookup",
        }
    if tool_name == "get_entity_month_table":
        month = time_scope.get("single_month") or time_scope.get("month")
        args = {"entity_dimension": target.get("dimension"), "metric": metric, "month": month}
        if parent_filter:
            args["parent_filter"] = parent_filter
        return {"tool_name": tool_name, "args": args, "reason": "canonical entity month table"}
    if tool_name == "get_chart_payload":
        args: dict[str, Any] = {}
        if time_scope.get("single_month"):
            args["month"] = time_scope.get("single_month")
        if target.get("dimension"):
            args["entity_dimension"] = target.get("dimension")
        if metric:
            args["metric"] = metric
        return {"tool_name": tool_name, "args": args, "reason": "canonical chart request"}
    if tool_name == "get_metric_table":
        return {"tool_name": tool_name, "args": {"metric": "revenue_trend"}, "reason": "canonical lookup"}
    return {"tool_name": tool_name, "args": {}, "reason": "canonical tool"}


def _snapshot(response: dict[str, Any]) -> dict[str, Any]:
    task_profile = response.get("task_profile", {}) or {}
    target_entity = task_profile.get("target_entity", {}) or {}
    parent_entity = task_profile.get("parent_entity", {}) or {}
    time_scope = task_profile.get("time_scope", {}) or {}
    display = (response.get("answer_contract", {}) or {}).get("display_blocks", {}) or {}
    chart = _first_chart_payload(response)
    return {
        "task_family": task_profile.get("task_family"),
        "target_entity.dimension": target_entity.get("dimension"),
        "target_entity.value": target_entity.get("value"),
        "parent_entity": parent_entity,
        "period_a": time_scope.get("period_a"),
        "period_b": time_scope.get("period_b"),
        "single_month": time_scope.get("single_month") or time_scope.get("month"),
        "metric": (task_profile.get("metrics") or [None])[0],
        "primary_tools": response.get("answer_plan", {}).get("primary_tools", []),
        "chart_key": chart.get("chart_key"),
        "chart_type": chart.get("chart_type"),
        "chart_month": (chart.get("filters") or {}).get("month"),
        "headline": display.get("headline"),
        "tools_used": response.get("answer_contract", {}).get("tools_used", []),
    }


def _first_chart_payload(response: dict[str, Any]) -> dict[str, Any]:
    for result in response.get("domain_results", []) or []:
        for chart in result.get("charts", []) or []:
            if isinstance(chart, dict):
                return chart
    display = (response.get("answer_contract", {}) or {}).get("display_blocks", {}) or {}
    for chart in display.get("charts", []) or []:
        if isinstance(chart, dict):
            return chart
    return {}



def _illegal_tools(tools_used: list[Any]) -> list[str]:
    illegal: list[str] = []
    for tool in tools_used or []:
        name = str(tool).split("(", 1)[0]
        if name and name not in TOOL_REGISTRY:
            illegal.append(str(tool))
    return illegal


def _planner_validation_summary(question: str) -> dict[str, Any]:
    routing = classify_business_question(question)
    profile = build_task_profile(question, routing)
    canonical = CanonicalTaskProfile.from_task_profile(profile, routing)
    answer_plan = build_answer_plan(profile, routing)
    allowed_tools = build_allowed_tool_names_for_task_family(canonical.task_family)
    payload = _build_planner_payload(question)
    try:
        plan = LLMToolPlanner("planner-regression-metrics")._validate_plan(
            question,
            payload,
            allowed_tool_names=allowed_tools,
            canonical_task_family=canonical.task_family,
            canonical_task_profile=canonical,
            deterministic_answer_plan=answer_plan,
        )
    except Exception as exc:
        return {
            "planner_called": True,
            "planner_valid": False,
            "planner_fallback_reason": str(exc),
            "planner_tool_count": len(payload.get("tool_calls") if "tool_calls" in payload else payload.get("tools") or []),
        }
    validation = PlanValidator().validate(canonical, plan, deterministic_answer_plan=answer_plan)
    return {
        "planner_called": True,
        "planner_valid": bool(validation["valid"]),
        "planner_fallback_reason": "none" if validation["valid"] else str(validation["reason"]),
        "planner_tool_count": len(plan.tools),
    }


def main() -> None:
    cases = load_cases()
    planner_llm = ScriptedPlannerLLM()
    off_assistant = build_stubbed_assistant("planner-regression-off", use_llm_planner=False, use_llm_rewriter=False)
    on_assistant = build_stubbed_assistant(
        "planner-regression-on",
        use_llm_planner=True,
        use_llm_rewriter=False,
        llm_client=planner_llm,
    )

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for case in cases:
        question = str(case["question"])
        off_response = off_assistant.answer(question)
        on_response = on_assistant.answer(question)
        off_snapshot = _snapshot(off_response)
        on_snapshot = _snapshot(on_response)
        compared_keys = [key for key in off_snapshot.keys() if key != "tools_used"]
        mismatches = [key for key in compared_keys if on_snapshot.get(key) != off_snapshot.get(key)]
        illegal_tools = _illegal_tools(on_snapshot.get("tools_used", []))
        if illegal_tools:
            mismatches.append("illegal_tools_used:" + ",".join(illegal_tools))
        planner_summary = _planner_validation_summary(question)
        row = {
            "question": question,
            "passed": not mismatches,
            "mismatches": ", ".join(mismatches),
            "tools_legal": not illegal_tools,
            **planner_summary,
        }
        row.update({f"off_{key}": json.dumps(value, ensure_ascii=False) for key, value in off_snapshot.items()})
        row.update({f"on_{key}": json.dumps(value, ensure_ascii=False) for key, value in on_snapshot.items()})
        rows.append(row)
        if mismatches:
            failures.append(f"{question}: {', '.join(mismatches)}")

    write_csv(rows)
    write_markdown(rows, failures)
    planner_called_count = sum(1 for row in rows if row.get("planner_called"))
    planner_valid_count = sum(1 for row in rows if row.get("planner_valid"))
    planner_rejected_count = planner_called_count - planner_valid_count
    planner_valid_rate = (planner_valid_count / planner_called_count) if planner_called_count else 0.0
    fallback_reason_counts = Counter(
        str(row.get("planner_fallback_reason") or "unknown")
        for row in rows
        if row.get("planner_called") and not row.get("planner_valid")
    )
    print(f"Wrote {CSV_FILE}")
    print(f"Wrote {MD_FILE}")
    print(f"Planner regression: {len(rows) - len(failures)}/{len(rows)} passed")
    print(f"planner_called_count={planner_called_count}")
    print(f"planner_valid_count={planner_valid_count}")
    print(f"planner_rejected_count={planner_rejected_count}")
    print(f"planner_valid_rate={planner_valid_rate:.1%}")
    print(f"fallback_reason_counts={dict(fallback_reason_counts)}")
    if failures:
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


def write_csv(rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "question",
        "passed",
        "mismatches",
        "planner_called",
        "planner_valid",
        "planner_fallback_reason",
        "planner_tool_count",
        "off_task_family",
        "on_task_family",
        "off_target_entity.dimension",
        "on_target_entity.dimension",
        "off_target_entity.value",
        "on_target_entity.value",
        "off_parent_entity",
        "on_parent_entity",
        "off_period_a",
        "on_period_a",
        "off_period_b",
        "on_period_b",
        "off_single_month",
        "on_single_month",
        "off_metric",
        "on_metric",
        "off_primary_tools",
        "on_primary_tools",
        "off_chart_key",
        "on_chart_key",
        "off_chart_type",
        "on_chart_type",
        "off_chart_month",
        "on_chart_month",
        "off_headline",
        "on_headline",
        "off_tools_used",
        "on_tools_used",
        "tools_legal",
    ]
    with CSV_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], failures: list[str]) -> None:
    planner_called_count = sum(1 for row in rows if row.get("planner_called"))
    planner_valid_count = sum(1 for row in rows if row.get("planner_valid"))
    planner_rejected_count = planner_called_count - planner_valid_count
    planner_valid_rate = (planner_valid_count / planner_called_count) if planner_called_count else 0.0
    fallback_reason_counts = Counter(
        str(row.get("planner_fallback_reason") or "unknown")
        for row in rows
        if row.get("planner_called") and not row.get("planner_valid")
    )
    top_rejection_reasons = fallback_reason_counts.most_common(5)
    lines = [
        "# Demo LLM Planner Regression",
        "",
        f"- cases: {len(rows)}",
        f"- passed: {len(rows) - len(failures)}",
        f"- failed: {len(failures)}",
        f"- planner_called_count: {planner_called_count}",
        f"- planner_valid_count: {planner_valid_count}",
        f"- planner_rejected_count: {planner_rejected_count}",
        f"- planner_valid_rate: {planner_valid_rate:.1%}",
        f"- fallback_reason_counts: {dict(fallback_reason_counts)}",
        f"- top_rejection_reasons: {top_rejection_reasons}",
        "- mode A: `USE_LLM_PLANNER=false`",
        "- mode B: `USE_LLM_PLANNER=true`, `USE_LLM_REWRITER=false`",
        "",
        "| Question | Passed | Planner Valid | Fallback Reason | Mismatches |",
        "|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {_escape(row['question'])} | {'yes' if row['passed'] else 'no'} | {'yes' if row.get('planner_valid') else 'no'} | {_escape(row.get('planner_fallback_reason') or '-')} | {_escape(row['mismatches'] or '-')} |"
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
