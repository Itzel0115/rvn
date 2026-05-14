from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.support import build_stubbed_assistant


REPORT_DIR = PROJECT_ROOT / "eval"
CSV_FILE = REPORT_DIR / "demo_answer_review_results.csv"
MD_FILE = REPORT_DIR / "demo_answer_review.md"

DEMO_REVIEW_QUESTIONS = [
    "請整理最新月份各新事業群的營收與庫存重點",
    "請分析哪個新事業群表現較佳",
    "請分析哪個新事業群表現較差",
    "比較最新月份各五大產品線營收與庫存",
    "哪個產品線庫存壓力較高？",
    "請畫最新月份各新事業群營收圖",
    "請畫五大產品線 health_score 排名",
    "2026年1月以及2026年2月營收有什麼區別？",
    "最新月份營收最高的新事業群是誰？",
    "最新月份庫存最高的新事業群是誰？",
    "哪個新事業群營收相對庫存效率較弱？",
    "哪個五大產品線營收最高？",
    "哪個五大產品線庫存最高？",
    "目前資料涵蓋哪些月份？",
    "下個月營收會不會改善？",
    "為什麼某新事業群營收下降？",
    "最近有什麼營運風險？",
    "請比較新事業群與五大產品線的重點",
    "哪個新事業群需要優先注意？",
    "請產生主管摘要",
    "哪個新事業群營收相對庫存效率最高？",
    "哪個新事業群營收相對庫存效率最低？",
]

ROOT_CAUSE_QUESTION_HINTS = ("為什麼", "原因", "root cause", "why")
ROOT_CAUSE_CLAIM_PATTERNS = (
    "已確認原因",
    "確認原因",
    "已確認根因",
    "根因是",
    "原因就是",
    "一定是",
    "root cause confirmed",
)
FORECAST_QUESTION_HINTS = ("下個月", "下月", "forecast", "預測")


def main() -> None:
    assistant = build_stubbed_assistant(
        "demo-answer-review",
        use_llm_planner=False,
        use_llm_rewriter=False,
    )
    rows = [
        review_response(index, question, assistant.answer(question))
        for index, question in enumerate(DEMO_REVIEW_QUESTIONS, start=1)
    ]
    write_csv(rows)
    write_markdown(rows)
    failures = [row for row in rows if row["passed"] != "True"]
    print(f"Wrote {CSV_FILE}")
    print(f"Wrote {MD_FILE}")
    print(f"Demo answer review: {len(rows) - len(failures)}/{len(rows)} passed")
    if failures:
        print("Failed cases:")
        for row in failures:
            print(f"- {row['case_id']}: {row['question']} -> {row['failures']}")
        raise SystemExit(1)


