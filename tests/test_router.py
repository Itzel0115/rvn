from __future__ import annotations

import unittest

from tests.support import build_stubbed_assistant


class RouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-router")

    def test_ranking_question_routes_to_sales(self) -> None:
        routing = self.assistant._plan_and_route("Which business group has the highest revenue?")
        self.assertEqual(routing.question_type, "ranking")
        self.assertEqual(routing.answer_strategy, "ranking")
        self.assertEqual(routing.domains, ["sales"])

    def test_trend_question_routes_to_sales(self) -> None:
        routing = self.assistant._plan_and_route("What is the revenue trend?")
        self.assertEqual(routing.question_type, "trend")
        self.assertEqual(routing.answer_strategy, "trend")
        self.assertEqual(routing.domains, ["sales"])

    def test_risk_question_routes_to_financial(self) -> None:
        routing = self.assistant._plan_and_route("What anomalies should I watch?")
        self.assertEqual(routing.question_type, "risk")
        self.assertEqual(routing.answer_strategy, "risk")
        self.assertEqual(routing.domains, ["financial"])

    def test_filter_extraction_routes_single_scope_query(self) -> None:
        routing = self.assistant._plan_and_route("What is revenue for GG-02 in 2024-08?")
        self.assertEqual(routing.domains, ["sales"])
        self.assertEqual(routing.filters.month, "2024-08")
        self.assertEqual(routing.filters.platform, "GG-02")

    def test_comparison_question_routes_to_financial(self) -> None:
        routing = self.assistant._plan_and_route("Compare GG-01 and GG-02 performance")
        self.assertEqual(routing.question_type, "comparison")
        self.assertEqual(routing.domains, ["financial"])

    def test_data_quality_question_routes_without_domains(self) -> None:
        routing = self.assistant._plan_and_route("What data coverage do we have by month?")
        self.assertEqual(routing.question_type, "data_quality")
        self.assertEqual(routing.domains, [])

    def test_chinese_chart_question_routes_to_chart(self) -> None:
        routing = self.assistant._plan_and_route("\u8acb\u5e6b\u6211\u756b\u71df\u6536\u8da8\u52e2\u5716\u3002")
        self.assertEqual(routing.question_type, "chart")
        self.assertEqual(routing.domains, ["chart"])

    def test_performance_weakness_question_routes_to_financial(self) -> None:
        routing = self.assistant._plan_and_route("請分析哪個平台表現較差")
        self.assertEqual(routing.question_type, "performance_weakness")
        self.assertEqual(routing.answer_strategy, "performance_weakness")
        self.assertEqual(routing.domains, ["financial"])
        self.assertEqual(routing.object_dimension, "platform")


if __name__ == "__main__":
    unittest.main()
