from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICY_PATH=Path(__file__).with_name("policies")/"regression_gate.v1.json"

_METRICS={
    "minimum_actual_execution_backed_cases": ("actual_execution_completed_count", ">="),
    "minimum_execution_backed_pass_rate": ("execution_backed_pass_rate", ">="),
    "minimum_trace_completeness_rate": ("trace_completeness_rate", ">="),
    "required_execution_fidelity_rate": ("execution_fidelity_rate", ">="),
    "minimum_hard_invariant_pass_rate": ("hard_invariant_pass_rate", ">="),
    "maximum_execution_mode_mismatches": ("execution_mode_mismatch_count", "<="),
    "maximum_unimplemented_adapters": ("pending_or_unimplemented_adapter_count", "<="),
}
_HARD_COUNTS={
    "maximum_approval_bypass_failures":"approval_bypass_failures",
    "maximum_unapproved_publications":"unapproved_publications",
    "maximum_mcp_boundary_failures":"mcp_boundary_failures",
    "maximum_secret_exposure_failures":"secret_exposure_failures",
    "maximum_execution_trace_mismatches":"execution_trace_mismatches",
    "maximum_supporting_as_primary_failures":"supporting_as_primary_failures",
}

def evaluate_gate(folder:Path)->tuple[bool,dict[str,Any]]:
    aggregate_path=folder/"aggregate.json"
    manifest_path=folder/"manifest.json"
    if not aggregate_path.exists(): raise FileNotFoundError(f"aggregate_missing:{folder.name}")
    aggregate=json.loads(aggregate_path.read_text(encoding="utf-8"))
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    policy=json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    checks=[]
    complete=manifest.get("status")=="completed"
    checks.append(_check("run_completed",True,complete,"=="))
    for policy_name,(aggregate_name,operator) in _METRICS.items():
        checks.append(_check(aggregate_name,policy[policy_name],aggregate.get(aggregate_name),operator))
    hard_counts=aggregate.get("hard_failure_counts") if isinstance(aggregate.get("hard_failure_counts"),dict) else {}
    for policy_name,count_name in _HARD_COUNTS.items():
        checks.append(_check(count_name,policy[policy_name],hard_counts.get(count_name),"<="))
    passed=all(item["passed"] for item in checks)
    failures=[item["metric"] for item in checks if not item["passed"]]
    report={"schema_version":"regression-gate-result.v1","eval_run_id":aggregate.get("eval_run_id") or folder.name,"status":"passed" if passed else "failed","passed":passed,"threshold_results":checks,"blocking_failures":failures}
    (folder/"regression_gate.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    return passed,report

def _check(metric:str,required:Any,actual:Any,operator:str)->dict[str,Any]:
    if actual is None:
        passed=False
    elif operator==">=": passed=actual>=required
    elif operator=="<=": passed=actual<=required
    else: passed=actual==required
    return {"metric":metric,"required":required,"actual":actual,"passed":passed,"failure_reason":None if passed else f"{metric} required {operator} {required}; actual={actual}"}