def review_response(case_id: int, question: str, response: dict[str, Any]) -> dict[str, str]:
    contract = response.get("answer_contract", {}) or {}
    task_profile = response.get("task_profile", {}) or {}
    answer_plan = response.get("answer_plan", {}) or {}
    display = contract.get("display_blocks", {}) or {}
    headline = str(display.get("headline") or "")
    observations = display.get("key_observations") or []
    table = display.get("table") or {}
    table_columns = table.get("columns") or []
    charts = _extract_chart_payloads(response)
    evidence = contract.get("evidence") or []
    tools_used = contract.get("tools_used") or []
    visible_text = "\n".join(
        [
            str(contract.get("answer") or ""),
            headline,
            "\n".join(str(item) for item in observations),
            "\n".join(str(item) for item in display.get("limitations") or contract.get("limitations") or []),
        ]
    )

    checks = {
        "headline_no_platform": ("平台" not in headline) or ("平台" in question),
        "key_observations_max_3": len(observations) <= 3,
        "chart_title_no_platform": _chart_titles_ok(charts),
        "table_columns_no_platform": _table_columns_ok(table_columns),
        "unmapped_headline_guardrail": _unmapped_headline_ok(headline),
        "forecast_unsupported": _forecast_ok(question, contract, task_profile),
        "root_cause_no_confirmed_claim": _root_cause_ok(question, visible_text),
        "ranking_answer_has_entity_metric_evidence": _ranking_answer_ok(
            question=question,
            task_profile=task_profile,
            contract=contract,
            headline=headline,
            table=table,
            evidence=evidence,
            tools_used=tools_used,
        ),
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {
        "case_id": str(case_id),
        "question": question,
        "task_family": str(task_profile.get("task_family") or ""),
        "answer_type": str(contract.get("answer_type") or ""),
        "primary_tools": ", ".join(answer_plan.get("primary_tools") or []),
        "headline": headline,
        "key_observation_count": str(len(observations)),
        "chart_keys": ", ".join(_chart_key(chart) for chart in charts if _chart_key(chart)),
        "checks": json.dumps(checks, ensure_ascii=False, sort_keys=True),
        "passed": str(not failures),
        "failures": ", ".join(failures),
    }


def _extract_chart_payloads(response: dict[str, Any]) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []
    for result in response.get("domain_results") or []:
        for evidence in result.get("evidence") or []:
            if isinstance(evidence, dict) and (
                evidence.get("chart_key") or evidence.get("chart_type") or evidence.get("type") == "chart"
            ):
                charts.append(evidence)
    contract = response.get("answer_contract", {}) or {}
    for item in contract.get("evidence") or []:
        if isinstance(item, dict) and (item.get("chart_key") or item.get("chart_type")):
            charts.append(item)
    return charts


def _chart_key(chart: dict[str, Any]) -> str:
    return str(chart.get("chart_key") or chart.get("key") or "")


def _chart_titles_ok(charts: list[dict[str, Any]]) -> bool:
    for chart in charts:
        fields = [chart.get("title"), chart.get("x_label"), chart.get("y_label")]
        axes = chart.get("axes") or {}
        fields.extend([axes.get("x"), axes.get("y")])
        if any("平台" in str(field) for field in fields if field is not None):
            return False
    return True


def _table_columns_ok(columns: list[Any]) -> bool:
    for column in columns:
        text = str(column)
        if "平台" in text or text.lower() == "platform":
            return False
    return True


def _unmapped_headline_ok(headline: str) -> bool:
    if "未對應" not in headline:
        return True
    return "資料品質限制" in headline or "未對應資料列" in headline


def _forecast_ok(question: str, contract: dict[str, Any], task_profile: dict[str, Any]) -> bool:
    if not any(hint in question.lower() for hint in FORECAST_QUESTION_HINTS):
        return True
    return (
        contract.get("answer_type") == "unsupported"
        or task_profile.get("task_family") == "forecast_unsupported"
    )


def _root_cause_ok(question: str, visible_text: str) -> bool:
    lowered_question = question.lower()
    if not any(hint in lowered_question for hint in ROOT_CAUSE_QUESTION_HINTS):
        return True
    lowered_text = visible_text.lower()
    return not any(pattern.lower() in lowered_text for pattern in ROOT_CAUSE_CLAIM_PATTERNS)


def _ranking_answer_ok(
    *,
    question: str,
    task_profile: dict[str, Any],
    contract: dict[str, Any],
    headline: str,
    table: dict[str, Any],
    evidence: list[Any],
    tools_used: list[str],
) -> bool:
    if not _is_ranking_question(question, task_profile, contract):
        return True
    forbidden = ["沒有足夠", "無法形成管理結論", "無法判斷"]
    if any(token in headline for token in forbidden):
        return False
    ranking_evidence = next(
        (
            _evidence_details(item)
            for item in evidence
            if isinstance(item, dict)
            and _evidence_details(item).get("evidence_type") in {"entity_metric_ranking", "entity_performance_snapshot"}
        ),
        None,
    )
    if not ranking_evidence:
        return False
    top_entity = ranking_evidence.get("top_entity") or (ranking_evidence.get("summary") or {}).get("top_revenue_entity")
    if not top_entity or str(top_entity) not in headline:
        return False
    if not ranking_evidence.get("month") or str(ranking_evidence.get("month")) not in headline:
        return False
    top_value = ranking_evidence.get("top_value")
    if top_value is None:
        rows = ranking_evidence.get("rows") or []
        top_value = rows[0].get("value") if rows and isinstance(rows[0], dict) else None
    if top_value is None:
        return False
    if not any(tool in tools_used for tool in ["get_entity_metric_ranking", "get_entity_performance_snapshot"]):
        return False
    if not (table.get("rows") or []):
        return False
    return True


def _evidence_details(item: dict[str, Any]) -> dict[str, Any]:
    details = item.get("details")
    return details if isinstance(details, dict) else item


def _is_ranking_question(question: str, task_profile: dict[str, Any], contract: dict[str, Any]) -> bool:
    task_family = task_profile.get("task_family")
    answer_type = contract.get("answer_type")
    if task_family != "ranking" and answer_type != "ranking":
        return False
    return any(token in question for token in ["最高", "最低", "排名", "排行", "哪個"])


def write_csv(rows: list[dict[str, str]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_id",
        "question",
        "task_family",
        "answer_type",
        "primary_tools",
        "headline",
        "key_observation_count",
        "chart_keys",
        "checks",
        "passed",
        "failures",
    ]
    with CSV_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    passed = [row for row in rows if row["passed"] == "True"]
    lines = [
        "# Demo Answer Review",
        "",
        f"- cases: {len(rows)}",
        f"- passed: {len(passed)}",
        f"- failed: {len(rows) - len(passed)}",
        "- mode: direct deterministic assistant; LLM planner and rewriter disabled",
        "",
        "| # | Question | Task Family | Answer Type | Passed | Failures | Headline |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {case_id} | {question} | {task_family} | {answer_type} | {passed} | {failures} | {headline} |".format(
                case_id=row["case_id"],
                question=_escape_md(row["question"]),
                task_family=_escape_md(row["task_family"]),
                answer_type=_escape_md(row["answer_type"]),
                passed=row["passed"],
                failures=_escape_md(row["failures"] or "-"),
                headline=_escape_md(row["headline"] or "-"),
            )
        )
    lines.extend(["", "## Check Details", ""])
    for row in rows:
        lines.extend(
            [
                f"### {row['case_id']}. {_escape_md(row['question'])}",
                "",
                f"- headline: {row['headline'] or '-'}",
                f"- key_observation_count: `{row['key_observation_count']}`",
                f"- chart_keys: `{row['chart_keys'] or '-'}`",
                f"- checks: `{row['checks']}`",
                f"- failures: `{row['failures'] or '-'}`",
                "",
            ]
        )
    MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
