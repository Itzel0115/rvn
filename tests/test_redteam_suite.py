from evaluation.runner import EvaluationRunner

def test_redteam_has_hard_safety_pass_rate(tmp_path):
    result=EvaluationRunner(tmp_path).run("redteam")
    assert result["hard_invariant_pass_rate"]==1.0
