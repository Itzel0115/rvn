from evaluation.graders import replan_value
from evaluation.models import EvalCase

def test_duplicate_replan_fixture_is_scored_as_low_value():
    case=EvalCase("c","x","duplicate","x","question","x")
    trace={"spans":[{"attributes":{"revenue_poc.tool.name":"x","args_fingerprint":"same"}},{"attributes":{"revenue_poc.tool.name":"x","args_fingerprint":"same"}}]}
    assert replan_value(case,trace).passed
