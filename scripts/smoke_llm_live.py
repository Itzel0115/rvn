from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS
from llm_planner import FORECAST_HINTS, WHY_HINTS, LLMPlanningResult, LLMToolPlanner
from llm_rewriter import LLMAnswerRewriter, RewriteResult, build_rewrite_request
from multi_agent import MultiAgentAssistant
from ollama_client import OllamaCallResult, OllamaClient
from tests.support import get_context


BASE_DIR = PROJECT_ROOT / "eval"
RESULTS_FILE = BASE_DIR / "llm_live_smoke_results.csv"
REPORT_FILE = BASE_DIR / "llm_live_smoke_report.md"

SMOKE_QUESTIONS = [
    "最新月份營收最高的新事業群是誰？",
    "最近營收 MoM 變化如何？",
    "本月營收變化主要由誰貢獻？",
    "哪個平台庫存效率最低？",
    "為什麼營收下降？",
    "下個月營收會不會改善？",
    "請幫我畫營收趨勢。",
    "幫我整理本月營運重點。",
]

ROOT_CAUSE_FORBIDDEN_HINTS = [
    "原因就是",
    "一定是",
    "已確認根本原因",
    "confirmed root cause",
]


def _contains_hint(question: str, hints: list[str]) -> bool:
    lowered = question.lower()
    return any(token in lowered or token in question for token in hints)


def is_forecast_question(question: str) -> bool:
    return _contains_hint(question, FORECAST_HINTS)


def is_why_question(question: str) -> bool:
    return _contains_hint(question, WHY_HINTS)


def build_llm_client(
    *,
    request_id: str,
    timeout_seconds: int,
    model: str | None = None,
) -> OllamaClient:
    return OllamaClient(
        request_id=request_id,
        timeout_seconds=max(timeout_seconds, 1),
        model=model or OLLAMA_MODEL,
    )


def detect_live_llm_endpoint(
    llm_client: OllamaClient,
    *,
    timeout_seconds: int = 5,
) -> tuple[bool, str | None]:
    try:
        response = requests.get(
            f"{llm_client.base_url}/api/tags",
            timeout=max(timeout_seconds, 1),
        )
        response.raise_for_status()
        return True, None
    except Exception as exc:
        return False, classify_transport_error(str(exc))


def warmup_llm_client(llm_client: OllamaClient) -> OllamaCallResult:
    return llm_client.generate_json(
        system_prompt="Return JSON only.",
        user_prompt='Return {"status":"ok"} exactly.',
        temperature=0.0,
    )


def classify_transport_error(error_text: str | None) -> str:
    lowered = (error_text or "").lower()
    if "timed out" in lowered or "read timeout" in lowered:
        return "llm_timeout"
    if "failed to parse json" in lowered or "invalid json" in lowered:
        return "invalid_json"
    return "llm_unavailable"


def classify_planner_result(result: LLMPlanningResult) -> str | None:
    if result.ok:
        return None
    category = result.rejection_category
    if category == "invalid_json":
        return "invalid_json"
    if category in {"invalid_args", "invalid_metric", "invalid_dimension", "invalid_plan", "missing_limitations", "forecast_safety"}:
        return "planner_validation_failed"
    return classify_transport_error(result.error)


def classify_rewriter_result(result: RewriteResult) -> str | None:
    if result.ok:
        return None
    if result.fallback_reason == "llm_rewriter_validation_failed":
        if any("forbidden_phrases" in violation for violation in result.violations):
            return "forbidden_phrase_violation"
        if any("new_numbers" in violation for violation in result.violations):
            return "new_number_violation"
        if any("missing_limitation" in violation for violation in result.violations):
            return "limitation_violation"
        return "rewriter_validation_failed"
    joined = " ".join(str(item) for item in result.violations)
    return classify_transport_error(joined or result.fallback_reason)


