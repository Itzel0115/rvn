from __future__ import annotations

import unittest

from tests.support import build_stubbed_assistant


class AnswerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-answer-contract", use_llm_planner=False, use_llm_rewriter=False)

    def test_latest_month_business_group_summary_uses_entity_scorecard_table(self) -> None:
        response = self.assistant.answer("請整理最新月份各事業群的營收與庫存重點")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "latest_month_entity_summary")
        self.assertIn("get_entity_performance_snapshot", contract["tools_used"])
        self.assertIn("事業群", contract["display_blocks"]["headline"])
        self.assertTrue(contract["display_blocks"]["table"]["rows"])
        self.assertNotIn("GG-01", contract["answer"])
        self.assertNotIn("GG-02", contract["answer"])

    def test_product_line_comparison_uses_product_line_wording(self) -> None:
        response = self.assistant.answer("比較最新月份各產品線營收與庫存")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["target_entity"]["dimension"], "product_line_5")
        self.assertEqual(contract["answer_type"], "comparison")
        self.assertIn("產品線", contract["display_blocks"]["headline"])
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
        response = self.assistant.answer("最新月份營收最高的事業群是誰？")
        contract = response["answer_contract"]
        headline = contract["display_blocks"]["headline"]

        self.assertEqual(response["task_profile"]["task_family"], "entity_ranking")
        self.assertIn("get_entity_metric_ranking", contract["tools_used"])
        self.assertIn("事業群", headline)
        self.assertIn("2026-02", headline)
        self.assertNotIn("沒有足夠", headline)
        self.assertTrue(contract["display_blocks"]["table"]["rows"])

    def test_overall_trend_answer_uses_overall_series_tool(self) -> None:
        response = self.assistant.answer("總體營收趨勢如何？")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "overall_trend_analysis")
        self.assertEqual(contract["answer_type"], "overall_trend_analysis")
        self.assertEqual(contract["tools_used"], ["get_overall_time_series"])
        self.assertIn("整體營收", contract["display_blocks"]["headline"])
        self.assertTrue(contract["display_blocks"]["table"]["rows"])

    def test_named_entity_time_series_answer_preserves_entity_and_months(self) -> None:
        response = self.assistant.answer("比較 3通路方案 各月營收")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "entity_time_series")
        self.assertEqual(contract["answer_type"], "entity_time_series")
        self.assertEqual(contract["tools_used"], ["get_entity_time_series"])
        self.assertIn("3通路方案", contract["display_blocks"]["headline"])
        self.assertIn("2025-01", contract["display_blocks"]["headline"])
        self.assertIn("2026-02", contract["display_blocks"]["headline"])

    def test_contribution_answer_preserves_explicit_period_pair(self) -> None:
        response = self.assistant.answer("2026-01 比 2025-12 成長主要來自哪個事業群？")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "contribution_analysis")
        self.assertEqual(contract["answer_type"], "contribution_analysis")
        self.assertEqual(contract["tools_used"], ["get_entity_contribution_analysis"])
        self.assertIn("2026-01", contract["display_blocks"]["headline"])
        self.assertIn("2025-12", contract["display_blocks"]["headline"])
        self.assertIn("3通路方案", contract["display_blocks"]["headline"])

    def test_named_entity_chart_answer_preserves_chart_filter_in_headline(self) -> None:
        response = self.assistant.answer("畫 3通路方案各月營收趨勢")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "chart_request")
        self.assertEqual(contract["answer_type"], "chart")
        self.assertIn("3通路方案", contract["display_blocks"]["headline"])
        self.assertIn("entity_time_series_line", contract["display_blocks"]["headline"])

    def test_phase10f_period_pair_all_entity_answer_uses_table_tool(self) -> None:
        response = self.assistant.answer("列出 2025/02 與 2025/03 產品線的庫存")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "entity_period_pair_table_lookup")
        self.assertEqual(contract["tools_used"], ["get_entity_period_pair_table"])
        self.assertIn("2025-02", contract["display_blocks"]["headline"])
        self.assertIn("2025-03", contract["display_blocks"]["headline"])
        self.assertIn("庫存金額", contract["display_blocks"]["headline"])
        self.assertNotIn("2026-02", contract["answer"])
        self.assertNotIn("營收相較", contract["answer"])
        self.assertTrue(contract["display_blocks"]["table"]["rows"])

    def test_phase10f_date_range_answer_uses_multi_month_table_tool(self) -> None:
        response = self.assistant.answer("顯示 2025Q1 各事業群營收")
        contract = response["answer_contract"]

        self.assertEqual(response["task_profile"]["task_family"], "entity_multi_month_table_lookup")
        self.assertEqual(contract["tools_used"], ["get_entity_multi_month_table"])
        self.assertIn("2025-01", contract["display_blocks"]["headline"])
        self.assertIn("2025-03", contract["display_blocks"]["headline"])
        self.assertTrue(contract["display_blocks"]["table"]["rows"])

    def test_management_risk_answer_selects_two_entities_with_counter_and_next_action(self) -> None:
        response = self.assistant.answer("請找出最近月份最需要管理層關注的兩個事業群。請先比較所有事業群，並同時考慮營收趨勢、庫存金額、庫存數量與異常訊號，再說明選出這兩個事業群的支持證據、可能反證、資料限制，以及建議管理層下一步優先確認什麼。")
        contract = response["answer_contract"]
        blocks = contract["display_blocks"]

        self.assertEqual(response["task_profile"]["task_requirements"]["requested_top_n"], 2)
        self.assertTrue(response["task_profile"]["task_requirements"]["requires_recommendation"])
        self.assertIn("第一優先事業群", blocks["headline"])
        self.assertIn("第二優先事業群", blocks["headline"])
        self.assertEqual(len(blocks["table"]["rows"]), 2)
        self.assertTrue(all(row.get("entity_value") for row in blocks["table"]["rows"]))
        answer = contract["answer"]
        self.assertIn("支持證據", answer)
        self.assertIn("可能反證", answer)
        self.assertIn("管理層下一步", answer)
        self.assertNotIn("已覆蓋指標", answer)
        self.assertNotIn("風險訊號訊號", answer)
        self.assertNotIn("health_score 為 deterministic", answer)


if __name__ == "__main__":
    unittest.main()
