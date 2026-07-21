from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .aggregation import execution_coverage, load_case_results

_METRICS=("actual_execution_coverage","execution_backed_pass_rate","trace_completeness_rate","execution_fidelity_rate","hard_invariant_pass_rate","overall_score")

def compare_runs(base:Path,candidate:Path)->dict[str,Any]:
    baseline=_load_run(base); current=_load_run(candidate)
    _validate_schema(baseline["aggregate"],current["aggregate"])
    deltas={name:_delta(baseline["aggregate"].get(name),current["aggregate"].get(name)) for name in _METRICS}
    case_deltas=_case_deltas(baseline["results"],current["results"])
    groups={name:[row["case_id"] for row in case_deltas if row["classification"]==name] for name in ("improved","unchanged","regressed","new_failure","fixed_failure")}
    classification="regressed" if groups["regressed"] or groups["new_failure"] else "improved" if groups["improved"] or groups["fixed_failure"] else "unchanged"
    result={"schema_version":"evaluation-comparison.v1","baseline":baseline["aggregate"].get("eval_run_id") or base.name,"candidate":current["aggregate"].get("eval_run_id") or candidate.name,"classification":classification,"metric_deltas":deltas,"actual_execution_coverage_delta":deltas["actual_execution_coverage"],"execution_backed_pass_rate_delta":deltas["execution_backed_pass_rate"],"trace_completeness_delta":deltas["trace_completeness_rate"],"execution_fidelity_delta":deltas["execution_fidelity_rate"],"hard_invariant_delta":deltas["hard_invariant_pass_rate"],"overall_score_delta":deltas["overall_score"],"case_level":groups}
    (candidate/"comparison.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    (candidate/"comparison.md").write_text(_markdown(result),encoding="utf-8")
    with (candidate/"case_deltas.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=["case_id","baseline_passed","candidate_passed","baseline_score","candidate_score","classification"]);writer.writeheader();writer.writerows(case_deltas)
    return result

def _load_run(folder:Path)->dict[str,Any]:
    aggregate_path=folder/"aggregate.json"
    if not aggregate_path.exists(): raise FileNotFoundError(f"aggregate_missing:{folder.name}")
    aggregate=json.loads(aggregate_path.read_text(encoding="utf-8"));results=load_case_results(folder)
    coverage=execution_coverage(results)["overall"]
    aggregate["actual_execution_coverage"]=coverage["actual_execution_completed"]/coverage["declared_execution_backed"] if coverage["declared_execution_backed"] else None
    aggregate["execution_backed_pass_rate"]=coverage["actual_execution_passed"]/coverage["actual_execution_completed"] if coverage["actual_execution_completed"] else None
    aggregate["trace_completeness_rate"]=_grader_rate(results,"trace_completeness")
    aggregate["execution_fidelity_rate"]=_grader_rate(results,"execution_fidelity")
    execution=[item for item in results if item.execution_mode=="execution_backed" and item.actual_execution_completed]
    aggregate["hard_invariant_pass_rate"]=sum(item.hard_invariants_passed for item in execution)/len(execution) if execution else None
    return {"aggregate":aggregate,"results":results}

def _grader_rate(results:list[Any],grader_id:str)->float|None:
    values=[grader.score for result in results if result.execution_mode=="execution_backed" and result.actual_execution_completed for grader in result.grader_results if grader.grader_id==grader_id]
    return sum(values)/len(values) if values else None

def _validate_schema(a:dict[str,Any],b:dict[str,Any])->None:
    left=str(a.get("schema_version") or "");right=str(b.get("schema_version") or "")
    if left.split(".")[0]!=right.split(".")[0]: raise ValueError(f"incompatible_scorecard_schema:{left}:{right}")

def _delta(a:Any,b:Any)->float|None:
    return float(b)-float(a) if a is not None and b is not None else None

def _case_deltas(base:list[Any],candidate:list[Any])->list[dict[str,Any]]:
    old={item.case_id:item for item in base};new={item.case_id:item for item in candidate};rows=[]
    for case_id in sorted(set(old)|set(new)):
        a=old.get(case_id);b=new.get(case_id);ap=bool(a and (a.actual_execution_passed if a.execution_mode=="execution_backed" else a.hard_invariants_passed));bp=bool(b and (b.actual_execution_passed if b.execution_mode=="execution_backed" else b.hard_invariants_passed))
        if a is None: kind="new_failure" if not bp else "improved"
        elif b is None: kind="regressed"
        elif not ap and bp: kind="fixed_failure"
        elif ap and not bp: kind="new_failure"
        elif b.overall_score>a.overall_score: kind="improved"
        elif b.overall_score<a.overall_score: kind="regressed"
        else: kind="unchanged"
        rows.append({"case_id":case_id,"baseline_passed":ap,"candidate_passed":bp,"baseline_score":a.overall_score if a else None,"candidate_score":b.overall_score if b else None,"classification":kind})
    return rows

def _markdown(result:dict[str,Any])->str:
    lines=["# Evaluation Comparison","",f"- Baseline: `{result['baseline']}`",f"- Candidate: `{result['candidate']}`",f"- Classification: **{result['classification']}**","","## Metric deltas",""]
    lines.extend(f"- {name}: {value if value is not None else 'n/a'}" for name,value in result["metric_deltas"].items())
    lines.extend(["","## Case deltas",""])
    lines.extend(f"- {name}: {len(values)}" for name,values in result["case_level"].items())
    return "\n".join(lines)+"\n"
