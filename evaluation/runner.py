from __future__ import annotations
import hashlib, json, os, platform, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from observability.normalization import normalize_trace, trajectory_fingerprint
from .datasets import load_suite, validate_cases
from .graders import grade_all
from .models import EvalCase, EvalCaseResult
from .adapters import ADAPTERS, EvalEnvironment

ROOT=Path("output/evaluations/runs")
def _now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
class EvaluationRunner:
    def __init__(self, output_root:Path|str=ROOT)->None: self.output_root=Path(output_root)
    def run(self,suite:str,*,case_id:str|None=None,runtime_mode:str="stateful",repeat:int=1)->dict[str,Any]:
        cases=load_suite(suite); errors=validate_cases(cases)
        if errors: raise ValueError("invalid_dataset:"+",".join(errors))
        if case_id:
            cases=[item for item in cases if item.case_id==case_id]
            if not cases: raise ValueError(f"unknown_case:{case_id}")
        run_id="eval-"+uuid.uuid4().hex[:12]; folder=self.output_root/run_id; folder.mkdir(parents=True,exist_ok=False)
        manifest={"eval_run_id":run_id,"suite_names":[suite],"started_at":_now(),"finished_at":None,"status":"running","code_version_reference":None,"working_tree_dirty":True,"working_tree_hash":self._safe_tree_hash(),"python_version":sys.version.split()[0],"platform":platform.system(),"dependency_lock_hash":self._file_hash(Path("uv.lock")),"runtime_mode":runtime_mode,"semantic_catalog_version":"semantic-layer.v1","tool_registry_version":"tool-registry.v1","policy_versions":{"regression_gate":"v1","reliability_score":"v1"},"dataset_versions":sorted({item.dataset_version for item in cases}),"fixture_versions":["synthetic.v1"],"model_configuration":{"mode":"stub"},"random_seed":17,"case_count":len(cases)*repeat,"grader_versions":["graders.v1"],"report_schema_version":"scorecard.v1"}
        (folder/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
        results=[]
        for round_index in range(repeat):
            for case in cases:
                try: result=self._run_case(case,runtime_mode,round_index)
                except Exception as exc:
                    result=EvalCaseResult(case.case_id,None,"failed",[],False,0.0,["execution_failure"],artifact_references=[type(exc).__name__],execution_mode=case.execution_mode,suite=case.suite,task_type=case.expected_task_type,execution_adapter=case.execution_adapter,actual_execution_mode="execution_backed" if case.execution_mode=="execution_backed" else case.execution_mode,adapter_status="failed",actual_execution_attempted=case.execution_mode=="execution_backed",stop_reason="execution_failure")
                results.append(result)
        with (folder/"case_results.jsonl").open("w",encoding="utf-8") as handle:
            for result in results: handle.write(json.dumps(result.to_dict(),ensure_ascii=False,allow_nan=False)+"\n")
        manifest["finished_at"]=_now();manifest["status"]="completed";(folder/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
        from .report import generate_report
        return generate_report(folder,manifest,results)
    def grade_trace(self,case:EvalCase,trace:dict[str,Any])->EvalCaseResult:
        graders=grade_all(case,trace); hard=all(item.passed for item in graders if item.severity=="hard"); score=sum(item.score for item in graders)/len(graders) if graders else 0; cats=sorted({category for item in graders for category in item.failure_categories})
        return EvalCaseResult(case.case_id,trace.get("trace_id"),trace.get("final_status") or trace.get("status","failed"),grader_results=graders,hard_invariants_passed=hard,overall_score=score,failure_categories=cats,duration_ms=float(trace.get("duration_ms") or 0),tool_call_count=int(trace.get("tool_call_count") or 0),replan_count=int(trace.get("replan_count") or 0),artifact_references=[trajectory_fingerprint(normalize_trace(trace))],execution_mode=case.execution_mode,suite=case.suite,task_type=case.expected_task_type,execution_adapter=case.execution_adapter,stop_reason=trace.get("stop_reason"))
    def _run_case(self,case:EvalCase,mode:str,round_index:int)->EvalCaseResult:
        if case.execution_mode == "synthetic_trajectory":
            result=self.grade_trace(case, self._synthetic_trace(case, mode))
            result.actual_execution_mode="synthetic_trajectory"; result.adapter_status="completed"; result.actual_execution_passed=result.hard_invariants_passed
            return result
        adapter = ADAPTERS.get(case.execution_adapter)
        if adapter is None:
            return EvalCaseResult(case.case_id, None, "failed", [], False, 0.0, ["missing_execution_adapter"], execution_mode=case.execution_mode,suite=case.suite,task_type=case.expected_task_type,execution_adapter=case.execution_adapter,actual_execution_mode="not_attempted",adapter_status="missing",stop_reason="missing_execution_adapter")
        import tempfile
        with tempfile.TemporaryDirectory(prefix="revenue-poc-eval-") as root:
            execution = adapter.execute(case, EvalEnvironment(Path(root), mode, Path(root) / "traces.sqlite3"))
        trace = execution.trace or {"schema_version":"revenue-poc-trace.v1", "status":"failed", "final_status":"failed", "spans":[]}
        trace = self._attach_execution_projection(case, trace, execution)
        result = self.grade_trace(case, trace)
        normalized=dict(execution.normalized_output or {})
        actual_adapter=str(normalized.get("adapter_id") or getattr(adapter,"adapter_id",case.execution_adapter))
        adapter_status=str(normalized.get("adapter_status") or ("failed" if execution.error_summary else "completed"))
        mode_match=actual_adapter==case.execution_adapter
        completed=adapter_status=="completed" and mode_match
        grader_passed=all(item.passed for item in result.grader_results)
        result.execution_status=execution.execution_status; result.execution_mode=case.execution_mode; result.execution_adapter=actual_adapter; result.actual_execution_mode="execution_backed"; result.adapter_status=adapter_status; result.actual_execution_attempted=True; result.actual_execution_completed=completed; result.actual_execution_passed=completed and grader_passed; result.security_outcome=normalized.get("security_outcome")
        if not mode_match:
            result.failure_categories=sorted(set(result.failure_categories)|{"execution_mode_mismatch"}); result.hard_invariants_passed=False; result.actual_execution_passed=False
        if adapter_status in {"pending","not_implemented"}:
            result.failure_categories=sorted(set(result.failure_categories)|{"execution_adapter_unimplemented"}); result.hard_invariants_passed=False; result.actual_execution_passed=False
        elif adapter_status!="completed":
            result.failure_categories=sorted(set(result.failure_categories)|{"execution_adapter_failure"}); result.hard_invariants_passed=False; result.actual_execution_passed=False
        if execution.error_summary:
            result.artifact_references.append(execution.error_summary)
        return result
    def _attach_execution_projection(self, case: EvalCase, trace: dict[str, Any], execution: Any) -> dict[str, Any]:
        projected = dict(trace)
        normalized = dict(execution.normalized_output or {})
        projected["_evaluation"] = {
            "declared_execution_mode": case.execution_mode,
            "actual_execution_mode": "execution_backed",
            "adapter_id": normalized.get("adapter_id") or case.execution_adapter,
            "adapter_status": normalized.get("adapter_status") or ("failed" if execution.error_summary else "completed"),
            "execution_status": execution.execution_status,
            "normalized_output": normalized,
            "artifact_references": list(execution.artifact_references or []),
            "error_summary": execution.error_summary,
        }
        response = normalized.get("response") if isinstance(normalized.get("response"), dict) else {}
        state = normalized.get("state") if isinstance(normalized.get("state"), dict) else {}
        projected.setdefault("limitations", response.get("limitations") or state.get("limitations") or normalized.get("limitations") or [])
        projected.setdefault("answer_summary", "summary-present" if response.get("has_summary") else "")
        effective_stop=state.get("stop_reason") or response.get("stop_reason")
        effective_status=state.get("status") or response.get("status")
        if effective_stop:
            projected["stop_reason"] = effective_stop
        if effective_status:
            projected["final_status"] = effective_status
            projected["status"] = effective_status
        return projected

    def _synthetic_trace(self,case:EvalCase,mode:str)->dict[str,Any]:
        bad = "partial" in case.expected_statuses and "completed" not in case.expected_statuses
        status = "partial" if bad else "completed"; stop=None
        if case.category=="unsupported": stop="unsupported_task"
        elif case.category=="tool_exception": stop="tool_failures"
        elif case.category=="duplicate": stop="no_progress"
        elif case.category=="capability_gap": stop="capability_gap"
        elif case.category=="no_progress": stop="no_progress"
        elif case.input_type in {"publication_action","mcp_call"} and "allowed" not in case.case_id and "resource" not in case.case_id: stop="mcp_policy_rejection" if case.input_type=="mcp_call" else "approval_required"
        tools=list(case.required_tools_all) or (list(case.required_tools_any[:1]) if case.required_tools_any else [])
        if not tools and status=="completed": tools=["get_entity_month_table"]
        evidence=list(case.required_evidence_types) or (["entity_month_table"] if tools else [])
        spans=[{"span_name":"agent.run","status":"ok","attributes":{"revenue_poc.runtime.mode":mode,"revenue_poc.semantic.requirement_id":case.expected_semantic_requirement_id}}]
        for name in tools: spans.append({"span_name":"tool.execute","status":"ok","attributes":{"revenue_poc.tool.name":name,"args_fingerprint":hashlib.sha256((name+case.case_id).encode()).hexdigest()[:16],"revenue_poc.evidence.types":evidence}})
        if case.category in {"empty_result","incomplete_evidence","duplicate","no_progress"}: spans.extend([{"span_name":"evidence.validate","status":"ok","attributes":{}},{"span_name":"agent.replan","status":"ok","attributes":{}}])
        limitations=list(case.required_limitations)
        return {"schema_version":"revenue-poc-trace.v1","trace_id":"synthetic-"+hashlib.sha256(case.case_id.encode()).hexdigest()[:16],"operation_name":"eval.case","status":status,"final_status":status,"stop_reason":stop,"tool_call_count":len(tools),"replan_count":1 if "replan" in case.category or case.category in {"empty_result","incomplete_evidence","duplicate","no_progress"} else 0,"duration_ms":1.0,"spans":spans,"limitations":limitations,"safety_findings":[],"answer_summary":""}
    @staticmethod
    def _file_hash(path:Path)->str|None: return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    @staticmethod
    def _safe_tree_hash()->str:
        paths=[str(item) for item in sorted(Path("evaluation").rglob("*.py"))]+[str(item) for item in sorted(Path("observability").rglob("*.py"))]
        return hashlib.sha256("\n".join(paths).encode()).hexdigest()
