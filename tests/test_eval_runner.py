from evaluation.runner import EvaluationRunner

def test_runner_emits_repeatable_artifacts(tmp_path):
    output=EvaluationRunner(tmp_path).run("core")
    folder=tmp_path/output["eval_run_id"]
    assert output["case_count"]==8 and (folder/"reliability_scorecard.md").exists() and (folder/"case_results.jsonl").exists()
