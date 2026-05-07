from __future__ import annotations

import re
from typing import Any

import pandas as pd

from analysis_tools import AnalysisToolbox, QueryFilters
from business_question_classifier import BusinessQuestionProfile, classify_business_question, describe_lenses
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
    COL_REVENUE_INV_AMOUNT_RATIO,
    COL_REVENUE_INV_QTY_RATIO,
)
from utils import format_number


AVAILABLE_ANALYTIC_FIELDS = [
    "月份",
    "平台",
    "新事業群",
    "營收",
    "庫存金額",
    "庫存 QTY",
    "營收/庫存金額比值",
    "營收/庫存 QTY 比值",
    "異常類型",
    "異常訊號",
    "異常原因",
    "相關係數",
]

UNSUPPORTED_ANALYTIC_FIELDS = [
    "毛利",
    "毛利率",
    "成本",
    "費用",
    "營業利益",
    "營運利潤",
    "EPS",
    "現金流",
    "客戶",
    "訂單",
    "產品",
    "SKU",
]

LLM_FIELD_BOUNDARY_PROMPT = (
    "Use only the evidence and the available fields. "
    f"Available fields: {', '.join(AVAILABLE_ANALYTIC_FIELDS)}. "
    f"Do not mention unsupported fields unless explicitly saying they are unavailable: {', '.join(UNSUPPORTED_ANALYTIC_FIELDS)}. "
    "Do not introduce gross margin, cost, operating profit, EPS, cashflow, customer, order, product, or SKU analysis when those fields are absent."
)


def compose_evidence_first_answer(
    *,
    request_id: str,
    question: str,
    routing: Any,
    domain_results: list[Any],
    toolbox: AnalysisToolbox,
    context: Any,
) -> str | None:
    profile = classify_business_question(question)

    if profile.question_type == "ranking":
        return _with_request_id(request_id, _compose_ranking(profile, routing, toolbox))
    if profile.question_type == "trend":
        return _with_request_id(request_id, _compose_trend(profile, routing, toolbox))
    if profile.question_type == "risk":
        return _with_request_id(request_id, _compose_risk(profile, routing, toolbox))
    if profile.question_type == "data_quality":
        return _with_request_id(request_id, _compose_data_quality(toolbox, context))
    if profile.question_type == "decision":
        return _with_request_id(request_id, _compose_decision(profile, routing, toolbox))
    if profile.question_type == "comparison":
        return _with_request_id(request_id, _compose_comparison(profile, routing, toolbox))
    if profile.question_type == "diagnosis":
        return _with_request_id(request_id, _compose_diagnosis(profile, routing, toolbox, domain_results))

    return None


def _compose_ranking(profile: BusinessQuestionProfile, routing: Any, toolbox: AnalysisToolbox) -> str:
    if profile.object_dimension == "platform" or _question_mentions_platform(routing.question):
        return _compose_platform_ranking(profile, routing, toolbox)

    filters = _filters_from_routing(routing)
    metric = "inventory" if _has_any(routing.question, ["庫存", "QTY", "存貨"]) else "revenue"
    rows = toolbox.get_top_groups(metric, top_n=5, filters=filters)
    if not rows:
        return "目前沒有足夠資料可產生事業群排名。"

    metric_label = "庫存金額" if metric == "inventory" else "營收"
    top = rows[0]
    lines = [
        f"以{metric_label}排名來看，最高的新事業群是 {top.get('group_name')}（代碼 {top.get('group_code')}），數值為 {top.get('value_text')}。",
        "",
        "前幾名如下：",
    ]
    for index, row in enumerate(rows[:5], start=1):
        lines.append(f"{index}. {row.get('group_name')}（{row.get('group_code')}）：{row.get('value_text')}")
    return "\n".join(lines)


