from __future__ import annotations

import unittest

from tests.support import build_stubbed_assistant


class AnswerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-answer-contract", use_llm_planner=False, use_llm_rewriter=False)

    def test_latest_month_business_group_summary_uses_entity_scorecard_table(self) -> None:
        response = self.assistant.answer("請整理最新月份各新事業群的營收與庫存重點")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "latest_month_entity_summary")
        self.assertIn("get_entity_performance_snapshot", contract["tools_used"])
        self.assertIn("新事業群", contract["display_blocks"]["headline"])
        self.assertTrue(contract["display_blocks"]["table"]["rows"])
        self.assertNotIn("GG-01", contract["answer"])
        self.assertNotIn("GG-02", contract["answer"])

    def test_product_line_comparison_uses_product_line_wording(self) -> None:
        response = self.assistant.answer("比較最新月份各五大產品線營收與庫存")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["target_entity"]["dimension"], "product_line_5")
        self.assertEqual(contract["answer_type"], "comparison")
        self.assertIn("五大產品線", contract["display_blocks"]["headline"])
        self.assertTrue(contract["display_blocks"]["table"]["rows"])

    def test_period_pair_compare_uses_entity_period_tool(self) -> None:
        response = self.assistant.answer("2026年1月以及2026年2月營收有什麼區別？")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "period_pair_compare")
        self.assertIn("get_entity_period_pair_comparison(revenue)", contract["tools_used"])
        self.assertIn("2026-01", contract["answer"])
        self.assertIn("2026-02", contract["answer"])

    def test_data_quality_contract_includes_real_quality_report(self) -> None:
        response = self.assistant.answer("資料涵蓋哪些月份？")
        contract = response["answer_contract"]

        self.assertEqual(contract["answer_type"], "data_quality")
        quality = contract["data_scope"]["real_data_quality_report"]
        self.assertEqual(quality["latest_common_month"], "2026-02")
        self.assertGreater(quality["both_rows"], 0)

    def test_forecast_remains_unsupported(self) -> None:
        response = self.assistant.answer("下個月營收會不會改善？")

        self.assertEqual(response["answer_contract"]["answer_type"], "unsupported")
        self.assertFalse(response["answer_contract"]["tools_used"])

    def test_entity_ranking_answer_has_concrete_headline_and_table(self) -> None:
        response = self.assistant.answer("最新月份營收最高的新事業群是誰？")
        contract = response["answer_contract"]
        headline = contract["display_blocks"]["headline"]

        self.assertEqual(response["task_profile"]["task_family"], "ranking")
        self.assertIn("get_entity_metric_ranking", contract["tools_used"])
        self.assertIn("新事業群", headline)
        self.assertIn("2026-02", headline)
        self.assertNotIn("沒有足夠", headline)
        self.assertTrue(contract["display_blocks"]["table"]["rows"])


if __name__ == "__main__":
    unittest.main()
