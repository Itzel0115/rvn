from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.eval_llm_planner import evaluate_cases, summarize_metrics, write_csv, write_report


class LLMPlannerEvalTest(unittest.TestCase):
    def test_mock_eval_runs_and_produces_metrics(self) -> None:
        cases = [
            {
                "id": "case_001",
                "case_source": "router",
                "question": "What is the recent revenue MoM change?",
                "expected_question_type": "trend",
                "expected_domains": ["sales"],
                "expected_tools": ["get_yoy_mom_breakdown(revenue)"],
            },
            {
                "id": "case_002",
                "case_source": "answer",
                "question": "Will next month revenue improve?",
                "expected_answer_type": "unsupported",
                "expected_tools": [],
            },
        ]
        rows = evaluate_cases(cases, mock_mode=True)
        metrics = summarize_metrics(rows)

        self.assertEqual(len(rows), 2)
        self.assertGreaterEqual(metrics["planner_success_rate"], 0.5)
        self.assertEqual(metrics["forecast_safety_pass_rate"], 1.0)

    def test_invalid_tool_is_counted_as_rejection(self) -> None:
        cases = [
            {
                "id": "case_bad_tool",
                "case_source": "router",
                "question": "What is the revenue trend?",
                "expected_question_type": "trend",
                "expected_domains": ["sales"],
                "expected_tools": ["get_yoy_mom_breakdown(revenue)"],
            }
        ]
        rows = evaluate_cases(
            cases,
            mock_mode=True,
            mock_overrides={
                "case_bad_tool": {
                    "question_type": "trend",
                    "domains": ["sales"],
                    "tools": [{"tool_name": "invented_tool", "args": {}, "reason": "bad"}],
                    "answer_mode": "trend",
                    "requires_limitations": False,
                    "unsupported_reason": None,
                }
            },
        )
        metrics = summarize_metrics(rows)
        self.assertEqual(metrics["unknown_tool_rejection_count"], 1)
        self.assertEqual(rows[0]["rejection_category"], "unknown_tool")

    def test_invalid_args_are_counted(self) -> None:
        cases = [
            {
                "id": "case_bad_args",
                "case_source": "router",
                "question": "Which platform revenue declined the most?",
                "expected_question_type": "trend",
                "expected_domains": ["sales"],
                "expected_tools": ["get_yoy_mom_breakdown(revenue)"],
            }
        ]
        rows = evaluate_cases(
            cases,
            mock_mode=True,
            mock_overrides={
                "case_bad_args": {
                    "question_type": "trend",
                    "domains": ["sales"],
                    "tools": [
                        {
                            "tool_name": "get_yoy_mom_breakdown",
                            "args": {"metric": "revenue", "bad_arg": "oops"},
                            "reason": "bad args",
                        }
                    ],
                    "answer_mode": "trend",
                    "requires_limitations": False,
                    "unsupported_reason": None,
                }
            },
        )
        metrics = summarize_metrics(rows)
        self.assertEqual(metrics["invalid_args_rejection_count"], 1)
        self.assertEqual(rows[0]["rejection_category"], "invalid_args")

    def test_why_and_forecast_rules_are_measured(self) -> None:
        cases = [
            {
                "id": "case_why",
                "case_source": "answer",
                "question": "Why is revenue down?",
                "expected_answer_type": "diagnosis",
                "expected_tools": ["get_root_cause_candidates"],
            },
            {
                "id": "case_forecast",
                "case_source": "answer",
                "question": "Will next month revenue improve?",
                "expected_answer_type": "unsupported",
                "expected_tools": [],
            },
        ]
        rows = evaluate_cases(cases, mock_mode=True)
        metrics = summarize_metrics(rows)
        self.assertEqual(metrics["why_requires_limitation_pass_rate"], 1.0)
        self.assertEqual(metrics["forecast_safety_pass_rate"], 1.0)

    def test_report_files_can_be_written(self) -> None:
        rows = [
            {
                "case_source": "router",
                "id": "case_001",
                "question": "What is the revenue trend?",
                "deterministic_question_type": "trend",
                "deterministic_domains": ["sales"],
                "deterministic_tools": ["get_metric_table(revenue_trend)"],
                "expected_tools": ["get_yoy_mom_breakdown(revenue)"],
                "planner_success": True,
                "planning_failed": False,
                "planned_question_type": "trend",
                "planned_domains": ["sales"],
                "planned_tools": ["get_yoy_mom_breakdown(revenue)"],
                "tool_count": 1,
                "comparable_expected_tools": ["get_yoy_mom_breakdown(revenue)"],
                "overlap_tools": ["get_yoy_mom_breakdown(revenue)"],
                "extra_tools": [],
                "missing_tools": [],
                "overlap_ratio": 1.0,
                "fallback_reason": None,
                "rejection_category": None,
                "why_requires_limitation_pass": None,
                "forecast_safety_pass": None,
                "raw_planner_response": {"question_type": "trend"},
                "validated_plan": {"question_type": "trend"},
                "materialized_tools": ["get_yoy_mom_breakdown(revenue)"],
                "debug_trace": {"question": "What is the revenue trend?"},
            }
        ]
        metrics = summarize_metrics(rows)
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "planner.csv"
            report_path = Path(temp_dir) / "planner.md"
            write_csv(rows, csv_path)
            write_report(rows, metrics, report_path, mock_mode=True)
            self.assertTrue(csv_path.exists())
            self.assertTrue(report_path.exists())
            self.assertIn("planner_success_rate", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
