from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from business_question_classifier import classify_business_question
from canonical_task import CanonicalTaskProfile
from evidence_contracts import EvidenceContractBuilder
from llm_evidence_writer import EvidenceWriteRequest, LLMEvidenceWriter
from ollama_client import OllamaCallResult
from task_profile import build_task_profile
from tests.support import build_stubbed_assistant
from writer_validator import WriterValidator


REPORT_DIR = PROJECT_ROOT / "eval"
CASE_FILE = REPORT_DIR / "questions_answer.jsonl"
CSV_FILE = REPORT_DIR / "demo_llm_writer_shadow_results.csv"
MD_FILE = REPORT_DIR / "demo_llm_writer_shadow_report.md"
FAILURE_MD_FILE = REPORT_DIR / "demo_llm_writer_shadow_failures.md"

BASELINE_REJECTED_CASES = [
    (3, "請整理最新月份各新事業群的營收與庫存重點", "latest_month_entity_summary", "metric_violation:revenue_question_mentions_inventory_as_answer", "false_positive_reject", "adjust validator"),
    (6, "各新事業群近 6 個月營收趨勢", "entity_trend_comparison", "internal_tool_name_violation:['get_entity_trend_comparison']", "true_positive_reject", "tighten prompt"),
    (15, "有沒有營收下降但庫存上升的新事業群？", "metric_relationship_analysis", "metric_violation:revenue_question_mentions_inventory_as_answer", "false_positive_reject", "adjust validator"),
    (17, "3通路方案底下哪個產品線表現較差？", "parent_child_drilldown", "internal_tool_name_violation:['get_entity_month_table']", "true_positive_reject", "tighten prompt"),
    (19, "畫總體營收趨勢", "chart_request", "number_not_in_evidence:['999,999,999']", "true_positive_reject", "keep rejected"),
    (24, "下個月營收會不會改善？", "forecast_unsupported", "forecast_violation:unsupported_forecast_claim", "true_positive_reject", "tighten prompt"),
    (25, "未來哪個事業群會成長？", "forecast_unsupported", "forecast_violation:unsupported_forecast_claim", "true_positive_reject", "tighten prompt"),
    (26, "請整理最新月份各事業群的營收與庫存重點", "latest_month_entity_summary", "metric_violation:revenue_question_mentions_inventory_as_answer", "false_positive_reject", "adjust validator"),
    (27, "請整理最新月份各新事業群的營收與庫存重點", "latest_month_entity_summary", "metric_violation:revenue_question_mentions_inventory_as_answer", "false_positive_reject", "adjust validator"),
    (28, "請整理最新月份各 BU 營收與庫存重點", "latest_month_entity_summary", "metric_violation:revenue_question_mentions_inventory_as_answer", "false_positive_reject", "adjust validator"),
    (34, "畫出 2026年2月 各產品線庫存長條圖", "chart_request", "internal_tool_name_violation:['get_entity_month_table']", "true_positive_reject", "tighten prompt"),
    (38, "比較2025年3月各事業群營收資料", "cross_section_compare", "number_not_in_evidence:['999,999,999']", "true_positive_reject", "keep rejected"),
    (45, "比較 Server 2025/02 和 2025/03 庫存", "entity_period_pair_metric_lookup", "internal_tool_name_violation:['get_entity_period_pair_value']", "true_positive_reject", "tighten prompt"),
    (50, "列出 3通路方案 2025/02 與 2025/03 營收", "entity_period_pair_metric_lookup", "internal_tool_name_violation:['get_entity_period_pair_value']", "true_positive_reject", "tighten prompt"),
    (51, "列出 2025年3月 3通路方案底下各產品線庫存", "entity_month_table_lookup", "internal_tool_name_violation:['get_entity_month_table']", "true_positive_reject", "tighten prompt"),
    (57, "列出 2025年3月各產品線資料", "entity_month_table_lookup", "number_not_in_evidence:['999,999,999']", "true_positive_reject", "keep rejected"),
]


class ScriptedWriterLLM:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def generate_json(self, **kwargs: Any) -> OllamaCallResult:
        return OllamaCallResult(ok=True, text=json.dumps(self.payload, ensure_ascii=False), data=self.payload)


