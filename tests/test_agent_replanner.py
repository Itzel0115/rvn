from __future__ import annotations

import unittest

from agent_runtime.models import AgentRunState, PlanStep, PlanStepStatus
from agent_runtime.replanner import DeterministicReplanner


class AgentReplannerTest(unittest.TestCase):
    def test_does_not_repeat_empty_tool_and_uses_supporting_plan_tool(self) -> None:
        state = AgentRunState(
            request_id="req-replan", thread_id="t", question="q",
            canonical_task={"task_family": "metric_relationship_analysis", "metric": "revenue_amount",
                            "time_scope": {"mode": "latest_month"}, "target_entity": {"dimension": "business_group"}},
            answer_plan_summary={"primary_tools": ["get_revenue_inventory_relationship"], "supporting_tools": ["get_entity_performance_snapshot"]},
            steps=[PlanStep("p1-s1", 1, 1, "get_revenue_inventory_relationship", status=PlanStepStatus.EMPTY)],
        )
        proposal = DeterministicReplanner().propose(state, ["rows"])
        self.assertEqual([step.tool_name for step in proposal.steps], ["get_entity_performance_snapshot"])
        self.assertEqual(proposal.steps[0].plan_version, 2)
