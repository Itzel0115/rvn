from __future__ import annotations

import unittest

from agent_runtime.models import AgentRunState, AgentRunStatus, PlanStep
from agent_runtime.runtime import StatefulAgentRuntime
from answer_plan import AnswerPlan
from semantic_layer.adapters import enrich_answer_plan

class ReplannerSemanticIntegrationTest(unittest.TestCase):
    def _state(self) -> AgentRunState:
        return AgentRunState(request_id="semantic-runtime", thread_id="t", question="q", canonical_task={"task_family":"metric_relationship_analysis","semantic_task_requirement_id":"req.metric_relationship.v1","metric":"revenue_amount","time_scope":{"mode":"time_range"},"target_entity":{}}, answer_plan_summary={"primary_tools":["get_revenue_inventory_relationship"],"supporting_tools":["get_entity_performance_snapshot"]}, steps=[PlanStep("p1-s1", 1, 1, "get_revenue_inventory_relationship", {"entity_dimension":"business_group"}, "primary evidence")])

    def test_incomplete_relationship_does_not_complete(self) -> None:
        def execute(name, args):
            if name == "get_revenue_inventory_relationship": return {"rows":[{"revenue_change":1}], "summary":{}}
            return {"rows":[{"entity_value":"A"}], "summary":{}}
        state = StatefulAgentRuntime(executor=execute).run(self._state())
        self.assertNotEqual(state.status, AgentRunStatus.COMPLETED)
        self.assertIn(state.stop_reason, {"capability_gap", "max_replans_reached", "insufficient_evidence"})

    def test_empty_primary_is_capability_gap(self) -> None:
        state = StatefulAgentRuntime(executor=lambda name, args: {"rows":[], "summary":{}}).run(self._state())
        self.assertEqual(state.stop_reason, "capability_gap")

    def test_requirement_limitations_reach_plan(self) -> None:
        canonical = type("Canonical", (), {"task_family":"metric_relationship_analysis"})()
        plan = enrich_answer_plan(AnswerPlan(primary_tools=["get_revenue_inventory_relationship"]), canonical)
        self.assertEqual(plan.semantic_requirement_id, "req.metric_relationship.v1")
        self.assertTrue(plan.required_limitations)
