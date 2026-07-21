from __future__ import annotations

import unittest

from agent_runtime.evidence_validator import EvidenceValidator
from agent_runtime.models import AgentRunState, PlanStep, PlanStepStatus


class EvidenceValidatorTest(unittest.TestCase):
    def _state(self) -> AgentRunState:
        return AgentRunState(
            request_id="req-evidence", thread_id="thread", question="q",
            canonical_task={"task_family": "entity_month_table_lookup", "metric": "revenue_amount",
                            "time_scope": {"mode": "single_month", "month": "2025-03"},
                            "target_entity": {"dimension": "business_group", "value": None}},
            answer_plan_summary={"primary_tools": ["get_entity_month_table"]},
            steps=[PlanStep("p1-s1", 1, 1, "get_entity_month_table", purpose="primary evidence", status=PlanStepStatus.SUCCEEDED)],
        )

    def test_sufficient_month_metric_rows(self) -> None:
        state = self._state()
        state.evidence = [{"source_tool": "get_entity_month_table", "metric": "revenue_amount", "month": "2025-03", "rows": [{"entity_value": "A"}]}]
        result = EvidenceValidator().validate(state)
        self.assertTrue(result.sufficient, result)

    def test_empty_results_need_replan(self) -> None:
        state = self._state()
        state.steps[0].status = PlanStepStatus.EMPTY
        result = EvidenceValidator().validate(state)
        self.assertFalse(result.sufficient)
        self.assertTrue(result.needs_replan)
        self.assertIn("no_successful_tool_execution", result.issues)
