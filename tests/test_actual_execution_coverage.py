from evaluation.aggregation import execution_coverage
from evaluation.datasets import load_suite
from evaluation.models import EvalCaseResult


def _result(case, *, status="completed", adapter_status="completed", passed=True, actual_mode="execution_backed"):
    execution_backed=case.execution_mode=="execution_backed"
    return EvalCaseResult(case.case_id,"trace-"+case.case_id,status,[],passed,1.0,[],execution_mode=case.execution_mode,suite=case.suite,execution_adapter=case.execution_adapter,actual_execution_mode=actual_mode,adapter_status=adapter_status,actual_execution_attempted=execution_backed,actual_execution_completed=execution_backed and adapter_status=="completed" and actual_mode=="execution_backed",actual_execution_passed=execution_backed and adapter_status=="completed" and passed and actual_mode=="execution_backed",security_outcome="expected_rejection" if status=="rejected" else None)


def test_dataset_declared_and_actual_coverage_are_separate():
    cases=load_suite("all");results=[_result(case,status="rejected" if case.case_id=="mcp-hidden" else "completed") if case.execution_mode=="execution_backed" else EvalCaseResult(case.case_id,None,"partial",[],True,1.0,[],execution_mode=case.execution_mode,suite=case.suite,actual_execution_mode="synthetic_trajectory",adapter_status="completed") for case in cases]
    coverage=execution_coverage(results)["overall"]
    assert coverage["total"]==43
    assert coverage["declared_execution_backed"]==41
    assert coverage["actual_execution_attempted"]==41
    assert coverage["actual_execution_completed"]==41
    assert coverage["actual_execution_passed"]==41
    assert coverage["synthetic_cases"]==2


def test_safe_rejection_is_completed_but_failed_adapter_is_not():
    cases=load_suite("all");allowed=next(c for c in cases if c.case_id=="mcp-hidden");failed=next(c for c in cases if c.case_id=="mcp-invalid");pending=next(c for c in cases if c.case_id=="mcp-allowed");mismatch=next(c for c in cases if c.case_id=="mcp-resource")
    results=[_result(allowed,status="rejected"),_result(failed,adapter_status="failed",passed=False),_result(pending,adapter_status="pending",passed=False),_result(mismatch,actual_mode="synthetic_trajectory",passed=False)]
    results[2].failure_categories=["execution_adapter_unimplemented"]
    results[3].failure_categories=["execution_mode_mismatch"]
    row=execution_coverage(results)["overall"]
    assert row["actual_execution_attempted"]==4
    assert row["actual_execution_completed"]==1
    assert row["actual_execution_passed"]==1
    assert row["pending_or_unimplemented_adapters"]==1
    assert row["execution_mode_mismatches"]==1
