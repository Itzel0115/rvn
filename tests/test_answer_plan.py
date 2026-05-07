from __future__ import annotations

import unittest

from answer_plan import build_answer_plan
from task_profile import build_task_profile
from tests.support import build_stubbed_assistant


class AnswerPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-answer-plan")

    def _plan_for(self, question: str):
        routing = self.assistant._plan_and_route(question)
        profile = build_task_profile(question, routing)
        return build_answer_plan(profile, routing)

    def test_cross_section_compare_forbids_contribution_as_primary(self) -> None:
        plan = self._plan_for("比較 8 月各平台營收與庫存")

        self.assertIn("get_platform_ratios", plan.primary_tools)
        self.assertIn("get_contribution_analysis(revenue)", plan.forbidden_primary_tools)
        self.assertEqual(plan.max_key_observations, 3)
        self.assertTrue(plan.requires_table)
        self.assertFalse(plan.display_debug_findings)

    def test_performance_assessment_uses_proxy_tools(self) -> None:
        plan = self._plan_for("請分析哪個平台表現較差")

        self.assertIn("get_inventory_turnover_proxy", plan.primary_tools)
        self.assertIn("get_platform_ratios", plan.primary_tools)
        self.assertIn("get_anomalies", plan.supporting_tools)
        self.assertIn("get_platform_ranking(inventory_amount)", plan.forbidden_primary_tools)
        self.assertEqual(plan.max_key_observations, 3)
        self.assertFalse(plan.requires_table)

    def test_time_compare_uses_contribution_tools(self) -> None:
        plan = self._plan_for("8 月相較 7 月營收變化主要由誰貢獻")

        self.assertIn("get_yoy_mom_breakdown", plan.primary_tools)
        self.assertIn("get_contribution_analysis", plan.primary_tools)
        self.assertEqual(plan.max_key_observations, 3)


if __name__ == "__main__":
    unittest.main()
