import json
from evaluation.regression_gate import evaluate_gate
from evaluation.runner import EvaluationRunner


def test_all_suite_runs_43_cases_without_synthetic_fallback_and_emits_artifacts(tmp_path):
    aggregate=EvaluationRunner(tmp_path).run("all");folder=tmp_path/aggregate["eval_run_id"]
    assert aggregate["total_case_count"]==43
    assert aggregate["declared_execution_backed_count"]==41
    assert aggregate["actual_execution_attempted_count"]==41
    assert aggregate["actual_execution_completed_count"]>=37
    assert aggregate["execution_backed_pass_rate"]>=0.95
    assert aggregate["trace_completeness_rate"]>=0.95
    assert aggregate["execution_fidelity_rate"]==1.0
    assert aggregate["hard_invariant_pass_rate"]==1.0
    assert aggregate["synthetic_case_count"]==2
    rows=[json.loads(line) for line in (folder/"case_results.jsonl").read_text(encoding="utf-8").splitlines()]
    execution=[row for row in rows if row["execution_mode"]=="execution_backed"]
    assert len(rows)==43 and len(execution)==41
    assert all(row["actual_execution_mode"]=="execution_backed" for row in execution)
    assert all(row["adapter_status"]=="completed" for row in execution)
    assert evaluate_gate(folder)[0]
    for name in ("manifest.json","case_results.jsonl","aggregate.json","reliability_scorecard.md","reliability_scorecard.json","trajectory_summary.csv","failure_analysis.csv","regression_gate.json"):
        assert (folder/name).exists()
