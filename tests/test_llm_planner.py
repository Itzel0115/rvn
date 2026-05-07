from __future__ import annotations

import unittest

from llm_planner import (
    LLMToolPlanner,
    PROMPT_MODE_FULL,
    PROMPT_MODE_SLIM,
    allowed_tools_registry_payload,
    build_compact_tool_registry,
    select_planner_tool_subset,
)
from ollama_client import OllamaCallResult
from tests.support import build_stubbed_assistant


class FakePlannerLLM:
    def __init__(self, *, data=None, ok: bool = True, error: str | None = None) -> None:
        self._data = data
        self._ok = ok
        self._error = error

    def generate(self, **kwargs):
        return OllamaCallResult(ok=self._ok, text="", data=self._data, error=self._error)

    def generate_json(self, **kwargs):
        return OllamaCallResult(ok=self._ok, text="", data=self._data, error=self._error)


class LLMPlannerTest(unittest.TestCase):
    def test_valid_planner_json_can_parse(self) -> None:
        planner = LLMToolPlanner("test-llm-planner")
        llm = FakePlannerLLM(
            data={
                "question_type": "trend",
                "domains": ["sales"],
                "tools": [
                    {
                        "tool_name": "get_yoy_mom_breakdown",
                        "args": {"metric": "revenue", "dimension": "overall"},
                        "reason": "MoM",
                    }
                ],
                "answer_mode": "trend",
                "requires_limitations": False,
                "unsupported_reason": None,
            }
        )
        result = planner.plan_question("What is the recent revenue MoM change?", llm)
        self.assertTrue(result.ok)
        self.assertFalse(result.planning_failed)
        self.assertEqual(result.plan.question_type, "trend")
        self.assertEqual(result.plan.tools[0].tool_name, "get_yoy_mom_breakdown")

    def test_unknown_tool_is_rejected(self) -> None:
        planner = LLMToolPlanner("test-llm-planner")
        llm = FakePlannerLLM(
            data={
                "question_type": "trend",
                "domains": ["sales"],
                "tools": [{"tool_name": "invented_tool", "args": {}, "reason": "bad"}],
                "answer_mode": "trend",
                "requires_limitations": False,
                "unsupported_reason": None,
            }
        )
        result = planner.plan_question("What is the revenue trend?", llm)
        self.assertFalse(result.ok)
        self.assertTrue(result.planning_failed)
        self.assertIn("Unknown tool", result.error)
        self.assertEqual(result.rejection_category, "unknown_tool")
        self.assertEqual(result.trace["fallback_reason"], "llm_planner_invalid_output")

    def test_invalid_json_falls_back(self) -> None:
        planner = LLMToolPlanner("test-llm-planner")
        llm = FakePlannerLLM(ok=False, error="invalid json")
        result = planner.plan_question("What is the revenue trend?", llm)
        self.assertFalse(result.ok)
        self.assertTrue(result.planning_failed)
        self.assertEqual(result.fallback_reason, "llm_planner_unavailable")
        self.assertEqual(result.rejection_category, "invalid_json")

    def test_forecast_question_does_not_allow_forecasting_tools(self) -> None:
        planner = LLMToolPlanner("test-llm-planner")
        llm = FakePlannerLLM(
            data={
                "question_type": "unsupported",
                "domains": [],
                "tools": [
                    {"tool_name": "get_data_coverage", "args": {}, "reason": "coverage"},
                ],
                "answer_mode": "unsupported",
                "requires_limitations": True,
                "unsupported_reason": "Forecasting is out of scope.",
            }
        )
        result = planner.plan_question("Will next month revenue improve?", llm)
        self.assertTrue(result.ok)
        self.assertTrue(all(call.tool_name != "forecast" for call in result.plan.tools))

    def test_why_question_requires_limitations_true(self) -> None:
        planner = LLMToolPlanner("test-llm-planner")
        llm = FakePlannerLLM(
            data={
                "question_type": "diagnosis",
                "domains": ["sales", "financial"],
                "tools": [
                    {
                        "tool_name": "get_root_cause_candidates",
                        "args": {"metric": "revenue"},
                        "reason": "Need candidate observations only.",
                    }
                ],
                "answer_mode": "diagnosis",
                "requires_limitations": False,
                "unsupported_reason": None,
            }
        )
        result = planner.plan_question("Why is revenue down?", llm)
        self.assertFalse(result.ok)
        self.assertIn("requires_limitations=true", result.error)

    def test_deterministic_path_default_is_unchanged(self) -> None:
        assistant = build_stubbed_assistant("test-default-planner")
        self.assertFalse(assistant.use_llm_planner)
        response = assistant.answer("Which business group has the highest revenue?")
        self.assertEqual(response["answer_contract"]["answer_type"], "ranking")
        self.assertNotIn("planning_source", response["routing"])

    def test_allowed_tool_registry_contains_expected_tools(self) -> None:
        registry = allowed_tools_registry_payload()
        self.assertIn("get_root_cause_candidates", registry)
        self.assertIn("get_yoy_mom_breakdown", registry)
        self.assertIn("get_data_coverage", registry)

    def test_slim_prompt_is_shorter_than_full_prompt(self) -> None:
        slim = LLMToolPlanner("test-slim", prompt_mode=PROMPT_MODE_SLIM)
        full = LLMToolPlanner("test-full", prompt_mode=PROMPT_MODE_FULL)
        slim_prompt, slim_meta = slim._build_system_prompt("最近營收 MoM 變化如何？")
        full_prompt, full_meta = full._build_system_prompt("最近營收 MoM 變化如何？")
        self.assertLess(len(slim_prompt), len(full_prompt))
        self.assertEqual(slim_meta["planner_prompt_mode"], PROMPT_MODE_SLIM)
        self.assertEqual(full_meta["planner_prompt_mode"], PROMPT_MODE_FULL)

    def test_chart_subset_contains_only_chart_style_tools(self) -> None:
        subset = select_planner_tool_subset("請幫我畫營收趨勢。")
        self.assertEqual(subset, ["get_chart_payload", "get_chart_table", "get_data_coverage"])

    def test_why_subset_includes_root_cause_candidates(self) -> None:
        subset = select_planner_tool_subset("為什麼營收下降？")
        self.assertIn("get_root_cause_candidates", subset)

    def test_forecast_subset_contains_only_safe_coverage_tools(self) -> None:
        subset = select_planner_tool_subset("下個月營收會不會改善？")
        self.assertEqual(set(subset), {"get_data_coverage", "get_mapping_summary", "get_tool_capability_matrix"})

    def test_compact_registry_for_chart_is_small(self) -> None:
        lines = build_compact_tool_registry("請幫我畫營收趨勢。")
        self.assertEqual(len(lines), 3)
        self.assertTrue(all("get_chart_" in line or "get_data_coverage" in line for line in lines))

    def test_validation_still_rejects_invalid_args(self) -> None:
        planner = LLMToolPlanner("test-llm-planner")
        llm = FakePlannerLLM(
            data={
                "question_type": "trend",
                "domains": ["sales"],
                "tools": [
                    {
                        "tool_name": "get_yoy_mom_breakdown",
                        "args": {"metric": "revenue", "bad": "x"},
                        "reason": "MoM",
                    }
                ],
                "answer_mode": "trend",
                "requires_limitations": False,
                "unsupported_reason": None,
            }
        )
        result = planner.plan_question("What is the recent revenue MoM change?", llm)
        self.assertFalse(result.ok)
        self.assertEqual(result.rejection_category, "invalid_args")


if __name__ == "__main__":
    unittest.main()
