import json
from pathlib import Path
from evaluation.datasets import load_suite,validate_cases


def test_phase4c_policy_and_dataset_acceptance_contract():
    cases=load_suite("all")
    assert len(cases)==43 and not validate_cases(cases)
    assert sum(case.execution_mode=="execution_backed" for case in cases)==41
    assert sum(case.execution_mode=="synthetic_trajectory" for case in cases)==2
    assert {case.case_id for case in cases if case.execution_mode=="synthetic_trajectory"}=={"replan-duplicate","red-output-injection"}
    policy=json.loads(Path("evaluation/policies/regression_gate.v1.json").read_text(encoding="utf-8"))
    assert policy["minimum_actual_execution_backed_cases"]==37
    assert policy["minimum_execution_backed_pass_rate"]==0.95
    assert policy["minimum_trace_completeness_rate"]==0.95
    assert policy["required_execution_fidelity_rate"]==1.0
    assert policy["minimum_hard_invariant_pass_rate"]==1.0
    assert all(policy[key]==0 for key in policy if key.startswith("maximum_"))


def test_evaluation_outputs_are_ignored_and_score_policy_weights_are_bounded():
    score=json.loads(Path("evaluation/policies/reliability_score.v1.json").read_text(encoding="utf-8"))
    assert score["execution_backed_weight"]>=.85
    assert score["synthetic_grader_weight"]<=.15
    assert abs(sum(score["execution_components"].values())-1.0)<1e-9
    assert "output/" in Path(".gitignore").read_text(encoding="utf-8")
