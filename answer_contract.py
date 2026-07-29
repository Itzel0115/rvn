from __future__ import annotations

from dataclasses import asdict
from typing import Any

from analysis_rubrics import assign_evidence_roles, rubric_result_to_dict
from analysis_tools import AnalysisToolbox
from answer_policy import AnswerPolicy, get_answer_policy
from evidence_projector import build_display_blocks_from_roles
from config import (
    COL_ANOMALY_REASON,
    COL_ANOMALY_SIGNAL,
    COL_ANOMALY_TYPE,
    COL_GROUP_CODE,
    COL_INV_AMOUNT,
    COL_INV_QTY,
    COL_MONTH,
    COL_PLATFORM,
    COL_REVENUE,
)
from utils import format_number


UNSUPPORTED_FIELD_HINTS = {
    "gross margin": ["gross margin", "毛利"],
    "cost": ["cost", "成本"],
    "operating profit": ["operating profit", "營業利益", "營業利潤"],
    "eps": ["eps"],
    "cashflow": ["cashflow", "cash flow", "現金流"],
    "customer": ["customer", "客戶"],
    "order": ["order", "訂單"],
    "product": ["product", "產品", "商品"],
    "sku": ["sku"],
    "shipment": ["shipment", "shipping", "出貨"],
    "market demand": ["market demand", "demand", "市場需求"],
    "forecast": ["forecast", "predict", "prediction", "預測", "下個月", "下月", "next month"],
}

WHY_OR_FORECAST_HINTS = [
    "why",
    "cause",
    "root cause",
    "forecast",
    "predict",
    "prediction",
    "為什麼",
    "原因",
    "解釋",
    "診斷",
    "預測",
    "下個月",
    "下月",
]

MISSING_INFO_TEXT = "目前資料中尚未提供足夠資訊"
TURNOVER_PROXY_LIMITATION = "此為營收與庫存資料推導的 proxy，非正式周轉指標。"
PROXY_ANOMALY_LIMITATION = "這是根據目前營收與庫存資料偵測出的風險訊號，尚不能直接代表根本原因。"


def build_answer_contract(
    *,
    request_id: str,
    question: str,
    routing: Any,
    domain_results: list[Any],
    toolbox: AnalysisToolbox,
    task_profile: Any | None = None,
    answer_plan: Any | None = None,
) -> dict[str, Any]:
    unsupported_topics = _detect_unsupported_topics(question)
    tools_used = _collect_tools(domain_results)
    evidence = _collect_evidence(domain_results)
    if unsupported_topics:
        tools_used = []
        evidence = []

    coverage = toolbox.get_data_coverage()
    latest_month = coverage["months"][-1] if coverage.get("months") else None
    filters = asdict(routing.filters) if hasattr(routing, "filters") else {}
    task_time_scope = getattr(task_profile, "time_scope", {}) if task_profile is not None else {}
    if isinstance(task_time_scope, dict) and task_time_scope.get("mode") == "period_pair":
        filters = dict(filters)
        filters["month"] = None
    answer_type = (
        "unsupported"
        if unsupported_topics
        else (getattr(routing, "answer_strategy", None) or getattr(routing, "question_type", "query"))
    )
    policy = get_answer_policy(routing, question)
    rubric_result = assign_evidence_roles(task_profile, answer_plan, domain_results) if task_profile is not None else None

    answer = _build_direct_answer(
        question=question,
        routing=routing,
        domain_results=domain_results,
        unsupported_topics=unsupported_topics,
        latest_month=latest_month,
    )
    limitations = _build_limitations(
        question=question,
        routing=routing,
        domain_results=domain_results,
        unsupported_topics=unsupported_topics,
        has_evidence=bool(evidence),
    )
    display_blocks = _build_display_blocks(
        question=question,
        routing=routing,
        domain_results=domain_results,
        answer=answer,
        limitations=limitations,
        policy=policy,
        task_profile=task_profile,
        answer_plan=answer_plan,
        rubric_result=rubric_result,
    )
    if getattr(task_profile, "task_family", None) in {
        "cross_section_compare",
        "performance_assessment",
        "time_compare",
        "latest_month_platform_summary",
        "latest_month_entity_summary",
        "period_pair_compare",
        "entity_period_pair_table_lookup",
        "entity_multi_month_table_lookup",
        "entity_period_pair_metric_lookup",
        "forecast_unsupported",
        "entity_ranking",
        "entity_time_series",
        "overall_trend_analysis",
        "entity_trend_comparison",
        "metric_relationship_analysis",
        "contribution_analysis",
        "parent_child_drilldown",
        "risk_scan",
    }:
        answer = _compose_answer_from_display_blocks(display_blocks)

    return {
        "request_id": request_id,
        "answer_type": answer_type,
        "answer": answer,
        "evidence": evidence,
        "tools_used": tools_used,
        "data_scope": {
            "question_type": getattr(routing, "question_type", "query"),
            "domains": list(getattr(routing, "domains", [])),
            "filters": filters,
            "time_scope": task_time_scope if isinstance(task_time_scope, dict) else {},
            "available_months": coverage.get("months", []),
            "latest_month": latest_month,
            "supported_domains": coverage.get("supported_domains", {}),
        },
        "limitations": limitations,
        "suggested_followups": _suggest_followups(
            answer_type=answer_type,
            unsupported_topics=unsupported_topics,
            filters=filters,
        ),
        "display_blocks": display_blocks,
        "role_based_evidence": rubric_result_to_dict(rubric_result) if rubric_result is not None else None,
        "task_profile": asdict(task_profile) if task_profile is not None else None,
        "answer_plan": asdict(answer_plan) if answer_plan is not None else None,
    }


def build_data_quality_answer_contract(
    *,
    request_id: str,
    routing: Any,
    toolbox: AnalysisToolbox,
    context: Any,
    task_profile: Any | None = None,
    answer_plan: Any | None = None,
) -> dict[str, Any]:
    coverage = toolbox.get_data_coverage()
    mapping = toolbox.get_mapping_summary()
    messages = getattr(context, "messages", None)
    warnings = list(getattr(messages, "warnings", []) if messages else [])
    errors = list(getattr(messages, "errors", []) if messages else [])
    months = coverage.get("months", [])
    latest_month = months[-1] if months else None
    real_quality = coverage.get("real_data_quality_report") or {}
    filters = asdict(routing.filters) if hasattr(routing, "filters") else {}
    mapping_success = bool(coverage.get("mapping_success", mapping.get("mapping_success")))

    if real_quality:
        answer = (
            f"目前真實資料已讀取：營收 {real_quality.get('revenue_rows', coverage.get('revenue_rows', 0))} 筆，"
            f"庫存 {real_quality.get('inventory_rows', coverage.get('inventory_rows', 0))} 筆；"
            f"共同月份 {len(real_quality.get('common_months', []))} 個，"
            f"最新共同月份為 {real_quality.get('latest_common_month') or latest_month or 'N/A'}。"
            f"aligned rows={real_quality.get('aligned_rows', 0)}，"
            f"both={real_quality.get('both_rows', 0)}，"
            f"revenue_only={real_quality.get('revenue_only_rows', 0)}，"
            f"inventory_only={real_quality.get('inventory_only_rows', 0)}。"
        )
    else:
        answer = (
            f"目前資料涵蓋 {len(months)} 個月份，最新月份為 {latest_month or 'N/A'}。"
            f"營收資料 {coverage.get('revenue_rows', 0)} 筆，"
            f"庫存資料 {coverage.get('inventory_rows', 0)} 筆，"
            f"mapping 資料 {coverage.get('mapping_rows', 0)} 筆，"
            f"mapping_success={mapping_success}。"
        )
    if errors:
        answer += f" 另外，目前有 {len(errors)} 筆 pipeline errors。"
    elif warnings:
        answer += f" 另外，目前有 {len(warnings)} 筆 pipeline warnings。"
    else:
        answer += " 目前沒有額外的 pipeline warnings 或 errors。"

    limitations = [
        "目前資料品質報告僅反映已載入資料與 pipeline 狀態。",
        "營收/庫存 ratio 僅在 revenue 與 inventory 同時存在且分母合法時計算，屬 proxy 指標。",
        "若有 missing 事業群、missing 產品線、revenue_only 或 inventory_only rows，需納入解讀限制。",
    ]
    if warnings:
        limitations.append("目前仍有 pipeline warnings，解讀結果時需一併納入。")
    if errors:
        limitations.append("目前存在 pipeline errors，部分結果可能需要重新檢查資料處理流程。")

    evidence = [
        {
            "domain": "data_quality",
            "summary": (
                f"coverage: months={len(months)}, latest_month={latest_month}, "
                f"revenue_rows={coverage.get('revenue_rows', 0)}, inventory_rows={coverage.get('inventory_rows', 0)}, "
                f"mapping_rows={coverage.get('mapping_rows', 0)}, mapping_success={mapping_success}"
            ),
            "details": {
                "available_months": months,
                "latest_month": latest_month,
                "revenue_rows": coverage.get("revenue_rows", 0),
                "inventory_rows": coverage.get("inventory_rows", 0),
                "mapping_rows": coverage.get("mapping_rows", 0),
                "mapping_success": mapping_success,
                "real_data_quality_report": real_quality,
            },
        },
        {
            "domain": "data_quality",
            "summary": f"pipeline: warnings={len(warnings)}, errors={len(errors)}",
            "details": {
                "pipeline_warnings": warnings,
                "pipeline_errors": errors,
                "bridge_candidate_count": mapping.get("bridge_candidate_count", 0),
            },
        },
    ]

    return {
        "request_id": request_id,
        "answer_type": "data_quality",
        "answer": answer,
        "evidence": evidence,
        "tools_used": ["get_data_coverage", "get_mapping_summary"],
        "data_scope": {
            "question_type": getattr(routing, "question_type", "data_quality"),
            "domains": list(getattr(routing, "domains", [])),
            "filters": filters,
            "available_months": months,
            "latest_month": latest_month,
            "revenue_rows": coverage.get("revenue_rows", 0),
            "inventory_rows": coverage.get("inventory_rows", 0),
            "mapping_rows": coverage.get("mapping_rows", 0),
            "mapping_success": mapping_success,
            "real_data_quality_report": real_quality,
            "pipeline_warnings": warnings,
            "pipeline_errors": errors,
            "supported_domains": coverage.get("supported_domains", {}),
        },
        "limitations": list(dict.fromkeys(limitations)),
        "suggested_followups": [
            "要不要查看目前各月份的資料覆蓋情況？",
            "要不要列出所有 pipeline warnings 與 errors？",
            "要不要檢查目前資料品質與 mapping 狀態？",
        ],
        "display_blocks": {
            "headline": answer,
            "key_observations": [
                f"coverage: months={len(months)}, latest_month={latest_month}",
                f"rows: revenue={coverage.get('revenue_rows', 0)}, inventory={coverage.get('inventory_rows', 0)}, mapping={coverage.get('mapping_rows', 0)}",
            ],
            "table": None,
            "limitations": list(dict.fromkeys(limitations))[:3],
        },
        "task_profile": asdict(task_profile) if task_profile is not None else None,
        "answer_plan": asdict(answer_plan) if answer_plan is not None else None,
    }


