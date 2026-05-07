from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.support import build_stubbed_assistant


BASE_DIR = Path(__file__).resolve().parent
ROUTER_FILE = BASE_DIR / "questions_router.jsonl"
ANSWER_FILE = BASE_DIR / "questions_answer.jsonl"
RESULTS_FILE = BASE_DIR / "eval_results.csv"
REPORT_FILE = BASE_DIR / "eval_report.md"

WHY_OR_FORECAST_HINTS = [
    "why",
    "cause",
    "root cause",
    "forecast",
    "predict",
    "prediction",
    "原因",
    "為什麼",
    "預測",
    "下月",
    "下個月",
]

LIMITATION_HINTS = [
    "無法直接判斷",
    "無法直接預測",
    "不能直接回答",
    "cannot directly determine",
    "cannot directly predict",
    "不足以",
    "限制",
    "proxy",
    "scorecard",
    "not a forecast",
    "不是預測",
    "無法直接",
]

CONCLUSION_PREFIXES = ("結論", "Conclusion", "目前", "Direct answer")
ROOT_CAUSE_CONFIRMED_PATTERNS = (
    "root cause confirmed",
    "原因就是",
    "一定是",
    "確認根因",
    "根因是",
)
INVENTORY_RANKING_ONLY_PATTERNS = (
    "庫存金額最高作為唯一理由",
    "highest inventory amount as the only reason",
)
MOM_CONTRIBUTION_HEADLINE_PATTERNS = (
    "相較 2024-07 的營收變化主要由",
    "revenue change was mainly contributed",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    assistant = build_stubbed_assistant("eval-runner")
    router_cases = load_jsonl(ROUTER_FILE)
    answer_cases = load_jsonl(ANSWER_FILE)

    rows: list[dict[str, Any]] = []

    for case in router_cases:
        response = assistant.answer(case["question"])
        routing = response["routing"]
        contract = response["answer_contract"]

        expected_domains = case.get("expected_domains")
        if expected_domains is None:
            expected_domain = case.get("expected_domain")
            expected_domains = [expected_domain] if expected_domain else []

        rows.append(
            {
                "kind": "router",
                "id": case["id"],
                "question": case["question"],
                "task_family": response.get("task_profile", {}).get("task_family", ""),
                "question_type_accuracy": 1.0 if routing["question_type"] == case.get("expected_question_type") else 0.0,
                "domain_accuracy": 1.0 if routing["domains"] == expected_domains else 0.0,
                "tool_accuracy": 1.0 if set(case.get("expected_tools", [])).issubset(set(contract.get("tools_used", []))) else 0.0,
                "filter_extraction_accuracy": _filters_match(case.get("expected_filters", {}), routing["filters"]),
                "task_family_accuracy": _task_family_match(case, response),
                "answer_plan_score": _answer_plan_match(case, response),
                "display_observation_count_score": "",
                "display_blocks_presence_score": "",
                "headline_score": "",
                "observation_count_score": "",
                "no_background_leakage_score": "",
                "table_score": "",
                "limitation_preservation_score": "",
                "answer_grounding_score": "",
                "hallucination_rate": "",
                "unsupported_question_rejection_rate": "",
                "must_include_score": "",
                "must_not_score": "",
                "evidence_tools_score": "",
                "limitation_score": "",
                "answer_filter_accuracy": "",
            }
        )

    for case in answer_cases:
        response = assistant.answer(case["question"])
        contract = response["answer_contract"]
        task_profile = response.get("task_profile", {})
        answer_plan = response.get("answer_plan", {})
        answer_text = str(contract.get("answer", ""))
        limitations = [str(item) for item in contract.get("limitations", [])]
        must_include = case.get("must_include", [])
        must_not_include = case.get("must_not_include", [])
        expected_filters = case.get("expected_filters") or _infer_filters_from_question(case["question"])
        answer_type_accuracy = 1.0 if contract.get("answer_type") == case.get("expected_answer_type") else 0.0

        include_score = 1.0 if all(token in answer_text for token in must_include) else 0.0
        must_not_score = 1.0 if all(token not in answer_text for token in must_not_include) else 0.0
        hallucination_rate = 0.0 if must_not_score == 1.0 else 1.0

        is_unsupported = contract.get("answer_type") == "unsupported"
        if is_unsupported:
            evidence_tools_score = 1.0 if not contract.get("evidence") and not contract.get("tools_used") else 0.0
            unsupported_rejection = 1.0
        else:
            evidence_tools_score = 1.0 if contract.get("evidence") and contract.get("tools_used") else 0.0
            unsupported_rejection = ""

        if _needs_reasoning_limitation(case["question"]):
            limitation_score = 1.0 if _has_limitation_semantics(answer_text, limitations) else 0.0
        else:
            limitation_score = ""

        display_blocks_presence_score = _display_blocks_presence_score(contract)
        headline_score = _headline_score(contract, task_profile)
        observation_count_score = _observation_count_score(contract, answer_plan)
        no_background_leakage_score = _no_background_leakage_score(contract, task_profile)
        table_score = _table_score(contract, task_profile, answer_plan)
        limitation_preservation_score = _limitation_preservation_score(case, contract, task_profile)

        answer_filter_accuracy = ""
        if expected_filters:
            answer_filter_accuracy = _filters_match(expected_filters, contract.get("data_scope", {}).get("filters", {}))

        grounding_components = [
            answer_type_accuracy,
            include_score,
            must_not_score,
            evidence_tools_score,
        ]
        if limitation_score != "":
            grounding_components.append(float(limitation_score))
        if answer_filter_accuracy != "":
            grounding_components.append(float(answer_filter_accuracy))

        rows.append(
            {
                "kind": "answer",
                "id": case["id"],
                "question": case["question"],
                "task_family": task_profile.get("task_family", ""),
                "question_type_accuracy": answer_type_accuracy,
                "domain_accuracy": "",
                "tool_accuracy": "",
                "filter_extraction_accuracy": "",
                "task_family_accuracy": _task_family_match(case, response),
                "answer_plan_score": _answer_plan_match(case, response),
                "display_observation_count_score": _display_observation_count_match(case, contract),
                "display_blocks_presence_score": display_blocks_presence_score,
                "headline_score": headline_score,
                "observation_count_score": observation_count_score,
                "no_background_leakage_score": no_background_leakage_score,
                "table_score": table_score,
                "limitation_preservation_score": limitation_preservation_score,
                "answer_grounding_score": sum(grounding_components) / len(grounding_components),
                "hallucination_rate": hallucination_rate,
                "unsupported_question_rejection_rate": unsupported_rejection,
                "must_include_score": include_score,
                "must_not_score": must_not_score,
                "evidence_tools_score": evidence_tools_score,
                "limitation_score": limitation_score,
                "answer_filter_accuracy": answer_filter_accuracy,
            }
        )

    write_csv(rows)
    write_report(rows)
    print(f"Wrote {RESULTS_FILE}")
    print(f"Wrote {REPORT_FILE}")


def _filters_match(expected_filters: dict[str, Any], actual_filters: dict[str, Any]) -> float:
    for key, expected_value in expected_filters.items():
        if actual_filters.get(key) != expected_value:
            return 0.0
    return 1.0


def _task_family_match(case: dict[str, Any], response: dict[str, Any]) -> str | float:
    expected = case.get("expected_task_family")
    if not expected:
        return ""
    return 1.0 if response.get("task_profile", {}).get("task_family") == expected else 0.0


def _answer_plan_match(case: dict[str, Any], response: dict[str, Any]) -> str | float:
    expected_forbidden = case.get("expected_forbidden_primary_tools", [])
    expected_primary = case.get("expected_answer_plan_primary_tools", [])
    if not expected_forbidden and not expected_primary:
        return ""
    plan = response.get("answer_plan", {})
    forbidden_ok = set(expected_forbidden).issubset(set(plan.get("forbidden_primary_tools", [])))
    primary_ok = set(expected_primary).issubset(set(plan.get("primary_tools", [])))
    return 1.0 if forbidden_ok and primary_ok else 0.0


def _display_observation_count_match(case: dict[str, Any], contract: dict[str, Any]) -> str | float:
    expected_max = case.get("expected_max_key_observations")
    if expected_max is None:
        return ""
    observations = contract.get("display_blocks", {}).get("key_observations", [])
    return 1.0 if len(observations) <= int(expected_max) else 0.0


def _display_blocks_presence_score(contract: dict[str, Any]) -> str | float:
    if contract.get("answer_type") == "unsupported":
        return ""
    blocks = contract.get("display_blocks")
    return 1.0 if isinstance(blocks, dict) and bool(blocks) else 0.0


def _headline_score(contract: dict[str, Any], task_profile: dict[str, Any]) -> str | float:
    if contract.get("answer_type") == "unsupported":
        return ""
    headline = str(contract.get("display_blocks", {}).get("headline", "")).strip()
    if not headline:
        return 0.0

    task_family = task_profile.get("task_family")
    answer_style = task_profile.get("answer_style")
    requires_conclusion_tone = task_family in {"performance_assessment", "cross_section_compare"} or answer_style == "conclusion_first"
    if requires_conclusion_tone and not headline.startswith(CONCLUSION_PREFIXES):
        return 0.0
    return 1.0


def _observation_count_score(contract: dict[str, Any], answer_plan: dict[str, Any]) -> str | float:
    if contract.get("answer_type") == "unsupported":
        return ""
    max_observations = int(answer_plan.get("max_key_observations") or 3)
    observations = contract.get("display_blocks", {}).get("key_observations", [])
    return 1.0 if len(observations) <= max_observations else 0.0


def _no_background_leakage_score(contract: dict[str, Any], task_profile: dict[str, Any]) -> str | float:
    if contract.get("answer_type") == "unsupported":
        return ""

    blocks = contract.get("display_blocks", {}) or {}
    headline = str(blocks.get("headline", ""))
    observations = [str(item) for item in blocks.get("key_observations", [])]
    observation_text = "\n".join(observations)
    visible_text = "\n".join([headline, observation_text])
    task_family = task_profile.get("task_family")

    role_evidence = contract.get("role_based_evidence", {}) or {}
    for role_name in ("background", "debug"):
        for item in role_evidence.get(role_name, []) or []:
            summary = str(item.get("summary", "")).strip()
            if summary and summary in observation_text:
                return 0.0

    if task_family == "performance_assessment":
        if any(pattern in headline for pattern in INVENTORY_RANKING_ONLY_PATTERNS):
            return 0.0
        if "庫存金額最高" in headline and "health_score" not in headline and "效率" not in headline:
            return 0.0

    if task_family == "cross_section_compare":
        if any(pattern in headline for pattern in MOM_CONTRIBUTION_HEADLINE_PATTERNS):
            return 0.0

    if task_family == "diagnosis":
        lowered = visible_text.lower()
        negated_root_cause = any(token in lowered for token in ("不能確認根因", "無法確認根因", "not confirmed", "cannot confirm"))
        if not negated_root_cause and any(pattern.lower() in lowered for pattern in ROOT_CAUSE_CONFIRMED_PATTERNS):
            return 0.0

    return 1.0


def _table_score(contract: dict[str, Any], task_profile: dict[str, Any], answer_plan: dict[str, Any]) -> str | float:
    if contract.get("answer_type") == "unsupported":
        return ""
    requires_table = bool(task_profile.get("requires_table") or answer_plan.get("requires_table"))
    if not requires_table:
        return ""

    table = contract.get("display_blocks", {}).get("table")
    if table and table.get("rows") and table.get("columns"):
        return 1.0

    combined = "\n".join(
        [
            str(contract.get("answer", "")),
            str(contract.get("display_blocks", {}).get("headline", "")),
            *[str(item) for item in contract.get("limitations", [])],
            *[str(item) for item in contract.get("display_blocks", {}).get("limitations", [])],
        ]
    ).lower()
    if any(token in combined for token in ("insufficient", "not enough", "不足", "無足夠")):
        return 1.0
    return 0.0


def _limitation_preservation_score(case: dict[str, Any], contract: dict[str, Any], task_profile: dict[str, Any]) -> str | float:
    if contract.get("answer_type") == "unsupported":
        return ""

    combined_text = "\n".join(
        [
            case.get("question", ""),
            str(contract.get("answer", "")),
            str(contract.get("display_blocks", {}).get("headline", "")),
            *[str(item) for item in contract.get("limitations", [])],
            *[str(item) for item in contract.get("display_blocks", {}).get("limitations", [])],
        ]
    )
    tools = set(contract.get("tools_used", []) or [])
    needs_limitation = (
        _needs_reasoning_limitation(case.get("question", ""))
        or "proxy" in combined_text.lower()
        or "health_score" in combined_text
        or any("get_platform_performance_snapshot" in tool for tool in tools)
        or task_profile.get("task_family") in {"diagnosis"}
    )
    if not needs_limitation:
        return ""

    limitations = [str(item) for item in contract.get("limitations", [])]
    limitations.extend(str(item) for item in contract.get("display_blocks", {}).get("limitations", []))
    return 1.0 if _has_limitation_semantics(combined_text, limitations) else 0.0


def _infer_filters_from_question(question: str) -> dict[str, str]:
    filters: dict[str, str] = {}
    month_match = re.search(r"(20\d{2})[-/]?(0[1-9]|1[0-2])", question)
    if month_match:
        filters["month"] = f"{month_match.group(1)}-{month_match.group(2)}"
    platform_match = re.search(r"GG-(0[1-9]|[1-8][0-9]|9[0-1])", question.upper())
    if platform_match:
        filters["platform"] = platform_match.group(0)
    return filters


def _needs_reasoning_limitation(question: str) -> bool:
    lowered = question.lower()
    return any(token in lowered or token in question for token in WHY_OR_FORECAST_HINTS)


def _has_limitation_semantics(answer_text: str, limitations: list[str]) -> bool:
    combined = "\n".join([answer_text, *limitations]).lower()
    return any(target.lower() in combined for target in LIMITATION_HINTS)


def write_csv(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "kind",
        "id",
        "question",
        "task_family",
        "question_type_accuracy",
        "domain_accuracy",
        "tool_accuracy",
        "filter_extraction_accuracy",
        "task_family_accuracy",
        "answer_plan_score",
        "display_observation_count_score",
        "display_blocks_presence_score",
        "headline_score",
        "observation_count_score",
        "no_background_leakage_score",
        "table_score",
        "limitation_preservation_score",
        "answer_grounding_score",
        "hallucination_rate",
        "unsupported_question_rejection_rate",
        "must_include_score",
        "must_not_score",
        "evidence_tools_score",
        "limitation_score",
        "answer_filter_accuracy",
    ]
    with RESULTS_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(rows: list[dict[str, Any]]) -> None:
    router_rows = [row for row in rows if row["kind"] == "router"]
    answer_rows = [row for row in rows if row["kind"] == "answer"]

    def average(key: str, subset: list[dict[str, Any]]) -> float:
        values = [float(row[key]) for row in subset if row.get(key) not in {"", None}]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def failed_cases(keys: list[str]) -> list[str]:
        failures: list[str] = []
        for row in answer_rows:
            failed_keys = [key for key in keys if row.get(key) == 0.0]
            if failed_keys:
                failures.append(f"- {row['id']}: {row['question']} ({', '.join(failed_keys)})")
        return failures[:20]

    quality_keys = [
        "display_blocks_presence_score",
        "headline_score",
        "observation_count_score",
        "no_background_leakage_score",
        "table_score",
        "limitation_preservation_score",
    ]
    supported_task_families = sorted({str(row.get("task_family")) for row in rows if row.get("task_family")})
    failed_summary = failed_cases(quality_keys + ["answer_grounding_score", "must_include_score", "must_not_score"])

    report_lines = [
        "# Eval Report",
        "",
        f"- router_cases: {len(router_rows)}",
        f"- answer_cases: {len(answer_rows)}",
        "",
        "## Router Metrics",
        "",
        f"- question_type_accuracy: {average('question_type_accuracy', router_rows):.2%}",
        f"- domain_accuracy: {average('domain_accuracy', router_rows):.2%}",
        f"- tool_accuracy: {average('tool_accuracy', router_rows):.2%}",
        f"- filter_extraction_accuracy: {average('filter_extraction_accuracy', router_rows):.2%}",
        f"- task_family_accuracy: {average('task_family_accuracy', rows):.2%}",
        f"- answer_plan_score: {average('answer_plan_score', rows):.2%}",
        f"- display_observation_count_score: {average('display_observation_count_score', answer_rows):.2%}",
        "",
        "## Answer Metrics",
        "",
        f"- answer_grounding_score: {average('answer_grounding_score', answer_rows):.2%}",
        f"- must_include_score: {average('must_include_score', answer_rows):.2%}",
        f"- must_not_score: {average('must_not_score', answer_rows):.2%}",
        f"- evidence_tools_score: {average('evidence_tools_score', answer_rows):.2%}",
        f"- limitation_score: {average('limitation_score', answer_rows):.2%}",
        f"- answer_filter_accuracy: {average('answer_filter_accuracy', answer_rows):.2%}",
        f"- hallucination_rate: {average('hallucination_rate', answer_rows):.2%}",
        f"- unsupported_question_rejection_rate: {average('unsupported_question_rejection_rate', answer_rows):.2%}",
        "",
        "## Display Quality Metrics",
        "",
        f"- display_blocks_presence_score: {average('display_blocks_presence_score', answer_rows):.2%}",
        f"- headline_score: {average('headline_score', answer_rows):.2%}",
        f"- observation_count_score: {average('observation_count_score', answer_rows):.2%}",
        f"- no_background_leakage_score: {average('no_background_leakage_score', answer_rows):.2%}",
        f"- table_score: {average('table_score', answer_rows):.2%}",
        f"- limitation_preservation_score: {average('limitation_preservation_score', answer_rows):.2%}",
        f"- supported_task_family_count: {len(supported_task_families)}",
        f"- supported_task_families: {', '.join(supported_task_families)}",
        "",
        "## Failed Cases Summary",
        "",
        *(failed_summary or ["- none"]),
        "",
        "## Notes",
        "",
        "- Eval runs with a stubbed LLM so routing and answers are measured against deterministic fallback behavior.",
        "- Non-unsupported answers must include both evidence and tools_used.",
        "- Unsupported answers only pass when evidence and tools_used are both empty.",
        "- Why/cause/forecast questions must surface limitation semantics in answer or limitations.",
        "- If the question mentions a month or platform, data_scope.filters must match that scope.",
    ]
    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