def _compose_platform_ranking(profile: BusinessQuestionProfile, routing: Any, toolbox: AnalysisToolbox) -> str:
    filters = _filters_from_routing(routing)
    month = filters.month or _latest_month(toolbox)
    platform_df = toolbox.get_metric_table("platform_monthly", QueryFilters(month=month, group_code=filters.group_code))
    if platform_df.empty:
        return "目前沒有可對齊的平台層級資料，無法判斷平台表現排名。"

    lens_names = {lens.name for lens in profile.kpi_lenses}
    revenue_min = _first_sorted(platform_df, COL_REVENUE, ascending=True)
    amount_ratio_min = _first_sorted(platform_df, COL_REVENUE_INV_AMOUNT_RATIO, ascending=True)
    qty_ratio_min = _first_sorted(platform_df, COL_REVENUE_INV_QTY_RATIO, ascending=True)
    risk_row = _top_anomaly(toolbox, QueryFilters(month=month, group_code=filters.group_code))

    if lens_names == {"revenue_scale"} and revenue_min is not None:
        return "\n".join(
            [
                f"以最新可用月份 {month} 的營收規模來看，表現較弱的平台是 {_platform_name(revenue_min)}，營收為 {format_number(revenue_min.get(COL_REVENUE))}。",
                "",
                "判斷口徑：營收越低，代表平台銷售規模越弱。",
                _platform_row_detail(revenue_min),
            ]
        )

    if "inventory_efficiency" in lens_names and "revenue_scale" not in lens_names and amount_ratio_min is not None:
        return "\n".join(
            [
                f"以最新可用月份 {month} 的庫存效率來看，表現較弱的平台是 {_platform_name(amount_ratio_min)}。",
                "",
                "判斷口徑：營收/庫存金額比值越低，代表同樣庫存金額創造的營收越少。",
                _platform_row_detail(amount_ratio_min),
            ]
        )

    lines = [
        f"以最新可用月份 {month} 來看，「平台表現較差」需要先看 KPI 口徑；目前資料可支援以下判斷：",
        "",
    ]
    if revenue_min is not None:
        lines.append(
            f"- 營收規模最低：{_platform_name(revenue_min)}，營收 {format_number(revenue_min.get(COL_REVENUE))}。"
        )
    if amount_ratio_min is not None:
        lines.append(
            f"- 庫存效率最低：{_platform_name(amount_ratio_min)}，營收/庫存金額比值 {format_number(amount_ratio_min.get(COL_REVENUE_INV_AMOUNT_RATIO))}。"
        )
    if qty_ratio_min is not None:
        lines.append(
            f"- 營收/QTY 效率最低：{_platform_name(qty_ratio_min)}，營收/庫存 QTY 比值 {format_number(qty_ratio_min.get(COL_REVENUE_INV_QTY_RATIO))}。"
        )
    if risk_row is not None:
        lines.append(
            f"- 異常風險優先關注：{risk_row.get(COL_PLATFORM) or '未標示平台'}，原因為 {risk_row.get(COL_ANOMALY_REASON) or risk_row.get(COL_ANOMALY_TYPE)}。"
        )

    lines.extend(
        [
            "",
            "建議管理判讀：若主管要看營收規模，優先看營收最低的平台；若要看營運效率，優先看營收/庫存比值最低的平台。",
            "本題若採預設經營效率口徑，應優先關注庫存效率最低的平台。",
        ]
    )
    if amount_ratio_min is not None:
        lines.append(_platform_row_detail(amount_ratio_min))
    return "\n".join(lines)


def _compose_trend(profile: BusinessQuestionProfile, routing: Any, toolbox: AnalysisToolbox) -> str:
    filters = _filters_from_routing(routing)
    inventory_like = _has_any(routing.question, ["庫存", "QTY", "存貨"])
    metric = "inventory_amount_trend" if inventory_like else "revenue_trend"
    value_col = COL_INV_AMOUNT if inventory_like else COL_REVENUE
    label = "庫存金額" if inventory_like else "營收"
    df = toolbox.get_metric_table(metric, filters)
    if df.empty:
        return f"目前沒有符合條件的{label}趨勢資料。"

    ordered = df.sort_values(COL_MONTH).reset_index(drop=True)
    latest = ordered.iloc[-1]
    lines = [
        f"{label}趨勢判斷：{_direction_text(ordered, value_col)}",
        f"最新月份 {latest.get(COL_MONTH)} 的{label}為 {format_number(latest.get(value_col))}。",
        "",
        "最近三期：",
    ]
    for _, row in ordered.tail(3).iterrows():
        mom = row.get("月增率")
        mom_text = "N/A" if pd.isna(mom) else f"{mom:.2%}"
        lines.append(f"- {row.get(COL_MONTH)}：{format_number(row.get(value_col))}，月增率 {mom_text}")
    return "\n".join(lines)


