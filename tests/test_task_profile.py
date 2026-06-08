from __future__ import annotations

import unittest

from business_question_classifier import classify_business_question
from task_profile import build_task_profile


class TaskProfileTest(unittest.TestCase):
    def _profile(self, question: str):
        routing = classify_business_question(question)
        return build_task_profile(question, routing)

    def test_latest_month_business_group_summary_profile(self) -> None:
        profile = self._profile("請整理最新月份各事業群的營收與庫存重點")

        self.assertEqual(profile.task_family, "latest_month_entity_summary")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertTrue(profile.requires_table)

    def test_product_line_cross_section_profile(self) -> None:
        profile = self._profile("比較最新月份各產品線營收與庫存")

        self.assertEqual(profile.task_family, "cross_section_compare")
        self.assertEqual(profile.target_entity["dimension"], "product_line_5")

    def test_business_group_performance_profile(self) -> None:
        profile = self._profile("請分析哪個事業群表現較佳")

        self.assertEqual(profile.task_family, "performance_assessment")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.polarity, "best")

    def test_product_line_under_business_group_parent_profile(self) -> None:
        profile = self._profile("某事業群底下哪個產品線表現較差？")

        self.assertEqual(profile.target_entity["dimension"], "product_line_5")
        self.assertEqual(profile.parent_entity["dimension"], "business_group")
        self.assertEqual(profile.polarity, "worst")

    def test_legacy_platform_maps_to_business_group(self) -> None:
        profile = self._profile("請分析哪個平台表現較差")

        self.assertEqual(profile.target_entity["dimension"], "business_group")

    def test_business_group_revenue_ranking_profile(self) -> None:
        profile = self._profile("最新月份營收最高的事業群是誰？")

        self.assertEqual(profile.task_family, "entity_ranking")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.metrics, ["revenue_amount"])
        self.assertEqual(profile.polarity, "best")
        self.assertTrue(profile.requires_table)

    def test_product_line_inventory_ranking_profile(self) -> None:
        profile = self._profile("哪個產品線庫存最高？")

        self.assertEqual(profile.task_family, "entity_ranking")
        self.assertEqual(profile.target_entity["dimension"], "product_line_5")
        self.assertEqual(profile.metrics, ["inventory_amount"])

    def test_named_business_group_entity_time_series_profile(self) -> None:
        profile = self._profile("比較 3通路方案 各月營收")

        self.assertEqual(profile.task_family, "entity_time_series")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.target_entity["value"], "3通路方案")
        self.assertEqual(profile.metrics, ["revenue_amount"])
        self.assertEqual(profile.time_scope["mode"], "multi_month_series")

    def test_overall_trend_profile(self) -> None:
        profile = self._profile("總體營收趨勢如何？")

        self.assertEqual(profile.task_family, "overall_trend_analysis")
        self.assertEqual(profile.target_entity["dimension"], "overall")
        self.assertEqual(profile.metrics, ["revenue_amount"])
        self.assertEqual(profile.time_scope["mode"], "multi_month_series")

    def test_entity_trend_comparison_profile(self) -> None:
        profile = self._profile("各事業群近 6 個月營收趨勢")

        self.assertEqual(profile.task_family, "entity_trend_comparison")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.time_scope["mode"], "recent_n_months")
        self.assertEqual(profile.time_scope["recent_n"], 6)

    def test_metric_relationship_profile(self) -> None:
        profile = self._profile("有沒有營收下降但庫存上升的事業群？")

        self.assertEqual(profile.task_family, "metric_relationship_analysis")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertIn("revenue_amount", profile.metrics)
        self.assertIn("inventory_amount", profile.metrics)

    def test_contribution_profile_preserves_month_pair_semantics(self) -> None:
        profile = self._profile("2026-01 比 2025-12 成長主要來自哪個事業群？")

        self.assertEqual(profile.task_family, "contribution_analysis")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.time_scope["period_a"], "2025-12")
        self.assertEqual(profile.time_scope["period_b"], "2026-01")

    def test_forecast_questions_are_unsupported(self) -> None:
        profile = self._profile("下個月營收會不會改善？")

        self.assertEqual(profile.task_family, "forecast_unsupported")
        self.assertEqual(profile.time_scope["mode"], "future_period")

    def test_phase10f_period_pair_all_entity_table_profile(self) -> None:
        profile = self._profile("列出 2025/02 與 2025/03 產品線的庫存")

        self.assertEqual(profile.task_family, "entity_period_pair_table_lookup")
        self.assertEqual(profile.time_scope["period_a"], "2025-02")
        self.assertEqual(profile.time_scope["period_b"], "2025-03")
        self.assertEqual(profile.target_entity, {"dimension": "product_line_5", "value": None, "scope": "all"})
        self.assertEqual(profile.metrics, ["inventory_amount"])

    def test_phase10f_date_range_all_entity_table_profile(self) -> None:
        profile = self._profile("顯示 2025Q1 各事業群營收")

        self.assertEqual(profile.task_family, "entity_multi_month_table_lookup")
        self.assertEqual(profile.time_scope["mode"], "date_range")
        self.assertEqual(profile.time_scope["start_month"], "2025-01")
        self.assertEqual(profile.time_scope["end_month"], "2025-03")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.metrics, ["revenue_amount"])

    def test_phase10f_single_entity_period_pair_profile(self) -> None:
        profile = self._profile("比較 Server 2025/02 和 2025/03 庫存")

        self.assertEqual(profile.task_family, "entity_period_pair_metric_lookup")
        self.assertEqual(profile.target_entity, {"dimension": "product_line_5", "value": "Server", "scope": "single"})
        self.assertEqual(profile.time_scope["period_a"], "2025-02")
        self.assertEqual(profile.time_scope["period_b"], "2025-03")
        self.assertEqual(profile.metrics, ["inventory_amount"])

    def test_phase10f_parent_child_month_and_period_pair_profiles(self) -> None:
        month_profile = self._profile("列出 2025年3月 3通路方案底下各產品線庫存")
        pair_profile = self._profile("比較 2025/02 與 2025/03 3通路方案底下各產品線營收")

        self.assertEqual(month_profile.task_family, "entity_month_table_lookup")
        self.assertEqual(month_profile.parent_entity, {"dimension": "business_group", "value": "3通路方案"})
        self.assertEqual(pair_profile.task_family, "entity_period_pair_table_lookup")
        self.assertEqual(pair_profile.parent_entity, {"dimension": "business_group", "value": "3通路方案"})

    def test_phase10f_no_each_dimension_word_means_all_scope(self) -> None:
        profile = self._profile("列出 2025年3月產品線庫存")

        self.assertEqual(profile.task_family, "entity_month_table_lookup")
        self.assertEqual(profile.target_entity, {"dimension": "product_line_5", "value": None, "scope": "all"})


if __name__ == "__main__":
    unittest.main()
