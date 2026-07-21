from __future__ import annotations

from pathlib import Path

from evaluation.adapters import AssistantExecutionAdapter, EvalEnvironment
from evaluation.datasets import load_suite
from evaluation.runner import EvaluationRunner


def _case(case_id: str):
    return {case.case_id: case for case in load_suite("replanning")}[case_id]


def test_capability_gap_runs_public_assistant_and_does_not_become_invalid_replan(tmp_path: Path):
    case = _case("replan-capability")
    result = AssistantExecutionAdapter().execute(case, EvalEnvironment(tmp_path))

    assert result.execution_status == "partial"
    state = result.normalized_output["state"]
    response = result.normalized_output["response"]
    assert state["status"] == "partial"
    assert state["stop_reason"] == "capability_gap"
    assert response["stop_reason"] == "capability_gap"
    assert "invalid_replan" not in state["validation_issues"]
    assert any("能力缺口" in item for item in state["limitations"])
    assert any(item["tool_name"] == "get_revenue_inventory_relationship" and item["status"] == "empty" for item in state["steps"])
    assert any(item["source_tool"] == "get_entity_performance_snapshot" for item in state["evidence"])


def test_capability_gap_runner_projection_passes_existing_case(tmp_path: Path):
    output = EvaluationRunner(tmp_path).run("replanning", case_id="replan-capability")
    assert output["hard_invariant_pass_rate"] == 1.0
    assert "invalid_replan" not in output["failure_categories"]
    assert "missing_required_limitation" not in output["failure_categories"]
