from __future__ import annotations

import unittest

from answer_plan import AnswerPlan
from canonical_task import CanonicalTaskProfile
from llm_planner import PlannedToolCall, ToolPlan
from plan_validator import PlanValidator


class PlanValidatorTest(unittest.TestCase):
    def _month_table_canonical(self) -> CanonicalTaskProfile:
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

    def _plan(self, task_family: str, tool_name: str, args: dict) -> ToolPlan:
        return ToolPlan(
            task_family=task_family,
            question_type="overview",
            domains=["financial"],
            tools=[PlannedToolCall(tool_name=tool_name, args=args, reason="test")],
            answer_mode="overview",
            requires_limitations=True,
        )

    def test_valid_entity_month_table_plan_passes(self) -> None:
        result = PlanValidator().validate(
            self._month_table_canonical(),
            self._plan(
                "entity_month_table_lookup",
                "get_entity_month_table",
                {"entity_dimension": "product_line_5", "metric": "inventory_amount", "month": "2025-03"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"]),
        )

        self.assertTrue(result["valid"], result)
        self.assertFalse(result["fallback_to_deterministic"])

    def test_wrong_month_rejected(self) -> None:
        result = PlanValidator().validate(
            self._month_table_canonical(),
            self._plan(
                "entity_month_table_lookup",
                "get_entity_month_table",
                {"entity_dimension": "product_line_5", "metric": "inventory_amount", "month": "2026-02"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"]),
        )

        self.assertFalse(result["valid"])
        self.assertIn("date_mismatch:month", result["violations"])

    def test_wrong_metric_rejected(self) -> None:
        result = PlanValidator().validate(
            self._month_table_canonical(),
            self._plan(
                "entity_month_table_lookup",
                "get_entity_month_table",
                {"entity_dimension": "product_line_5", "metric": "revenue_amount", "month": "2025-03"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"]),
        )

        self.assertFalse(result["valid"])
        self.assertIn("metric_mismatch", result["violations"])

    def test_wrong_task_tool_rejected(self) -> None:
        result = PlanValidator().validate(
            self._month_table_canonical(),
            self._plan(
                "entity_month_table_lookup",
                "get_entity_period_pair_comparison",
                {"entity_dimension": "product_line_5", "metric": "inventory_amount", "period_a": "2025-02", "period_b": "2025-03"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_month_table"]),
        )

        self.assertFalse(result["valid"])
        self.assertIn("tool_not_allowed_for_task:get_entity_period_pair_comparison", result["violations"])

    def test_chart_type_mismatch_rejected(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="畫出2025年2月各事業群營收圓餅圖",
            task_family="chart_request",
            time_scope={"mode": "single_month", "month": "2025-02", "period_a": None, "period_b": None, "recent_n": None},
            target_entity={"dimension": "business_group", "scope": "all", "value": None},
            parent_entity={"dimension": None, "value": None},
            metric="revenue_amount",
            chart_type="pie",
            answer_mode="chart",
        )
        result = PlanValidator().validate(
            canonical,
            self._plan(
                "chart_request",
                "get_chart_payload",
                {"chart_type": "bar", "month": "2025-02", "entity_dimension": "business_group", "metric": "revenue_amount"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_chart_payload"]),
        )

        self.assertFalse(result["valid"])
        self.assertIn("chart_type_mismatch", result["violations"])

    def test_entity_value_missing_rejected(self) -> None:
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
        result = PlanValidator().validate(
            canonical,
            self._plan(
                "entity_time_series",
                "get_entity_time_series",
                {"entity_dimension": "business_group", "metric": "revenue_amount"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_time_series"]),
        )

        self.assertFalse(result["valid"])
        self.assertIn("Planner omitted required args for get_entity_time_series: ['entity_value']", result["violations"])

    def test_forecast_unsupported_cannot_have_data_tool(self) -> None:
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
        result = PlanValidator().validate(
            canonical,
            self._plan(
                "forecast_unsupported",
                "get_entity_time_series",
                {"entity_dimension": "business_group", "entity_value": "3通路方案", "metric": "revenue_amount"},
            ),
            deterministic_answer_plan=AnswerPlan(),
        )

        self.assertFalse(result["valid"])
        self.assertIn("forecast_tool_violation", result["violations"])

    def test_overall_dimension_cannot_be_replaced_with_business_group(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="總體營收趨勢如何？",
            task_family="overall_trend_analysis",
            time_scope={"mode": "multi_month_series", "month": None, "period_a": None, "period_b": None, "recent_n": None},
            target_entity={"dimension": "overall", "scope": "overall", "value": None},
            parent_entity={"dimension": None, "value": None},
            metric="revenue_amount",
            chart_type=None,
            answer_mode="trend",
        )
        result = PlanValidator().validate(
            canonical,
            self._plan(
                "overall_trend_analysis",
                "get_overall_time_series",
                {"metric": "revenue_amount", "dimension": "business_group"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_overall_time_series"]),
        )

        self.assertFalse(result["valid"])
        self.assertTrue(any("unsupported args" in violation or violation == "entity_dimension_mismatch" for violation in result["violations"]))

    def test_phase10f_period_pair_table_plan_preserves_periods_parent_and_metric(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="比較 2025/02 與 2025/03 3通路方案底下各產品線營收",
            task_family="entity_period_pair_table_lookup",
            time_scope={"mode": "period_pair", "month": "2025-03", "period_a": "2025-02", "period_b": "2025-03", "recent_n": None},
            target_entity={"dimension": "product_line_5", "scope": "all", "value": None},
            parent_entity={"dimension": "business_group", "value": "3通路方案"},
            metric="revenue_amount",
            chart_type=None,
            answer_mode="overview",
        )
        result = PlanValidator().validate(
            canonical,
            self._plan(
                "entity_period_pair_table_lookup",
                "get_entity_period_pair_table",
                {
                    "entity_dimension": "product_line_5",
                    "metric": "revenue_amount",
                    "period_a": "2025-02",
                    "period_b": "2025-03",
                    "parent_filter": {"business_group": "3通路方案"},
                },
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_period_pair_table"]),
        )

        self.assertTrue(result["valid"], result)

    def test_phase10f_period_pair_table_rejects_wrong_metric_and_missing_parent(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="比較 2025/02 與 2025/03 3通路方案底下各產品線營收",
            task_family="entity_period_pair_table_lookup",
            time_scope={"mode": "period_pair", "month": "2025-03", "period_a": "2025-02", "period_b": "2025-03", "recent_n": None},
            target_entity={"dimension": "product_line_5", "scope": "all", "value": None},
            parent_entity={"dimension": "business_group", "value": "3通路方案"},
            metric="revenue_amount",
            chart_type=None,
            answer_mode="overview",
        )
        result = PlanValidator().validate(
            canonical,
            self._plan(
                "entity_period_pair_table_lookup",
                "get_entity_period_pair_table",
                {"entity_dimension": "product_line_5", "metric": "inventory_amount", "period_a": "2025-02", "period_b": "2025-03"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_period_pair_table"]),
        )

        self.assertFalse(result["valid"])
        self.assertIn("metric_mismatch", result["violations"])
        self.assertIn("parent_filter_missing", result["violations"])

    def test_phase10f_multi_month_table_rejects_changed_start_month(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="顯示 2025Q1 各事業群營收",
            task_family="entity_multi_month_table_lookup",
            time_scope={"mode": "date_range", "month": None, "period_a": None, "period_b": None, "start_month": "2025-01", "end_month": "2025-03", "recent_n": None},
            target_entity={"dimension": "business_group", "scope": "all", "value": None},
            parent_entity={"dimension": None, "value": None},
            metric="revenue_amount",
            chart_type=None,
            answer_mode="overview",
        )
        result = PlanValidator().validate(
            canonical,
            self._plan(
                "entity_multi_month_table_lookup",
                "get_entity_multi_month_table",
                {"entity_dimension": "business_group", "metric": "revenue_amount", "start_month": "2025-02", "end_month": "2025-03"},
            ),
            deterministic_answer_plan=AnswerPlan(primary_tools=["get_entity_multi_month_table"]),
        )

        self.assertFalse(result["valid"])
        self.assertIn("date_mismatch:start_month", result["violations"])


if __name__ == "__main__":
    unittest.main()
