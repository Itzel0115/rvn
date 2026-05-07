from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ollama_client import OllamaCallResult
from scripts.smoke_llm_live import (
    build_llm_client,
    build_unavailable_rows,
    classify_planner_result,
    classify_rewriter_result,
    run_live_smoke,
    summarize_rows,
    write_csv,
    write_report,
)


class _FakeLLMClient:
    def __init__(self, responses: list[OllamaCallResult]) -> None:
        self.responses = list(responses)

    def generate_json(self, **_: object) -> OllamaCallResult:
        if self.responses:
            return self.responses.pop(0)
        return OllamaCallResult(ok=False, text="", data=None, error="stub_exhausted")


class LLMLiveSmokeTest(unittest.TestCase):
    def test_timeout_does_not_count_as_validation_failure(self) -> None:
        rows = [
            {
                "question": "最近營收 MoM 變化如何？",
                "planner_attempted": True,
                "planner_success": False,
                "planned_tools": [],
                "planned_tool_count": 0,
                "planner_fallback_reason": "llm_planner_unavailable",
                "planner_failure_category": "llm_timeout",
                "planner_prompt_mode": "slim",
                "compact_registry_tool_count": 5,
                "prompt_char_count": 600,
                "deterministic_answer": "",
                "rewrite_attempted": True,
                "rewrite_success": False,
                "rewrite_validation_passed": False,
                "rewrite_fallback_reason": "llm_rewriter_unavailable",
                "rewriter_failure_category": "llm_timeout",
                "final_answer": "",
                "violations": ["HTTPConnectionPool read timed out"],
                "llm_available": True,
                "raw_planner_response": None,
                "raw_rewriter_response": None,
            }
        ]
        summary = summarize_rows(rows, llm_available=True)

        self.assertEqual(summary["timeout_count"], 2)
        self.assertEqual(summary["validation_failure_count"], 0)
        self.assertEqual(summary["rewrite_validation_failure_rate"], 0.0)

    def test_unavailable_report_can_be_written(self) -> None:
        rows = build_unavailable_rows(["下個月營收會不會改善？"], "llm_unavailable")
        summary = summarize_rows(rows, llm_available=False, warmup_success=False, warmup_failure_reason="llm_unavailable")

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "live.csv"
            report_path = Path(temp_dir) / "live.md"
            write_csv(rows, csv_path)
            write_report(
                rows,
                summary,
                report_path,
                unavailable_reason="llm_unavailable",
                live_requested=True,
                detected_llm_available=False,
            )

            self.assertTrue(csv_path.exists())
            self.assertTrue(report_path.exists())
            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("llm_available: False", report_text)
            self.assertIn("warmup_failure_reason: llm_unavailable", report_text)

    def test_warmup_failed_can_be_reported(self) -> None:
        rows = build_unavailable_rows(["請幫我畫營收趨勢。"], "warmup_failed")
        summary = summarize_rows(rows, llm_available=False, warmup_success=False, warmup_failure_reason="llm_timeout")

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "live.md"
            write_report(
                rows,
                summary,
                report_path,
                unavailable_reason="warmup_failed",
                live_requested=True,
                detected_llm_available=True,
                planner_only=True,
            )
            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("warmup_success: False", report_text)
            self.assertIn("warmup_failure_reason: llm_timeout", report_text)
            self.assertIn("unavailable_reason: warmup_failed", report_text)

    def test_planner_only_does_not_run_rewriter(self) -> None:
        planner_response = OllamaCallResult(
            ok=True,
            text='{"question_type":"ranking","domains":["sales"],"tools":[{"tool_name":"get_top_groups","args":{"metric":"revenue"},"reason":"rank"}],"answer_mode":"ranking","requires_limitations":false,"unsupported_reason":null}',
            data={
                "question_type": "ranking",
                "domains": ["sales"],
                "tools": [{"tool_name": "get_top_groups", "args": {"metric": "revenue"}, "reason": "rank"}],
                "answer_mode": "ranking",
                "requires_limitations": False,
                "unsupported_reason": None,
            },
        )
        rows = run_live_smoke(
            questions=["最新月份營收最高的新事業群是誰？"],
            llm_client=_FakeLLMClient([planner_response]),
            planner_only=True,
        )

        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["planner_attempted"])
        self.assertFalse(rows[0]["rewrite_attempted"])
        self.assertIsNone(rows[0]["rewriter_failure_category"])
        self.assertEqual(rows[0]["planned_tool_count"], 1)

    def test_timeout_seconds_can_be_passed_into_client(self) -> None:
        client = build_llm_client(request_id="test", timeout_seconds=30, model="demo-model")
        self.assertEqual(client.timeout_seconds, 30)
        self.assertEqual(client.model, "demo-model")

    def test_validation_categories_are_counted(self) -> None:
        rows = [
            {
                "question": "為什麼營收下降？",
                "planner_attempted": True,
                "planner_success": True,
                "planned_tools": ["get_root_cause_candidates"],
                "planned_tool_count": 1,
                "planner_fallback_reason": None,
                "planner_failure_category": None,
                "planner_prompt_mode": "slim",
                "compact_registry_tool_count": 6,
                "prompt_char_count": 700,
                "deterministic_answer": "目前尚無法直接判斷根本原因。",
                "rewrite_attempted": True,
                "rewrite_success": False,
                "rewrite_validation_passed": False,
                "rewrite_fallback_reason": "llm_rewriter_validation_failed",
                "rewriter_failure_category": "forbidden_phrase_violation",
                "final_answer": "目前尚無法直接判斷根本原因。",
                "violations": ["forbidden_phrases=['原因就是']"],
                "llm_available": True,
                "raw_planner_response": {},
                "raw_rewriter_response": {},
            }
        ]
        summary = summarize_rows(rows, llm_available=True)

        self.assertEqual(summary["validation_failure_count"], 1)
        self.assertEqual(summary["safety_violation_count"], 1)
        self.assertEqual(summary["forbidden_phrase_violation_count"], 1)

    def test_planner_invalid_json_is_separate_from_timeout(self) -> None:
        from llm_planner import LLMPlanningResult

        result = LLMPlanningResult(
            ok=False,
            planning_failed=True,
            error="Failed to parse JSON from Ollama response.",
            fallback_reason="llm_planner_invalid_output",
            rejection_category="invalid_json",
        )
        self.assertEqual(classify_planner_result(result), "invalid_json")

    def test_rewriter_timeout_is_separate_from_validation_failure(self) -> None:
        from llm_rewriter import RewriteResult

        result = RewriteResult(
            ok=False,
            rewritten_answer="fallback",
            validation_passed=False,
            fallback_reason="llm_rewriter_unavailable",
            violations=["HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)"],
        )
        self.assertEqual(classify_rewriter_result(result), "llm_timeout")

    def test_report_contains_prompt_diagnostics(self) -> None:
        rows = [
            {
                "question": "最近營收 MoM 變化如何？",
                "planner_attempted": True,
                "planner_success": False,
                "planned_tools": [],
                "planned_tool_count": 0,
                "planner_fallback_reason": "llm_planner_unavailable",
                "planner_failure_category": "llm_timeout",
                "planner_prompt_mode": "slim",
                "compact_registry_tool_count": 5,
                "prompt_char_count": 612,
                "deterministic_answer": "",
                "rewrite_attempted": False,
                "rewrite_success": False,
                "rewrite_validation_passed": False,
                "rewrite_fallback_reason": None,
                "rewriter_failure_category": None,
                "final_answer": "",
                "violations": [],
                "llm_available": True,
                "raw_planner_response": None,
                "raw_rewriter_response": None,
            }
        ]
        summary = summarize_rows(rows, llm_available=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "live.md"
            write_report(
                rows,
                summary,
                report_path,
                live_requested=True,
                detected_llm_available=True,
                planner_only=True,
                model="demo-model",
                timeout_seconds=30,
            )
            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("planner_prompt_mode: slim", report_text)
            self.assertIn("compact_registry_tool_count: 5", report_text)
            self.assertIn("prompt_char_count: 612", report_text)


if __name__ == "__main__":
    unittest.main()
