from __future__ import annotations

import json
import unittest

from agent_runtime.models import AgentRunState, AgentRunStatus, PlanStep, PlanStepStatus, SCHEMA_VERSION


class AgentRuntimeModelsTest(unittest.TestCase):
    def test_round_trip_is_json_safe_and_restores_enums(self) -> None:
        state = AgentRunState(
            request_id="req-model", thread_id="thread-model", question="test",
            canonical_task={"task_family": "metric_lookup"},
            steps=[PlanStep("p1-s1", 1, 1, "get_entity_metric_value", status=PlanStepStatus.SUCCEEDED)],
            status=AgentRunStatus.EXECUTING,
        )
        payload = state.to_dict()
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        encoded = json.dumps(payload)
        restored = AgentRunState.from_json(encoded)
        self.assertEqual(restored.status, AgentRunStatus.EXECUTING)
        self.assertEqual(restored.steps[0].status, PlanStepStatus.SUCCEEDED)
        self.assertTrue(restored.created_at.endswith("Z"))
