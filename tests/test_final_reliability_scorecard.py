import json
from evaluation.models import EvalCaseResult,GraderResult
from evaluation.runner import EvaluationRunner
from evaluation.scorecard import build_scorecard


def test_final_scorecard_separates_execution_and_synthetic_and_writes_safe_artifacts(tmp_path):
    aggregate=EvaluationRunner(tmp_path).run("core");folder=tmp_path/aggregate["eval_run_id"]
    scorecard=json.loads((folder/"reliability_scorecard.json").read_text(encoding="utf-8"))
    assert scorecard["policy"]["execution_backed_weight"]>=0.85
    assert scorecard["policy"]["synthetic_grader_weight"]<=0.15
    assert aggregate["declared_execution_backed_count"]==8
    assert aggregate["actual_execution_completed_count"]==8
    assert aggregate["synthetic_case_count"]==0
    assert aggregate["token_usage"] is None and aggregate["estimated_cost"] is None
    assert aggregate["cost_status"]=="local_or_unavailable"
    for name in ("reliability_scorecard.md","reliability_scorecard.json","trajectory_summary.csv","failure_analysis.csv"):
        text=(folder/name).read_text(encoding="utf-8")
        assert "/home/" not in text and "raw_rows" not in text and "api_key" not in text.lower()


def test_fidelity_or_hard_failure_forces_scorecard_status_failed():
    grader=GraderResult("execution_fidelity","graders.v1",0.0,False,"hard","mismatch",failure_categories=["execution_trace_mismatch"])
    result=EvalCaseResult("x","trace-x","completed",[grader],False,0.0,["execution_trace_mismatch"],execution_mode="execution_backed",suite="core",execution_adapter="assistant",actual_execution_mode="execution_backed",adapter_status="completed",actual_execution_attempted=True,actual_execution_completed=True,actual_execution_passed=False)
    aggregate,_=build_scorecard({"eval_run_id":"eval-x"},[result])
    assert aggregate["overall_status"]=="failed"
    assert aggregate["execution_fidelity_rate"]==0.0
    assert aggregate["hard_invariant_pass_rate"]==0.0