def _compose_risk(profile: BusinessQuestionProfile, routing: Any, toolbox: AnalysisToolbox) -> str:
    filters = _filters_from_routing(routing)
    rows = toolbox.get_anomalies(top_n=8, filters=filters)
    if not rows:
        return "目前在符合條件的範圍內，沒有偵測到主要異常訊號。"

    rows = sorted(rows, key=lambda item: abs(float(item.get(COL_ANOMALY_SIGNAL, 0) or 0)), reverse=True)
    lead = rows[0]
    lines = [
        f"目前最需要優先關注的風險是 {lead.get(COL_MONTH)} / 平台 {lead.get(COL_PLATFORM) or '未標示'} / {lead.get(COL_ANOMALY_TYPE)}。",
        f"原因：{lead.get(COL_ANOMALY_REASON) or '未提供原因'}；訊號值 {format_number(lead.get(COL_ANOMALY_SIGNAL))}。",
        "",
        "高風險清單：",
    ]
    for index, row in enumerate(rows[:5], start=1):
        lines.append(
            f"{index}. {row.get(COL_MONTH)} / {row.get(COL_PLATFORM) or '未標示平台'} / {row.get(COL_ANOMALY_TYPE)}：{row.get(COL_ANOMALY_REASON) or '未提供原因'}"
        )
    return "\n".join(lines)


def _compose_data_quality(toolbox: AnalysisToolbox, context: Any) -> str:
    coverage = toolbox.get_data_coverage()
    mapping = toolbox.get_mapping_summary()
    messages = getattr(context, "messages", None)
    warnings = getattr(messages, "warnings", []) if messages else []
    errors = getattr(messages, "errors", []) if messages else []

    lines = [
        "目前資料品質檢查摘要如下：",
        f"- 營收資料筆數：{coverage.get('revenue_rows')}",
        f"- 庫存資料筆數：{coverage.get('inventory_rows')}",
        f"- Mapping 筆數：{coverage.get('mapping_rows')}",
        f"- Mapping 是否可建立橋接：{'是' if coverage.get('mapping_success') else '否'}",
        f"- HQBU / 平台橋接候選數：{mapping.get('bridge_candidate_count')}",
    ]
    if errors:
        lines.append("")
        lines.append("錯誤：")
        lines.extend(f"- {item}" for item in errors[:5])
    if warnings:
        lines.append("")
        lines.append("警告：")
        lines.extend(f"- {item}" for item in warnings[:5])
    if not errors and not warnings:
        lines.append("- 目前 pipeline 未回報主要錯誤或警告。")
    return "\n".join(lines)


