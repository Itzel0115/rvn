from __future__ import annotations

import unittest

from analysis_tools import AnalysisToolbox
from business_question_classifier import classify_business_question
from task_profile import build_task_profile
from tests.support import build_stubbed_assistant, get_context


class Phase10ESingleMonthEntityTableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = get_context()
        cls.toolbox = AnalysisToolbox(cls.context, "test-phase10e")
        cls.assistant = build_stubbed_assistant("test-phase10e", use_llm_planner=False, use_llm_rewriter=False)

    def test_parser_routes_single_month_all_entity_table_lookup(self) -> None:
        cases = [
            ("列出2025年3月各產品線庫存資料", "entity_month_table_lookup", "product_line_5", "inventory_amount"),
            ("顯示2025/3各BU營收資料", "entity_month_table_lookup", "business_group", "revenue_amount"),
            ("查詢2025-03各產品線庫存QTY", "entity_month_table_lookup", "product_line_5", "inventory_qty"),
            ("看一下2025年3月各事業群資料", "entity_month_table_lookup", "business_group", "revenue_amount"),
        ]
        for question, task_family, dimension, metric in cases:
            with self.subTest(question=question):
                profile = build_task_profile(question, classify_business_question(question))
                self.assertEqual(profile.task_family, task_family)
                self.assertEqual(profile.target_entity, {"dimension": dimension, "value": None, "scope": "all"})
                self.assertEqual(profile.time_scope["month"], "2025-03")
                self.assertEqual(profile.metrics[0], metric)

    def test_parser_routes_single_month_all_entity_compare_to_cross_section(self) -> None:
        cases = [
            ("比較2025年3月各產品線庫存資料", "product_line_5", "inventory_amount"),
            ("比較2025年3月各事業群庫存資料", "business_group", "inventory_amount"),
            ("比較2025年3月各事業群營收資料", "business_group", "revenue_amount"),
        ]
        for question, dimension, metric in cases:
            with self.subTest(question=question):
                profile = build_task_profile(question, classify_business_question(question))
                self.assertEqual(profile.task_family, "cross_section_compare")
                self.assertEqual(profile.business_intent, "single_month_entity_cross_section")
                self.assertEqual(profile.target_entity, {"dimension": dimension, "value": None, "scope": "all"})
                self.assertEqual(profile.time_scope["month"], "2025-03")
                self.assertEqual(profile.metrics[0], metric)

    def test_entity_month_table_tool_preserves_inventory_only_rows(self) -> None:
        payload = self.toolbox.get_entity_month_table("product_line_5", "inventory_amount", "2025-03")
        self.assertEqual(payload["evidence_type"], "entity_month_table")
        self.assertEqual(payload["entity_label"], "產品線")
        self.assertEqual(payload["metric"], "inventory_amount")
        self.assertEqual(payload["month"], "2025-03")
        self.assertTrue(payload["rows"])
        self.assertEqual(payload["summary"]["row_count"], len(payload["rows"]))
        self.assertIn("data_presence_flag", payload["rows"][0])

    def test_single_month_table_answers_do_not_fallback_to_latest_or_period_pair(self) -> None:
        cases = [
            ("列出2025年3月各產品線庫存資料", "entity_month_table_lookup", "產品線", "庫存金額"),
            ("比較2025年3月各產品線庫存資料", "cross_section_compare", "產品線", "庫存金額"),
            ("比較2025年3月各事業群庫存資料", "cross_section_compare", "事業群", "庫存金額"),
            ("比較2025年3月各事業群營收資料", "cross_section_compare", "事業群", "營收"),
        ]
        for question, task_family, label, metric_label in cases:
            with self.subTest(question=question):
                response = self.assistant.answer(question)
                self.assertEqual(response["task_profile"]["task_family"], task_family)
                self.assertEqual(response["task_profile"]["time_scope"]["month"], "2025-03")
                self.assertIn("get_entity_month_table", response["answer_plan"]["primary_tools"])
                headline = response["answer_contract"]["display_blocks"]["headline"]
                self.assertIn("2025-03", headline)
                self.assertIn(label, headline)
                self.assertIn(metric_label, headline)
                self.assertNotIn("沒有足夠 primary evidence", headline)
                self.assertNotIn("2026-02", headline)
                self.assertNotIn("2026-01", headline)
                self.assertNotIn("營收相較", headline)
                self.assertTrue(response["answer_contract"]["display_blocks"].get("table"))


if __name__ == "__main__":
    unittest.main()
