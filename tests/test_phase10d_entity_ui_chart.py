from __future__ import annotations

import unittest

from business_question_classifier import classify_business_question
from entity_labels import display_label_for_dimension, resolve_entity_value
from task_profile import build_task_profile
from tests.support import build_stubbed_assistant, get_context
from analysis_tools import AnalysisToolbox


class Phase10DEntityUiChartTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = get_context()
        cls.toolbox = AnalysisToolbox(cls.context, "test-phase10d")
        cls.assistant = build_stubbed_assistant("test-phase10d")

    def test_entity_label_mapping_and_synonyms(self) -> None:
        self.assertEqual(display_label_for_dimension("business_group"), "事業群")
        self.assertEqual(display_label_for_dimension("product_line_5"), "產品線")
        self.assertEqual(resolve_entity_value("通路方案", "business_group"), "3通路方案")
        self.assertEqual(resolve_entity_value("網通技鋼", "business_group"), "1網通+技鋼")
        self.assertEqual(resolve_entity_value("Server", "product_line_5"), "Server")

    def test_bu_synonym_normalizes_to_business_group_with_display_label(self) -> None:
        for question in [
            "請整理最新月份各事業群的營收與庫存重點",
            "請整理最新月份各新事業群的營收與庫存重點",
            "請整理最新月份各 BU 營收與庫存重點",
        ]:
            profile = build_task_profile(question, classify_business_question(question))
            self.assertEqual(profile.task_family, "latest_month_entity_summary")
            self.assertEqual(profile.target_entity["dimension"], "business_group")
            response = self.assistant.answer(question)
            headline = response["answer_contract"]["display_blocks"]["headline"]
            self.assertIn("事業群", headline)
            self.assertNotIn("新事業群", headline)

    def test_observe_options_are_canonical_and_all_dimensions_have_rows(self) -> None:
        options = self.toolbox.get_observation_options()
        self.assertEqual(
            options["row_dimensions"],
            [
                {"value": "month", "label": "月份"},
                {"value": "business_group", "label": "事業群"},
                {"value": "product_line_5", "label": "產品線"},
            ],
        )
        for dimension in ["month", "business_group", "product_line_5"]:
            table = self.toolbox.get_observation_table(
                {"row_dimension": dimension, "metric": "revenue", "compare_mode": "previous_period"}
            )
            self.assertTrue(table["rows"], dimension)

    def test_entity_month_metric_lookup_does_not_fallback_to_query(self) -> None:
        response = self.assistant.answer("列出通路方案 2026/2 最新營收")
        self.assertEqual(response["task_profile"]["task_family"], "metric_lookup")
        self.assertEqual(response["task_profile"]["target_entity"]["value"], "3通路方案")
        self.assertEqual(response["task_profile"]["time_scope"]["month"], "2026-02")
        self.assertIn("get_entity_metric_value", response["answer_plan"]["primary_tools"])
        headline = response["answer_contract"]["display_blocks"]["headline"]
        self.assertIn("2026-02 事業群 3通路方案", headline)
        self.assertNotIn("沒有足夠 primary evidence", headline)

    def test_explicit_month_pie_chart_preserves_month_type_and_dimension(self) -> None:
        response = self.assistant.answer("畫出 2025年 2 月 各事業群營收圓餅圖")
        headline = response["answer_contract"]["display_blocks"]["headline"]
        self.assertIn("2025-02", headline)
        self.assertIn("business_group_revenue_pie", headline)
        self.assertIn("圓餅圖", headline)
        self.assertNotIn("最新月份", headline)
        chart = next(
            item
            for result in response["domain_results"]
            for item in result.get("evidence", [])
            if isinstance(item, dict) and item.get("chart_key") == "business_group_revenue_pie"
        )
        self.assertEqual(chart["chart_type"], "pie")
        self.assertEqual(chart["filters"]["month"], "2025-02")


if __name__ == "__main__":
    unittest.main()
