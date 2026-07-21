from __future__ import annotations

from evaluation.adapters import ADAPTERS, AssistantExecutionAdapter
from evaluation.datasets import load_suite
from evaluation.runner import EvaluationRunner


def test_phase4b_replanning_cases_are_execution_backed_and_use_assistant_adapter(tmp_path):
    cases = {case.case_id: case for case in load_suite("replanning")}
    for case_id in ("replan-empty", "replan-capability"):
        case = cases[case_id]
        assert case.execution_mode == "execution_backed"
        assert case.execution_adapter == "assistant"
    assert isinstance(ADAPTERS["assistant"], AssistantExecutionAdapter)

    empty = EvaluationRunner(tmp_path).run("replanning", case_id="replan-empty")
    capability = EvaluationRunner(tmp_path).run("replanning", case_id="replan-capability")
    assert empty["execution_backed_case_count"] == 1
    assert empty["synthetic_case_count"] == 0
    assert empty["failure_categories"] == []
    assert capability["execution_backed_case_count"] == 1
    assert capability["synthetic_case_count"] == 0
    assert "invalid_replan" not in capability["failure_categories"]