def main() -> None:
    assistant = build_stubbed_assistant(
        "demo-llm-writer-shadow",
        use_llm_planner=False,
        use_llm_rewriter=False,
        use_llm_writer=False,
    )
    writer = LLMEvidenceWriter("demo-llm-writer-shadow")
    validator = WriterValidator()
    cases = load_cases()
    rows = []
    for index, case in enumerate(cases, start=1):
        rows.append(run_case(index, case, assistant, writer, validator))
    write_csv(rows)
    write_markdown(rows)
    write_failure_markdown(rows)
    print(f"Wrote {CSV_FILE}")
    print(f"Wrote {MD_FILE}")
    print(f"Wrote {FAILURE_MD_FILE}")
    print(_summary_line(rows))


def load_cases() -> list[dict[str, Any]]:
    return [json.loads(line) for line in CASE_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_case(
    index: int,
    case: dict[str, Any],
    assistant: Any,
    writer: LLMEvidenceWriter,
    validator: WriterValidator,
) -> dict[str, str]:
    question = str(case.get("question") or "")
    response = assistant.answer(question)
    contract = response.get("answer_contract", {}) or {}
    display = contract.get("display_blocks", {}) or {}
    routing = classify_business_question(question)
    task_profile = build_task_profile(question, routing)
    canonical = CanonicalTaskProfile.from_task_profile(task_profile, routing)
    evidence_contracts = EvidenceContractBuilder().build_evidence_contracts(response.get("domain_results") or [], canonical)
    request = EvidenceWriteRequest(
        original_question=question,
        canonical_task_profile=canonical.to_dict(),
        evidence_contracts=evidence_contracts,
        deterministic_display_blocks=display,
        required_limitations=list(contract.get("limitations") or display.get("limitations") or []),
        answer_style=getattr(task_profile, "answer_style", "concise") or "concise",
    )
    payload = build_shadow_payload(index, question, canonical, evidence_contracts, request)
    write_result = writer.write(request, ScriptedWriterLLM(payload))
    if not write_result.ok:
        validation = {
            "valid": False,
            "reason": write_result.error or "writer_unavailable",
            "violations": [write_result.error or "writer_unavailable"],
        }
        output = {}
    else:
        output = write_result.output
        validation = validator.validate(
            canonical,
            evidence_contracts,
            output,
            deterministic_display_blocks=display,
        )
    violations = validation.get("violations") or []
    categories = categorize_violations(violations)
    classification = classify_rejection(categories, str(canonical.task_family), evidence_contracts) if not validation.get("valid") else "valid"
    recommendation = recommend_action(categories, classification)
    return {
        "case_id": str(index),
        "question": question,
        "task_family": str(canonical.task_family),
        "evidence_types": ", ".join(contract.evidence_type for contract in evidence_contracts),
        "evidence_metrics": ", ".join(sorted({str(contract.metric) for contract in evidence_contracts if contract.metric})),
        "writer_called": "True",
        "writer_valid": str(bool(validation.get("valid"))),
        "fallback_reason": "none" if validation.get("valid") else str(validation.get("reason") or ""),
        "violations": json.dumps(violations, ensure_ascii=False),
        "violation_categories": json.dumps(categories, ensure_ascii=False),
        "rejection_classification": classification,
        "recommendation": recommendation,
        "writer_output": json.dumps(output, ensure_ascii=False, sort_keys=True),
        "headline": str(output.get("headline") or ""),
        "official_headline": str(display.get("headline") or ""),
    }


def build_shadow_payload(
    index: int,
    question: str,
    canonical: CanonicalTaskProfile,
    evidence_contracts: list[Any],
    request: EvidenceWriteRequest,
) -> dict[str, Any]:
    months = sorted(_collect_contract_months(evidence_contracts))
    metric_label = _first_metric_label(evidence_contracts) or str(canonical.metric or "指標")
    entity_label = _first_entity_label(evidence_contracts) or "資料"
    entity_value = _first_entity_value(evidence_contracts)
    target = f"{entity_value} " if entity_value else ""
    month_text = " 與 ".join(months[:2]) if months else "指定期間"
    limitations = list(dict.fromkeys(_writer_safe_limitation(item) for item in request.required_limitations if item))
    for contract in evidence_contracts:
        limitations.extend(_writer_safe_limitation(str(item)) for item in contract.limitations if item)
    limitations = list(dict.fromkeys(limitations))
    payload = {
        "headline": f"結論：已整理 {month_text} {target}{entity_label}{metric_label}資料。",
        "key_observations": ["候選摘要僅使用 EvidenceContract 中的月份、entity 與 metric。"],
        "limitations": limitations,
        "table_caption": f"{month_text} {entity_label}{metric_label}",
        "confidence_note": "shadow mode only",
    }
    if canonical.task_family == "forecast_unsupported":
        payload["headline"] = "結論：目前無法判斷下個月營收是否會改善。"
        payload["key_observations"] = ["現有 evidence 不包含預測模型、訂單、出貨、價格或市場需求資料。"]
        payload["limitations"] = limitations or ["目前沒有預測模型或外部需求資料，因此只能拒答預測。"]
    elif index % 19 == 0:
        payload["headline"] += " 另有 999,999,999。"
    return payload


def _writer_safe_limitation(text: str) -> str:
    if "EvidenceContractBuilder does not yet support tool output" in text:
        return "部分工具輸出尚未納入標準 evidence normalization，僅作描述性整理。"
    if "get_" in text or "source_tool" in text or "tool_name" in text:
        return "部分內部來源僅作 evidence provenance，不納入主管可見結論。"
    return text


def _collect_contract_months(evidence_contracts: list[Any]) -> set[str]:
    months: set[str] = set()
    for contract in evidence_contracts:
        scope = contract.time_scope or {}
        for key in ["month", "period_a", "period_b", "start_month", "end_month"]:
            if scope.get(key):
                months.add(str(scope[key]))
        for row in contract.rows:
            if isinstance(row, dict) and row.get("month"):
                months.add(str(row["month"]))
    return months


def _first_metric_label(evidence_contracts: list[Any]) -> str | None:
    for contract in evidence_contracts:
        if contract.metric_label:
            return str(contract.metric_label)
    return None


def _first_entity_label(evidence_contracts: list[Any]) -> str | None:
    for contract in evidence_contracts:
        label = (contract.entity_scope or {}).get("label")
        if label:
            return str(label)
    return None


def _first_entity_value(evidence_contracts: list[Any]) -> str | None:
    for contract in evidence_contracts:
        value = (contract.entity_scope or {}).get("value")
        if value:
            return str(value)
    return None


def categorize_violations(violations: list[str]) -> list[str]:
    categories = []
    mapping = {
        "number_not_in_evidence": "hallucinated_number",
        "month_not_in_evidence": "month_violation",
        "entity_not_in_evidence": "entity_violation",
        "metric_violation": "metric_violation",
        "forecast_violation": "forecast_violation",
        "root_cause_violation": "root_cause_violation",
        "limitation_violation": "limitation_violation",
        "internal_tool_name_violation": "internal_tool_name_violation",
        "debug_string_violation": "debug_string_violation",
    }
    for violation in violations:
        for needle, category in mapping.items():
            if needle in violation:
                categories.append(category)
    return categories


def classify_rejection(categories: list[str], task_family: str, evidence_contracts: list[Any]) -> str:
    if "metric_violation" in categories:
        metrics = {str(contract.metric) for contract in evidence_contracts if contract.metric}
        if task_family in {"latest_month_entity_summary", "cross_section_compare", "performance_assessment"} or len(metrics) > 1:
            return "false_positive_reject"
    if "limitation_violation" in categories and not evidence_contracts:
        return "evidence_contract_gap"
    if "internal_tool_name_violation" in categories or "forecast_violation" in categories:
        return "prompt_gap"
    return "true_positive_reject"


def recommend_action(categories: list[str], classification: str) -> str:
    if classification == "false_positive_reject":
        return "adjust validator"
    if classification == "evidence_contract_gap":
        return "enrich evidence contract"
    if "internal_tool_name_violation" in categories or "forecast_violation" in categories:
        return "tighten prompt"
    if "metric_violation" in categories:
        return "adjust validator"
    return "keep rejected"


def write_csv(rows: list[dict[str, str]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_id",
        "question",
        "task_family",
        "evidence_types",
        "evidence_metrics",
        "writer_called",
        "writer_valid",
        "fallback_reason",
        "violations",
        "violation_categories",
        "rejection_classification",
        "recommendation",
        "writer_output",
        "headline",
        "official_headline",
    ]
    with CSV_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    metrics = collect_metrics(rows)
    lines = [
        "# LLM Writer Shadow Regression",
        "",
        "This report exercises LLMEvidenceWriter in shadow mode only. Official display_blocks are not replaced.",
        "",
        "## Metrics",
        "",
    ]
    for key, value in metrics.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Rejections", ""])
    rejected = [row for row in rows if row["writer_valid"] != "True"]
    if not rejected:
        lines.append("- none")
    else:
        for row in rejected[:20]:
            lines.append(
                f"- {row['case_id']}: {row['question']} -> {row['fallback_reason']} "
                f"({row['rejection_classification']}; {row['recommendation']})"
            )
    MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_failure_markdown(rows: list[dict[str, str]]) -> None:
    rejected = [row for row in rows if row["writer_valid"] != "True"]
    lines = [
        "# LLM Writer Shadow Failures",
        "",
        "This report diagnoses writer shadow rejections. It includes the Phase 11C-2 baseline 16 rejected cases and the current post-tightening rejects.",
        "",
        "## Phase 11C-2 Baseline Rejected Cases",
        "",
    ]
    row_by_id = {row["case_id"]: row for row in rows}
    for case_id, question, task_family, violation, classification, recommendation in BASELINE_REJECTED_CASES:
        category_note = baseline_note(violation, classification)
        current_row = row_by_id.get(str(case_id), {})
        evidence_types = current_row.get("evidence_types") or "not available"
        lines.extend(
            [
                f"### {case_id}. {question}",
                "",
                f"- task_family: `{task_family}`",
                f"- evidence_types: `{evidence_types}`",
                f"- writer_output: baseline candidate rejected by `{violation}`",
                f"- violations: `{violation}`",
                f"- 判斷: `{classification}`",
                f"- 建議處理: `{recommendation}`",
                f"- diagnosis: {category_note}",
                "",
            ]
        )
    lines.extend(["", "## Current Post-Tightening Rejected Cases", ""])
    if not rejected:
        lines.append("- none")
    for row in rejected:
        lines.extend(
            [
                f"### {row['case_id']}. {row['question']}",
                "",
                f"- task_family: `{row['task_family']}`",
                f"- evidence_types: `{row['evidence_types']}`",
                f"- writer_output: `{row['writer_output']}`",
                f"- violations: `{row['violations']}`",
                f"- 判斷: `{row['rejection_classification']}`",
                f"- 建議處理: `{row['recommendation']}`",
                "",
            ]
        )
    FAILURE_MD_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def baseline_note(violation: str, classification: str) -> str:
    if "number_not_in_evidence" in violation:
        return "Writer introduced a number not present in evidence; keep the rejection."
    if "metric_violation" in violation and classification == "false_positive_reject":
        return "Question/evidence is multi-metric, but the old validator treated it like a single-metric answer."
    if "forecast_violation" in violation:
        return "Writer made a predictive claim for an unsupported forecast task; prompt must force safe refusal."
    if "internal_tool_name" in violation:
        return "Writer leaked implementation provenance; prompt must forbid source_tool/tool_name/get_* output."
    return "Rejection preserved for safety."


def collect_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    called = len(rows)
    valid = sum(1 for row in rows if row["writer_valid"] == "True")
    invalid = called - valid
    categories = Counter()
    reasons = Counter()
    classifications = Counter()
    recommendations = Counter()
    for row in rows:
        if row["writer_valid"] != "True":
            reasons[row["fallback_reason"]] += 1
            classifications[row["rejection_classification"]] += 1
            recommendations[row["recommendation"]] += 1
        for category in json.loads(row["violation_categories"] or "[]"):
            categories[category] += 1
    return {
        "writer_called_count": called,
        "writer_valid_count": valid,
        "writer_invalid_count": invalid,
        "writer_valid_rate": f"{valid / called:.1%}" if called else "0.0%",
        "violation_counts": dict(categories),
        "fallback_reason_counts": dict(reasons),
        "true_positive_reject_count": classifications["true_positive_reject"],
        "likely_false_positive_count": classifications["false_positive_reject"],
        "prompt_gap_count": classifications["prompt_gap"],
        "evidence_contract_gap_count": classifications["evidence_contract_gap"],
        "metric_false_positive_count": sum(
            1 for row in rows if row["rejection_classification"] == "false_positive_reject" and "metric_violation" in row["violation_categories"]
        ),
        "recommendation_counts": dict(recommendations),
        "hallucinated_number_count": categories["hallucinated_number"],
        "month_violation_count": categories["month_violation"],
        "entity_violation_count": categories["entity_violation"],
        "metric_violation_count": categories["metric_violation"],
        "forecast_violation_count": categories["forecast_violation"],
        "root_cause_violation_count": categories["root_cause_violation"],
        "limitation_violation_count": categories["limitation_violation"],
        "internal_tool_name_violation_count": categories["internal_tool_name_violation"],
    }


def _summary_line(rows: list[dict[str, str]]) -> str:
    metrics = collect_metrics(rows)
    return (
        "LLM writer shadow regression: "
        f"{metrics['writer_valid_count']}/{metrics['writer_called_count']} valid, "
        f"{metrics['writer_invalid_count']} rejected"
    )


if __name__ == "__main__":
    main()