def _compose_decision(profile: BusinessQuestionProfile, routing: Any, toolbox: AnalysisToolbox) -> str:
    filters = _filters_from_routing(routing)
    month = filters.month or _latest_month(toolbox)
    platform_df = toolbox.get_metric_table("platform_monthly", QueryFilters(month=month, group_code=filters.group_code))
    if platform_df.empty:
        return "目前沒有足夠的平台層級資料可產生處理優先順序。"

    weak_efficiency = _first_sorted(platform_df, COL_REVENUE_INV_AMOUNT_RATIO, ascending=True)
    weak_revenue = _first_sorted(platform_df, COL_REVENUE, ascending=True)
    risk_row = _top_anomaly(toolbox, QueryFilters(month=month, group_code=filters.group_code))

    lines = [f"以 {month} 的資料來看，建議優先處理順序如下：", ""]
    rank = 1
    if weak_efficiency is not None:
        lines.append(
            f"{rank}. 優先檢查 {_platform_name(weak_efficiency)} 的庫存效率：營收/庫存金額比值 {format_number(weak_efficiency.get(COL_REVENUE_INV_AMOUNT_RATIO))}。"
        )
        rank += 1
    if risk_row is not None:
        lines.append(
            f"{rank}. 追蹤 {risk_row.get(COL_PLATFORM) or '未標示平台'} 的異常訊號：{risk_row.get(COL_ANOMALY_REASON) or risk_row.get(COL_ANOMALY_TYPE)}。"
        )
        rank += 1
    if weak_revenue is not None:
        lines.append(
            f"{rank}. 檢視 {_platform_name(weak_revenue)} 的營收規模：最新營收 {format_number(weak_revenue.get(COL_REVENUE))}。"
        )
    lines.append("")
    lines.append("管理建議：先釐清低效率平台是否為需求下滑、庫存配置過高，或 mapping 對齊造成的結構性差異。")
    return "\n".join(lines)


def _compose_comparison(profile: BusinessQuestionProfile, routing: Any, toolbox: AnalysisToolbox) -> str:
    platforms = _extract_platforms(routing.question)
    if len(platforms) < 2:
        return "請提供至少兩個平台代碼，例如 GG-01 與 GG-02，才能進行平台比較。"

    filters = _filters_from_routing(routing)
    month = filters.month or _latest_month(toolbox)
    platform_df = toolbox.get_metric_table("platform_monthly", QueryFilters(month=month, group_code=filters.group_code))
    subset = platform_df[platform_df[COL_PLATFORM].astype(str).str.upper().isin(platforms)]
    if subset.empty:
        return f"目前在 {month} 找不到指定平台的可比較資料。"

    lines = [f"以下以 {month} 的平台資料比較 {'、'.join(platforms)}：", ""]
    for _, row in subset.iterrows():
        lines.append(f"- {_platform_row_detail(row)}")
    if COL_REVENUE_INV_AMOUNT_RATIO in subset.columns and len(subset) >= 2:
        best = _first_sorted(subset, COL_REVENUE_INV_AMOUNT_RATIO, ascending=False)
        weakest = _first_sorted(subset, COL_REVENUE_INV_AMOUNT_RATIO, ascending=True)
        if best is not None and weakest is not None:
            lines.append("")
            lines.append(
                f"以庫存效率來看，{_platform_name(best)} 較佳；{_platform_name(weakest)} 較弱。"
            )
    return "\n".join(lines)


def _compose_diagnosis(
    profile: BusinessQuestionProfile,
    routing: Any,
    toolbox: AnalysisToolbox,
    domain_results: list[Any],
) -> str:
    filters = _filters_from_routing(routing)
    month = filters.month or _latest_month(toolbox)
    platform_df = toolbox.get_metric_table("platform_monthly", QueryFilters(month=month, platform=filters.platform, group_code=filters.group_code))
    anomalies = toolbox.get_anomalies(top_n=5, filters=QueryFilters(month=month, platform=filters.platform, group_code=filters.group_code))

    lines = [f"診斷結論會以目前資料可支持的證據為主；目前可用欄位不包含毛利、成本、費用或現金流。", ""]
    if not platform_df.empty:
        weak_efficiency = _first_sorted(platform_df, COL_REVENUE_INV_AMOUNT_RATIO, ascending=True)
        if weak_efficiency is not None:
            lines.append(
                f"- 資料支持的主要訊號：{_platform_name(weak_efficiency)} 的營收/庫存金額比值較弱，數值為 {format_number(weak_efficiency.get(COL_REVENUE_INV_AMOUNT_RATIO))}。"
            )
    if anomalies:
        lead = sorted(anomalies, key=lambda item: abs(float(item.get(COL_ANOMALY_SIGNAL, 0) or 0)), reverse=True)[0]
        lines.append(
            f"- 異常訊號：{lead.get(COL_MONTH)} / {lead.get(COL_PLATFORM) or '未標示平台'} / {lead.get(COL_ANOMALY_TYPE)}，原因為 {lead.get(COL_ANOMALY_REASON) or '未提供'}。"
        )
    if len(lines) <= 2:
        lines.append("- 目前沒有足夠異常或平台效率訊號可形成明確診斷。")
    lines.append("")
    lines.append("需要補充資料才能判斷的原因：毛利率、成本、價格折扣、客戶/訂單或產品/SKU 結構。")
    return "\n".join(lines)


