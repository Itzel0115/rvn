from __future__ import annotations

import unittest

from business_question_classifier import classify_business_question
from task_profile import build_task_profile


class TaskProfileTest(unittest.TestCase):
    def _profile(self, question: str):
        routing = classify_business_question(question)
        return build_task_profile(question, routing)

    def test_latest_month_business_group_summary_profile(self) -> None:
        profile = self._profile("請整理最新月份各新事業群的營收與庫存重點")

        self.assertEqual(profile.task_family, "latest_month_entity_summary")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertTrue(profile.requires_table)

    def test_product_line_cross_section_profile(self) -> None:
        profile = self._profile("比較最新月份各五大產品線營收與庫存")

        self.assertEqual(profile.task_family, "cross_section_compare")
        self.assertEqual(profile.target_entity["dimension"], "product_line_5")

    def test_business_group_performance_profile(self) -> None:
        profile = self._profile("請分析哪個新事業群表現較佳")

        self.assertEqual(profile.task_family, "performance_assessment")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.polarity, "best")

    def test_product_line_under_business_group_parent_profile(self) -> None:
        profile = self._profile("某新事業群底下哪個產品線表現較差？")

        self.assertEqual(profile.target_entity["dimension"], "product_line_5")
        self.assertEqual(profile.parent_entity["dimension"], "business_group")
        self.assertEqual(profile.polarity, "worst")

    def test_legacy_platform_maps_to_business_group(self) -> None:
        profile = self._profile("請分析哪個平台表現較差")

        self.assertEqual(profile.target_entity["dimension"], "business_group")

    def test_business_group_revenue_ranking_profile(self) -> None:
        profile = self._profile("最新月份營收最高的新事業群是誰？")

        self.assertEqual(profile.task_family, "ranking")
        self.assertEqual(profile.target_entity["dimension"], "business_group")
        self.assertEqual(profile.metrics, ["revenue_amount"])
        self.assertEqual(profile.polarity, "best")
        self.assertTrue(profile.requires_table)

    def test_product_line_inventory_ranking_profile(self) -> None:
        profile = self._profile("哪個五大產品線庫存最高？")

        self.assertEqual(profile.task_family, "ranking")
        self.assertEqual(profile.target_entity["dimension"], "product_line_5")
        self.assertEqual(profile.metrics, ["inventory_amount"])


if __name__ == "__main__":
    unittest.main()
