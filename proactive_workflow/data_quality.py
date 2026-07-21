from __future__ import annotations

from typing import Any

from .models import DataQualityFinding, Severity, stable_hash

def run_data_quality_checks(context: Any, catalog: Any) -> list[DataQualityFinding]:
    findings: list[DataQualityFinding] = []
    frames = {"revenue_logical": context.revenue_df, "inventory_logical": context.inventory_df}
    periods: dict[str, set[str]] = {}
    for dataset_id, frame in frames.items():
        contract = next(item for item in catalog.list_data_contracts() if item.dataset_id == dataset_id)
        period_field = "month_key" if "month_key" in frame.columns else "month"
        missing = [name for name in contract.required_columns if name not in frame.columns and not (name == "month" and period_field in frame.columns) and not (name == "revenue" and "revenue_amount" in frame.columns)]
        if missing: findings.append(_finding(dataset_id, "required_columns", Severity.CRITICAL, "必要欄位缺失", True, {"missing_columns": missing}))
        if frame.empty: findings.append(_finding(dataset_id, "empty_dataset", Severity.CRITICAL, "邏輯資料集為空", True, {}))
        parsed = frame[period_field].dropna().astype(str) if period_field in frame.columns else []
        valid = [item for item in parsed if len(item) == 7 and item[4] == "-"]
        periods[dataset_id] = set(valid)
        if len(valid) != len(parsed): findings.append(_finding(dataset_id, "invalid_period", Severity.HIGH, "存在無法解析的期間", False, {"invalid_count": len(parsed)-len(valid)}))
        if valid:
            ordered = sorted(set(valid)); expected = _month_span(ordered[0], ordered[-1])
            if len(expected - set(valid)): findings.append(_finding(dataset_id, "period_continuity", Severity.LOW, "期間不連續", False, {"missing_period_count": len(expected-set(valid))}))
        numeric = [item for item in contract.numeric_fields if item in frame.columns]
        bad = sum(int(frame[item].isna().sum()) for item in numeric)
        if bad: findings.append(_finding(dataset_id, "numeric_missing", Severity.LOW, "數值欄位含缺失或非數值", False, {"count": bad}))
        entities = [item for item in contract.entity_fields if item in frame.columns]
        if entities and all(frame[item].dropna().empty for item in entities): findings.append(_finding(dataset_id, "missing_entity_dimension", Severity.HIGH, "主要實體維度全數缺失", True, {}))
        keys = [item for item in [period_field, *entities[:1]] if item in frame.columns]
        if keys and int(frame.duplicated(keys).sum()) > 0: findings.append(_finding(dataset_id, "duplicate_logical_key", Severity.MEDIUM, "存在重複 logical key", False, {"count": int(frame.duplicated(keys).sum())}))
    if periods["revenue_logical"] and periods["inventory_logical"] and not periods["revenue_logical"] & periods["inventory_logical"]:
        findings.append(_finding("revenue_inventory", "no_period_overlap", Severity.CRITICAL, "營收與庫存沒有重疊期間", True, {}))
    return findings

def _finding(dataset_id: str, check_id: str, severity: Severity, description: str, blocks: bool, summary: dict[str, Any]) -> DataQualityFinding:
    return DataQualityFinding(finding_id="qf-"+stable_hash({"dataset":dataset_id,"check":check_id,"summary":summary})[:12], dataset_id=dataset_id, check_id=check_id, severity=severity, status="open", description=description, affected_scope=summary, evidence_summary=summary, suggested_action="review data contract and source load", blocks_investigation=blocks, limitations=[description])

def _month_span(start: str, end: str) -> set[str]:
    year, month = map(int, start.split("-")); end_year, end_month = map(int, end.split("-")); values=set()
    while (year, month) <= (end_year, end_month):
        values.add(f"{year:04d}-{month:02d}"); year, month = (year+1, 1) if month == 12 else (year, month+1)
    return values
