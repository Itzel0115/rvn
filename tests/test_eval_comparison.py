from evaluation.runner import EvaluationRunner
from evaluation.comparison import compare_runs

def test_same_suite_comparison_is_unchanged(tmp_path):
    runner=EvaluationRunner(tmp_path); a=runner.run("core"); b=runner.run("core")
    assert compare_runs(tmp_path/a["eval_run_id"],tmp_path/b["eval_run_id"])["classification"]=="unchanged"