def render_answer_contract(request_id: str, contract: dict[str, Any]) -> str:
    answer = str(contract.get("answer", "")).strip() or "目前沒有可呈現的直接回答。"
    lines = [f"Request ID: {request_id}", "", answer]

    evidence = contract.get("evidence", [])
    if evidence:
        lines.extend(["", "Evidence:"])
        for item in evidence[:5]:
            lines.append(f"- {item.get('summary')}")

    tools_used = contract.get("tools_used", [])
    if tools_used:
        lines.extend(["", "Tools used:"])
        lines.append("- " + ", ".join(tools_used))

    data_scope = contract.get("data_scope", {})
    scope_parts: list[str] = []
    if data_scope:
        filters = data_scope.get("filters", {})
        time_scope = data_scope.get("time_scope", {}) if isinstance(data_scope.get("time_scope", {}), dict) else {}
        if time_scope.get("period_a") and time_scope.get("period_b"):
            scope_parts.append(f"period_a={time_scope['period_a']}")
            scope_parts.append(f"period_b={time_scope['period_b']}")
        elif time_scope.get("mode") == "recent_n_months" and time_scope.get("recent_n"):
            scope_parts.append(f"recent_n_months={time_scope['recent_n']}")
        if filters.get("month"):
            scope_parts.append(f"month={filters['month']}")
        if filters.get("platform"):
            scope_parts.append(f"platform={filters['platform']}")
        if filters.get("group_code"):
            scope_parts.append(f"group_code={filters['group_code']}")
        if data_scope.get("latest_month"):
            scope_parts.append(f"latest_month={data_scope['latest_month']}")
        if data_scope.get("mapping_success") is not None:
            scope_parts.append(f"mapping_success={data_scope['mapping_success']}")
    if scope_parts:
        lines.extend(["", "Data scope:"])
        lines.append("- " + ", ".join(scope_parts))

    limitations = contract.get("limitations", [])
    if limitations:
        lines.extend(["", "Limitations:"])
        for item in limitations:
            lines.append(f"- {item}")

    followups = contract.get("suggested_followups", [])
    if followups:
        lines.extend(["", "Suggested follow-ups:"])
        for item in followups[:3]:
            lines.append(f"- {item}")

    return "\n".join(lines)


def _build_display_blocks(
    *,
    question: str,
    routing: Any,
    domain_results: list[Any],
    answer: str,
    limitations: list[str],
    policy: AnswerPolicy,
    task_profile: Any | None = None,
    answer_plan: Any | None = None,
    rubric_result: Any | None = None,
) -> dict[str, Any]:
    max_items = int(getattr(answer_plan, "max_key_observations", policy.max_key_observations) or 3)
    task_family = getattr(task_profile, "task_family", None)
    answer_type = getattr(routing, "answer_strategy", None) or getattr(routing, "question_type", "query")
    if task_family == "chart_request" or answer_type == "chart":
        return _build_chart_display_blocks(domain_results, answer, limitations)

    if task_family == "metric_relationship_analysis" and getattr(task_profile, "time_scope", {}).get("mode") == "recent_n_months":
        return _build_recent_relationship_display_blocks(task_profile, domain_results, limitations, max_items)
    if task_family == "metric_relationship_analysis" and "inventory_qty" in ((getattr(task_profile, "task_requirements", {}) or {}).get("requested_metrics") or []):
        return _build_relationship_cross_check_display_blocks(task_profile, domain_results, limitations, max_items)
    if task_family == "performance_assessment":
        blocks = _build_performance_assessment_display_blocks(task_profile, domain_results, limitations, max_items)
        return blocks
    if task_family == "risk_scan":
        return _build_risk_scan_display_blocks(task_profile, domain_results, limitations, max_items)
    if task_family == "cross_section_compare" and "proxy" in ((getattr(task_profile, "task_requirements", {}) or {}).get("requested_operations") or []) and _find_turnover_proxy_rows(domain_results):
        return _build_risk_scan_display_blocks(task_profile, domain_results, limitations, max_items)
    if task_family == "entity_period_pair_table_lookup" and _has_multimetric_period_pair_evidence(domain_results):
        return _build_multimetric_period_pair_display_blocks(task_profile, domain_results, limitations, max_items)
    if task_family == "entity_trend_comparison" and _is_management_risk_selection_task(task_profile):
        return _build_management_risk_selection_display_blocks(task_profile, domain_results, limitations, max_items)
    if task_family == "entity_trend_comparison" and _has_multimetric_trend_evidence(domain_results):
        return _build_multimetric_trend_display_blocks(task_profile, domain_results, limitations, max_items)

    if rubric_result is not None:
        return build_display_blocks_from_roles(
            task_profile=task_profile,
            answer_plan=answer_plan,
            rubric_result=rubric_result,
            limitations=limitations,
        )
    if task_family == "cross_section_compare":
        return _build_cross_section_compare_display_blocks(task_profile, domain_results, limitations, max_items)
    if task_family == "time_compare":
        return _build_time_compare_display_blocks(domain_results, answer, limitations, max_items)

    if answer_type == "performance_weakness":
        blocks = _build_performance_weakness_display_blocks(domain_results)
        blocks["key_observations"] = list(blocks.get("key_observations", []))[:max_items]
        blocks["limitations"] = list(dict.fromkeys(blocks.get("limitations", []) + limitations))[:3]
        blocks.setdefault("table", None)
        return blocks

    return {
        "headline": _extract_headline(answer),
        "key_observations": _collect_policy_key_observations(domain_results, policy)[:max_items],
        "table": None,
        "limitations": list(dict.fromkeys(limitations))[:3],
    }


def _build_recent_relationship_display_blocks(
    task_profile: Any,
    domain_results: list[Any],
    limitations: list[str],
    max_items: int,
) -> dict[str, Any]:
    evidence_items = [item for result in domain_results for item in getattr(result, "evidence", [])]
    trend_by_metric: dict[str, dict[str, list[dict[str, Any]]]] = {}
    relationship_rows: list[dict[str, Any]] = []
    for item in evidence_items:
        if item.get("source_tool") == "get_entity_trend_comparison":
            metric = str(item.get("metric") or "")
            grouped: dict[str, list[dict[str, Any]]] = {}
            for row in item.get("rows") or []:
                if isinstance(row, dict):
                    grouped.setdefault(str(row.get("entity_value")), []).append(row)
            for rows in grouped.values():
                rows.sort(key=lambda row: str(row.get("month") or ""))
            if metric:
                trend_by_metric[metric] = grouped
        elif item.get("source_tool") == "get_revenue_inventory_relationship":
            relationship_rows = [row for row in item.get("rows") or [] if isinstance(row, dict)]

    candidates: list[dict[str, Any]] = []
    entities = set(trend_by_metric.get("revenue_amount", {})) & set(trend_by_metric.get("inventory_amount", {}))
    for entity in sorted(entities):
        revenue_rows = trend_by_metric["revenue_amount"].get(entity, [])
        inventory_rows = trend_by_metric["inventory_amount"].get(entity, [])
        qty_rows = trend_by_metric.get("inventory_qty", {}).get(entity, [])
        if not (_is_consecutive_direction(revenue_rows, negative=True) and _is_consecutive_direction(inventory_rows, positive=True)):
            continue
        latest_revenue = _latest_non_null_change(revenue_rows)
        latest_inventory = _latest_non_null_change(inventory_rows)
        latest_qty = _latest_non_null_change(qty_rows)
        candidates.append({
            "entity_value": entity,
            "latest_month": revenue_rows[-1].get("month") if revenue_rows else None,
            "revenue_change": latest_revenue,
            "inventory_amount_change": latest_inventory,
            "inventory_qty_change": latest_qty,
            "qty_consistent": latest_qty is not None and latest_qty > 0,
            "severity": abs(float(latest_revenue or 0)) + abs(float(latest_inventory or 0)),
        })
    candidates.sort(key=lambda row: row.get("severity") or 0, reverse=True)

    observations: list[str] = []
    table_rows: list[dict[str, Any]] = []
    if candidates:
        top = candidates[0]
        headline = f"最近 {getattr(task_profile, 'time_scope', {}).get('recent_n') or 3} 個月中，最異常的營收連降且庫存金額連升事業群是 {top.get('entity_value')}。"
        observations.append(
            f"{top.get('entity_value')} 最新月營收變化 {_format_number(top.get('revenue_change'))}，庫存金額變化 {_format_number(top.get('inventory_amount_change'))}。"
        )
        qty_text = "同向上升" if top.get("qty_consistent") else "未同向上升或資料不足"
        observations.append(f"庫存 QTY 反證檢查：{qty_text}，最新月 QTY 變化 {_format_number(top.get('inventory_qty_change'))}。")
        table_rows = candidates[:8]
    else:
        headline = "最近三個月未找到同時符合『營收連續下降且庫存金額連續上升』的事業群。"
        downside_rows = [row for row in relationship_rows if row.get("revenue_change") is not None and row.get("inventory_change") is not None]
        downside_rows.sort(key=lambda row: (float(row.get("revenue_change") or 0), -float(row.get("inventory_change") or 0)))
        if downside_rows:
            row = downside_rows[0]
            observations.append(
                f"最接近的最新月背離訊號是 {row.get('entity_value')}：營收變化 {_format_number(row.get('revenue_change'))}，庫存金額變化 {_format_number(row.get('inventory_change'))}。"
            )
        observations.append("反證：三個月序列檢查未同時滿足兩段營收下降與兩段庫存金額上升。")
        table_rows = [_canonical_relationship_table_row(row) for row in downside_rows[:8]]

    merged_limitations = list(dict.fromkeys([
        *limitations,
        "營收/庫存關係為歷史描述與 proxy，不代表因果或正式庫存週轉率。",
        "連續三個月條件以現有可對齊月份和事業群彙總資料判斷。",
    ]))
    return {
        "headline": headline,
        "key_observations": observations[:max_items],
        "table": {
            "columns": ["entity_value", "latest_month", "revenue_change", "inventory_amount_change", "inventory_qty_change", "relationship_label"],
            "rows": table_rows,
        },
        "limitations": merged_limitations[:4],
    }



