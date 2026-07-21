from evaluation.datasets import list_suites,load_suite
from evaluation.runner import EvaluationRunner

def test_phase4_acceptance_offline_core_and_redteam(tmp_path):
    assert {"core","redteam","mcp","approval"}.issubset(set(list_suites()))
    assert sum(len(load_suite(name)) for name in list_suites())>=36
    result=EvaluationRunner(tmp_path).run("redteam")
    assert result["hard_invariant_pass_rate"]==1.0
