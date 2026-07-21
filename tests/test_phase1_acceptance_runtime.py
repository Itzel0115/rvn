from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_runtime.evidence_validator import EvidenceValidator
from agent_runtime.models import AgentRunState, AgentRunStatus, PlanStep, PlanStepStatus
from agent_runtime.plan_validation import validate_stateful_steps
from agent_runtime.replanner import DeterministicReplanner, ReplanProposal
from agent_runtime.runtime import StatefulAgentRuntime
from agent_runtime.state_store import SQLiteAgentStateStore
from answer_plan import AnswerPlan
from canonical_task import CanonicalTaskProfile


def relationship_state(*, rows: list[dict], source_tool: str = "get_revenue_inventory_relationship") -> AgentRunState:
    return AgentRunState(
        request_id="驗收-關係", thread_id="thread", question="營收與庫存關係",
        canonical_task={"task_family": "metric_relationship_analysis", "metric": "revenue_amount",
                        "time_scope": {"mode": "multi_month_series"},
                        "target_entity": {"dimension": "business_group", "value": None}},
        answer_plan_summary={"primary_tools": ["get_revenue_inventory_relationship"],
                             "supporting_tools": ["get_entity_performance_snapshot"]},
        steps=[PlanStep("p1-s1", 1, 1, source_tool, purpose="primary evidence", status=PlanStepStatus.SUCCEEDED)],
        evidence=[{"evidence_id": "ev-1", "source_tool": source_tool, "rows": rows}],
    )


class InvalidReplanner:
    def propose(self, state, missing):
        return ReplanProposal(steps=[PlanStep("p2-s1", 2, 2, "invented_tool", {}, "repair")], reason="test")


class EmptyReplanner:
    def propose(self, state, missing):
        return ReplanProposal(reason="no_legal_non_duplicate_repair")


class Phase1AcceptanceRuntimeTest(unittest.TestCase):
    def test_snapshot_cannot_complete_relationship_analysis(self) -> None:
        state = relationship_state(rows=[{"entity_value": "A", "revenue_amount": 10, "inventory_amount": 20}],
                                   source_tool="get_entity_performance_snapshot")
        result = EvidenceValidator().validate(state)
        self.assertFalse(result.sufficient)
        self.assertIn("missing_relationship_evidence", result.issues)

    def test_relationship_requires_both_change_sides(self) -> None:
        state = relationship_state(rows=[{"entity_value": "A", "revenue_change": -0.1, "inventory_change": None}])
        result = EvidenceValidator().validate(state)
        self.assertFalse(result.sufficient)
        self.assertIn("incomplete_relationship_evidence", result.issues)

    def test_snapshot_is_rejected_as_relationship_primary(self) -> None:
        canonical = CanonicalTaskProfile(
            question_text="關係", task_family="metric_relationship_analysis", time_scope={"mode": "multi_month_series"},
            target_entity={"dimension": "business_group", "scope": "all", "value": None}, parent_entity={"dimension": None, "value": None},
            metric="revenue_amount", chart_type=None, answer_mode="diagnosis",
        )
        result = validate_stateful_steps(canonical, [PlanStep("p1-s1", 1, 1, "get_entity_performance_snapshot", {"entity_dimension": "business_group"}, "primary evidence")],
                                         AnswerPlan(primary_tools=["get_entity_performance_snapshot"]))
        self.assertFalse(result["valid"])
        self.assertIn("relationship_snapshot_must_be_supporting", result["violations"])

    def test_invalid_replan_is_stopped_after_validation(self) -> None:
        state = AgentRunState(request_id="invalid-replan", thread_id="t", question="q", canonical_task={"task_family": "metric_lookup"},
                              answer_plan_summary={}, steps=[PlanStep("p1-s1", 1, 1, "get_entity_metric_value", purpose="primary evidence")])
        runtime = StatefulAgentRuntime(executor=lambda *_: None, replanner=InvalidReplanner(),
                                       replan_validator=lambda *_: {"valid": False, "violations": ["unknown_tool:invented_tool"]})
        state = runtime.run(state)
        self.assertEqual(state.stop_reason, "invalid_replan")
        self.assertEqual(state.replanning_history[-1].trigger, "invalid_replan")

    def test_no_valid_alternative_stops_without_retry(self) -> None:
        state = AgentRunState(request_id="no-alt", thread_id="t", question="q", canonical_task={"task_family": "metric_lookup"},
                              answer_plan_summary={}, steps=[PlanStep("p1-s1", 1, 1, "get_entity_metric_value", purpose="primary evidence")])
        state = StatefulAgentRuntime(executor=lambda *_: (_ for _ in ()).throw(RuntimeError("unavailable")), replanner=EmptyReplanner()).run(state)
        self.assertIn(state.status, {AgentRunStatus.FAILED, AgentRunStatus.PARTIAL})
        self.assertEqual(state.stop_reason, "no_progress")
        self.assertEqual(len(state.tool_executions), 1)

    def test_checkpoint_compacts_rows_and_store_keeps_unicode_requests_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteAgentStateStore(Path(directory) / "nested" / "agent.sqlite3")
            first = AgentRunState(request_id="請求-A", thread_id="t", question="中文問題", canonical_task={})
            second = AgentRunState(request_id="請求-B", thread_id="t", question="第二題", canonical_task={}, final_answer="部分答案")
            store.save(first)
            store.save(second)
            self.assertEqual(SQLiteAgentStateStore(Path(directory) / "nested" / "agent.sqlite3").load("請求-A").question, "中文問題")
            self.assertEqual(store.load("請求-B").final_answer, "部分答案")

        state = AgentRunState(request_id="compact", thread_id="t", question="q", canonical_task={},
                              steps=[PlanStep("p1-s1", 1, 1, "fake", purpose="primary evidence")])
        compact = StatefulAgentRuntime(executor=lambda *_: {"rows": [{"n": index} for index in range(100)], "summary": {"ok": True}}).run(state)
        self.assertLessEqual(len(compact.evidence[0]["rows"]), 20)
        json.dumps(compact.to_dict(), ensure_ascii=False)