def _canonical_relationship_table_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "entity_value": row.get("entity_value") or row.get("business_group") or row.get("platform") or row.get("entity"),
        "latest_month": row.get("latest_month") or row.get("month"),
        "revenue_change": row.get("revenue_change") or row.get("revenue_amount_change"),
        "inventory_amount_change": row.get("inventory_amount_change") if row.get("inventory_amount_change") is not None else row.get("inventory_change"),
        "inventory_qty_change": row.get("inventory_qty_change"),
        "relationship_label": row.get("relationship_label"),
    }


def _has_multimetric_period_pair_evidence(domain_results: list[Any]) -> bool:
    metrics = {item.get("metric") for item in _iter_evidence_items(domain_results) if item.get("source_tool") == "get_entity_period_pair_table"}
    return len(metrics & {"revenue_amount", "inventory_amount", "inventory_qty"}) > 1


def _has_multimetric_trend_evidence(domain_results: list[Any]) -> bool:
    metrics = {item.get("metric") for item in _iter_evidence_items(domain_results) if item.get("source_tool") == "get_entity_trend_comparison"}
    return len(metrics & {"revenue_amount", "inventory_amount", "inventory_qty"}) > 1


def _build_multimetric_period_pair_display_blocks(task_profile: Any, domain_results: list[Any], limitations: list[str], max_items: int) -> dict[str, Any]:
    evidence_by_metric = {item.get("metric"): item for item in _iter_evidence_items(domain_results) if item.get("source_tool") == "get_entity_period_pair_table"}
    revenue_rows = {str(row.get("entity_value")): row for row in (evidence_by_metric.get("revenue_amount") or {}).get("rows", [])}
    inventory_rows = {str(row.get("entity_value")): row for row in (evidence_by_metric.get("inventory_amount") or {}).get("rows", [])}
    qty_rows = {str(row.get("entity_value")): row for row in (evidence_by_metric.get("inventory_qty") or {}).get("rows", [])}
    top_n = (getattr(task_profile, "task_requirements", {}) or {}).get("top_n") or 3
    ranked = sorted([row for row in revenue_rows.values() if row.get("change") is not None], key=lambda row: float(row.get("change") or 0))[: int(top_n)]
    table_rows: list[dict[str, Any]] = []
    for row in ranked:
        entity = str(row.get("entity_value"))
        inv = inventory_rows.get(entity, {})
        qty = qty_rows.get(entity, {})
        table_rows.append({
            "entity_value": entity,
            "period_a": row.get("period_a") or (evidence_by_metric.get("revenue_amount") or {}).get("period_a"),
            "period_b": row.get("period_b") or (evidence_by_metric.get("revenue_amount") or {}).get("period_b"),
            "revenue_change": row.get("change"),
            "inventory_amount_change": inv.get("change"),
            "inventory_qty_change": qty.get("change"),
            "risk_sort_basis": "revenue decline plus inventory amount/qty cross-check",
        })
    headline = "結論：已先依營收下降幅度篩選，再交叉檢查同期庫存金額與庫存數量變化。"
    observations = []
    if table_rows:
        first = table_rows[0]
        observations.append(f"營收下降最多的是 {first.get('entity_value')}，營收變化 {_format_number(first.get('revenue_change'))}。")
        observations.append(f"其庫存金額變化 {_format_number(first.get('inventory_amount_change'))}，庫存數量變化 {_format_number(first.get('inventory_qty_change'))}。")
    return {
        "headline": headline,
        "key_observations": observations[:max_items],
        "table": {"columns": ["entity_value", "period_a", "period_b", "revenue_change", "inventory_amount_change", "inventory_qty_change", "risk_sort_basis"], "rows": table_rows},
        "limitations": list(dict.fromkeys([*limitations, "風險排序為 deterministic cross-check proxy，不代表根本原因。"]))[:4],
    }


def _is_management_risk_selection_task(task_profile: Any | None) -> bool:
    requirements = getattr(task_profile, "task_requirements", {}) or {}
    operations = set(requirements.get("requested_operations") or [])
    metrics = set(requirements.get("requested_metrics") or [])
    return bool(
        requirements.get("requires_named_selection")
        and (requirements.get("requested_top_n") or requirements.get("top_n"))
        and {"revenue_amount", "inventory_amount", "inventory_qty"}.issubset(metrics)
        and ({"rank", "select"} & operations)
    )


def _build_management_risk_selection_display_blocks(task_profile: Any, domain_results: list[Any], limitations: list[str], max_items: int) -> dict[str, Any]:
    requirements = getattr(task_profile, "task_requirements", {}) or {}
    top_n = int(requirements.get("requested_top_n") or requirements.get("top_n") or 2)
    candidates = _rank_management_risk_candidates(domain_results)
    selected = candidates[:top_n]
    if len(selected) < top_n:
        return {
            "headline": "結論：目前 evidence 不足以完成具名 Top-N 管理風險選擇。",
            "key_observations": ["缺少足夠的營收趨勢、庫存金額、庫存數量或異常訊號交叉證據。"],
            "table": None,
            "limitations": list(dict.fromkeys([*limitations, "完成管理風險選擇前，必須同時具備多指標證據與具名候選對象。"]))[:4],
        }

    first = selected[0].get("entity_value")
    second = selected[1].get("entity_value") if len(selected) > 1 else None
    headline = f"結論：第一優先事業群是 {first}" + (f"；第二優先事業群是 {second}。" if second else "。")
    observations: list[str] = []
    for item in selected:
        rank = int(item.get("rank") or 0)
        label = "第一優先" if rank == 1 else "第二優先" if rank == 2 else f"第 {rank} 優先"
        observations.append(
            f"{label}事業群 {item.get('entity_value')}：支持證據：{'; '.join(item.get('supporting_evidence') or ['N/A'])}。"
        )
        observations.append(
            f"{label}事業群 {item.get('entity_value')}：可能反證：{'; '.join(item.get('counter_evidence') or ['目前未見明確降低風險證據'])}。"
        )
        observations.append(
            f"{label}事業群 {item.get('entity_value')}：管理層下一步：{item.get('next_action')}。"
        )
    observations.append(f"排序方法：先比較完整事業群集合，再以營收趨勢、庫存金額、庫存數量與異常訊號形成綜合風險分數；本次選出 {len(selected)} 個具名事業群。")
    table_rows = [
        {
            "rank": row.get("rank"),
            "entity_value": row.get("entity_value"),
            "composite_risk_score": round(float(row.get("score") or 0), 3),
            "latest_month": row.get("latest_month"),
            "revenue_change_pct": row.get("revenue_change_pct"),
            "inventory_amount_change_pct": row.get("inventory_amount_change_pct"),
            "inventory_qty_change_pct": row.get("inventory_qty_change_pct"),
            "anomaly_signal": row.get("anomaly_signal"),
            "evidence_metric_count": row.get("evidence_metric_count"),
            "counter_evidence": "；".join(row.get("counter_evidence") or []),
            "next_action": row.get("next_action"),
        }
        for row in selected
    ]
    merged_limitations = list(dict.fromkeys([
        *limitations,
        "多指標管理風險排序為歷史資料 proxy，不代表因果或預測。",
        "異常訊號只能指出需追蹤的觀察點，不能直接證明產品賣不出去或庫存增加原因。",
    ]))
    return {
        "headline": headline,
        "key_observations": observations[: max(max_items, top_n * 3 + 1)],
        "table": {
            "columns": ["rank", "entity_value", "composite_risk_score", "latest_month", "revenue_change_pct", "inventory_amount_change_pct", "inventory_qty_change_pct", "anomaly_signal", "evidence_metric_count", "counter_evidence", "next_action"],
            "rows": table_rows,
        },
        "limitations": merged_limitations[:4],
    }


def _rank_management_risk_candidates(domain_results: list[Any]) -> list[dict[str, Any]]:
    metric_summaries: dict[str, dict[str, dict[str, Any]]] = {}
    latest_month = None
    for item in _iter_evidence_items(domain_results):
        if item.get("source_tool") != "get_entity_trend_comparison":
            continue
        metric = str(item.get("metric") or "")
        if not metric:
            continue
        by_entity: dict[str, dict[str, Any]] = {}
        for summary in item.get("entity_summaries") or []:
            if not isinstance(summary, dict):
                continue
            entity = str(summary.get("entity_value") or "").strip()
            if not entity or entity in {"N/A", "未對應", "None", "null"}:
                continue
            by_entity[entity] = summary
            latest_month = latest_month or summary.get("latest_month")
        if by_entity:
            metric_summaries[metric] = by_entity
    entities = set().union(*(set(value) for value in metric_summaries.values())) if metric_summaries else set()
    anomaly_by_entity: dict[str, dict[str, Any]] = {}
    for row in _find_anomaly_rows(domain_results):
        entity = str(row.get("entity_value") or row.get(COL_GROUP_CODE) or row.get("group_code") or row.get(COL_PLATFORM) or row.get("platform") or "").strip()
        if entity:
            anomaly_by_entity[entity] = row
            entities.add(entity)
    candidates: list[dict[str, Any]] = []
    for entity in sorted(entities):
        metrics = {metric: metric_summaries.get(metric, {}).get(entity) for metric in metric_summaries}
        revenue = metrics.get("revenue_amount") or {}
        amount = metrics.get("inventory_amount") or {}
        qty = metrics.get("inventory_qty") or {}
        ratio = metrics.get("revenue_inventory_amount_ratio") or {}
        anomaly = anomaly_by_entity.get(entity, {})
        score = 0.0
        supporting: list[str] = []
        counter: list[str] = []
        revenue_pct = _as_float(revenue.get("overall_change_pct"))
        amount_pct = _as_float(amount.get("overall_change_pct"))
        qty_pct = _as_float(qty.get("overall_change_pct"))
        ratio_pct = _as_float(ratio.get("overall_change_pct"))
        if revenue_pct is not None:
            if revenue_pct < 0:
                score += min(abs(revenue_pct), 2.0) * 2.0
                supporting.append(f"營收趨勢下降 {revenue_pct:.1%}")
            else:
                counter.append(f"營收仍成長 {revenue_pct:.1%}")
        if amount_pct is not None:
            if amount_pct > 0:
                score += min(amount_pct, 2.0) * 1.5
                supporting.append(f"庫存金額上升 {amount_pct:.1%}")
            else:
                counter.append(f"庫存金額下降 {amount_pct:.1%}")
        if qty_pct is not None:
            if qty_pct > 0:
                score += min(qty_pct, 2.0) * 1.2
                supporting.append(f"庫存數量上升 {qty_pct:.1%}")
            else:
                counter.append(f"庫存數量下降 {qty_pct:.1%}")
        if ratio_pct is not None:
            if ratio_pct < 0:
                score += min(abs(ratio_pct), 2.0)
                supporting.append(f"營收/庫存效率 proxy 走弱 {ratio_pct:.1%}")
            else:
                counter.append(f"營收/庫存效率 proxy 改善 {ratio_pct:.1%}")
        anomaly_signal = _as_float(anomaly.get(COL_ANOMALY_SIGNAL) if anomaly else None)
        if anomaly:
            score += min(abs(anomaly_signal or 0.0), 5.0)
            supporting.append(f"異常訊號 {anomaly.get(COL_ANOMALY_TYPE) or 'detected'}，訊號值 {_format_number(anomaly_signal)}")
        else:
            counter.append("目前未列入主要異常訊號清單")
        evidence_metric_count = sum(1 for item in [revenue, amount, qty, ratio] if item) + (1 if anomaly else 0)
        if evidence_metric_count < 3:
            continue
        candidates.append({
            "entity_value": entity,
            "score": score,
            "latest_month": revenue.get("latest_month") or amount.get("latest_month") or qty.get("latest_month") or latest_month,
            "revenue_change_pct": revenue_pct,
            "inventory_amount_change_pct": amount_pct,
            "inventory_qty_change_pct": qty_pct,
            "ratio_change_pct": ratio_pct,
            "anomaly_signal": anomaly_signal,
            "evidence_metric_count": evidence_metric_count,
            "supporting_evidence": supporting or ["多指標資料完整但未見單一突出風險"],
            "counter_evidence": counter or ["目前缺少明確反向證據"],
            "next_action": _management_next_action(entity, supporting, counter),
        })
    candidates.sort(key=lambda row: (float(row.get("score") or 0), row.get("evidence_metric_count") or 0), reverse=True)
    for index, row in enumerate(candidates, start=1):
        row["rank"] = index
    return candidates


