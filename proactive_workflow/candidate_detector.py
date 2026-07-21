from __future__ import annotations

from typing import Any, Protocol

from .models import InvestigationCandidate, Severity, stable_hash
from .policies import ProactivePolicy

class CandidateDetector(Protocol):
    detector_id: str
    version: str
    def detect(self, toolbox: Any, event: Any, catalog: Any, policy: ProactivePolicy) -> list[InvestigationCandidate]: ...

class RelationshipDetector:
    detector_id="revenue_inventory_relationship"; version="v1"
    def detect(self, toolbox: Any, event: Any, catalog: Any, policy: ProactivePolicy) -> list[InvestigationCandidate]:
        result=toolbox.get_revenue_inventory_relationship(entity_dimension="business_group")
        candidates=[]
        for row in result.get("rows", []):
            revenue=row.get("revenue_change"); inventory=row.get("inventory_change")
            if revenue is None or inventory is None: continue
            if revenue < -policy.minimum_absolute_change and inventory > policy.minimum_absolute_change:
                candidates.append(_candidate(event, "revenue_inventory_divergence", row, ["revenue_amount","inventory_amount"], "metric_relationship_analysis", "req.metric_relationship.v1", Severity.HIGH, "配對營收下降與庫存增加；僅描述性關係。", ["paired_revenue_inventory_evidence"], list(result.get("limitations") or [])))
            if revenue < -policy.minimum_absolute_change:
                candidates.append(_candidate(event, "revenue_drop", row, ["revenue_amount"], "entity_time_series", None, Severity.MEDIUM, "既有關係工具顯示最新期營收下降。", ["revenue_change"], ["需以 paired evidence 驗證。"] ))
            if inventory > policy.minimum_absolute_change:
                candidates.append(_candidate(event, "inventory_increase", row, ["inventory_amount"], "entity_time_series", None, Severity.MEDIUM, "既有關係工具顯示最新期庫存金額增加。", ["inventory_change"], ["庫存金額不代表庫存數量。"] ))
        return _cap(candidates, policy)

class QualityDetector:
    detector_id="data_quality"; version="v1"
    def __init__(self, findings: list[Any]) -> None: self.findings=findings
    def detect(self, toolbox: Any, event: Any, catalog: Any, policy: ProactivePolicy) -> list[InvestigationCandidate]:
        return [_quality_candidate(event, finding) for finding in self.findings if finding.blocks_investigation or finding.severity.value in {"high", "critical"}]

def detect_candidates(toolbox: Any, event: Any, catalog: Any, policy: ProactivePolicy, quality_findings: list[Any]) -> list[InvestigationCandidate]:
    all_items=[]
    for detector in (RelationshipDetector(), InventoryQuantityDetector(), QualityDetector(quality_findings)):
        all_items.extend(detector.detect(toolbox,event,catalog,policy))
    seen={};
    for item in all_items: seen.setdefault(item.deduplication_key,item)
    return list(seen.values())[:policy.candidate_limit_per_scan]

def _candidate(event: Any, candidate_type: str, row: dict[str,Any], metrics: list[str], task_type: str, requirement: str, severity: Severity, description: str, signals: list[str], limitations: list[str]) -> InvestigationCandidate:
    entity=str(row.get("entity_value") or "unknown"); period={"period_a":row.get("previous_month"),"period_b":row.get("month"),"mode":"period_pair"}; key=stable_hash({"event":event.current_fingerprint.get("fingerprint"),"type":candidate_type,"entity":entity,"period":period})
    return InvestigationCandidate(candidate_id="cand-"+key[:12],event_id=event.event_id,candidate_type=candidate_type,title=f"{candidate_type}: {entity}",description=description,metric_ids=metrics,dimension_ids=["business_group"],entity_scope={"dimension":"business_group","value":entity},period_scope=period,detector_id="revenue_inventory_relationship",detector_version="v1",severity=severity,confidence="medium",supporting_signals=[{"fields":signals,"summary":"detector signal only; investigation must independently validate evidence","initial_signal_tool":"get_revenue_inventory_relationship","primary_evidence":"metric_relationship" if candidate_type == "revenue_inventory_divergence" else "entity_time_series"}],required_task_type=task_type,semantic_requirement_id=requirement,deduplication_key=key,limitations=limitations)

def _quality_candidate(event: Any, finding: Any) -> InvestigationCandidate:
    key=stable_hash({"event":event.current_fingerprint.get("fingerprint"),"finding":finding.finding_id})
    return InvestigationCandidate(candidate_id="cand-"+key[:12],event_id=event.event_id,candidate_type="data_quality_issue",title=f"Data quality: {finding.check_id}",description=finding.description,metric_ids=[],dimension_ids=[],entity_scope={},period_scope={},detector_id="data_quality",detector_version="v1",severity=finding.severity,confidence="high" if finding.blocks_investigation else "medium",supporting_signals=[finding.evidence_summary],required_task_type="data_quality",semantic_requirement_id=None,deduplication_key=key,limitations=list(finding.limitations))
def _cap(items: list[InvestigationCandidate], policy: ProactivePolicy) -> list[InvestigationCandidate]: return items[:policy.candidate_limit_per_detector]

class InventoryQuantityDetector:
    detector_id="inventory_quantity_time_series"; version="v1"
    def detect(self, toolbox: Any, event: Any, catalog: Any, policy: ProactivePolicy) -> list[InvestigationCandidate]:
        relationship=toolbox.get_revenue_inventory_relationship(entity_dimension="business_group")
        candidates=[]
        for paired in relationship.get("rows", []):
            entity=paired.get("entity_value")
            if not entity: continue
            series=toolbox.get_entity_time_series(entity_dimension="business_group",entity_value=str(entity),metric="inventory_qty",start_month=paired.get("previous_month"),end_month=paired.get("month"))
            rows=series.get("rows") or []
            if len(rows) < 2 or rows[-1].get("mom_change") is None or rows[-1].get("mom_change") <= policy.minimum_absolute_change: continue
            row={"entity_value":entity,"previous_month":rows[-2].get("month"),"month":rows[-1].get("month")}
            candidates.append(_candidate(event,"inventory_quantity_increase",row,["inventory_qty"],"entity_time_series",None,Severity.MEDIUM,"既有 inventory quantity time-series 顯示最新期庫存數量增加。",["inventory_qty mom_change"],["庫存數量不可描述為庫存金額。","僅描述歷史資料。"] ))
        return _cap(candidates,policy)
