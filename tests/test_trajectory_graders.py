from evaluation.models import EvalCase
from evaluation.graders import grade_all

def test_forbidden_tool_fails_deterministically():
    case=EvalCase(case_id="x",suite="x",category="x",description="x",input_type="question",question_or_event="x",forbidden_tools=["bad"],expected_statuses=["completed"])
    trace={"status":"completed","spans":[{"span_name":"tool.execute","attributes":{"revenue_poc.tool.name":"bad"}}]}
    assert not next(item for item in grade_all(case,trace) if item.grader_id=="tool_selection").passed