def _with_request_id(request_id: str, body: str | None) -> str | None:
    if not body:
        return None
    return f"Request ID: {request_id}\n\n{body}"


def _filters_from_routing(routing: Any) -> QueryFilters:
    filters = getattr(routing, "filters", None)
    if isinstance(filters, QueryFilters):
        return filters
    return QueryFilters(
        month=getattr(filters, "month", None),
        platform=getattr(filters, "platform", None),
        group_code=getattr(filters, "group_code", None),
    )


def _latest_month(toolbox: AnalysisToolbox) -> str | None:
    coverage = toolbox.get_data_coverage()
    months = coverage.get("months") or []
    return months[-1] if months else None


def _first_sorted(df: pd.DataFrame, column: str, *, ascending: bool) -> pd.Series | None:
    if df.empty or column not in df.columns:
        return None
    subset = df.dropna(subset=[column]).sort_values(column, ascending=ascending).reset_index(drop=True)
    if subset.empty:
        return None
    return subset.iloc[0]


def _top_anomaly(toolbox: AnalysisToolbox, filters: QueryFilters) -> dict[str, Any] | None:
    rows = toolbox.get_anomalies(top_n=8, filters=filters)
    if not rows:
        return None
    rows = sorted(rows, key=lambda item: abs(float(item.get(COL_ANOMALY_SIGNAL, 0) or 0)), reverse=True)
    return rows[0]


def _platform_name(row: pd.Series | dict[str, Any]) -> str:
    value = row.get(COL_PLATFORM)
    return str(value) if value not in {None, ""} and not pd.isna(value) else "未標示平台"


def _platform_row_detail(row: pd.Series | dict[str, Any]) -> str:
    parts = [
        f"平台 {_platform_name(row)}",
        f"新事業群 {row.get(COL_GROUP_CODE, 'N/A')}",
        f"營收 {format_number(row.get(COL_REVENUE))}",
        f"庫存金額 {format_number(row.get(COL_INV_AMOUNT))}",
        f"QTY {format_number(row.get(COL_INV_QTY), decimals=0)}",
    ]
    if COL_REVENUE_INV_AMOUNT_RATIO in row:
        parts.append(f"營收/庫存金額比值 {format_number(row.get(COL_REVENUE_INV_AMOUNT_RATIO))}")
    if COL_REVENUE_INV_QTY_RATIO in row:
        parts.append(f"營收/QTY 比值 {format_number(row.get(COL_REVENUE_INV_QTY_RATIO))}")
    return " / ".join(parts)


def _direction_text(df: pd.DataFrame, value_col: str) -> str:
    if df.empty or value_col not in df.columns or len(df) < 2:
        return "資料點不足，無法判斷明確趨勢"
    first = df.iloc[0]
    latest = df.iloc[-1]
    start = first.get(value_col)
    end = latest.get(value_col)
    if pd.isna(start) or pd.isna(end):
        return "資料中有缺值，無法判斷明確趨勢"
    if end > start:
        direction = "整體上升"
    elif end < start:
        direction = "整體下降"
    else:
        direction = "大致持平"
    return f"{direction}，從 {first.get(COL_MONTH)} 的 {format_number(start)} 到 {latest.get(COL_MONTH)} 的 {format_number(end)}"


def _extract_platforms(question: str) -> list[str]:
    return list(dict.fromkeys(match.group(0).upper() for match in re.finditer(r"GG-(0[1-9]|[1-8][0-9]|9[0-1])", question.upper())))


def _question_mentions_platform(question: str) -> bool:
    return _has_any(question, ["平台", "平臺", "GG-"])


def _has_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)
