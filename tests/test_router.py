from __future__ import annotations

import unittest

from tests.support import build_stubbed_assistant


class RouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-router")

    def test_business_group_summary_routes_to_financial(self) -> None:
        routing = self.assistant._plan_and_route("請整理最新月份各事業群的營收與庫存重點")

        self.assertEqual(routing.question_type, "summary")
        self.assertEqual(routing.answer_strategy, "latest_month_entity_summary")
        self.assertEqual(routing.domains, ["financial"])
        self.assertEqual(routing.object_dimension, "business_group")

    def test_product_line_comparison_routes_to_financial(self) -> None:
        routing = self.assistant._plan_and_route("比較最新月份各產品線營收與庫存")

        self.assertEqual(routing.question_type, "comparison")
        self.assertEqual(routing.domains, ["financial"])
        self.assertEqual(routing.object_dimension, "product_line_5")

    def test_period_pair_routes_to_sales(self) -> None:
        routing = self.assistant._plan_and_route("2026年1月以及2026年2月營收有什麼區別？")

        self.assertEqual(routing.question_type, "comparison")
        self.assertEqual(routing.answer_strategy, "period_pair_compare")
        self.assertEqual(routing.domains, ["sales"])

    def test_data_quality_question_routes_without_domains(self) -> None:
        routing = self.assistant._plan_and_route("資料涵蓋哪些月份？")
        self.assertEqual(routing.question_type, "data_quality")
        self.assertEqual(routing.domains, [])

    def test_chinese_chart_question_routes_to_chart(self) -> None:
        routing = self.assistant._plan_and_route("請幫我畫營收趨勢圖。")
        self.assertEqual(routing.question_type, "chart")
        self.assertEqual(routing.domains, ["chart"])

    def test_legacy_platform_routes_as_business_group(self) -> None:
        routing = self.assistant._plan_and_route("請分析哪個平台表現較差")

        self.assertEqual(routing.question_type, "performance_weakness")
        self.assertEqual(routing.answer_strategy, "performance_weakness")
        self.assertEqual(routing.object_dimension, "business_group")


if __name__ == "__main__":
    unittest.main()
