from __future__ import annotations

import unittest

from agent_runtime.models import AgentRunState, AgentRunStatus, PlanStep
from agent_runtime.replanner import ReplanProposal
from agent_runtime.runtime import StatefulAgentRuntime


class OneRepairReplanner:
    def propose(self, state, missing):
        return ReplanProposal(steps=[PlanStep("p2-s2", 2, 2, "get_entity_performance_snapshot", {"month": "2025-03"}, "replan evidence repair")])


class DuplicateReplanner:
    def propose(self, state, missing):
        return ReplanProposal(steps=[PlanStep("p2-s1", 2, 2, "get_entity_month_table", {"month": "2025-03"}, "retry")])


class AgentRuntimeTest(unittest.TestCase):
    def _state(self, tool="get_entity_month_table"):
        return AgentRunState(request_id="req-runtime", thread_id="t", question="q",
                             canonical_task={"task_family": "entity_month_table_lookup", "metric": "revenue_amount",
                                             "time_scope": {"mode": "single_month", "month": "2025-03"}, "target_entity": {}},
                             answer_plan_summary={"primary_tools": [tool]},
                             steps=[PlanStep("p1-s1", 1, 1, tool, {"month": "2025-03"}, "primary evidence")])

    def test_empty_then_replan_completes(self) -> None:
        def execute(name, args):
            if name == "get_entity_month_table":
                return {"rows": [], "metric": "revenue_amount", "month": "2025-03"}
            return {"rows": [{"entity_value": "A"}], "metric": "revenue_amount", "month": "2025-03"}
        state = StatefulAgentRuntime(executor=execute, replanner=OneRepairReplanner()).run(self._state())
        self.assertEqual(state.status, AgentRunStatus.COMPLETED)
        self.assertEqual(state.replan_count, 1)
        self.assertEqual(state.steps[0].status.value, "empty")

    def test_tool_exception_is_partial_not_crash(self) -> None:
        state = StatefulAgentRuntime(executor=lambda *_: (_ for _ in ()).throw(RuntimeError("boom")), replanner=DuplicateReplanner()).run(self._state())
        self.assertIn(state.status, {AgentRunStatus.PARTIAL, AgentRunStatus.FAILED})
        self.assertIn(state.stop_reason, {"no_progress", "max_replans_reached", "insufficient_evidence"})
        self.assertEqual(state.tool_executions[0].error_type, "RuntimeError")

    def test_max_steps_guard(self) -> None:
        state = self._state()
        state.max_steps = 0
        state = StatefulAgentRuntime(executor=lambda *_: {}).run(state)
        self.assertEqual(state.stop_reason, "max_steps_reached")
