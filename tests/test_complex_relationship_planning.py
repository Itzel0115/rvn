from __future__ import annotations

import unittest

from agent_runtime.evidence_validator import EvidenceValidator
from agent_runtime.integration import _materialize_steps
from agent_runtime.models import AgentRunState, PlanStep, PlanStepStatus
from agent_runtime.replanner import DeterministicReplanner
from answer_plan import build_answer_plan
from analysis_tools import QueryFilters
from canonical_task import CanonicalTaskProfile
from llm_planner import PlannedToolCall, ToolPlan
from multi_agent import RoutingDecision
from plan_validator import PlanValidator
from task_profile import build_task_profile


QUESTION = (
    "請找出最近三個月中，營收連續下降但庫存金額連續上升的事業群。"
    "先比較所有事業群，再挑出最異常的一個，檢查它的庫存數量、庫存金額與營收變化是否一致，"
    "列出支持證據、可能反證、資料限制及代理指標。"
)


class ComplexRelationshipPlanningTest(unittest.TestCase):
    def _routing(self) -> RoutingDecision:
        return RoutingDecision(
            question=QUESTION,
            question_type="risk",
            intents=["risk"],
            domains=["financial"],
            filters=QueryFilters(),
            object_dimension="business_group",
            answer_strategy="risk",
        )

    def _recent_relationship_state_missing_inventory_qty(self) -> AgentRunState:
        return AgentRunState(
            request_id="req-complex", thread_id="thread", question=QUESTION,
            canonical_task={
                "task_family": "metric_relationship_analysis",
                "metric": "revenue_amount",
                "time_scope": {"mode": "recent_n_months", "recent_n": 3},
                "target_entity": {"dimension": "business_group", "value": None},
                "parent_entity": {"dimension": None, "value": None},
                "semantic_task_requirement_id": "req.metric_relationship.v1",
            },
            answer_plan_summary={"primary_tools": ["get_revenue_inventory_relationship", "get_entity_trend_comparison"], "supporting_tools": ["get_entity_performance_snapshot"]},
            steps=[
                PlanStep("p1-s1", 1, 1, "get_revenue_inventory_relationship", {"entity_dimension": "business_group", "recent_n": 3}, purpose="primary evidence", status=PlanStepStatus.SUCCEEDED),
                PlanStep("p1-s2", 1, 2, "get_entity_trend_comparison", {"entity_dimension": "business_group", "metric": "revenue_amount", "recent_n": 3}, purpose="primary evidence", status=PlanStepStatus.SUCCEEDED),
                PlanStep("p1-s3", 1, 3, "get_entity_trend_comparison", {"entity_dimension": "business_group", "metric": "inventory_amount", "recent_n": 3}, purpose="primary evidence", status=PlanStepStatus.SUCCEEDED),
            ],
        )

    def test_chinese_recent_three_months_is_preserved_for_relationship_task(self) -> None:
        profile = build_task_profile(QUESTION, self._routing())
        self.assertEqual(profile.task_family, "metric_relationship_analysis")
        self.assertEqual(profile.time_scope["mode"], "recent_n_months")
        self.assertEqual(profile.time_scope["recent_n"], 3)
        self.assertIn("inventory_qty", profile.metrics)

    def test_relationship_plan_accepts_multimetric_trend_calls(self) -> None:
        profile = build_task_profile(QUESTION, self._routing())
        canonical = CanonicalTaskProfile.from_task_profile(profile, self._routing())
        answer_plan = build_answer_plan(profile, self._routing())
        plan = ToolPlan(
            task_family="metric_relationship_analysis",
            question_type="risk",
            domains=["financial"],
            answer_mode="risk",
            requires_limitations=True,
            tools=[
                PlannedToolCall("get_revenue_inventory_relationship", {"entity_dimension": "business_group", "recent_n": 3}, "paired relationship"),
                PlannedToolCall("get_entity_trend_comparison", {"entity_dimension": "business_group", "metric": "revenue_amount", "recent_n": 3}, "revenue trend"),
                PlannedToolCall("get_entity_trend_comparison", {"entity_dimension": "business_group", "metric": "inventory_amount", "recent_n": 3}, "inventory amount trend"),
                PlannedToolCall("get_entity_trend_comparison", {"entity_dimension": "business_group", "metric": "inventory_qty", "recent_n": 3}, "inventory quantity counter evidence"),
                PlannedToolCall("get_entity_performance_snapshot", {"entity_dimension": "business_group"}, "supporting scorecard"),
            ],
        )
        result = PlanValidator().validate(canonical, plan, deterministic_answer_plan=answer_plan)
        self.assertTrue(result["valid"], result)

        steps = _materialize_steps(
            canonical,
            answer_plan,
            [call.tool_name for call in plan.tools],
            [{"tool_name": call.tool_name, "args": call.args, "reason": call.reason} for call in plan.tools],
        )
        self.assertEqual([step.tool_name for step in steps], [call.tool_name for call in plan.tools])
        self.assertEqual(steps[2].tool_args["metric"], "inventory_amount")
        self.assertEqual(steps[3].tool_args["metric"], "inventory_qty")
        self.assertEqual(steps[0].tool_args["recent_n"], 3)

    def test_recent_relationship_is_not_sufficient_without_inventory_qty_trend(self) -> None:
        state = self._recent_relationship_state_missing_inventory_qty()
        state.evidence = [
            {"source_tool": "get_revenue_inventory_relationship", "rows": [{"revenue_change": -1, "inventory_change": 1}], "limitations": ["proxy only"]},
            {"source_tool": "get_entity_trend_comparison", "metric": "revenue_amount", "rows": [{"entity_value": "A"}]},
            {"source_tool": "get_entity_trend_comparison", "metric": "inventory_amount", "rows": [{"entity_value": "A"}]},
        ]
        result = EvidenceValidator().validate(state)
        self.assertFalse(result.sufficient)
        self.assertIn("trend_metric:inventory_qty", result.missing_requirements)

    def test_replanner_repairs_missing_inventory_qty_with_new_tool_args(self) -> None:
        state = self._recent_relationship_state_missing_inventory_qty()
        proposal = DeterministicReplanner().propose(state, ["trend_metric:inventory_qty"])
        self.assertEqual(proposal.reason, "missing_multimetric_trend_evidence")
        self.assertEqual(len(proposal.steps), 1)
        self.assertEqual(proposal.steps[0].tool_name, "get_entity_trend_comparison")
        self.assertEqual(proposal.steps[0].tool_args["metric"], "inventory_qty")
        self.assertEqual(proposal.steps[0].tool_args["recent_n"], 3)


if __name__ == "__main__":
    unittest.main()
