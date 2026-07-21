from evaluation.runner import EvaluationRunner

def test_scorecard_json_and_csv_are_written(tmp_path):
    result=EvaluationRunner(tmp_path).run("core"); folder=tmp_path/result["eval_run_id"]
    assert (folder/"reliability_scorecard.json").exists() and (folder/"failure_analysis.csv").exists()
