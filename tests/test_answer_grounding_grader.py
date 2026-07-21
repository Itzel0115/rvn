from evaluation.graders import answer_grounding
from evaluation.models import EvalCase

def test_causal_claim_pattern_is_rejected():
    case=EvalCase("c","x","x","x","question","x",forbidden_claim_patterns=["caused"])
    assert not answer_grounding(case,{"answer_summary":"inventory caused revenue"}).passed
