from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .datasets import list_suites,load_suite,validate_cases
from .runner import EvaluationRunner
from .comparison import compare_runs
from .regression_gate import evaluate_gate
from .models import EvalCase
from .aggregation import execution_coverage, load_case_results
from .report import generate_report
def _folder(value):
    path=Path("output/evaluations/runs")/value
    if not path.exists(): raise ValueError(f"eval_run_not_found:{value}")
    return path
def main(argv=None)->int:
    parser=argparse.ArgumentParser(description="Offline deterministic evaluation");sub=parser.add_subparsers(dest="cmd",required=True)
    sub.add_parser("list-suites");sub.add_parser("validate-datasets");coverage=sub.add_parser("coverage");coverage.add_argument("--run-id")
    run=sub.add_parser("run");run.add_argument("--suite",required=True);run.add_argument("--case-id");run.add_argument("--runtime",default="stateful",choices=["stateful","legacy"]);run.add_argument("--repeat",type=int,default=1);run.add_argument("--json",action="store_true")
    grade=sub.add_parser("grade-trace");grade.add_argument("trace_json")
    report=sub.add_parser("report");report.add_argument("run_id")
    compare=sub.add_parser("compare");compare.add_argument("baseline");compare.add_argument("candidate")
    gate=sub.add_parser("gate");gate.add_argument("run_id")
    a=parser.parse_args(argv)
    try:
        if a.cmd=="list-suites": output={"suites":list_suites()}
        elif a.cmd=="validate-datasets":
            errors=[err for suite in list_suites() for err in validate_cases(load_suite(suite))];output={"valid":not errors,"errors":errors,"case_count":sum(len(load_suite(s)) for s in list_suites())}
            if errors: print(json.dumps(output,ensure_ascii=False));return 1
        elif a.cmd=="coverage":
            declared=[{"suite":suite,"total":len(load_suite(suite)),"declared_execution_backed":sum(item.execution_mode=="execution_backed" for item in load_suite(suite)),"execution_backed":sum(item.execution_mode=="execution_backed" for item in load_suite(suite)),"recorded_trace":sum(item.execution_mode=="recorded_trace" for item in load_suite(suite)),"synthetic":sum(item.execution_mode=="synthetic_trajectory" for item in load_suite(suite)),"missing_adapter":sum(item.execution_mode=="execution_backed" and item.execution_adapter not in {"assistant","proactive","mcp","approval","publication"} for item in load_suite(suite))} for suite in list_suites()]
            output={"declared_coverage":declared,"suites":declared}
            if a.run_id: output["actual_coverage"]={"eval_run_id":a.run_id,**execution_coverage(load_case_results(_folder(a.run_id)))}
        elif a.cmd=="run": output=EvaluationRunner().run(a.suite,case_id=a.case_id,runtime_mode=a.runtime,repeat=max(1,a.repeat))
        elif a.cmd=="grade-trace":
            trace=json.loads(Path(a.trace_json).read_text(encoding="utf-8"));case=EvalCase(case_id="recorded-trace",suite="recorded",category="recorded",description="recorded",input_type="recorded_trace",question_or_event="recorded",expected_statuses=[trace.get("final_status") or trace.get("status", "completed")]);output=EvaluationRunner().grade_trace(case,trace).to_dict()
        elif a.cmd=="report":
            folder=_folder(a.run_id);manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"));output=generate_report(folder,manifest,load_case_results(folder))
        elif a.cmd=="compare": output=compare_runs(_folder(a.baseline),_folder(a.candidate))
        else:
            passed,output=evaluate_gate(_folder(a.run_id));print(json.dumps(output,ensure_ascii=False,indent=2));return 0 if passed else 1
        print(json.dumps(output,ensure_ascii=False,indent=2));return 0
    except (ValueError,FileNotFoundError,json.JSONDecodeError) as exc: print(str(exc),file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
