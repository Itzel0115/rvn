from evaluation.adapters import ADAPTERS, EvalEnvironment
from evaluation.datasets import load_suite

def test_execution_backed_case_uses_declared_adapter(tmp_path):
    case=next(item for item in load_suite("core") if item.case_id=="core-unsupported")
    result=ADAPTERS[case.execution_adapter].execute(case, EvalEnvironment(tmp_path))
    assert result.execution_status in {"completed","partial","failed"}
    assert result.request_id is not None or result.error_summary is not None
