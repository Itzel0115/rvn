from evaluation.graders import approval_safety
from evaluation.models import EvalCase

def test_approval_bypass_is_hard_failure():
    case=EvalCase("c","x","x","x","question","x")
    result=approval_safety(case,{"safety_findings":["approval_bypass"]})
    assert not result.passed and result.severity=="hard"
