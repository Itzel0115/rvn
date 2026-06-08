from __future__ import annotations

import unittest

from answer_plan import AnswerPlan
from canonical_task import CanonicalTaskProfile
from llm_planner import LLMToolPlanner
from ollama_client import OllamaCallResult


class FakePlannerLLM:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.system_prompt = ""
        self.user_prompt = ""

    def generate_json(self, **kwargs):
        self.system_prompt = str(kwargs.get("system_prompt") or "")
        self.user_prompt = str(kwargs.get("user_prompt") or "")
        return OllamaCallResult(ok=True, text="", data=self.data, error=None)


class LLMPlannerCanonicalTest(unittest.TestCase):
    def _canonical(self) -> CanonicalTaskProfile:
        return CanonicalTaskProfile(
            question_text="列出2025年3月各產品線庫存資料",
            task_family="entity_month_table_lookup",
            time_scope={"mode": "single_month", "month": "2025-03", "period_a": None, "period_b": None, "recent_n": None},
            target_entity={"dimension": "product_line_5", "scope": "all", "value": None},
            parent_entity={"dimension": None, "value": None},
            metric="inventory_amount",
            chart_type=None,
            answer_mode="entity_month_table_lookup",
        )

    def test_canonical_candidate_schema_parses_to_tool_plan(self) -> None:
        llm = FakePlannerLLM(
            {
                "planner_intent": "use canonical month table",
                "tool_calls": [
                    {
                        "tool_name": "get_entity_month_table",
                        "args": {"entity_dimension": "product_line_5", "metric": "inventory_amount", "month": "2025-03"},
                        "reason": "canonical table lookup",
                    }
                ],
                "answer_mode": "overview",
                "needs_table": True,
                "needs_chart": False,
                "fallback_required": False,
            }
        )

        result = LLMToolPlanner("test-canonical-planner").plan_question(
            "列出2025年3月各產品線庫存資料",
            llm,
            canonical_task_profile=self._canonical(),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"], requires_table=True),
        )

        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.plan.task_family, "entity_month_table_lookup")
        self.assertEqual(result.plan.tools[0].tool_name, "get_entity_month_table")
        self.assertTrue(result.plan.needs_table)
        self.assertIn("canonical_task_profile", llm.user_prompt)
        self.assertIn("allowed_tools", llm.system_prompt)

    def test_canonical_prompt_restricts_tools_by_task_family(self) -> None:
        llm = FakePlannerLLM(
            {
                "planner_intent": "bad tool",
                "tool_calls": [
                    {
                        "tool_name": "get_entity_period_pair_comparison",
                        "args": {"entity_dimension": "product_line_5", "metric": "inventory_amount", "period_a": "2025-02", "period_b": "2025-03"},
                        "reason": "bad",
                    }
                ],
                "answer_mode": "comparison",
                "needs_table": True,
                "needs_chart": False,
                "fallback_required": False,
            }
        )

        result = LLMToolPlanner("test-canonical-planner").plan_question(
            "列出2025年3月各產品線庫存資料",
            llm,
            canonical_task_profile=self._canonical(),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"], requires_table=True),
        )

        self.assertFalse(result.ok)
        self.assertIn("outside allowed baseline", result.error or "")

    def test_table_lookup_alias_normalized_to_canonical_task_family(self) -> None:
        llm = FakePlannerLLM(
            {
                "task_family": "table_lookup",
                "question_type": "table_lookup",
                "domains": ["financial"],
                "tools": [
                    {
                        "tool_name": "get_entity_month_table",
                        "args": {"entity_dimension": "product_line_5", "metric": "inventory_amount", "month": "2025-03"},
                        "reason": "legacy alias",
                    }
                ],
                "answer_mode": "table_lookup",
                "requires_limitations": True,
            }
        )

        result = LLMToolPlanner("test-canonical-planner").plan_question(
            "列出2025年3月各產品線庫存資料",
            llm,
            canonical_task_profile=self._canonical(),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"], requires_table=True),
        )

        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.plan.task_family, "entity_month_table_lookup")
        self.assertEqual(result.plan.question_type, "overview")
        self.assertEqual(result.plan.answer_mode, "overview")

    def test_value_alias_normalized_to_metric_lookup(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="查詢 Server 2026-02 營收",
            task_family="metric_lookup",
            time_scope={"mode": "single_month", "month": "2026-02", "period_a": None, "period_b": None, "recent_n": None},
            target_entity={"dimension": "product_line_5", "scope": "single", "value": "Server"},
            parent_entity={"dimension": None, "value": None},
            metric="revenue_amount",
            chart_type=None,
            answer_mode="overview",
        )
        llm = FakePlannerLLM(
            {
                "task_family": "value",
                "question_type": "value",
                "domains": ["financial"],
                "tools": [
                    {
                        "tool_name": "get_entity_metric_value",
                        "args": {"entity_dimension": "product line", "entity_value": "Server", "metric": "revenue", "month": "2026-02"},
                        "reason": "legacy value alias",
                    }
                ],
                "answer_mode": "value",
                "requires_limitations": True,
            }
        )

        result = LLMToolPlanner("test-canonical-planner").plan_question(
            "查詢 Server 2026-02 營收",
            llm,
            canonical_task_profile=canonical,
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_metric_value"]),
        )

        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.plan.task_family, "metric_lookup")
        self.assertEqual(result.plan.question_type, "overview")
        self.assertEqual(result.plan.tools[0].args["entity_dimension"], "product_line_5")
        self.assertEqual(result.plan.tools[0].args["metric"], "revenue_amount")

    def test_forecast_alias_normalized_to_unsupported_without_tools(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="下個月營收會不會改善？",
            task_family="forecast_unsupported",
            time_scope={"mode": "future_period", "month": None, "period_a": None, "period_b": None, "recent_n": None},
            target_entity={"dimension": "overall", "scope": "overall", "value": None},
            parent_entity={"dimension": None, "value": None},
            metric="revenue_amount",
            chart_type=None,
            answer_mode="unsupported",
        )
        llm = FakePlannerLLM(
            {
                "task_family": "forecast",
                "question_type": "forecast",
                "domains": [],
                "tools": [],
                "answer_mode": "forecast",
                "requires_limitations": True,
                "fallback_required": False,
            }
        )

        result = LLMToolPlanner("test-canonical-planner").plan_question(
            "下個月營收會不會改善？",
            llm,
            canonical_task_profile=canonical,
            deterministic_answer_plan=AnswerPlan(),
        )

        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.plan.task_family, "forecast_unsupported")
        self.assertEqual(result.plan.question_type, "unsupported")
        self.assertEqual(result.plan.answer_mode, "unsupported")
        self.assertEqual(result.plan.tools, [])

    def test_entity_dimension_aliases_normalized(self) -> None:
        for alias in ["group", "BU", "新事業群"]:
            with self.subTest(alias=alias):
                canonical = CanonicalTaskProfile(
                    question_text="比較 3通路方案 各月營收",
                    task_family="entity_time_series",
                    time_scope={"mode": "multi_month_series", "month": None, "period_a": None, "period_b": None, "recent_n": None},
                    target_entity={"dimension": "business_group", "scope": "single", "value": "3通路方案"},
                    parent_entity={"dimension": None, "value": None},
                    metric="revenue_amount",
                    chart_type=None,
                    answer_mode="trend",
                )
                llm = FakePlannerLLM(
                    {
                        "planner_intent": "entity series",
                        "tool_calls": [
                            {
                                "tool_name": "get_entity_time_series",
                                "args": {"dimension": alias, "entity_value": "3通路方案", "metric": "revenue_amount"},
                                "reason": "dimension alias",
                            }
                        ],
                        "answer_mode": "trend",
                    }
                )

                result = LLMToolPlanner("test-canonical-planner").plan_question(
                    "比較 3通路方案 各月營收",
                    llm,
                    canonical_task_profile=canonical,
                    deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_time_series"]),
                )

                self.assertTrue(result.ok, result.error)
                self.assertEqual(result.plan.tools[0].args["entity_dimension"], "business_group")
                self.assertNotIn("dimension", result.plan.tools[0].args)

    def test_product_line_aliases_normalized(self) -> None:
        for alias in ["product line", "五大產品線"]:
            with self.subTest(alias=alias):
                llm = FakePlannerLLM(
                    {
                        "planner_intent": "month table",
                        "tool_calls": [
                            {
                                "tool_name": "get_entity_month_table",
                                "args": {"entity_dimension": alias, "metric": "inventory_amount", "month": "2025-03"},
                                "reason": "dimension alias",
                            }
                        ],
                        "answer_mode": "overview",
                        "needs_table": True,
                    }
                )

                result = LLMToolPlanner("test-canonical-planner").plan_question(
                    "列出2025年3月各產品線庫存資料",
                    llm,
                    canonical_task_profile=self._canonical(),
                    deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"], requires_table=True),
                )

                self.assertTrue(result.ok, result.error)
                self.assertEqual(result.plan.tools[0].args["entity_dimension"], "product_line_5")

    def test_period_pair_revenue_amount_normalized_to_tool_metric(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="比較 2025 年 12 月與 2026 年 1 月營收差別",
            task_family="period_pair_compare",
            time_scope={"mode": "period_pair", "month": "2026-01", "period_a": "2025-12", "period_b": "2026-01", "recent_n": None},
            target_entity={"dimension": "business_group", "scope": "all", "value": None},
            parent_entity={"dimension": None, "value": None},
            metric="revenue_amount",
            chart_type=None,
            answer_mode="comparison",
        )
        llm = FakePlannerLLM(
            {
                "planner_intent": "period pair",
                "tool_calls": [
                    {
                        "tool_name": "get_period_pair_metric_comparison",
                        "args": {"metric": "revenue_amount", "period_a": "2025-12", "period_b": "2026-01", "dimension": "business_group"},
                        "reason": "canonical metric alias",
                    }
                ],
                "answer_mode": "comparison",
            }
        )

        result = LLMToolPlanner("test-canonical-planner").plan_question(
            "比較 2025 年 12 月與 2026 年 1 月營收差別",
            llm,
            canonical_task_profile=canonical,
            deterministic_answer_plan=AnswerPlan(
                primary_tools=["get_entity_period_pair_comparison"],
                supporting_tools=["get_period_pair_metric_comparison"],
            ),
        )

        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.plan.tools[0].args["metric"], "revenue")


if __name__ == "__main__":
    unittest.main()
