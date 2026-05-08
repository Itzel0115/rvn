from __future__ import annotations

import unittest

from task_profile import build_task_profile
from tests.support import build_stubbed_assistant


class TaskProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-task-profile")

    def _profile_for(self, question: str):
        routing = self.assistant._plan_and_route(question)
        return build_task_profile(question, routing)

    def test_cross_section_compare_platform_revenue_inventory(self) -> None:
        profile = self._profile_for("比較 8 月各平台營收與庫存")

        self.assertEqual(profile.task_family, "cross_section_compare")
        self.assertEqual(profile.target_entity["dimension"], "platform")
        self.assertIn("revenue", profile.metrics)
        self.assertIn("inventory_amount", profile.metrics)
        self.assertIn("inventory_qty", profile.metrics)
        self.assertIn("revenue_inventory_ratio", profile.metrics)
        self.assertEqual(profile.time_scope["mode"], "single_month")
        self.assertEqual(profile.time_scope["month"], "2024-08")
        self.assertEqual(profile.comparison_axis["axis"], "entity")
        self.assertEqual(profile.answer_style, "table_first")

    def test_platform_performance_assessment_best(self) -> None:
        profile = self._profile_for("請分析哪個平台表現較佳")

        self.assertEqual(profile.task_family, "performance_assessment")
        self.assertEqual(profile.target_entity["dimension"], "platform")
        self.assertEqual(profile.polarity, "best")
        self.assertIn("inventory_turnover_proxy", profile.metrics)
        self.assertIn("anomaly", profile.metrics)
        self.assertEqual(profile.answer_style, "conclusion_first")

    def test_platform_performance_assessment_worst(self) -> None:
        profile = self._profile_for("請分析哪個平台表現較差")

        self.assertEqual(profile.task_family, "performance_assessment")
        self.assertEqual(profile.polarity, "worst")

    def test_time_compare_contribution(self) -> None:
        profile = self._profile_for("8 月相較 7 月營收變化主要由誰貢獻")

        self.assertEqual(profile.task_family, "time_compare")
        self.assertEqual(profile.comparison_axis["axis"], "time")
        self.assertEqual(profile.answer_style, "evidence_first")


    def test_latest_month_platform_summary_profile(self) -> None:
        profile = self._profile_for("\u8acb\u6574\u7406\u6700\u65b0\u6708\u4efd\u5404\u5e73\u53f0\u7684\u71df\u6536\u8207\u5eab\u5b58\u91cd\u9ede")

        self.assertEqual(profile.task_family, "latest_month_platform_summary")
        self.assertEqual(profile.target_entity["dimension"], "platform")
        self.assertEqual(profile.time_scope["mode"], "latest_month")
        self.assertEqual(profile.answer_style, "executive_summary_with_table")
        self.assertTrue(profile.requires_table)
        self.assertIn("health_score", profile.metrics)

    def test_period_pair_compare_profile_extracts_two_months(self) -> None:
        profile = self._profile_for("2024\u5e742\u6708\u4ee5\u53ca2024\u5e747\u6708\u71df\u6536\u6709\u751a\u9ebc\u5340\u5225\uff1f")

        self.assertEqual(profile.task_family, "period_pair_compare")
        self.assertEqual(profile.time_scope["mode"], "explicit_period_pair")
        self.assertEqual(profile.time_scope["period_a"], "2024-02")
        self.assertEqual(profile.time_scope["period_b"], "2024-07")
        self.assertEqual(profile.comparison_axis["axis"], "time")
        self.assertTrue(profile.requires_table)

    def test_forecast_unsupported_profile(self) -> None:
        profile = self._profile_for("\u4e0b\u500b\u6708\u71df\u6536\u6703\u4e0d\u6703\u6539\u5584\uff1f")

        self.assertEqual(profile.task_family, "forecast_unsupported")
        self.assertEqual(profile.business_intent, "forecast_unsupported")
        self.assertTrue(profile.requires_limitations)
        self.assertFalse(profile.requires_table)


if __name__ == "__main__":
    unittest.main()
