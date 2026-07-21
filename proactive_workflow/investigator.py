from __future__ import annotations

from typing import Any
from uuid import uuid4

from observability import get_recorder
from .models import InvestigationCandidate, InvestigationRun, utc_now
from .counter_evidence import CounterEvidenceStatus, assess_counter_evidence

class ProactiveInvestigator:
    def __init__(self, assistant_factory: Any) -> None: self.assistant_factory=assistant_factory
    def investigate(self, candidate: InvestigationCandidate) -> InvestigationRun:
        request_id="proactive-"+uuid4().hex[:12]
        run=InvestigationRun(investigation_id="inv-"+uuid4().hex[:12],candidate_id=candidate.candidate_id,event_id=candidate.event_id,agent_request_id=request_id,status="running",semantic_requirement_id=candidate.semantic_requirement_id)
        question=self._question(candidate)
        try:
            response=self.assistant_factory(request_id).answer(question)
            trace=response.get("agent_runtime") or {}
            status=trace.get("status") or ("completed" if response.get("summary") else "failed")
            run.status="completed" if status=="completed" else "partial" if status in {"partial","failed"} else status
            run.agent_runtime_status=status; run.stop_reason=trace.get("stop_reason")
            contract=response.get("answer_contract") or {}; run.canonical_task_summary={"task_type":candidate.required_task_type,"question":question,"semantic_requirement_id":candidate.semantic_requirement_id}
            run.evidence_summary=_summarize(response.get("domain_results") or [])
            with get_recorder().span("proactive.counter_evidence"):
                assessment=assess_counter_evidence(CounterEvidenceStatus.NOT_AVAILABLE)
            run.counter_evidence_summary={"status":assessment.status.value,"search_performed":assessment.search_performed,"reason":assessment.limitation}
            run.limitations.append(assessment.limitation)
            if assessment.confidence_cap == "low": run.confidence="low"
            run.limitations=list(dict.fromkeys([*candidate.limitations, *(contract.get("limitations") or []), *(["調查未完成。"] if run.status != "completed" else [])]))
            run.confidence="medium" if run.status=="completed" else "low"; run.finished_at=utc_now()
        except (ValueError, RuntimeError, OSError, KeyError) as exc:
            run.status="failed"; run.stop_reason="investigation_error"; run.limitations=[f"調查失敗：{type(exc).__name__}"]; run.finished_at=utc_now()
        return run
    def _question(self, candidate: InvestigationCandidate) -> str:
        entity=candidate.entity_scope.get("value") or "目標實體"; period=candidate.period_scope.get("period_b") or "可用期間"
        if candidate.candidate_type == "revenue_inventory_divergence":
            return f"調查 {period} 的 {entity} 是否出現營收下降但庫存上升的背離。請用 paired revenue/inventory primary evidence、supporting evidence 與 counter evidence 驗證，並清楚區分描述性關係、proxy 指標與可證實原因。"
        metric = "營收" if candidate.candidate_type == "revenue_drop" else "庫存金額"
        return f"調查 {period} 的 {entity} 是否出現 {metric} 的明顯變化。請提供歷史趨勢、限制與可取得的反向證據。"
def _summarize(results: list[dict[str,Any]]) -> list[dict[str,Any]]:
    return [{"domain":item.get("domain"),"status":item.get("status"),"used_tools":item.get("used_tools",[]),"finding_count":len(item.get("key_findings",[]))} for item in results[:5] if isinstance(item,dict)]
