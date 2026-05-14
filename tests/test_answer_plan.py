from __future__ import annotations

import unittest

from answer_plan import build_answer_plan
from business_question_classifier import classify_business_question
from task_profile import build_task_profile


class AnswerPlanTest(unittest.TestCase):
    def _plan(self, question: str):
        routing = classify_business_question(question)
        profile = build_task_profile(question, routing)
        return profile, build_answer_plan(profile, routing)

    def test_latest_month_entity_summary_uses_entity_tool(self) -> None:
        profile, plan = self._plan("請整理最新月份各新事業群的營收與庫存重點")

        self.assertEqual(profile.task_family, "latest_month_entity_summary")
        self.assertIn("get_entity_performance_snapshot", plan.primary_tools)
        self.assertTrue(plan.requires_table)

    def test_cross_section_compare_forbids_contribution_as_primary(self) -> None:
        _, plan = self._plan("比較最新月份各五大產品線營收與庫存")

        self.assertIn("get_entity_cross_section_comparison", plan.primary_tools)
        self.assertIn("get_contribution_analysis(revenue)", plan.forbidden_primary_tools)

    def test_performance_assessment_uses_proxy_tools(self) -> None:
        _, plan = self._plan("請分析哪個新事業群表現較差")

        self.assertIn("get_entity_performance_snapshot", plan.primary_tools)
        self.assertIn("get_inventory_turnover_proxy", plan.supporting_tools)
        self.assertIn("get_platform_ranking(inventory_amount)", plan.forbidden_primary_tools)

    def test_entity_ranking_uses_metric_ranking_tool(self) -> None:
        profile, plan = self._plan("哪個五大產品線營收最高？")

        self.assertEqual(profile.task_family, "ranking")
        self.assertEqual(profile.target_entity["dimension"], "product_line_5")
        self.assertEqual(plan.primary_tools, ["get_entity_metric_ranking"])
        self.assertTrue(plan.requires_table)


if __name__ == "__main__":
    unittest.main()
