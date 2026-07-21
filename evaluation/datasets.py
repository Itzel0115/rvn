from __future__ import annotations
import json
from pathlib import Path
from .models import EvalCase

DATASET_DIR=Path(__file__).with_name("datasets")
def list_suites()->list[str]: return sorted(path.stem.split(".")[0] for path in DATASET_DIR.glob("*.v1.jsonl"))
def load_suite(suite:str)->list[EvalCase]:
    if suite=="all": return [case for name in list_suites() for case in load_suite(name)]
    path=DATASET_DIR/f"{suite}.v1.jsonl"
    if not path.exists(): raise ValueError(f"unknown_suite:{suite}")
    return [EvalCase.from_dict(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
def validate_cases(cases:list[EvalCase])->list[str]:
    errors=[]; ids=set()
    for item in cases:
        if item.case_id in ids: errors.append(f"duplicate_case_id:{item.case_id}")
        ids.add(item.case_id)
        if set(item.required_tools_all)&set(item.forbidden_tools): errors.append(f"tool_conflict:{item.case_id}")
        if item.input_type not in {"question","proactive_event","mcp_call","approval_action","publication_action","recorded_trace"}: errors.append(f"invalid_input_type:{item.case_id}")
        if not item.dataset_version: errors.append(f"missing_dataset_version:{item.case_id}")
        if item.execution_mode not in {"execution_backed", "recorded_trace", "synthetic_trajectory"}: errors.append(f"invalid_execution_mode:{item.case_id}")
        if item.execution_adapter not in {"assistant", "proactive", "mcp", "approval", "publication", "trace_only"}: errors.append(f"invalid_execution_adapter:{item.case_id}")
        if item.execution_mode == "execution_backed" and (not item.fixture_id or item.execution_adapter == "trace_only"): errors.append(f"invalid_execution_fixture:{item.case_id}")
        if item.execution_mode == "synthetic_trajectory" and not item.synthetic_rationale: errors.append(f"missing_synthetic_rationale:{item.case_id}")
        if item.execution_mode == "recorded_trace" and item.execution_adapter != "trace_only": errors.append(f"recorded_trace_adapter_mismatch:{item.case_id}")
        if "/" in item.question_or_event or "\\" in item.question_or_event: errors.append(f"unsafe_path_content:{item.case_id}")
    return errors
