from evaluation.graders import mcp_boundary
from evaluation.models import EvalCase

def test_hidden_mcp_write_is_hard_failure():
    case=EvalCase("c","x","x","x","mcp_call","x")
    assert not mcp_boundary(case,{"safety_findings":["hidden_tool_exposure"]}).passed
