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
        profile, plan = self._plan("請整理最新月份各事業群的營收與庫存重點")

        self.assertEqual(profile.task_family, "latest_month_entity_summary")
        self.assertIn("get_entity_performance_snapshot", plan.primary_tools)
        self.assertTrue(plan.requires_table)

    def test_cross_section_compare_forbids_contribution_as_primary(self) -> None:
        _, plan = self._plan("比較最新月份各產品線營收與庫存")

        self.assertIn("get_entity_cross_section_comparison", plan.primary_tools)
        self.assertIn("get_contribution_analysis(revenue)", plan.forbidden_primary_tools)

    def test_performance_assessment_uses_proxy_tools(self) -> None:
        _, plan = self._plan("請分析哪個事業群表現較差")

        self.assertIn("get_entity_performance_snapshot", plan.primary_tools)
        self.assertIn("get_inventory_turnover_proxy", plan.supporting_tools)
        self.assertIn("get_platform_ranking(inventory_amount)", plan.forbidden_primary_tools)

    def test_entity_ranking_uses_metric_ranking_tool(self) -> None:
        profile, plan = self._plan("哪個產品線營收最高？")

        self.assertEqual(profile.task_family, "entity_ranking")
        self.assertEqual(profile.target_entity["dimension"], "product_line_5")
        self.assertEqual(plan.primary_tools, ["get_entity_metric_ranking"])
        self.assertTrue(plan.requires_table)

    def test_entity_time_series_uses_series_tool(self) -> None:
        profile, plan = self._plan("比較 3通路方案 各月營收")

        self.assertEqual(profile.task_family, "entity_time_series")
        self.assertEqual(plan.primary_tools, ["get_entity_time_series"])
        self.assertTrue(plan.requires_table)

    def test_overall_trend_uses_overall_series_tool(self) -> None:
        profile, plan = self._plan("總體營收趨勢如何？")

        self.assertEqual(profile.task_family, "overall_trend_analysis")
        self.assertEqual(plan.primary_tools, ["get_overall_time_series"])
        self.assertTrue(plan.requires_table)

    def test_contribution_analysis_uses_deterministic_contribution_tool(self) -> None:
        profile, plan = self._plan("2026-01 比 2025-12 成長主要來自哪個事業群？")

        self.assertEqual(profile.task_family, "contribution_analysis")
        self.assertEqual(plan.primary_tools, ["get_entity_contribution_analysis"])
        self.assertIn("get_yoy_mom_breakdown", plan.forbidden_primary_tools)

    def test_metric_relationship_uses_relationship_tool(self) -> None:
        profile, plan = self._plan("有沒有營收下降但庫存上升的事業群？")

        self.assertEqual(profile.task_family, "metric_relationship_analysis")
        self.assertEqual(plan.primary_tools, ["get_revenue_inventory_relationship"])
        self.assertIn("get_root_cause_candidates", plan.forbidden_primary_tools)

    def test_parent_child_drilldown_uses_snapshot_with_parent_filter(self) -> None:
        profile, plan = self._plan("3通路方案底下哪個產品線表現較差？")

        self.assertEqual(profile.task_family, "parent_child_drilldown")
        self.assertEqual(plan.primary_tools, ["get_entity_performance_snapshot"])
        self.assertTrue(plan.requires_table)


if __name__ == "__main__":
    unittest.main()