def _find_anomaly_rows(domain_results: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _iter_evidence_items(domain_results):
        if item.get("source_tool") == "get_anomalies" and isinstance(item.get("rows"), list):
            rows.extend(row for row in item.get("rows") or [] if isinstance(row, dict))
        elif item.get(COL_ANOMALY_TYPE) or item.get(COL_ANOMALY_SIGNAL) is not None:
            rows.append(item)
    return rows


def _management_next_action(entity: str, supporting: list[str], counter: list[str]) -> str:
    joined = " ".join(supporting)
    if "庫存金額上升" in joined and "庫存數量上升" in joined:
        return f"先核對 {entity} 的庫齡、在途/呆滯庫存與近期出貨節奏，確認庫存累積是否可消化"
    if "營收趨勢下降" in joined:
        return f"先核對 {entity} 最新訂單、出貨與價格變動，判斷營收下降是否延續"
    if "異常訊號" in joined:
        return f"先追查 {entity} 異常訊號來源資料列，確認是否為資料品質或真實營運風險"
    return f"先補查 {entity} 的訂單、出貨、庫齡與產品組合，再決定是否升級管理處置"


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_multimetric_trend_display_blocks(task_profile: Any, domain_results: list[Any], limitations: list[str], max_items: int) -> dict[str, Any]:
    items = [item for item in _iter_evidence_items(domain_results) if item.get("source_tool") == "get_entity_trend_comparison"]
    metrics = [str(item.get("metric")) for item in items if item.get("metric")]
    first = items[0] if items else {}
    headline = "結論：已依使用者要求用多個指標檢查事業群趨勢，而不是只看單一營收趨勢。"
    observations = [f"已覆蓋指標：{', '.join(dict.fromkeys(metrics))}。"]
    anomaly = _find_anomaly(domain_results)
    if anomaly:
        observations.append(f"異常指標參考：{anomaly.get(COL_MONTH, anomaly.get('month', 'N/A'))} / {anomaly.get(COL_PLATFORM, anomaly.get('entity_value', 'N/A'))}。")
    table_rows = []
    for item in items[:4]:
        for row in (item.get("entity_summaries") or [])[:3]:
            table_rows.append({"metric": item.get("metric"), **row})
    return {
        "headline": headline,
        "key_observations": observations[:max_items],
        "table": {"columns": ["metric", "entity_value", "latest_month", "latest_value", "overall_change", "overall_change_pct", "direction"], "rows": table_rows[:12]} if table_rows else None,
        "limitations": list(dict.fromkeys([*limitations, "多角度評估為歷史資料 proxy，不代表根本原因或預測。"])),
    }


def _build_relationship_cross_check_display_blocks(task_profile: Any, domain_results: list[Any], limitations: list[str], max_items: int) -> dict[str, Any]:
    relationship = next((item for item in _iter_evidence_items(domain_results) if item.get("source_tool") == "get_revenue_inventory_relationship"), {})
    snapshot = next((item for item in _iter_evidence_items(domain_results) if item.get("source_tool") == "get_entity_performance_snapshot"), {})
    snapshot_by_entity = {str(row.get("entity_value") or row.get("platform") or row.get("business_group")): row for row in (snapshot.get("rows") or []) if isinstance(row, dict)}
    rows: list[dict[str, Any]] = []
    for row in (relationship.get("rows") or [])[:8]:
        if not isinstance(row, dict):
            continue
        entity = str(row.get("entity_value") or row.get("platform") or row.get("business_group") or "")
        snap = snapshot_by_entity.get(entity, {})
        rows.append({
            "entity_value": entity or None,
            "latest_month": row.get("month") or snap.get("month"),
            "previous_month": row.get("previous_month"),
            "relationship_label": row.get("relationship_label"),
            "revenue_change": row.get("revenue_change"),
            "inventory_amount_change": row.get("inventory_amount_change", row.get("inventory_change")),
            "inventory_qty": snap.get("inventory_qty"),
            "inventory_amount": snap.get("inventory_amount"),
            "revenue_inventory_amount_ratio": row.get("latest_ratio") or snap.get("revenue_inventory_amount_ratio"),
        })
    observations = []
    if relationship.get("summary"):
        observations.append(f"庫存風險關係分布：{relationship.get('summary', {}).get('relationship_counts')}。")
    if snapshot_by_entity:
        observations.append("已用 performance snapshot 補齊庫存數量與庫存金額水位，避免只依單一 relationship table 判斷。")
    return {
        "headline": "結論：已用營收變化、庫存金額變化與庫存數量水位交叉檢查庫存風險。",
        "key_observations": observations[:max_items],
        "table": {"columns": ["entity_value", "latest_month", "previous_month", "relationship_label", "revenue_change", "inventory_amount_change", "inventory_qty", "inventory_amount", "revenue_inventory_amount_ratio"], "rows": rows} if rows else None,
        "limitations": list(dict.fromkeys([*limitations, "營收/庫存關係為描述性 proxy，庫存數量水位來自同月 snapshot；不宣稱因果。"])),
    }


def _build_risk_scan_display_blocks(task_profile: Any, domain_results: list[Any], limitations: list[str], max_items: int) -> dict[str, Any]:
    relationship = next((item for item in _iter_evidence_items(domain_results) if item.get("source_tool") == "get_revenue_inventory_relationship"), {})
    proxy_rows = _find_turnover_proxy_rows(domain_results)
    anomaly = _find_anomaly(domain_results)
    comparable = [row for row in proxy_rows if row.get("is_comparable") is not False]
    non_comparable = [row for row in proxy_rows if row.get("is_comparable") is False]
    leading = comparable[0] if comparable else (non_comparable[0] if non_comparable else None)
    if leading and leading.get("is_comparable") is False:
        headline = "結論：部分營收/庫存 proxy 因營收或分母不合法而不可比較，不能直接當作正常週轉效率排名。"
    elif leading:
        headline = f"結論：目前庫存風險需以營收/庫存關係、庫存 proxy 與異常訊號交叉判斷；{leading.get('entity_value') or leading.get('platform')} 是優先檢查對象。"
    else:
        headline = "結論：目前沒有足夠庫存風險 evidence 可以形成完成判斷。"
    observations = []
    if relationship.get("summary"):
        observations.append(f"營收/庫存關係分布：{relationship.get('summary', {}).get('relationship_counts')}")
    if leading:
        observations.append(
            f"proxy 公式：{leading.get('proxy_formula', 'revenue / inventory_amount')}；分子={leading.get('proxy_numerator', 'revenue')}，分母={leading.get('proxy_denominator', 'inventory_amount')}，單位={leading.get('proxy_unit', 'ratio')}。"
        )
    if anomaly:
        observations.append(f"異常訊號：{anomaly.get(COL_MONTH, anomaly.get('month', 'N/A'))} / {anomaly.get(COL_ANOMALY_TYPE, MISSING_INFO_TEXT)}。")
    table_rows = proxy_rows[:8]
    return {
        "headline": headline,
        "key_observations": observations[:max_items],
        "table": {"columns": ["month", "entity_value", "revenue", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio", "is_comparable", "non_comparable_reason", "risk_label"], "rows": table_rows} if table_rows else None,
        "limitations": list(dict.fromkeys([*limitations, "營收/庫存 proxy 是描述性替代指標；負營收或非正分母列為 non-comparable，不納入正常效率排名。"])),
    }


def _iter_evidence_items(domain_results: list[Any]):
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if isinstance(item, dict):
                yield item


def _is_consecutive_direction(rows: list[dict[str, Any]], *, positive: bool = False, negative: bool = False) -> bool:
    changes = [row.get("mom_change") for row in rows[1:] if row.get("mom_change") is not None]
    if len(changes) < 2:
        return False
    if positive:
        return all(float(change) > 0 for change in changes[-2:])
    if negative:
        return all(float(change) < 0 for change in changes[-2:])
    return False


def _latest_non_null_change(rows: list[dict[str, Any]]) -> Any:
    for row in reversed(rows):
        if row.get("mom_change") is not None:
            return row.get("mom_change")
    return None


def _build_chart_display_blocks(domain_results: list[Any], answer: str, limitations: list[str]) -> dict[str, Any]:
    chart = _find_chart_payload(domain_results)
    if not chart:
        return {
            "headline": _extract_headline(answer) or "結論：目前無法產生指定圖表。",
            "key_observations": [],
            "table": None,
            "limitations": list(dict.fromkeys(limitations))[:3],
        }

    table_rows = chart.get("table_preview") or []
    chart_key = chart.get("chart_key")
    title = chart.get("title") or chart_key
    chart_type = chart.get("chart_type") or "chart"
    observations = [
        f"圖表 key 為 {chart_key}，圖型為 {chart_type}。",
        f"圖表包含 {len(chart.get('series') or [])} 組資料序列。",
    ]
    if table_rows:
        observations.append(f"已同步提供 {len(table_rows)} 列表格預覽。")
    return {
        "headline": f"結論：已產生 {title}（{chart_key}），可用於前端圖表渲染與表格檢視。",
        "key_observations": observations[:3],
        "table": {
            "columns": list(table_rows[0].keys()),
            "rows": table_rows[:8],
        }
        if table_rows
        else None,
        "limitations": list(dict.fromkeys(limitations))[:3],
    }


def _build_performance_assessment_display_blocks(
    task_profile: Any,
    domain_results: list[Any],
    limitations: list[str],
    max_items: int,
) -> dict[str, Any]:
    polarity = getattr(task_profile, "polarity", None)
    proxy_rows = _find_turnover_proxy_rows(domain_results) or _find_platform_ratio_rows(domain_results)
    anomaly = _find_anomaly(domain_results)
    observations: list[str] = []

    weakest = proxy_rows[0] if proxy_rows else None
    if polarity == "best":
        if weakest:
            headline = (
                "結論：這題屬於事業群表現評估，不以庫存金額最高作為較佳結論；"
                f"目前可先用營收/庫存效率 proxy 與異常訊號排除風險事業群，{weakest.get('platform')} 是較弱參考點。"
            )
        else:
            headline = "結論：這題屬於事業群表現評估，不能只用庫存金額最高判定較佳事業群；目前缺少足夠 proxy 證據。"
    elif polarity == "worst" and weakest:
        headline = (
            f"結論：目前較差的事業群優先看 {weakest.get('platform')}，依據是營收/庫存效率 proxy 偏弱，"
            "而不是庫存金額最高排序。"
        )
    elif weakest:
        headline = (
            f"結論：事業群表現需綜合營收、庫存效率 proxy 與異常訊號；目前 {weakest.get('platform')} "
            "是需要優先檢查的弱勢事業群。"
        )
    else:
        headline = "結論：事業群表現需綜合營收、庫存效率 proxy 與異常訊號，目前沒有足夠證據形成排序。"

    if weakest:
        observations.append(
            f"{weakest.get('month')} / {weakest.get('platform')} 的營收/庫存金額 proxy 為 {_format_number(weakest.get('revenue_inventory_amount_ratio'))}。"
        )
        observations.append(
            f"proxy 公式：{weakest.get('proxy_formula', 'revenue / inventory_amount')}；分子={weakest.get('proxy_numerator', 'revenue')}，分母={weakest.get('proxy_denominator', 'inventory_amount')}，單位={weakest.get('proxy_unit', 'ratio')}；non-comparable policy：revenue<=0 或 inventory_amount<=0 不列入正常效率排名。"
        )
    if len(proxy_rows) > 1:
        second = proxy_rows[1]
        observations.append(
            f"次弱參考點為 {second.get('platform')}，proxy 為 {_format_number(second.get('revenue_inventory_amount_ratio'))}。"
        )
    if anomaly:
        observations.append(
            f"異常訊號出現在 {anomaly.get(COL_MONTH, 'N/A')} / {anomaly.get(COL_PLATFORM, 'N/A')}，類型為 {anomaly.get(COL_ANOMALY_TYPE, MISSING_INFO_TEXT)}。"
        )

    return {
        "headline": headline,
        "key_observations": observations[:max_items],
        "table": None,
        "limitations": list(dict.fromkeys(limitations))[:3],
    }


def _build_cross_section_compare_display_blocks(
    task_profile: Any,
    domain_results: list[Any],
    limitations: list[str],
    max_items: int,
) -> dict[str, Any]:
    rows = _find_platform_ratio_rows(domain_results)
    month = (getattr(task_profile, "time_scope", {}) or {}).get("month")
    scope = month or (rows[0].get("month") if rows else "指定月份")
    observations: list[str] = []
    if rows:
        first = rows[0]
        observations.append(
            f"{scope} 事業群橫向比較中，{first.get('platform')} 的營收/庫存金額 proxy 為 {_format_number(first.get('revenue_inventory_amount_ratio'))}。"
        )
        if first.get("revenue") is not None or first.get("inventory_amount") is not None:
            observations.append(
                f"{first.get('platform')} 營收 {_format_number(first.get('revenue'))}，庫存金額 {_format_number(first.get('inventory_amount'))}。"
            )
    anomaly = _find_anomaly(domain_results)
    if anomaly:
        observations.append(
            f"同月另有異常參考：{anomaly.get(COL_PLATFORM, 'N/A')} / {anomaly.get(COL_ANOMALY_TYPE, MISSING_INFO_TEXT)}。"
        )

    table_rows = [
        {
            "month": row.get("month"),
            "事業群": row.get("platform"),
            "revenue": row.get("revenue"),
            "inventory_amount": row.get("inventory_amount"),
            "inventory_qty": row.get("inventory_qty"),
            "revenue_inventory_ratio": row.get("revenue_inventory_amount_ratio"),
        }
        for row in rows[:5]
    ]
    return {
        "headline": f"結論：{scope} 這題應解讀為同月份事業群橫向比較，主軸是各事業群營收與庫存差異，不是 MoM contribution。",
        "key_observations": observations[:max_items],
        "table": {
            "columns": ["month", "事業群", "revenue", "inventory_amount", "inventory_qty", "revenue_inventory_ratio"],
            "rows": table_rows,
        }
        if table_rows
        else None,
        "limitations": list(dict.fromkeys(limitations))[:3],
    }


def _build_time_compare_display_blocks(
    domain_results: list[Any],
    answer: str,
    limitations: list[str],
    max_items: int,
) -> dict[str, Any]:
    observations: list[str] = []
    contribution = _find_contribution_analysis(domain_results)
    trend = _find_yoy_mom_breakdown(domain_results)
    if contribution and contribution.get("contributors"):
        first = contribution["contributors"][0]
        observations.append(
            f"{contribution.get('month')} 相較 {contribution.get('previous_month')} 的主要貢獻者是 {first.get('name')}，變化 {_format_number(first.get('change'))}。"
        )
    if trend:
        observations.append(
            f"{trend.get('month')} 相較 {trend.get('previous_month')} 變化 {_format_number(trend.get('mom_change'))}。"
        )
    return {
        "headline": _extract_headline(answer),
        "key_observations": observations[:max_items],
        "table": None,
        "limitations": list(dict.fromkeys(limitations))[:3],
    }


def _compose_answer_from_display_blocks(blocks: dict[str, Any]) -> str:
    sections = [str(blocks.get("headline") or "").strip()]
    observations = [str(item).strip() for item in blocks.get("key_observations", []) if str(item).strip()]
    if observations:
        sections.append("重點觀測：" + " ".join(observations))
    limitations = [str(item).strip() for item in blocks.get("limitations", []) if str(item).strip()]
    if limitations:
        sections.append("限制說明：" + " ".join(limitations))
    return "\n\n".join(section for section in sections if section)


def _extract_headline(answer: str) -> str:
    compact = " ".join(str(answer or "").split())
    if not compact:
        return ""
    for delimiter in ["。", "\n"]:
        if delimiter in compact:
            return compact.split(delimiter, 1)[0].strip() + ("。" if delimiter == "。" else "")
    return compact


def _collect_policy_key_observations(domain_results: list[Any], policy: AnswerPolicy) -> list[str]:
    observations: list[str] = []
    seen: set[str] = set()
    for evidence_type in [*policy.primary_evidence_types, *policy.secondary_evidence_types]:
        for text in _observations_for_evidence_type(domain_results, evidence_type):
            normalized = text.strip()
            if normalized and normalized not in seen:
                observations.append(normalized)
                seen.add(normalized)
            if len(observations) >= policy.max_key_observations:
                return observations
    if observations or not policy.show_background_findings:
        return observations[: policy.max_key_observations]

    for result in domain_results:
        for finding in getattr(result, "key_findings", []):
            normalized = str(finding).strip()
            if normalized and normalized not in seen:
                observations.append(normalized)
                seen.add(normalized)
            if len(observations) >= policy.max_key_observations:
                return observations
    return observations


def _observations_for_evidence_type(domain_results: list[Any], evidence_type: str) -> list[str]:
    if evidence_type == "inventory_turnover_proxy":
        rows = _find_turnover_proxy_rows(domain_results)
        return [
            f"{row.get('month')} / {row.get('platform')} / 事業群 {row.get('group_code')} 的營收/庫存金額比為 {_format_number(row.get('revenue_inventory_amount_ratio'))}。"
            for row in rows[:2]
        ]
    if evidence_type == "platform_ratio":
        ratio = _find_weakest_ratio(domain_results)
        if ratio:
            return [
                f"{ratio.get('month')} / {ratio.get('platform')} / 事業群 {ratio.get('group_code')} 的營收相對庫存表現偏弱，比值為 {_format_number(ratio.get('revenue_inventory_amount_ratio'))}。"
            ]
        return []
    if evidence_type == "anomaly":
        anomaly = _find_anomaly(domain_results)
        if anomaly:
            return [
                f"{anomaly.get(COL_MONTH, 'N/A')} / {anomaly.get(COL_PLATFORM, 'N/A')} / 事業群 {anomaly.get(COL_GROUP_CODE, 'N/A')} 出現異常訊號，類型為 {anomaly.get(COL_ANOMALY_TYPE, MISSING_INFO_TEXT)}。"
            ]
        return []
    if evidence_type == "yoy_mom":
        trend = _find_yoy_mom_breakdown(domain_results)
        if trend:
            return [
                f"{trend.get('month')} 相較 {trend.get('previous_month')} {_change_label(trend.get('mom_direction'))} {_format_number(abs(trend.get('mom_change') or 0))}。"
            ]
        return []
    if evidence_type == "contribution":
        contribution = _find_contribution_analysis(domain_results)
        if contribution and contribution.get("contributors"):
            first = contribution["contributors"][0]
            return [
                f"{contribution.get('month')} 相較 {contribution.get('previous_month')} 的變化，主要由 {first.get('name')} 貢獻 {_format_number(first.get('change'))}。"
            ]
        return []
    if evidence_type == "root_cause_candidate":
        root_cause = _find_root_cause_candidates(domain_results)
        if root_cause and root_cause.get("candidates"):
            return [
                f"候選觀察方向包括 {candidate.get('title')}。"
                for candidate in root_cause.get("candidates", [])[:2]
            ]
        return []
    if evidence_type == "platform_ranking":
        platform_rank = _find_platform_ranking(domain_results)
        if platform_rank:
            return [f"事業群 {platform_rank.get('platform')} 的觀測值為 {platform_rank.get('value_text')}。"]
        return []
    if evidence_type == "group_ranking":
        group_rank = _find_group_ranking(domain_results)
        if group_rank:
            return [f"事業群 {group_rank.get('group_code')} 的觀測值為 {group_rank.get('value_text')}。"]
        return []
    return []


def _build_direct_answer(
    *,
    question: str,
    routing: Any,
    domain_results: list[Any],
    unsupported_topics: list[str],
    latest_month: str | None,
) -> str:
    if unsupported_topics:
        return _build_unsupported_answer(question, unsupported_topics)

    if not domain_results:
        return "目前沒有足夠的已載入證據可供整理。"

    if _is_proxy_anomaly_question(question):
        return _build_proxy_anomaly_answer(domain_results)

    answer_type = getattr(routing, "answer_strategy", None) or getattr(routing, "question_type", "query")

    if answer_type == "ranking":
        return _build_ranking_answer(question, routing, domain_results, latest_month)
    if answer_type == "trend":
        return _build_trend_answer(question, domain_results)
    if answer_type == "comparison":
        return _build_comparison_answer(domain_results)
    if answer_type == "risk":
        return _build_risk_answer(domain_results)
    if answer_type == "diagnosis":
        return _build_diagnosis_answer(domain_results)
    if answer_type == "performance_weakness":
        return _build_performance_weakness_answer(domain_results)
    if answer_type == "chart":
        chart = _find_chart_payload(domain_results)
        if chart:
            chart_type = chart.get("chart_type")
            chart_type_label = {"pie": "圓餅圖", "bar": "長條圖", "line": "折線圖"}.get(chart_type, chart_type or "圖表")
            title = chart.get("title") or chart.get("chart_key")
            return (
                f"已整理好 {title}（{chart.get('chart_key')}，{chart_type_label}），"
                "並附上表格預覽，方便直接檢視或續做圖表。"
            )

    if _looks_like_contribution_question(question):
        comparison_answer = _build_comparison_answer(domain_results)
        if comparison_answer:
            return comparison_answer

    primary_finding = _first_finding(domain_results)
    if primary_finding:
        return primary_finding
    return "目前沒有足夠的已載入證據可供整理。"


def _build_unsupported_answer(question: str, unsupported_topics: list[str]) -> str:
    joined = ", ".join(unsupported_topics)
    lowered = question.lower()
    if "forecast" in unsupported_topics and any(
        token in lowered or token in question
        for token in ["預測", "下個月", "下月", "未來", "會不會改善", "會不會下降", "next month", "future"]
    ):
        return (
            "結論：目前無法判斷下個月營收是否會改善，"
            "因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。"
        )
    return (
        f"目前尚無法直接回答 {joined}，因為現有資料沒有對應欄位，"
        "或沒有足夠證據支撐這類問題。"
    )


def _build_ranking_answer(
    question: str,
    routing: Any,
    domain_results: list[Any],
    latest_month: str | None,
) -> str:
    entity_ranking = _find_entity_metric_ranking(domain_results)
    if entity_ranking:
        month = entity_ranking.get("month") or latest_month or "最新月份"
        label = entity_ranking.get("entity_label") or "事業群"
        metric_label = entity_ranking.get("metric_label") or entity_ranking.get("metric") or "指標"
        direction_text = "最低" if entity_ranking.get("sort_direction") == "ascending" else "最高"
        return (
            f"結論：最新月份 {month} {metric_label}{direction_text}的{label}是 "
            f"{entity_ranking.get('top_entity')}，{metric_label}為 {_format_number(entity_ranking.get('top_value'))}。"
        )

    lowered = question.lower()
    efficiency_like = any(token in question for token in ["效率", "週轉", "周轉", "比值"]) or any(
        token in lowered for token in ["efficiency", "turnover", "ratio"]
    )
    if efficiency_like:
        turnover = _find_turnover_proxy(domain_results)
        if turnover:
            return (
                f"依目前已載入資料，庫存效率最低的事業群為 {turnover.get('platform')}，"
                f"事業群 {turnover.get('group_code')} 的營收/庫存金額 proxy 為 "
                f"{_format_number(turnover.get('revenue_inventory_amount_ratio'))}。"
            )

    platform_rank = _find_platform_ranking(domain_results)
    if platform_rank:
        if routing.filters.month:
            return (
                f"依目前已載入資料，{routing.filters.month} 庫存金額最高的事業群為 "
                f"{platform_rank['platform']}，數值為 {platform_rank['value_text']}。"
            )
        return (
            f"依目前已載入資料，目前為累計排名，庫存金額最高的事業群為 "
            f"{platform_rank['platform']}，數值為 {platform_rank['value_text']}。"
        )

    group_rank = _find_group_ranking(domain_results)
    if group_rank:
        metric_label = group_rank["metric_label"]
        if routing.filters.month:
            return (
                f"依目前已載入資料，{routing.filters.month} {metric_label}最高的事業群為代碼 "
                f"{group_rank['group_code']}，數值為 {group_rank['value_text']}。"
            )
        if _asks_latest_month(question) and latest_month:
            return (
                f"依目前已載入資料，{latest_month} {metric_label}最高的事業群為代碼 "
                f"{group_rank['group_code']}，數值為 {group_rank['value_text']}。"
            )
        return (
            f"依目前已載入資料，目前為累計排名，{metric_label}最高的事業群為代碼 "
            f"{group_rank['group_code']}，數值為 {group_rank['value_text']}。"
        )

    weakest_ratio = _find_weakest_ratio(domain_results)
    if weakest_ratio:
        return (
            f"依目前已載入資料，營收相對庫存表現最弱的是 {weakest_ratio.get('month')} / "
            f"{weakest_ratio.get('platform')} / 事業群 {weakest_ratio.get('group_code')}，"
            f"營收/庫存金額比值為 {_format_number(weakest_ratio.get('revenue_inventory_amount_ratio'))}。"
        )
    return _first_finding(domain_results) or "目前沒有足夠的排名證據可供整理。"


def _build_trend_answer(question: str, domain_results: list[Any]) -> str:
    trend = _find_yoy_mom_breakdown(domain_results, question=question)
    if trend:
        metric_label = _metric_label(trend.get("metric"))
        name = _dimension_subject(trend)
        direction = _change_label(trend.get("mom_direction"))
        message = (
            f"依目前已載入資料，{trend.get('month')} {name}{metric_label}相較 {trend.get('previous_month')} "
            f"{direction} {_format_number(abs(trend.get('mom_change') or 0))}。"
        )
        if trend.get("mom_change_pct") is not None:
            message += f" MoM 變化率為 {float(trend['mom_change_pct']):.2%}。"
        if trend.get("yoy_available") and trend.get("yoy_change_pct") is not None:
            message += f" YoY 變化率為 {float(trend['yoy_change_pct']):.2%}。"
        else:
            message += " 目前沒有去年同期資料，因此暫時無法提供 YoY。"
        return message
    return _first_finding(domain_results) or "目前沒有足夠的趨勢證據可供整理。"


def _build_comparison_answer(domain_results: list[Any]) -> str:
    contribution = _find_contribution_analysis(domain_results)
    if contribution and contribution.get("contributors"):
        first = contribution["contributors"][0]
        metric_label = _metric_label(contribution.get("metric"))
        return (
            f"依目前已載入資料，{contribution.get('month')} 相較 {contribution.get('previous_month')} 的{metric_label}變化，"
            f"主要由 {first.get('name')} 貢獻，變動 {_format_number(first.get('change'))}。"
        )
    return _build_trend_answer("", domain_results)


def _build_proxy_anomaly_answer(domain_results: list[Any]) -> str:
    anomaly = _find_anomaly(domain_results)
    if anomaly:
        anomaly_type = anomaly.get(COL_ANOMALY_TYPE) or MISSING_INFO_TEXT
        reason = anomaly.get(COL_ANOMALY_REASON) or MISSING_INFO_TEXT
        signal = _format_number(anomaly.get(COL_ANOMALY_SIGNAL))
        return (
            f"有。依目前已載入資料，偵測到風險訊號出現在 {anomaly.get(COL_MONTH, 'N/A')} / "
            f"{anomaly.get(COL_PLATFORM, 'N/A')} / 事業群 {anomaly.get(COL_GROUP_CODE, 'N/A')}，"
            f"異常類型為 {anomaly_type}，原因為 {reason}，訊號值為 {signal}。"
            "這代表營收與庫存之間出現需要追蹤的風險訊號，建議進一步檢查該事業群的近期變化。"
        )

    turnover = _find_turnover_proxy(domain_results)
    if turnover:
        return (
            f"有。依目前已載入資料，{turnover.get('month')} / {turnover.get('platform')} / 事業群 "
            f"{turnover.get('group_code')} 的庫存效率 proxy 偏弱，營收/庫存金額 ratio 為 "
            f"{_format_number(turnover.get('revenue_inventory_amount_ratio'))}。"
        )

    return "目前未偵測到明確的營收下降且庫存上升風險訊號。"


def _build_risk_answer(domain_results: list[Any]) -> str:
    anomaly = _find_anomaly(domain_results)
    turnover = _find_turnover_proxy(domain_results)
    if anomaly:
        anomaly_type = anomaly.get(COL_ANOMALY_TYPE) or MISSING_INFO_TEXT
        reason = anomaly.get(COL_ANOMALY_REASON) or MISSING_INFO_TEXT
        signal = _format_number(anomaly.get(COL_ANOMALY_SIGNAL))
        message = (
            f"目前最需要注意的是 {anomaly.get(COL_MONTH, 'N/A')} / {anomaly.get(COL_PLATFORM, 'N/A')} / 事業群 "
            f"{anomaly.get(COL_GROUP_CODE, 'N/A')}，異常類型為 {anomaly_type}，原因為 {reason}，訊號值為 {signal}。"
            "這代表營收與庫存之間出現需要追蹤的風險訊號，建議進一步檢查該事業群的近期變化。"
        )
        if turnover:
            message += (
                f" 另外，{turnover.get('month')} / {turnover.get('platform')} / 事業群 {turnover.get('group_code')} "
                f"的庫存效率 proxy 為 {_format_number(turnover.get('revenue_inventory_amount_ratio'))}，"
                f"效率層級為 {turnover.get('efficiency_level')}。"
            )
        return message

    if turnover:
        return (
            f"依目前已載入資料，庫存效率 proxy 最弱的是 {turnover.get('month')} / {turnover.get('platform')} / "
            f"事業群 {turnover.get('group_code')}，營收/庫存金額 ratio 為 {_format_number(turnover.get('revenue_inventory_amount_ratio'))}。"
        )

    weakest_ratio = _find_weakest_ratio(domain_results)
    if weakest_ratio:
        return (
            f"依目前已載入資料，較需要關注的是 {weakest_ratio.get('month')} / {weakest_ratio.get('platform')} / "
            f"事業群 {weakest_ratio.get('group_code')}，營收/庫存金額比值為 {_format_number(weakest_ratio.get('revenue_inventory_amount_ratio'))}。"
        )

    return "目前未偵測到明確的高風險訊號。"


def _build_performance_weakness_answer(domain_results: list[Any]) -> str:
    blocks = _build_performance_weakness_display_blocks(domain_results)
    sections: list[str] = []
    if blocks.get("headline"):
        sections.append(blocks["headline"])
    if blocks.get("key_observations"):
        sections.append("重點觀測：" + " ".join(blocks["key_observations"]))
    if blocks.get("limitations"):
        sections.append("限制說明：" + " ".join(blocks["limitations"]))
    return "\n\n".join(section for section in sections if section)


def _build_performance_weakness_display_blocks(domain_results: list[Any]) -> dict[str, Any]:
    proxy_rows = _find_turnover_proxy_rows(domain_results)
    anomaly = _find_anomaly(domain_results)
    if not proxy_rows:
        return {
            "headline": "結論：目前沒有足夠的營收與庫存 proxy 證據，暫時無法判斷哪個事業群表現較弱。",
            "key_observations": [],
            "limitations": [
                "目前資料只能指出營收與庫存之間的弱勢訊號，尚不能直接判定根本原因。",
            ],
        }

    primary = proxy_rows[0]
    headline = (
        "結論：目前表現較弱的事業群應優先關注 "
        f"{primary.get('platform')}，尤其是 {primary.get('month')} / 事業群 {primary.get('group_code')}，"
        f"因為其營收相對庫存表現最弱，營收/庫存金額比為 {_format_number(primary.get('revenue_inventory_amount_ratio'))}。"
    )
    observations = [
        f"第一，{primary.get('platform')} / 事業群 {primary.get('group_code')} 是目前營收相對庫存最弱的組合，庫存效率 proxy 比值為 {_format_number(primary.get('revenue_inventory_amount_ratio'))}。",
    ]
    if len(proxy_rows) > 1:
        second = proxy_rows[1]
        observations.append(
            f"第二，次弱組合為 {second.get('platform')} / 事業群 {second.get('group_code')}，比值為 {_format_number(second.get('revenue_inventory_amount_ratio'))}。"
        )
    if anomaly and anomaly.get(COL_PLATFORM):
        observations.append(
            f"第三，系統也偵測到 {anomaly.get(COL_PLATFORM)} 相關異常訊號，類型為 {anomaly.get(COL_ANOMALY_TYPE, MISSING_INFO_TEXT)}。"
        )

    return {
        "headline": headline,
        "key_observations": observations[:3],
        "limitations": [
            "目前資料只能指出營收與庫存之間的弱勢訊號，尚不能直接判定根本原因。",
        ],
    }


def _build_diagnosis_answer(domain_results: list[Any]) -> str:
    root_cause = _find_root_cause_candidates(domain_results)
    if root_cause and root_cause.get("candidates"):
        directions: list[str] = []
        for candidate in root_cause.get("candidates", [])[:3]:
            directions.append(candidate.get("title") or candidate.get("description") or "需要進一步檢查的候選方向")
        direction_text = "；".join(directions)
        return (
            "目前尚無法直接判斷營收變化的根本原因，因為資料尚未包含訂單、出貨、價格、客戶與市場需求等欄位。"
            f"不過，根據目前營收與庫存資料，可先整理出幾個候選觀察方向：{direction_text}。"
            "這些都是後續可能需要檢查的方向，不代表原因已被確認。"
        )

    observations: list[str] = []
    trend = _find_yoy_mom_breakdown(domain_results)
    if trend:
        metric_label = _metric_label(trend.get("metric"))
        observations.append(
            f"{trend.get('month')} {metric_label}相較 {trend.get('previous_month')} {_change_label(trend.get('mom_direction'))} "
            f"{_format_number(abs(trend.get('mom_change') or 0))}"
        )
        if not trend.get("yoy_available"):
            observations.append("目前沒有去年同期資料，因此暫時無法提供 YoY")

    anomaly = _find_anomaly(domain_results)
    if anomaly:
        observations.append(
            f"風險訊號出現在 {anomaly.get(COL_MONTH, 'N/A')} / {anomaly.get(COL_PLATFORM, 'N/A')} / 事業群 "
            f"{anomaly.get(COL_GROUP_CODE, 'N/A')}"
        )
        observations.append(
            f"異常類型為 {anomaly.get(COL_ANOMALY_TYPE, MISSING_INFO_TEXT)}，訊號值為 {_format_number(anomaly.get(COL_ANOMALY_SIGNAL))}"
        )

    contribution = _find_contribution_analysis(domain_results)
    if contribution and contribution.get("contributors"):
        first = contribution["contributors"][0]
        observations.append(
            f"{contribution.get('month')} 相較 {contribution.get('previous_month')} 的變化，主要由 {first.get('name')} 貢獻，"
            f"變動 {_format_number(first.get('change'))}"
        )

    turnover = _find_turnover_proxy(domain_results)
    if turnover:
        observations.append(
            f"庫存效率 proxy 偏弱的是 {turnover.get('month')} / {turnover.get('platform')} / 事業群 {turnover.get('group_code')}，"
            f"營收/庫存金額 ratio 為 {_format_number(turnover.get('revenue_inventory_amount_ratio'))}"
        )

    weakest_ratio = _find_weakest_ratio(domain_results)
    if weakest_ratio and not turnover:
        observations.append(
            f"較弱的營收/庫存組合為 {weakest_ratio.get('month')} / {weakest_ratio.get('platform')} / 事業群 "
            f"{weakest_ratio.get('group_code')}，比值為 {_format_number(weakest_ratio.get('revenue_inventory_amount_ratio'))}"
        )

    observation_text = "；".join(observations) if observations else "目前沒有足夠的可觀察現象。"
    return (
        "目前尚無法直接判斷營收變化的根本原因，因為資料尚未包含訂單、客戶、出貨、價格與市場需求等欄位。"
        f"不過，從現有營收與庫存資料可先觀察到：{observation_text}。"
    )


def _build_limitations(
    *,
    question: str,
    routing: Any,
    domain_results: list[Any],
    unsupported_topics: list[str],
    has_evidence: bool,
) -> list[str]:
    limitations: list[str] = []

    if unsupported_topics:
        limitations.extend([f"目前資料無法直接支援 {topic} 類問題。" for topic in unsupported_topics])

    for warning in getattr(routing, "warnings", []):
        limitations.append(_productize_text(str(warning)))
    for result in domain_results:
        for warning in getattr(result, "warnings", []):
            limitations.append(_productize_text(str(warning)))

    if _is_proxy_anomaly_question(question):
        limitations.append(PROXY_ANOMALY_LIMITATION)

    answer_type = getattr(routing, "answer_strategy", None) or getattr(routing, "question_type", "query")
    if answer_type in {"risk", "diagnosis", "performance_weakness"}:
        limitations.append("目前回答仍以營收、庫存與異常訊號為主，不能直接等同完整因果判斷。")

    if _find_turnover_proxy(domain_results):
        limitations.append(TURNOVER_PROXY_LIMITATION)

    combined_chart_text = " ".join(
        str(item)
        for result in domain_results
        for item in getattr(result, "evidence", [])
        if isinstance(item, dict)
    )
    if "health_score" in question or "health score" in question.lower():
        limitations.append("health_score 為 deterministic scorecard 指標，需搭配營收、庫存 proxy 與資料品質限制解讀。")

    root_cause = _find_root_cause_candidates(domain_results)
    if root_cause:
        for item in root_cause.get("limitations", []):
            limitations.append(str(item))

    trend = _find_yoy_mom_breakdown(domain_results)
    if trend and not trend.get("yoy_available"):
        limitations.append("目前沒有去年同期資料，因此暫時無法提供 YoY。")

    if not unsupported_topics and not has_evidence:
        limitations.append("目前沒有足夠的證據可供支撐回答。")

    if _needs_reasoning_limitation(question):
        limitations.append("目前尚無法直接判斷原因或預測未來變化，因為資料不包含完整因果所需欄位。")

    if not limitations:
        limitations.append("回答已盡量依據現有資料整理，但仍需搭配實際業務背景解讀。")

    return list(dict.fromkeys(limitations))


def _productize_text(text: str) -> str:
    normalized = text.strip()
    normalized = normalized.replace("欄位不足", MISSING_INFO_TEXT)
    normalized = normalized.replace("代理異常", "風險訊號")
    while "風險訊號訊號" in normalized:
        normalized = normalized.replace("風險訊號訊號", "風險訊號")
    return normalized


def _suggest_followups(
    *,
    answer_type: str,
    unsupported_topics: list[str],
    filters: dict[str, Any],
) -> list[str]:
    if unsupported_topics:
        return [
            "要不要先查看現有資料能直接支援哪些營收與庫存分析？",
            "要不要改看事業群或產品線的最近變化？",
            "要不要檢查目前資料品質與 mapping 狀態？",
        ]

    if answer_type == "chart":
        return [
            "要不要產生其他相關圖表？",
            "要不要比較其他事業群或產品線？",
            "要不要改看最近三個月的變化？",
        ]

    if answer_type == "risk":
        return [
            "要不要列出所有偵測到的風險訊號？",
            "要不要查看該事業群近三個月的營收與庫存趨勢？",
            "要不要比較其他事業群或產品線？",
        ]

    if answer_type == "diagnosis":
        return [
            "要不要查看該事業群近三個月的營收與庫存趨勢？",
            "要不要列出本月變化的主要貢獻對象？",
            "要不要檢查目前資料品質與 mapping 狀態？",
        ]

    scope = []
    if filters.get("month"):
        scope.append("要不要改看其他月份？")
    if filters.get("platform"):
        scope.append("要不要比較其他事業群？")
    if filters.get("group_code"):
        scope.append("要不要比較其他事業群？")
    if not scope:
        scope.append("要不要比較其他事業群或產品線？")

    return [
        scope[0],
        "要不要查看近三個月的趨勢？",
        "要不要產生對應圖表？",
    ]


def _detect_unsupported_topics(question: str) -> list[str]:
    lowered = question.lower()
    matched: list[str] = []
    product_line_question = any(token in lowered or token in question for token in ["product line", "產品線", "產品線"])
    proxy_fallback_context = any(token in question for token in ["沒有正式", "如果目前沒有", "替代指標", "代理指標", "proxy"])
    for topic, hints in UNSUPPORTED_FIELD_HINTS.items():
        if topic == "product" and product_line_question:
            continue
        if topic == "cost" and proxy_fallback_context and any(token in question for token in ["銷貨成本", "成本"]):
            continue
        if any(hint.lower() in lowered for hint in hints):
            matched.append(topic)
    forecast_tokens = [
        "forecast",
        "predict",
        "prediction",
        "next month",
        "future",
        "下個月",
        "下月",
        "未來",
        "預測",
        "會不會改善",
        "會不會下降",
        "是否會成長",
    ]
    if any(token in lowered or token in question for token in forecast_tokens) and "forecast" not in matched:
        matched.append("forecast")
    return matched


def _collect_tools(domain_results: list[Any]) -> list[str]:
    tools: list[str] = []
    for result in domain_results:
        for tool in getattr(result, "used_tools", []):
            tool_name = str(tool)
            if tool_name not in tools:
                tools.append(tool_name)
    return tools


def _collect_evidence(domain_results: list[Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            evidence.append(
                {
                    "domain": result.domain,
                    "summary": _summarize_evidence(result.domain, item),
                    "details": item,
                }
            )
    return evidence


def _metric_label(metric: Any) -> str:
    return {
        "revenue": "營收",
        "inventory_amount": "庫存金額",
        "inventory_qty": "庫存數量",
    }.get(str(metric), "指標")


def _change_label(direction: Any) -> str:
    return {
        "up": "增加",
        "down": "下降",
        "flat": "持平",
    }.get(str(direction), "變動")


def _dimension_subject(item: dict[str, Any]) -> str:
    if item.get("dimension") == "platform" and item.get("platform"):
        return f"事業群 {item.get('platform')} 的"
    if item.get("dimension") == "business_group" and item.get("group_code"):
        return f"事業群 {item.get('group_code')} 的"
    return ""


def _summarize_evidence(domain: str, item: dict[str, Any]) -> str:
    if item.get("mom_change") is not None and item.get("metric"):
        metric_label = _metric_label(item.get("metric"))
        subject = item.get("platform") or item.get("group_code") or item.get("name") or "overall"
        return f"{domain}: {subject} {metric_label} month={item.get('month')} mom_change={_format_number(item.get('mom_change'))}"
    if item.get("root_cause_available") is False and item.get("candidates"):
        first = item.get("candidates", [{}])[0]
        return f"{domain}: root_cause_candidate={first.get('candidate_type')} title={first.get('title')}"
    if item.get("contributors"):
        top = item.get("contributors", [{}])[0]
        return f"{domain}: contribution month={item.get('month')} top={top.get('name')} change={_format_number(top.get('change'))}"
    if item.get("efficiency_level") and item.get("revenue_inventory_amount_ratio") is not None:
        return f"{domain}: inventory_proxy platform={item.get('platform')} ratio={_format_number(item.get('revenue_inventory_amount_ratio'))}"
    if item.get("dimension") == "platform":
        return f"{domain}: platform={item.get('platform')} value={item.get('value_text')}"
    if item.get("group_code") is not None and item.get("value_text") is not None:
        return f"{domain}: group_code={item.get('group_code')} value={item.get('value_text')}"
    if item.get(COL_MONTH):
        if item.get(COL_REVENUE) is not None:
            return f"{domain}: month={item.get(COL_MONTH)} revenue={_format_number(item.get(COL_REVENUE))}"
        if item.get(COL_INV_AMOUNT) is not None:
            return f"{domain}: month={item.get(COL_MONTH)} inventory_amount={_format_number(item.get(COL_INV_AMOUNT))}"
        if item.get(COL_INV_QTY) is not None:
            return f"{domain}: month={item.get(COL_MONTH)} inventory_qty={_format_number(item.get(COL_INV_QTY), decimals=0)}"
        if item.get(COL_ANOMALY_TYPE):
            return f"{domain}: month={item.get(COL_MONTH)} platform={item.get(COL_PLATFORM)} anomaly={item.get(COL_ANOMALY_TYPE)}"
    if item.get("chart_key") and item.get("chart_type"):
        return f"{domain}: chart_key={item.get('chart_key')} chart_type={item.get('chart_type')}"
    if item.get("output_path"):
        return f"{domain}: chart_image={item.get('output_path')}"
    if item.get("platform") and item.get("revenue_inventory_amount_ratio") is not None:
        return f"{domain}: platform={item.get('platform')} ratio={_format_number(item.get('revenue_inventory_amount_ratio'))}"
    return f"{domain}: evidence item captured"


def _find_group_ranking(domain_results: list[Any]) -> dict[str, Any] | None:
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if item.get("group_code") is not None and item.get("value_text") is not None:
                metric_label = "營收" if result.domain == "sales" else "庫存金額"
                return {
                    "group_code": item.get("group_code"),
                    "value_text": item.get("value_text"),
                    "metric_label": metric_label,
                }
    return None


def _find_platform_ranking(domain_results: list[Any]) -> dict[str, Any] | None:
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if item.get("dimension") == "platform" and item.get("platform") and item.get("value_text") is not None:
                return item
    return None


def _find_entity_metric_ranking(domain_results: list[Any]) -> dict[str, Any] | None:
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if isinstance(item, dict) and item.get("evidence_type") == "entity_metric_ranking":
                return item
    return None


def _find_weakest_ratio(domain_results: list[Any]) -> dict[str, Any] | None:
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if item.get("platform") and item.get("revenue_inventory_amount_ratio") is not None:
                return item
    return None


def _find_yoy_mom_breakdown(domain_results: list[Any], question: str = "") -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if isinstance(item, dict) and item.get("mom_change") is not None and item.get("metric"):
                candidates.append(item)
    if not candidates:
        return None
    lowered = question.lower()
    if any(token in lowered or token in question for token in ["下降", "decline", "down", "lowest", "最多下降"]):
        negative = [item for item in candidates if float(item.get("mom_change") or 0.0) < 0]
        if negative:
            return sorted(negative, key=lambda item: float(item.get("mom_change") or 0.0))[0]
    if any(token in lowered or token in question for token in ["上升", "increase", "up", "highest", "最多增加"]):
        positive = [item for item in candidates if float(item.get("mom_change") or 0.0) > 0]
        if positive:
            return sorted(positive, key=lambda item: float(item.get("mom_change") or 0.0), reverse=True)[0]
    return sorted(candidates, key=lambda item: abs(float(item.get("mom_change") or 0.0)), reverse=True)[0]


def _find_root_cause_candidates(domain_results: list[Any]) -> dict[str, Any] | None:
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if isinstance(item, dict) and item.get("root_cause_available") is False and isinstance(item.get("candidates"), list):
                return item
    return None


def _find_contribution_analysis(domain_results: list[Any]) -> dict[str, Any] | None:
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if isinstance(item, dict) and item.get("contributors"):
                return item
    return None


def _find_turnover_proxy(domain_results: list[Any]) -> dict[str, Any] | None:
    candidates = _find_turnover_proxy_rows(domain_results)
    if not candidates:
        return None
    return candidates[0]


def _find_turnover_proxy_rows(domain_results: list[Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            items = item.get("rows") if isinstance(item, dict) and item.get("source_tool") == "get_inventory_turnover_proxy" else [item]
            for row in items or []:
                if isinstance(row, dict) and row.get("efficiency_level") and row.get("revenue_inventory_amount_ratio") is not None:
                    candidates.append(row)
    return sorted(
        candidates,
        key=lambda item: (
            item.get("is_comparable") is False,
            float(item.get("revenue_inventory_amount_ratio")) if item.get("revenue_inventory_amount_ratio") is not None else float("inf"),
        ),
    )


def _find_platform_ratio_rows(domain_results: list[Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if (
                isinstance(item, dict)
                and item.get("platform")
                and item.get("revenue_inventory_amount_ratio") is not None
                and (item.get("revenue") is not None or item.get("inventory_amount") is not None)
            ):
                candidates.append(item)
    return sorted(
        candidates,
        key=lambda item: float(item.get("revenue_inventory_amount_ratio")) if item.get("revenue_inventory_amount_ratio") is not None else float("inf"),
    )


def _find_anomaly(domain_results: list[Any]) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if item.get(COL_ANOMALY_TYPE) or item.get(COL_ANOMALY_SIGNAL) is not None:
                candidates.append(item)
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            str(item.get(COL_MONTH, "")),
            float(item.get(COL_ANOMALY_SIGNAL) or 0),
        ),
        reverse=True,
    )
    return candidates[0]


def _find_chart_payload(domain_results: list[Any]) -> dict[str, Any] | None:
    for result in domain_results:
        for item in getattr(result, "evidence", []):
            if item.get("chart_key") and item.get("chart_type"):
                return item
    return None


def _find_latest_metric(domain_results: list[Any], domain_name: str, value_key: str) -> dict[str, str] | None:
    latest: tuple[str, dict[str, Any]] | None = None
    for result in domain_results:
        if getattr(result, "domain", None) != domain_name:
            continue
        for item in getattr(result, "evidence", []):
            month = item.get(COL_MONTH)
            value = item.get(value_key)
            if month is None or value is None:
                continue
            if latest is None or str(month) > latest[0]:
                latest = (
                    str(month),
                    {
                        "month": str(month),
                        "value_text": _format_number(value, decimals=0 if value_key == COL_INV_QTY else 2),
                    },
                )
    return latest[1] if latest else None


def _first_finding(domain_results: list[Any]) -> str | None:
    for result in domain_results:
        findings = getattr(result, "key_findings", [])
        if findings:
            return str(findings[0])
    return None


def _needs_reasoning_limitation(question: str) -> bool:
    lowered = question.lower()
    return any(token in lowered or token in question for token in WHY_OR_FORECAST_HINTS)


def _asks_latest_month(question: str) -> bool:
    lowered = question.lower()
    return any(token in question for token in ["最新月份", "最新月", "本月", "當月"]) or any(
        token in lowered for token in ["latest month", "current month", "this month"]
    )


def _is_proxy_anomaly_question(question: str) -> bool:
    lowered = question.lower()
    has_revenue = any(token in lowered for token in ["revenue", "sales", "營收", "銷售"])
    has_inventory = any(token in lowered for token in ["inventory", "stock", "庫存", "存貨"])
    has_down = any(token in lowered for token in ["down", "decline", "下降"])
    has_up = any(token in lowered for token in ["up", "rise", "上升"])
    has_divergence = any(token in lowered for token in ["divergence", "背離", "異常", "風險訊號"])
    return has_revenue and has_inventory and ((has_down and has_up) or has_divergence)


def _looks_like_contribution_question(question: str) -> bool:
    lowered = question.lower()
    return any(token in lowered or token in question for token in ["contribution", "contributed", "who drove", "誰貢獻", "主要由誰", "誰帶動"])


def _format_number(value: Any, *, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    return format_number(value, decimals=decimals)
