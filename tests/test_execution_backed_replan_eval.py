from __future__ import annotations

from pathlib import Path

from evaluation.adapters import AssistantExecutionAdapter, EvalEnvironment
from evaluation.datasets import load_suite
from evaluation.graders import execution_fidelity, replan_value, trace_completeness
from evaluation.runner import EvaluationRunner


def _case(case_id: str):
    return {case.case_id: case for case in load_suite("replanning")}[case_id]


def test_valuable_replan_runs_through_public_assistant_entrypoint(tmp_path: Path):
    case = _case("replan-empty")
    result = AssistantExecutionAdapter().execute(case, EvalEnvironment(tmp_path))

    assert result.execution_status == "completed"
    output = result.normalized_output
    state = output["state"]
    assert output["adapter_status"] == "completed"
    assert state["status"] == "completed"
    assert state["replan_count"] == 1
    assert [(step["tool_name"], step["status"], step["plan_version"]) for step in state["steps"]] == [
        ("get_entity_period_pair_comparison", "empty", 1),
        ("get_period_pair_metric_comparison", "succeeded", 2),
    ]
    assert state["replanning_history"][0]["trigger"] == "missing_evidence"
    assert state["evidence"][0]["source_tool"] == "get_period_pair_metric_comparison"


def test_valuable_replan_graders_pass_with_execution_projection(tmp_path: Path):
    output = EvaluationRunner(tmp_path).run("replanning", case_id="replan-empty")
    assert output["failure_categories"] == []
    assert output["overall_score"] == 1.0


def test_replan_value_and_fidelity_use_state_trace_projection(tmp_path: Path):
    case = _case("replan-empty")
    result = AssistantExecutionAdapter().execute(case, EvalEnvironment(tmp_path))
    trace = dict(result.trace or {})
    trace["_evaluation"] = {
        "adapter_id": "assistant",
        "adapter_status": "completed",
        "execution_status": result.execution_status,
        "normalized_output": result.normalized_output,
    }
    trace["status"] = result.normalized_output["state"]["status"]
    trace["final_status"] = result.normalized_output["state"]["status"]
    trace["stop_reason"] = result.normalized_output["state"]["stop_reason"]

    assert replan_value(case, trace).passed
    assert trace_completeness(case, trace).passed
    assert execution_fidelity(case, trace).passed