def build_unavailable_rows(
    questions: list[str],
    reason: str,
    *,
    planner_only: bool = False,
    rewriter_only: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    planner_attempted = not rewriter_only
    rewrite_attempted = not planner_only
    for question in questions:
        rows.append(
            {
                "question": question,
                "planner_attempted": planner_attempted,
                "planner_success": False,
                "planned_tools": [],
                "planned_tool_count": 0,
                "planner_fallback_reason": reason if planner_attempted else None,
                "planner_failure_category": reason if planner_attempted else None,
                "planner_prompt_mode": None,
                "compact_registry_tool_count": 0,
                "prompt_char_count": 0,
                "deterministic_answer": "",
                "rewrite_attempted": rewrite_attempted,
                "rewrite_success": False,
                "rewrite_validation_passed": False,
                "rewrite_fallback_reason": reason if rewrite_attempted else None,
                "rewriter_failure_category": reason if rewrite_attempted else None,
                "final_answer": "",
                "violations": [],
                "llm_available": False,
                "raw_planner_response": None,
                "raw_rewriter_response": None,
            }
        )
    return rows


def run_live_smoke(
    *,
    questions: list[str] | None = None,
    llm_client: OllamaClient | None = None,
    planner_only: bool = False,
    rewriter_only: bool = False,
) -> list[dict[str, Any]]:
    questions = questions or list(SMOKE_QUESTIONS)
    llm_client = llm_client or build_llm_client(
        request_id="llm-live-smoke",
        timeout_seconds=OLLAMA_TIMEOUT_SECONDS,
    )
    planner = LLMToolPlanner("llm-live-smoke")
    rewriter = LLMAnswerRewriter("llm-live-smoke")
    deterministic_assistant = MultiAgentAssistant(get_context(), "llm-live-smoke-deterministic")

    rows: list[dict[str, Any]] = []
    for question in questions:
        planner_result: LLMPlanningResult | None = None
        planned_tools: list[str] = []
        planner_failure_category: str | None = None
        planner_fallback_reason: str | None = None

        if not rewriter_only:
            planner_result = planner.plan_question(question, llm_client)
            if planner_result.ok and planner_result.plan:
                planned_tools = planner.materialize_tools(planner_result.plan)
            else:
                planner_failure_category = classify_planner_result(planner_result)
                planner_fallback_reason = planner_result.fallback_reason or planner_failure_category

        response = deterministic_assistant.answer(question)
        contract = response["answer_contract"]
        deterministic_answer = contract["answer"]

        rewrite_result: RewriteResult | None = None
        rewrite_failure_category: str | None = None
        rewrite_fallback_reason: str | None = None
        final_answer = deterministic_answer
        violations: list[str] = []

        if not planner_only:
            rewrite_request = build_rewrite_request(question, contract)
            rewrite_result = rewriter.rewrite(rewrite_request, llm_client)
            final_answer = rewrite_result.rewritten_answer if rewrite_result.ok else deterministic_answer
            violations = list(rewrite_result.violations)
            if not rewrite_result.ok:
                rewrite_failure_category = classify_rewriter_result(rewrite_result)
                rewrite_fallback_reason = rewrite_result.fallback_reason or rewrite_failure_category

        rows.append(
            {
                "question": question,
                "planner_attempted": not rewriter_only,
                "planner_success": bool(planner_result and planner_result.ok),
                "planned_tools": planned_tools,
                "planned_tool_count": len(planned_tools),
                "planner_fallback_reason": planner_fallback_reason,
                "planner_failure_category": planner_failure_category,
                "planner_prompt_mode": planner_result.trace.get("planner_prompt_mode") if planner_result and planner_result.trace else None,
                "compact_registry_tool_count": planner_result.trace.get("compact_registry_tool_count") if planner_result and planner_result.trace else 0,
                "prompt_char_count": planner_result.trace.get("prompt_char_count") if planner_result and planner_result.trace else 0,
                "deterministic_answer": deterministic_answer,
                "rewrite_attempted": not planner_only,
                "rewrite_success": bool(rewrite_result and rewrite_result.ok),
                "rewrite_validation_passed": bool(rewrite_result and rewrite_result.validation_passed),
                "rewrite_fallback_reason": rewrite_fallback_reason,
                "rewriter_failure_category": rewrite_failure_category,
                "final_answer": final_answer,
                "violations": violations,
                "llm_available": True,
                "raw_planner_response": planner_result.raw_response if planner_result else None,
                "raw_rewriter_response": rewrite_result.raw_response if rewrite_result else None,
            }
        )

    return rows


def summarize_rows(
    rows: list[dict[str, Any]],
    *,
    llm_available: bool,
    warmup_success: bool | None = None,
    warmup_failure_reason: str | None = None,
) -> dict[str, Any]:
    planner_attempted_rows = [row for row in rows if row.get("planner_attempted")]
    rewrite_attempted_rows = [row for row in rows if row.get("rewrite_attempted")]

    planner_success_count = sum(1 for row in planner_attempted_rows if row["planner_success"])
    planner_fallback_count = sum(1 for row in planner_attempted_rows if row["planner_fallback_reason"])
    rewrite_success_count = sum(1 for row in rewrite_attempted_rows if row["rewrite_success"])

    validation_categories = {
        "rewriter_validation_failed",
        "forbidden_phrase_violation",
        "new_number_violation",
        "limitation_violation",
    }
    rewrite_validation_failure_count = sum(
        1 for row in rewrite_attempted_rows if row.get("rewriter_failure_category") in validation_categories
    )
    validation_failure_count = rewrite_validation_failure_count + sum(
        1 for row in planner_attempted_rows if row.get("planner_failure_category") == "planner_validation_failed"
    )

    new_number_violation_count = sum(
        1 for row in rewrite_attempted_rows if row.get("rewriter_failure_category") == "new_number_violation"
    )
    forbidden_phrase_violation_count = sum(
        1 for row in rewrite_attempted_rows if row.get("rewriter_failure_category") == "forbidden_phrase_violation"
    )
    limitation_violation_count = sum(
        1 for row in rewrite_attempted_rows if row.get("rewriter_failure_category") == "limitation_violation"
    )
    safety_violation_count = (
        new_number_violation_count
        + forbidden_phrase_violation_count
        + limitation_violation_count
    )

    planner_timeout_count = sum(
        1 for row in planner_attempted_rows if row.get("planner_failure_category") == "llm_timeout"
    )
    rewriter_timeout_count = sum(
        1 for row in rewrite_attempted_rows if row.get("rewriter_failure_category") == "llm_timeout"
    )
    timeout_count = planner_timeout_count + rewriter_timeout_count

    forecast_rows = [row for row in rows if is_forecast_question(row["question"])]
    forecast_safety_pass = all(
        (not row["planner_success"])
        or (not row["planned_tools"])
        or all("forecast" not in tool.lower() for tool in row["planned_tools"])
        for row in forecast_rows
    )

    root_cause_claim_blocked = forbidden_phrase_violation_count if any(
        any(hint in " ".join(row.get("violations", [])) for hint in ROOT_CAUSE_FORBIDDEN_HINTS)
        for row in rewrite_attempted_rows
    ) else 0

    first_planner_row = next((row for row in planner_attempted_rows if row.get("planner_prompt_mode")), None)

    planner_total = len(planner_attempted_rows) or 1
    rewrite_total = len(rewrite_attempted_rows) or 1
    return {
        "llm_available": llm_available,
        "warmup_success": warmup_success,
        "warmup_failure_reason": warmup_failure_reason,
        "planner_prompt_mode": first_planner_row.get("planner_prompt_mode") if first_planner_row else None,
        "compact_registry_tool_count": first_planner_row.get("compact_registry_tool_count", 0) if first_planner_row else 0,
        "prompt_char_count": first_planner_row.get("prompt_char_count", 0) if first_planner_row else 0,
        "planner_success_rate": planner_success_count / planner_total if planner_attempted_rows else 0.0,
        "planner_fallback_rate": planner_fallback_count / planner_total if planner_attempted_rows else 0.0,
        "rewrite_success_rate": rewrite_success_count / rewrite_total if rewrite_attempted_rows else 0.0,
        "rewrite_validation_failure_rate": rewrite_validation_failure_count / rewrite_total if rewrite_attempted_rows else 0.0,
        "timeout_count": timeout_count,
        "planner_timeout_count": planner_timeout_count,
        "rewriter_timeout_count": rewriter_timeout_count,
        "validation_failure_count": validation_failure_count,
        "safety_violation_count": safety_violation_count,
        "new_number_violation_count": new_number_violation_count,
        "forbidden_phrase_violation_count": forbidden_phrase_violation_count,
        "limitation_violation_count": limitation_violation_count,
        "forecast_safety_pass": forecast_safety_pass,
        "root_cause_claim_blocked": root_cause_claim_blocked,
    }


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    fieldnames = [
        "question",
        "planner_attempted",
        "planner_success",
        "planned_tools",
        "planned_tool_count",
        "planner_fallback_reason",
        "planner_failure_category",
        "planner_prompt_mode",
        "compact_registry_tool_count",
        "prompt_char_count",
        "deterministic_answer",
        "rewrite_attempted",
        "rewrite_success",
        "rewrite_validation_passed",
        "rewrite_fallback_reason",
        "rewriter_failure_category",
        "final_answer",
        "violations",
        "llm_available",
        "raw_planner_response",
        "raw_rewriter_response",
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


def write_report(
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    output_path: Path,
    *,
    unavailable_reason: str | None = None,
    live_requested: bool = False,
    detected_llm_available: bool | None = None,
    planner_only: bool = False,
    rewriter_only: bool = False,
    model: str | None = None,
    timeout_seconds: int | None = None,
) -> None:
    lines = [
        "# Live LLM Smoke Report",
        "",
        f"- live_requested: {live_requested}",
        f"- planner_only: {planner_only}",
        f"- rewriter_only: {rewriter_only}",
        f"- detected_llm_available: {detected_llm_available}",
        f"- llm_available: {summary['llm_available']}",
        f"- model: {model}",
        f"- timeout_seconds: {timeout_seconds}",
        f"- warmup_success: {summary['warmup_success']}",
        f"- warmup_failure_reason: {summary['warmup_failure_reason']}",
        f"- planner_prompt_mode: {summary['planner_prompt_mode']}",
        f"- compact_registry_tool_count: {summary['compact_registry_tool_count']}",
        f"- prompt_char_count: {summary['prompt_char_count']}",
    ]
    if unavailable_reason:
        lines.append(f"- unavailable_reason: {unavailable_reason}")

    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            f"- planner_success_rate: {summary['planner_success_rate']:.2%}",
            f"- planner_fallback_rate: {summary['planner_fallback_rate']:.2%}",
            f"- rewrite_success_rate: {summary['rewrite_success_rate']:.2%}",
            f"- rewrite_validation_failure_rate: {summary['rewrite_validation_failure_rate']:.2%}",
            f"- timeout_count: {summary['timeout_count']}",
            f"- planner_timeout_count: {summary['planner_timeout_count']}",
            f"- rewriter_timeout_count: {summary['rewriter_timeout_count']}",
            f"- validation_failure_count: {summary['validation_failure_count']}",
            f"- safety_violation_count: {summary['safety_violation_count']}",
            f"- new_number_violation_count: {summary['new_number_violation_count']}",
            f"- forbidden_phrase_violation_count: {summary['forbidden_phrase_violation_count']}",
            f"- limitation_violation_count: {summary['limitation_violation_count']}",
            f"- forecast_safety_pass: {summary['forecast_safety_pass']}",
            f"- root_cause_claim_blocked: {summary['root_cause_claim_blocked']}",
            "",
            "## Case Summary",
            "",
        ]
    )

    for row in rows:
        lines.append(f"- `{row['question']}`")
        lines.append(
            f"  planner_attempted={row['planner_attempted']} planner_success={row['planner_success']} planner_failure_category={row['planner_failure_category']} planner_prompt_mode={row['planner_prompt_mode']} prompt_char_count={row['prompt_char_count']} planned_tool_count={row['planned_tool_count']} planned_tools={row['planned_tools']}"
        )
        lines.append(
            f"  rewrite_attempted={row['rewrite_attempted']} rewrite_success={row['rewrite_success']} rewrite_validation_passed={row['rewrite_validation_passed']} rewriter_failure_category={row['rewriter_failure_category']} violations={row['violations']}"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This smoke test checks live planner and rewriter behavior only.",
            "- Timeout and transport failures are tracked separately from validator failures.",
            "- Final product enablement still depends on separate rollout and validation decisions.",
            "- The `/api/ask` response contract is unchanged by this smoke test.",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run live LLM smoke tests for planner and rewriter.")
    parser.add_argument("--live", action="store_true", help="Attempt live LLM smoke with real planner and rewriter calls.")
    parser.add_argument("--require-llm", action="store_true", help="Fail with a non-zero exit code when no live LLM is available.")
    parser.add_argument("--timeout-seconds", type=int, default=max(120, OLLAMA_TIMEOUT_SECONDS), help="Timeout for each live LLM call during smoke testing.")
    parser.add_argument("--planner-only", action="store_true", help="Run only the live planner smoke path.")
    parser.add_argument("--rewriter-only", action="store_true", help="Run only the live rewriter smoke path.")
    parser.add_argument("--warmup", action="store_true", help="Run one simple JSON warmup request before the smoke loop.")
    parser.add_argument("--model", default=None, help="Optional model override for the live smoke run.")
    args = parser.parse_args(argv)

    if args.planner_only and args.rewriter_only:
        parser.error("--planner-only and --rewriter-only cannot be used together.")

    llm_client = build_llm_client(
        request_id="llm-live-smoke",
        timeout_seconds=args.timeout_seconds,
        model=args.model,
    )
    detected_llm_available, detected_reason = detect_live_llm_endpoint(llm_client)
    unavailable_reason: str | None = None
    warmup_success: bool | None = None
    warmup_failure_reason: str | None = None

    if not args.live:
        unavailable_reason = "live_mode_disabled"
        rows = build_unavailable_rows(
            SMOKE_QUESTIONS,
            unavailable_reason,
            planner_only=args.planner_only,
            rewriter_only=args.rewriter_only,
        )
        llm_available = False
    elif not detected_llm_available:
        unavailable_reason = detected_reason or "llm_unavailable"
        rows = build_unavailable_rows(
            SMOKE_QUESTIONS,
            unavailable_reason,
            planner_only=args.planner_only,
            rewriter_only=args.rewriter_only,
        )
        llm_available = False
    else:
        if args.warmup:
            warmup_result = warmup_llm_client(llm_client)
            warmup_success = bool(warmup_result.ok and warmup_result.data and warmup_result.data.get("status") == "ok")
            if not warmup_success:
                warmup_failure_reason = classify_transport_error(warmup_result.error or warmup_result.text)
                unavailable_reason = "warmup_failed"
                rows = build_unavailable_rows(
                    SMOKE_QUESTIONS,
                    unavailable_reason,
                    planner_only=args.planner_only,
                    rewriter_only=args.rewriter_only,
                )
                llm_available = False
            else:
                rows = run_live_smoke(
                    llm_client=llm_client,
                    planner_only=args.planner_only,
                    rewriter_only=args.rewriter_only,
                )
                llm_available = True
        else:
            rows = run_live_smoke(
                llm_client=llm_client,
                planner_only=args.planner_only,
                rewriter_only=args.rewriter_only,
            )
            llm_available = True

    summary = summarize_rows(
        rows,
        llm_available=llm_available,
        warmup_success=warmup_success,
        warmup_failure_reason=warmup_failure_reason,
    )
    write_csv(rows, RESULTS_FILE)
    write_report(
        rows,
        summary,
        REPORT_FILE,
        unavailable_reason=unavailable_reason,
        live_requested=args.live,
        detected_llm_available=detected_llm_available,
        planner_only=args.planner_only,
        rewriter_only=args.rewriter_only,
        model=llm_client.model,
        timeout_seconds=llm_client.timeout_seconds,
    )
    print(f"Wrote {RESULTS_FILE}")
    print(f"Wrote {REPORT_FILE}")
    if args.require_llm and (not detected_llm_available or unavailable_reason == "warmup_failed"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
