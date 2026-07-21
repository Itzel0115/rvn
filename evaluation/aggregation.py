from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .datasets import load_suite
from .models import EvalCase, EvalCaseResult

_EXECUTION_FAILURES = {
    "missing_execution_adapter",
    "execution_adapter_failure",
    "execution_adapter_unimplemented",
    "execution_mode_mismatch",
}


def load_case_results(folder: Path) -> list[EvalCaseResult]:
    path = folder / "case_results.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"case_results_missing:{folder.name}")
    results: list[EvalCaseResult] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        result = EvalCaseResult.from_dict(raw)
        if "actual_execution_attempted" not in raw:
            _upgrade_legacy_execution_fields(result)
        results.append(result)
    return results


def _upgrade_legacy_execution_fields(result: EvalCaseResult) -> None:
    if result.execution_mode == "execution_backed":
        result.actual_execution_mode = "execution_backed"
        result.actual_execution_attempted = True
        failed = bool(set(result.failure_categories) & _EXECUTION_FAILURES)
        result.adapter_status = "failed" if failed else "completed"
        result.actual_execution_completed = not failed
        result.actual_execution_passed = result.actual_execution_completed and all(item.passed for item in result.grader_results)
    elif result.execution_mode == "synthetic_trajectory":
        result.actual_execution_mode = "synthetic_trajectory"
        result.adapter_status = "completed"
        result.actual_execution_passed = result.hard_invariants_passed
    else:
        result.actual_execution_mode = result.execution_mode


def case_lookup() -> dict[str, EvalCase]:
    return {case.case_id: case for case in load_suite("all")}


def execution_coverage(results: Iterable[EvalCaseResult]) -> dict[str, Any]:
    rows = list(results)
    cases = case_lookup()
    grouped: dict[str, list[EvalCaseResult]] = defaultdict(list)
    for result in rows:
        suite = result.suite or (cases[result.case_id].suite if result.case_id in cases else "unknown")
        grouped[suite].append(result)
    suites = [_coverage_row(name, grouped[name]) for name in sorted(grouped)]
    return {"overall": _coverage_row("all", rows), "suites": suites}


def _coverage_row(suite: str, rows: list[EvalCaseResult]) -> dict[str, Any]:
    declared = [item for item in rows if item.execution_mode == "execution_backed"]
    attempted = [item for item in declared if item.actual_execution_attempted]
    completed = [item for item in declared if item.actual_execution_completed]
    passed = [item for item in completed if item.actual_execution_passed]
    synthetic = [item for item in rows if item.execution_mode == "synthetic_trajectory"]
    recorded = [item for item in rows if item.execution_mode == "recorded_trace"]
    mismatches = [item for item in declared if "execution_mode_mismatch" in item.failure_categories or (item.actual_execution_mode not in {None, "execution_backed"})]
    unimplemented = [item for item in declared if item.adapter_status in {"pending", "not_implemented", "missing"} or "execution_adapter_unimplemented" in item.failure_categories or "missing_execution_adapter" in item.failure_categories]
    return {
        "suite": suite,
        "total": len(rows),
        "declared_execution_backed": len(declared),
        "actual_execution_attempted": len(attempted),
        "actual_execution_completed": len(completed),
        "actual_execution_passed": len(passed),
        "actual_execution_failed": len(attempted) - len(passed),
        "synthetic_cases": len(synthetic),
        "recorded_trace_cases": len(recorded),
        "execution_mode_mismatches": len(mismatches),
        "pending_or_unimplemented_adapters": len(unimplemented),
    }
