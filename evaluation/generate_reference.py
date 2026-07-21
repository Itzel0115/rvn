from __future__ import annotations
from pathlib import Path
from .datasets import list_suites,load_suite

TARGET=Path("docs/EVALUATION_DATASET_REFERENCE.md")
def generate()->str:
    rows=[]
    for suite in list_suites():
        for case in load_suite(suite):
            required=", ".join(case.required_tools_all or case.required_tools_any) or "—"
            forbidden=", ".join(case.forbidden_tools) or "—"
            status=", ".join(case.expected_statuses)
            safety=", ".join(case.security_invariants) or "—"
            rows.append(f"| {suite} | {case.case_id} | {case.execution_mode} | {case.execution_adapter} | {case.category} | {case.expected_task_type or '—'} | {required} | {forbidden} | {status} | {safety} |")
    cases=[case for suite in list_suites() for case in load_suite(suite)]
    execution=sum(case.execution_mode=="execution_backed" for case in cases);synthetic=sum(case.execution_mode=="synthetic_trajectory" for case in cases)
    return f"# Evaluation Dataset Reference\n\nMachine-generated from `evaluation/datasets/*.v1.jsonl`. Regenerate with `uv run python -m evaluation.generate_reference`. The dataset contains {len(cases)} cases: {execution} execution-backed cases and {synthetic} intentionally synthetic grader-validation cases. All fixtures use synthetic data and contain no company rows, real values, secrets, or absolute paths.\n\n| Suite | Case ID | Execution mode | Adapter | Category | Task type | Expected tools | Forbidden tools | Expected status | Safety invariants |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"+"\n".join(rows)+"\n"
def main()->None:
    TARGET.write_text(generate(),encoding="utf-8")
    print(f"wrote {TARGET}")
if __name__=="__main__":main()
