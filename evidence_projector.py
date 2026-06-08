from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from config import (
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

UNMAPPED_ENTITY_VALUES = {"", "未對應", "未分類", "unknown", "n/a", "nan", "none", "null"}


def is_unmapped_entity(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in UNMAPPED_ENTITY_VALUES


@dataclass(frozen=True)
class ProjectedObservation:
    text: str
    source_tool: str
    evidence_type: str
    role: str
    display_priority: int


@dataclass(frozen=True)
class DisplayBlocks:
    headline: str
    key_observations: list[str]
    table: dict[str, Any] | None
    limitations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_display_blocks_from_roles(
    task_profile: Any | None,
    answer_plan: Any | None,
    rubric_result: Any,
    limitations: list[str],
) -> dict[str, Any]:
    if getattr(task_profile, "task_family", None) == "forecast_unsupported":
        return DisplayBlocks(
            headline=_forecast_unsupported_headline(task_profile),
            key_observations=[
                "目前資料可用於觀察歷史營收與庫存變化，但不足以直接預測下個月。",
                "若要評估改善機率，需補充訂單、出貨、價格、客戶需求或正式 forecast model。",
            ],
            table=None,
            limitations=list(dict.fromkeys(limitations))[:3],
        ).to_dict()

    max_items = int(getattr(answer_plan, "max_key_observations", 3) or 3)
    evidence_items = list(getattr(rubric_result, "evidence", []))
    primary = [item for item in evidence_items if getattr(item, "role", None) == "primary"]
    supporting = [item for item in evidence_items if getattr(item, "role", None) == "supporting"]

    headline = _build_headline(task_profile, primary, supporting)
    observations = _project_observations([*primary, *supporting], max_items)
    table = None
    if bool(getattr(task_profile, "requires_table", False)) or bool(getattr(answer_plan, "requires_table", False)):
        table = _project_table(primary)

    display_limitations = list(limitations)
    if _has_unmapped_entity(evidence_items):
        display_limitations.append("部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。")

    return DisplayBlocks(
        headline=headline,
        key_observations=[item.text for item in observations],
        table=table,
        limitations=list(dict.fromkeys(display_limitations))[:3],
    ).to_dict()


def _build_headline(task_profile: Any | None, primary: list[Any], supporting: list[Any]) -> str:
    task_family = getattr(task_profile, "task_family", None)
    if task_family == "forecast_unsupported":
        return _forecast_unsupported_headline(task_profile)
    if not primary:
        return "結論：目前沒有足夠的 primary evidence 可以形成管理結論。"
    if task_family == "entity_month_table_lookup":
        return _entity_month_table_headline(primary, compare=False)
    if task_family == "metric_lookup":
        return _metric_lookup_headline(primary)
    if task_family == "entity_period_pair_table_lookup":
        return _entity_period_pair_table_headline(primary)
    if task_family == "entity_multi_month_table_lookup":
        return _entity_multi_month_table_headline(primary)
    if task_family == "entity_period_pair_metric_lookup":
        return _entity_period_pair_value_headline(primary)
    if task_family in {"latest_month_platform_summary", "latest_month_entity_summary"}:
        return _latest_month_platform_summary_headline(primary, supporting)
    if task_family == "period_pair_compare":
        return _period_pair_headline(primary)
    if task_family == "entity_time_series":
        return _entity_time_series_headline(primary)
    if task_family == "overall_trend_analysis":
        return _overall_time_series_headline(primary)
    if task_family == "entity_trend_comparison":
        return _entity_trend_comparison_headline(primary)
    if task_family == "metric_relationship_analysis":
        return _metric_relationship_headline(primary)
    if task_family == "contribution_analysis":
        return _entity_contribution_headline(primary)
    if task_family == "parent_child_drilldown":
        return _parent_child_drilldown_headline(primary)
    if task_family == "cross_section_compare":
        return _cross_section_headline(task_profile, primary)
    if task_family == "performance_assessment":
        return _performance_headline(task_profile, primary, supporting)
    if task_family == "time_compare":
        return _time_compare_headline(primary)
    if task_family == "diagnosis":
        return _diagnosis_headline(primary)
    if task_family == "risk_scan":
        return _risk_headline(primary)
    if task_family == "entity_ranking":
        return _ranking_headline(primary)
    return _fallback_headline(primary[0])


def _entity_month_table_headline(primary: list[Any], *, compare: bool) -> str:
    evidence = _first_evidence(primary, "entity_month_table")
    if not evidence:
        return "結論：目前缺少單月 entity table evidence。"
    details = getattr(evidence, "details", {}) or {}
    rows = details.get("rows") or []
    summary = details.get("summary") or {}
    month = details.get("month")
    entity_label = details.get("entity_label") or "entity"
    metric_label = details.get("metric_label") or details.get("metric") or "指標"
    row_count = summary.get("row_count", len(rows))
    top_entity = summary.get("top_entity")
    lowest_entity = summary.get("lowest_entity")
    if compare:
        if top_entity and lowest_entity:
            return f"結論：{month} 各{entity_label}{metric_label}比較下，{metric_label}最高的是 {top_entity}，最低的是 {lowest_entity}。"
        return f"結論：已比較 {month} 各{entity_label}{metric_label}資料，共 {row_count} 筆。"
    if top_entity:
        return f"結論：已列出 {month} 各{entity_label}{metric_label}資料，共 {row_count} 筆；{metric_label}最高的是 {top_entity}。"
    return f"結論：已列出 {month} 各{entity_label}{metric_label}資料，共 {row_count} 筆。"


def _entity_period_pair_table_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "entity_period_pair_table")
    if not evidence:
        return "結論：目前缺少兩個指定月份的 entity table evidence。"
    details = getattr(evidence, "details", {}) or {}
    summary = details.get("summary") or {}
    rows = details.get("rows") or []
    metric_label = details.get("metric_label") or details.get("metric") or "指標"
    entity_label = details.get("entity_label") or "entity"
    top = summary.get("top_entity_period_b")
    if top:
        return (
            f"結論：已列出 {details.get('period_a')} 與 {details.get('period_b')} 各{entity_label}{metric_label}資料，"
            f"共 {summary.get('row_count', len(rows))} 筆；{details.get('period_b')} 最高的是 {top}。"
        )
    return f"結論：已列出 {details.get('period_a')} 與 {details.get('period_b')} 各{entity_label}{metric_label}資料，共 {summary.get('row_count', len(rows))} 筆。"


def _entity_multi_month_table_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "entity_multi_month_table")
    if not evidence:
        return "結論：目前缺少指定月份區間的 entity table evidence。"
    details = getattr(evidence, "details", {}) or {}
    summary = details.get("summary") or {}
    rows = details.get("rows") or []
    return (
        f"結論：已列出 {details.get('start_month')} 至 {details.get('end_month')} 各{details.get('entity_label', 'entity')}"
        f"{details.get('metric_label', details.get('metric'))}資料，共 {summary.get('row_count', len(rows))} 筆。"
    )


def _entity_period_pair_value_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "entity_period_pair_value")
    if not evidence:
        return "結論：目前缺少指定 entity 的兩期資料。"
    details = getattr(evidence, "details", {}) or {}
    metric_label = details.get("metric_label") or details.get("metric") or "指標"
    change = details.get("change")
    if change is None:
        return (
            f"結論：已查詢 {details.get('entity_value')} 在 {details.get('period_a')} 與 {details.get('period_b')} 的{metric_label}；"
            "其中至少一期目前沒有可用數值。"
        )
    direction = "增加" if float(change) > 0 else ("下降" if float(change) < 0 else "持平")
    return (
        f"結論：{details.get('entity_value')} {details.get('period_b')} {metric_label}相較 {details.get('period_a')} {direction} "
        f"{_format_number(abs(change or 0))}。"
    )


def _metric_lookup_headline(primary: list[Any]) -> str:
    lookup = _first_evidence(primary, "entity_metric_lookup")
    if not lookup:
        return _fallback_headline(primary[0]) if primary else "結論：目前缺少指定查詢資料。"
    details = getattr(lookup, "details", {}) or {}
    value = details.get("value")
    if value is None:
        return (
            f"結論：目前找不到 {details.get('month')} {details.get('entity_label', 'entity')} "
            f"{details.get('entity_value')} 的{details.get('metric_label', details.get('metric'))}資料。"
        )
    return (
        f"結論：{details.get('month')} {details.get('entity_label', 'entity')} {details.get('entity_value')} "
        f"的{details.get('metric_label', details.get('metric'))}為 {_format_number(value)}。"
    )


def _forecast_unsupported_headline(task_profile: Any | None) -> str:
    metrics = set(getattr(task_profile, "metrics", []) or [])
    if metrics & {"inventory_amount", "inventory_qty"} and "revenue" not in metrics:
        subject = "未來庫存是否會下降"
    elif metrics & {"inventory_amount", "inventory_qty"}:
        subject = "未來營收或庫存是否會改善"
    else:
        subject = "下個月營收是否會改善"
    return f"結論：目前無法判斷{subject}，因為系統尚未納入預測模型、訂單、出貨、價格或市場需求資料。"


def _latest_month_platform_summary_headline(primary: list[Any], supporting: list[Any]) -> str:
    snapshot = _first_evidence(primary, "entity_performance_snapshot") or _first_evidence(primary, "platform_performance_snapshot")
    details = getattr(snapshot, "details", {}) if snapshot else {}
    entity_label = details.get("entity_label") or "事業群"
    rows = _metric_rows([snapshot]) if snapshot else _metric_rows(primary)
    if not rows:
        return f"結論：最新月份各{entity_label}摘要目前缺少可投影的 scorecard evidence。"
    month = _first_value(rows, "month") or "最新月份"
    top_revenue = _max_mapped_row(rows, "revenue") or _max_row(rows, "revenue")
    top_inventory = _max_mapped_row(rows, "inventory_amount") or _max_row(rows, "inventory_amount")
    weakest = _min_row(rows, "health_score") or _max_row(rows, "risk_score")
    parts: list[str] = []
    if top_revenue:
        parts.append(f"{top_revenue['platform']} 營收規模較高")
    if top_inventory:
        parts.append(f"{top_inventory['platform']} 庫存水位較高")
    if weakest and is_unmapped_entity(weakest.get("platform")):
        parts.append("未對應資料列在 scorecard 下需作為資料品質限制追蹤")
    elif weakest:
        parts.append(f"{weakest['platform']} 在綜合 scorecard 下需要注意")
    if not parts:
        parts.append(f"各{entity_label}需要搭配營收、庫存與 scorecard 一併判讀")
    return f"結論：最新月份 {month} 各{entity_label}比較下，" + "，".join(parts) + "。"


def _period_pair_headline(primary: list[Any]) -> str:
    comparison = _first_evidence(primary, "entity_period_pair_comparison") or _first_evidence(primary, "period_pair_metric_comparison")
    if not comparison:
        return "結論：目前缺少兩個指定月份的可比較資料。"
    details = getattr(comparison, "details", {}) or {}
    overall = details.get("overall") or {}
    period_a = details.get("period_a")
    period_b = details.get("period_b")
    metric = _metric_name(details.get("metric"))
    change = overall.get("change")
    direction = overall.get("direction")
    direction_text = "增加" if direction == "up" else ("下降" if direction == "down" else "持平")
    pct = overall.get("change_pct")
    pct_text = f"，變化率為 {float(pct):.2%}" if pct is not None else ""
    return f"結論：{period_b} {metric}相較 {period_a} {direction_text} {_format_number(abs(change or 0))}{pct_text}。"


def _entity_time_series_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "entity_time_series")
    if not evidence:
        return "結論：目前缺少指定 entity 的各月資料。"
    details = getattr(evidence, "details", {}) or {}
    summary = details.get("summary") or {}
    rows = details.get("rows") or []
    start_month = rows[0].get("month") if rows else "起始月份"
    end_month = rows[-1].get("month") if rows else "結束月份"
    direction = {"up": "上升", "down": "下降", "flat": "持平"}.get(summary.get("direction"), "變化")
    return (
        f"結論：{details.get('entity_value')}各月{details.get('metric_label', details.get('metric'))}"
        f"在 {start_month} 至 {end_month} 期間呈現{direction}；最新月份 "
        f"{summary.get('latest_month')} 為 {_format_number(summary.get('latest_value'))}。"
    )


def _overall_time_series_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "overall_time_series")
    if not evidence:
        return "結論：目前缺少整體各月資料。"
    details = getattr(evidence, "details", {}) or {}
    rows = details.get("rows") or []
    summary = details.get("summary") or {}
    start_month = rows[0].get("month") if rows else "起始月份"
    end_month = rows[-1].get("month") if rows else "結束月份"
    direction = {"up": "上升", "down": "下降", "flat": "持平"}.get(summary.get("direction"), "變化")
    return (
        f"結論：整體{details.get('metric_label', details.get('metric'))}在 {start_month} 至 {end_month} 期間呈現{direction}，"
        f"最新月份 {summary.get('latest_month')} 為 {_format_number(summary.get('latest_value'))}。"
    )


def _entity_trend_comparison_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "entity_trend_comparison")
    if not evidence:
        return "結論：目前缺少跨 entity 趨勢比較資料。"
    details = getattr(evidence, "details", {}) or {}
    summary = details.get("summary") or {}
    top_entity = summary.get("top_growth_entity")
    top_pct = summary.get("top_growth_pct")
    return (
        f"結論：近月{details.get('metric_label', details.get('metric'))}成長較明顯的"
        f"{details.get('entity_label', 'entity')}是 {top_entity}，變化率為 {_format_number(top_pct)}。"
    )


def _metric_relationship_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "metric_relationship")
    if not evidence:
        return "結論：目前缺少營收與庫存關係資料。"
    details = getattr(evidence, "details", {}) or {}
    rows = details.get("rows") or []
    label = rows[0].get("relationship_label") if rows else "mixed"
    return f"結論：目前可觀察到{details.get('entity_label', 'entity')}存在營收與庫存背離訊號，例如 {label}。"


def _entity_contribution_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "entity_contribution_analysis")
    if not evidence:
        return "結論：目前缺少 contribution 分析資料。"
    details = getattr(evidence, "details", {}) or {}
    summary = details.get("summary") or {}
    return (
        f"結論：{details.get('period_b')} 相較 {details.get('period_a')} 的"
        f"{details.get('metric_label', details.get('metric'))}變化主要由 {summary.get('top_contributor')} 貢獻，"
        f"變化為 {_format_number(summary.get('top_change'))}。"
    )


def _parent_child_drilldown_headline(primary: list[Any]) -> str:
    evidence = _first_evidence(primary, "parent_child_drilldown") or _first_evidence(primary, "entity_performance_snapshot")
    if not evidence:
        return "結論：目前缺少 parent-child drilldown 資料。"
    details = getattr(evidence, "details", {}) or {}
    summary = details.get("summary") or {}
    weakest = summary.get("weakest_entity")
    parent = (details.get("parent_filter") or {}).get("business_group") or "指定事業群"
    return f"結論：在 {parent} 底下，{weakest} 產品線表現較弱 / 庫存壓力較高。"


def _cross_section_headline(task_profile: Any | None, primary: list[Any]) -> str:
    table = _first_evidence(primary, "entity_month_table")
    if table:
        return _entity_month_table_headline(primary, compare=True)
    rows = _metric_rows(primary)
    month = _profile_month(task_profile) or _first_value(rows, "month") or "目前期間"
    if not rows:
        return "目前沒有足夠證據形成完整橫向比較。"

    top_revenue = _max_mapped_row(rows, "revenue") or _max_row(rows, "revenue")
    top_inventory = _max_mapped_row(rows, "inventory_amount") or _max_row(rows, "inventory_amount")
    weakest_ratio = _min_row(rows, "revenue_inventory_ratio")
    if not (top_revenue and top_inventory and weakest_ratio):
        return "目前沒有足夠證據形成完整橫向比較。"

    entity_label = next((row.get("entity_label") for row in rows if row.get("entity_label")), "事業群")
    weakest_text = (
        "未對應資料列"
        if weakest_ratio and is_unmapped_entity(weakest_ratio.get("platform"))
        else weakest_ratio["platform"]
    )
    return (
        f"結論：{month} 各{entity_label}比較下，{top_revenue['platform']} 營收規模較高，"
        f"{top_inventory['platform']} 庫存水位較高；但 {weakest_text} "
        "的營收相對庫存效率較弱，需搭配庫存壓力判讀。"
    )


def _performance_headline(task_profile: Any | None, primary: list[Any], supporting: list[Any]) -> str:
    polarity = getattr(task_profile, "polarity", None)
    snapshot = _first_evidence(primary, "entity_performance_snapshot") or _first_evidence(primary, "platform_performance_snapshot")
    if snapshot:
        details = getattr(snapshot, "details", {}) or {}
        summary = details.get("summary") or {}
        entity_label = details.get("entity_label") or "事業群"
        rows = _metric_rows([snapshot])
        if polarity in {"best", "strong"}:
            best_platform = summary.get("best_entity") or summary.get("best_platform")
            if is_unmapped_entity(best_platform):
                best_platform = _first_mapped_entity(rows, "health_score", reverse=True)
            best_row = _find_row(rows, best_platform)
            if best_row:
                return (
                    f"結論：目前綜合表現較佳的{entity_label}是 {best_platform}，因為其 "
                    f"{best_row.get('primary_strength') or 'health_score 較高'}，"
                    f"health_score 為 {_format_number(best_row.get('health_score'))}。"
                )
        if polarity in {"worst", "weak"}:
            weakest_platform = summary.get("weakest_entity") or summary.get("weakest_platform")
            weakest_row = _find_row(rows, weakest_platform)
            if weakest_row:
                if is_unmapped_entity(weakest_platform):
                    return (
                        f"結論：目前未對應資料列在{entity_label} scorecard 下風險較高，"
                        "建議先視為資料對應限制；已對應資料則需搭配表格中的 health_score 與 proxy 判讀。"
                    )
                return (
                    f"結論：目前表現較弱的{entity_label}優先看 {weakest_platform}，因為其 "
                    f"{weakest_row.get('primary_risk') or 'health_score 較低'}，"
                    f"health_score 為 {_format_number(weakest_row.get('health_score'))}。"
                )

    ratio_rows = _metric_rows(primary)
    anomaly_platforms = {
        _platform(getattr(item, "details", {}) or {})
        for item in supporting
        if getattr(item, "evidence_type", None) == "anomaly"
    }
    anomaly_platforms.discard(None)

    weakest = _min_row(ratio_rows, "revenue_inventory_ratio")
    if polarity in {"best", "strong"}:
        explicit_strong = [
            row
            for row in ratio_rows
            if row.get("source_tool") not in {"get_inventory_turnover_proxy", "get_platform_ratios"}
            and row.get("platform") not in anomaly_platforms
        ]
        strongest = _max_row(explicit_strong, "revenue_inventory_ratio")
        if strongest:
            return (
                f"結論：目前較佳的新事業群候選是 {strongest['platform']}，因為其營收相對庫存效率 proxy "
                "較高，且在目前 primary/supporting evidence 中未見直接異常訊號。"
            )
        if weakest:
            return (
                "結論：目前資料較適合辨識弱勢新事業群，尚不足以明確判定最佳新事業群；"
                f"可先排除 {weakest['platform']} 等效率偏弱新事業群。"
            )
        return "目前沒有足夠證據形成明確結論。"

    anomaly = _top_anomaly(supporting)
    if weakest:
        suffix = ""
        if anomaly and _platform(getattr(anomaly, "details", {}) or {}) == weakest.get("platform"):
            suffix = "，且同新事業群也有異常訊號需要追蹤"
        return (
            f"結論：目前表現較弱的新事業群優先看 {weakest['platform']}，因為其營收相對庫存效率 proxy "
            f"偏弱{suffix}。"
        )
    if anomaly:
        details = getattr(anomaly, "details", {}) or {}
        return f"結論：目前表現較弱的新事業群優先看 {_platform(details) or 'N/A'}，因為其異常訊號較明顯。"
    return "目前沒有足夠證據形成明確結論。"


def _time_compare_headline(primary: list[Any]) -> str:
    contribution = _first_evidence(primary, "contribution_analysis")
    if contribution:
        details = getattr(contribution, "details", {}) or {}
        first = (details.get("contributors") or [{}])[0]
        return (
            f"結論：{details.get('month')} 相較 {details.get('previous_month')} 的營收變化主要由 "
            f"{first.get('name')} 貢獻，變化 {_format_number(first.get('change'))}。"
        )
    trend = _first_evidence(primary, "yoy_mom_breakdown")
    if trend:
        details = getattr(trend, "details", {}) or {}
        return (
            f"結論：{details.get('month')} 相較 {details.get('previous_month')} 的"
            f"{_metric_name(details.get('metric'))}變化為 {_format_number(details.get('mom_change'))}。"
        )
    return "目前沒有足夠證據形成明確結論。"


def _diagnosis_headline(primary: list[Any]) -> str:
    candidate = _first_evidence(primary, "root_cause_candidate")
    if candidate:
        details = getattr(candidate, "details", {}) or {}
        first = (details.get("candidates") or [{}])[0]
        title = first.get("title") or first.get("description") or first.get("candidate_type") or "候選觀察方向"
        return f"結論：目前不能確認根因，但可整理候選觀察方向，優先檢查 {title}。"
    return "結論：目前不能確認根因，但可整理候選觀察方向。"


def _risk_headline(primary: list[Any]) -> str:
    anomaly = _top_anomaly(primary)
    if anomaly:
        details = getattr(anomaly, "details", {}) or {}
        return (
            f"結論：目前最需優先追蹤的是 {_platform(details) or 'N/A'} 風險訊號，"
            f"異常類型為 {details.get(COL_ANOMALY_TYPE, 'N/A')}。"
        )
    weakest = _min_row(_metric_rows(primary), "revenue_inventory_ratio")
    if weakest:
        return f"結論：目前最需優先追蹤的是 {weakest['platform']} 風險訊號，因為營收相對庫存效率 proxy 偏弱。"
    return "目前沒有足夠證據形成明確結論。"


def _ranking_headline(primary: list[Any]) -> str:
    ranking = _first_evidence(primary, "entity_metric_ranking")
    if ranking:
        details = getattr(ranking, "details", {}) or {}
        month = details.get("month") or "最新月份"
        label = details.get("entity_label") or "事業群"
        metric_label = details.get("metric_label") or details.get("metric") or "指標"
        direction_text = "最低" if details.get("sort_direction") == "ascending" else "最高"
        top_entity = details.get("top_entity")
        top_value = details.get("top_value")
        if is_unmapped_entity(top_entity):
            return (
                f"結論：{month} {metric_label}排序中未對應資料列位居前段，"
                f"需先視為資料品質限制；目前無法把未對應列當作正式最佳{label}。"
            )
        return f"結論：最新月份 {month} {metric_label}{direction_text}的{label}是 {top_entity}，{metric_label}為 {_format_number(top_value)}。"
    return _fallback_headline(primary[0]) if primary else "目前沒有足夠證據形成明確結論。"


def _fallback_headline(lead: Any) -> str:
    observation = _observation_text(lead)
    return f"結論：{observation}" if observation else "目前沒有足夠證據形成明確結論。"


def _project_observations(items: list[Any], max_items: int) -> list[ProjectedObservation]:
    projected: list[ProjectedObservation] = []
    seen: set[str] = set()
    for item in items:
        if getattr(item, "role", None) not in {"primary", "supporting"}:
            continue
        text = _observation_text(item)
        if not text:
            continue
        key = _observation_key(item, text)
        if key in seen:
            continue
        seen.add(key)
        projected.append(
            ProjectedObservation(
                text=text,
                source_tool=getattr(item, "source_tool", ""),
                evidence_type=getattr(item, "evidence_type", ""),
                role=getattr(item, "role", ""),
                display_priority=int(getattr(item, "display_priority", 999) or 999),
            )
        )
        if len(projected) >= max_items:
            break
    return projected


def _observation_text(item: Any) -> str:
    details = getattr(item, "details", {}) or {}
    evidence_type = getattr(item, "evidence_type", "")
    if evidence_type == "entity_performance_snapshot":
        summary = details.get("summary") or {}
        label = details.get("entity_label") or "事業群"
        best = summary.get("best_entity")
        weakest = summary.get("weakest_entity")
        if is_unmapped_entity(best):
            best = "已對應資料中排名較前者"
        weakest_text = "未對應資料列需作為資料品質限制追蹤" if is_unmapped_entity(weakest) else f"需要注意的是 {weakest}"
        return f"{label} scorecard 顯示，綜合表現較佳的是 {best}，{weakest_text}。"
    if evidence_type == "entity_performance_row":
        label = details.get("entity_label") or "entity"
        entity = details.get("entity_value") or "N/A"
        return (
            f"{label} {entity} 的 health_score 為 {_format_number(details.get('health_score'))}，"
            f"主要風險為 {details.get('primary_risk', 'N/A')}。"
        )
    if evidence_type in {"entity_cross_section", "entity_cross_section_comparison"}:
        label = details.get("entity_label") or "事業群"
        rows = details.get("rows") or []
        return f"{label}橫向比較目前有 {len(rows)} 筆可投影列，請搭配表格查看營收、庫存與 proxy。"
    if evidence_type == "entity_metric_lookup":
        return (
            f"{details.get('month')} {details.get('entity_label', 'entity')} {details.get('entity_value')} "
            f"的{details.get('metric_label', details.get('metric'))}為 {_format_number(details.get('value'))}。"
        )
    if evidence_type == "entity_month_table":
        summary = details.get("summary") or {}
        return (
            f"{details.get('month')} 各{details.get('entity_label', 'entity')}"
            f"{details.get('metric_label', details.get('metric'))}資料共 {summary.get('row_count', len(details.get('rows') or []))} 筆；"
            f"最高的是 {summary.get('top_entity', 'N/A')}。"
        )
    if evidence_type == "entity_metric_ranking":
        label = details.get("entity_label") or "事業群"
        metric_label = details.get("metric_label") or details.get("metric") or "指標"
        rows = details.get("rows") or []
        top_rows = [
            f"第 {row.get('rank')} 名 {row.get('entity_value')}（{_format_number(row.get('value'))}）"
            for row in rows[:3]
        ]
        suffix = "；".join(top_rows) if top_rows else "目前沒有可排序資料"
        if any(is_unmapped_entity(row.get("entity_value")) for row in rows):
            suffix += "；未對應資料列已作為資料品質限制處理"
        return f"{label}{metric_label}排名：{suffix}。"
    if evidence_type == "entity_time_series":
        summary = details.get("summary") or {}
        return (
            f"{details.get('entity_value')} 在 {summary.get('latest_month')} 的"
            f"{details.get('metric_label', details.get('metric'))}為 {_format_number(summary.get('latest_value'))}。"
        )
    if evidence_type == "overall_time_series":
        summary = details.get("summary") or {}
        return (
            f"整體在 {summary.get('latest_month')} 的"
            f"{details.get('metric_label', details.get('metric'))}為 {_format_number(summary.get('latest_value'))}。"
        )
    if evidence_type == "entity_trend_comparison":
        summary = details.get("summary") or {}
        return (
            f"{details.get('entity_label', 'entity')}趨勢比較中，"
            f"{summary.get('top_growth_entity')} 的變化較明顯。"
        )
    if evidence_type == "metric_relationship":
        first = (details.get("rows") or [{}])[0]
        return f"{details.get('entity_label', 'entity')}可觀察到 {first.get('relationship_label', 'mixed')} 關係。"
    if evidence_type == "entity_contribution_analysis":
        summary = details.get("summary") or {}
        return f"{details.get('period_b')} 相較 {details.get('period_a')} 的主要貢獻者是 {summary.get('top_contributor')}。"
    if evidence_type == "parent_child_drilldown":
        summary = details.get("summary") or {}
        return f"{summary.get('weakest_entity')} 是目前較需要注意的子層產品線。"
    if evidence_type == "platform_performance_snapshot":
        summary = details.get("summary") or {}
        best = summary.get("best_platform")
        weakest = summary.get("weakest_platform")
        rows = _metric_rows([item])
        best_row = _find_row(rows, best)
        score_text = f"，health_score={_format_number(best_row.get('health_score'))}" if best_row else ""
        return f"新事業群 scorecard 綜合營收規模、營收動能、營收相對庫存效率 proxy 與異常訊號；最佳候選為 {best}{score_text}，需優先注意 {weakest}。"
    if evidence_type == "platform_performance_row":
        platform = _platform(details) or "N/A"
        return (
            f"{platform} 的 health_score 為 {_format_number(details.get('health_score'))}，"
            f"performance_label={details.get('performance_label', 'N/A')}，主要風險為 {details.get('primary_risk', 'N/A')}。"
        )
    if evidence_type in {"platform_ratio", "inventory_turnover_proxy"}:
        platform = _platform(details) or "N/A"
        ratio = details.get("revenue_inventory_amount_ratio")
        level = str(details.get("efficiency_level") or "").lower()
        if "low" in level or _to_float(ratio) is not None and _to_float(ratio) < 1:
            meaning = "代表在目前資料中營收相對庫存效率偏弱"
        else:
            meaning = "可作為營收相對庫存效率的比較依據"
        return f"{platform} 的營收/庫存金額 proxy 為 {_format_number(ratio)}，{meaning}。"
    if evidence_type == "anomaly":
        platform = _platform(details) or "N/A"
        signal = details.get(COL_ANOMALY_SIGNAL)
        signal_part = f"，signal={_format_number(signal)}" if signal is not None else ""
        return f"{platform} 在 {details.get(COL_MONTH, details.get('month', 'N/A'))} 出現 {details.get(COL_ANOMALY_TYPE, '異常')} 訊號{signal_part}，應作為輔助風險判讀。"
    if evidence_type == "contribution_analysis":
        first = (details.get("contributors") or [{}])[0]
        return (
            f"{details.get('month')} 相較 {details.get('previous_month')} 的主要貢獻者是 "
            f"{first.get('name')}，變化 {_format_number(first.get('change'))}。"
        )
    if evidence_type == "yoy_mom_breakdown":
        return (
            f"{details.get('month')} 相較 {details.get('previous_month')} 的"
            f"{_metric_name(details.get('metric'))}變化為 {_format_number(details.get('mom_change'))}。"
        )
    if evidence_type == "root_cause_candidate":
        first = (details.get("candidates") or [{}])[0]
        title = first.get("title") or first.get("description") or first.get("candidate_type")
        return f"候選觀察方向：{title or getattr(item, 'summary', '')}。"
    if evidence_type == "platform_metric_snapshot":
        platform = _platform(details) or "N/A"
        return (
            f"{platform} 在 {details.get(COL_MONTH, details.get('month', 'N/A'))} 的營收為 "
            f"{_format_number(details.get(COL_REVENUE))}，庫存金額為 {_format_number(details.get(COL_INV_AMOUNT))}。"
        )
    if evidence_type in {"period_pair_metric_comparison", "entity_period_pair_comparison"}:
        overall = details.get("overall") or {}
        period_a = details.get("period_a")
        period_b = details.get("period_b")
        direction = overall.get("direction")
        direction_text = "增加" if direction == "up" else ("下降" if direction == "down" else "持平")
        return (
            f"{period_b} 相較 {period_a} {_metric_name(details.get('metric'))}{direction_text} "
            f"{_format_number(abs(overall.get('change') or 0))}。"
        )
    return str(getattr(item, "summary", "")).strip()


def _project_table(primary_items: list[Any]) -> dict[str, Any] | None:
    entity_month_table = _first_evidence(primary_items, "entity_month_table")
    if entity_month_table:
        details = getattr(entity_month_table, "details", {}) or {}
        entity_label = details.get("entity_label") or "entity"
        metric_label = details.get("metric_label") or details.get("metric") or "value"
        return {
            "columns": [entity_label, metric_label, "revenue_amount", "inventory_amount", "inventory_qty", "data_presence_flag"],
            "rows": [
                {
                    entity_label: row.get("entity_value"),
                    metric_label: row.get("value"),
                    "revenue_amount": row.get("revenue_amount"),
                    "inventory_amount": row.get("inventory_amount"),
                    "inventory_qty": row.get("inventory_qty"),
                    "data_presence_flag": row.get("data_presence_flag"),
                }
                for row in (details.get("rows") or [])[:12]
            ],
        }

    period_pair_table = _first_evidence(primary_items, "entity_period_pair_table")
    if period_pair_table:
        details = getattr(period_pair_table, "details", {}) or {}
        entity_label = details.get("entity_label") or "entity"
        metric_label = details.get("metric_label") or details.get("metric") or "value"
        period_a = details.get("period_a") or "period_a"
        period_b = details.get("period_b") or "period_b"
        return {
            "columns": [entity_label, f"{period_a} {metric_label}", f"{period_b} {metric_label}", "change", "change_pct", "data_presence_flag"],
            "rows": [
                {
                    entity_label: row.get("entity_value"),
                    f"{period_a} {metric_label}": row.get("value_a"),
                    f"{period_b} {metric_label}": row.get("value_b"),
                    "change": row.get("change"),
                    "change_pct": row.get("change_pct"),
                    "data_presence_flag": row.get("data_presence_flag"),
                }
                for row in (details.get("rows") or [])[:12]
            ],
        }

    multi_month_table = _first_evidence(primary_items, "entity_multi_month_table")
    if multi_month_table:
        details = getattr(multi_month_table, "details", {}) or {}
        entity_label = details.get("entity_label") or "entity"
        metric_label = details.get("metric_label") or details.get("metric") or "value"
        return {
            "columns": ["month", entity_label, metric_label, "revenue_amount", "inventory_amount", "inventory_qty", "data_presence_flag"],
            "rows": [
                {
                    "month": row.get("month"),
                    entity_label: row.get("entity_value"),
                    metric_label: row.get("value"),
                    "revenue_amount": row.get("revenue_amount"),
                    "inventory_amount": row.get("inventory_amount"),
                    "inventory_qty": row.get("inventory_qty"),
                    "data_presence_flag": row.get("data_presence_flag"),
                }
                for row in (details.get("rows") or [])[:12]
            ],
        }

    period_pair_value = _first_evidence(primary_items, "entity_period_pair_value")
    if period_pair_value:
        details = getattr(period_pair_value, "details", {}) or {}
        metric_label = details.get("metric_label") or details.get("metric") or "value"
        return {
            "columns": ["month", details.get("entity_label", "entity"), metric_label],
            "rows": [
                {"month": row.get("month"), details.get("entity_label", "entity"): details.get("entity_value"), metric_label: row.get("value")}
                for row in (details.get("rows") or [])
            ],
        }

    entity_series = _first_evidence(primary_items, "entity_time_series")
    if entity_series:
        details = getattr(entity_series, "details", {}) or {}
        return {
            "columns": ["month", details.get("metric_label", details.get("metric")), "mom_change", "mom_change_pct"],
            "rows": (details.get("rows") or [])[:12],
        }

    overall_series = _first_evidence(primary_items, "overall_time_series")
    if overall_series:
        details = getattr(overall_series, "details", {}) or {}
        return {
            "columns": ["month", details.get("metric_label", details.get("metric")), "mom_change", "mom_change_pct"],
            "rows": (details.get("rows") or [])[:12],
        }

    trend_comparison = _first_evidence(primary_items, "entity_trend_comparison")
    if trend_comparison:
        details = getattr(trend_comparison, "details", {}) or {}
        return {
            "columns": [details.get("entity_label", "entity"), "latest_month", "latest_value", "overall_change", "overall_change_pct"],
            "rows": (details.get("entity_summaries") or [])[:8],
        }

    relationship = _first_evidence(primary_items, "metric_relationship")
    if relationship:
        details = getattr(relationship, "details", {}) or {}
        return {
            "columns": [details.get("entity_label", "entity"), "month", "previous_month", "relationship_label", "revenue_change", "inventory_change", "ratio_change"],
            "rows": (details.get("rows") or [])[:8],
        }

    contribution = _first_evidence(primary_items, "entity_contribution_analysis")
    if contribution:
        details = getattr(contribution, "details", {}) or {}
        return {
            "columns": [details.get("entity_label", "entity"), "value_a", "value_b", "change", "change_pct", "contribution_pct"],
            "rows": (details.get("rows") or [])[:8],
        }

    drilldown = _first_evidence(primary_items, "parent_child_drilldown")
    if drilldown:
        details = getattr(drilldown, "details", {}) or {}
        entity_label = details.get("entity_label") or "五大產品線"
        return {
            "columns": ["month", entity_label, "revenue", "inventory_amount", "inventory_qty", "revenue_inventory_ratio", "health_score", "risk_score"],
            "rows": [
                {
                    "month": row.get("month"),
                    entity_label: row.get("entity_value"),
                    "revenue": row.get("revenue"),
                    "inventory_amount": row.get("inventory_amount"),
                    "inventory_qty": row.get("inventory_qty"),
                    "revenue_inventory_ratio": row.get("revenue_inventory_amount_ratio"),
                    "health_score": row.get("health_score"),
                    "risk_score": row.get("risk_score"),
                }
                for row in (details.get("rows") or [])[:8]
            ],
        }

    period_pair = _first_evidence(primary_items, "entity_period_pair_comparison") or _first_evidence(primary_items, "period_pair_metric_comparison")
    if period_pair:
        details = getattr(period_pair, "details", {}) or {}
        rows = []
        overall = details.get("overall") or {}
        if overall:
            rows.append({"name": "overall", **overall})
        rows.extend(details.get("breakdown") or [])
        return {
            "columns": ["name", "value_a", "value_b", "change", "change_pct"],
            "rows": rows[:6],
        }

    ranking = _first_evidence(primary_items, "entity_metric_ranking")
    if ranking:
        details = getattr(ranking, "details", {}) or {}
        entity_label = details.get("entity_label") or "事業群"
        metric_label = details.get("metric_label") or details.get("metric") or "value"
        return {
            "columns": ["rank", entity_label, metric_label, "health_score", "data_presence"],
            "rows": [
                {
                    "rank": row.get("rank"),
                    entity_label: row.get("entity_value"),
                    metric_label: row.get("value"),
                    "health_score": row.get("health_score"),
                    "data_presence": row.get("data_presence_flag"),
                }
                for row in (details.get("rows") or [])[:5]
            ],
        }

    rows = _metric_rows(primary_items)
    if not rows:
        return None
    score_columns = ["health_score", "risk_score", "performance_label"]
    has_scorecard = any(any(row.get(column) is not None for column in score_columns) for row in rows)
    entity_label = next((row.get("entity_label") for row in rows if row.get("entity_label")), "事業群")
    columns = ["month", entity_label, "revenue", "inventory_amount", "inventory_qty", "revenue_inventory_ratio"]
    if has_scorecard:
        columns.extend(score_columns)
    return {
        "columns": columns,
        "rows": [
            {
                "month": row.get("month"),
                entity_label: row.get("platform"),
                "revenue": row.get("revenue"),
                "inventory_amount": row.get("inventory_amount"),
                "inventory_qty": row.get("inventory_qty"),
                "revenue_inventory_ratio": row.get("revenue_inventory_ratio"),
                **(
                    {
                        "health_score": row.get("health_score"),
                        "risk_score": row.get("risk_score"),
                        "performance_label": row.get("performance_label"),
                    }
                    if has_scorecard
                    else {}
                ),
            }
            for row in rows[:5]
        ],
    }


def _metric_rows(items: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        evidence_type = getattr(item, "evidence_type", "")
        details = getattr(item, "details", {}) or {}
        if evidence_type == "entity_month_table":
            for row in details.get("rows") or []:
                mapped = _scorecard_metric_row(row, getattr(item, "source_tool", ""))
                if mapped:
                    rows.append(mapped)
            continue
        if evidence_type in {"entity_performance_snapshot", "platform_performance_snapshot"}:
            for row in details.get("rows") or []:
                mapped = _scorecard_metric_row(row, getattr(item, "source_tool", ""))
                if mapped:
                    rows.append(mapped)
            continue
        if evidence_type in {"entity_performance_row", "platform_performance_row"}:
            mapped = _scorecard_metric_row(details, getattr(item, "source_tool", ""))
            if mapped:
                rows.append(mapped)
            continue
        if evidence_type not in {"platform_ratio", "inventory_turnover_proxy", "platform_metric_snapshot", "entity_cross_section", "entity_cross_section_comparison"}:
            continue
        if evidence_type in {"entity_cross_section", "entity_cross_section_comparison"}:
            for row in details.get("rows") or []:
                mapped = _scorecard_metric_row(row, getattr(item, "source_tool", ""))
                if mapped:
                    rows.append(mapped)
            continue
        platform = _platform(details)
        if not platform:
            continue
        rows.append(
            {
                "month": details.get("month") or details.get(COL_MONTH),
                "platform": platform,
                "group_code": details.get("group_code") or details.get(COL_GROUP_CODE),
                "revenue": _to_float(
                    details.get("revenue_amount")
                    if details.get("revenue_amount") is not None
                    else (details.get("revenue") if details.get("revenue") is not None else details.get(COL_REVENUE))
                ),
                "inventory_amount": _to_float(
                    details.get("inventory_amount") if details.get("inventory_amount") is not None else details.get(COL_INV_AMOUNT)
                ),
                "inventory_qty": _to_float(details.get("inventory_qty") if details.get("inventory_qty") is not None else details.get(COL_INV_QTY)),
                "revenue_inventory_ratio": _to_float(details.get("revenue_inventory_amount_ratio")),
                "source_tool": getattr(item, "source_tool", ""),
            }
        )
    return rows


def _scorecard_metric_row(details: dict[str, Any], source_tool: str) -> dict[str, Any] | None:
    platform = details.get("entity_value") or _platform(details)
    if not platform:
        return None
    return {
        "month": details.get("month") or details.get(COL_MONTH),
        "platform": platform,
        "entity_label": details.get("entity_label"),
        "entity_dimension": details.get("entity_dimension"),
        "group_code": details.get("group_code") or details.get(COL_GROUP_CODE),
        "revenue": _to_float(
            details.get("revenue_amount")
            if details.get("revenue_amount") is not None
            else (details.get("revenue") if details.get("revenue") is not None else details.get(COL_REVENUE))
        ),
        "inventory_amount": _to_float(details.get("inventory_amount") if details.get("inventory_amount") is not None else details.get(COL_INV_AMOUNT)),
        "inventory_qty": _to_float(details.get("inventory_qty") if details.get("inventory_qty") is not None else details.get(COL_INV_QTY)),
        "revenue_inventory_ratio": _to_float(details.get("revenue_inventory_amount_ratio")),
        "health_score": _to_float(details.get("health_score")),
        "risk_score": _to_float(details.get("risk_score")),
        "performance_label": details.get("performance_label"),
        "primary_strength": details.get("primary_strength"),
        "primary_risk": details.get("primary_risk"),
        "anomaly_count": details.get("anomaly_count"),
        "source_tool": source_tool,
    }


def _observation_key(item: Any, text: str) -> str:
    details = getattr(item, "details", {}) or {}
    evidence_type = str(getattr(item, "evidence_type", ""))
    if evidence_type == "platform_performance_snapshot":
        summary = details.get("summary") or {}
        return f"platform_performance_snapshot|{details.get('month')}|{summary.get('best_platform')}|{summary.get('weakest_platform')}"
    if evidence_type == "platform_performance_row":
        return f"platform_performance_row|{details.get('month') or details.get(COL_MONTH) or ''}|{_platform(details) or ''}"
    if evidence_type in {"platform_ratio", "inventory_turnover_proxy"}:
        return "|".join(
            [
                "revenue_inventory_proxy",
                str(details.get("month") or details.get(COL_MONTH) or ""),
                str(_platform(details) or ""),
                str(details.get("revenue_inventory_amount_ratio") or ""),
            ]
        )
    return "|".join(
        [
            evidence_type,
            str(details.get("month") or details.get(COL_MONTH) or ""),
            str(_platform(details) or ""),
            str(details.get("revenue_inventory_amount_ratio") or ""),
            text,
        ]
    )


def _first_evidence(items: list[Any], evidence_type: str) -> Any | None:
    for item in items:
        if getattr(item, "evidence_type", None) == evidence_type:
            return item
    return None


def _top_anomaly(items: list[Any]) -> Any | None:
    anomalies = [item for item in items if getattr(item, "evidence_type", None) == "anomaly"]
    if not anomalies:
        return None
    return sorted(
        anomalies,
        key=lambda item: abs(_to_float((getattr(item, "details", {}) or {}).get(COL_ANOMALY_SIGNAL)) or 0.0),
        reverse=True,
    )[0]


def _max_row(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [row for row in rows if row.get(key) is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda row: float(row[key]))


def _max_mapped_row(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [row for row in rows if row.get(key) is not None and not is_unmapped_entity(row.get("platform"))]
    if not candidates:
        return None
    return max(candidates, key=lambda row: float(row[key]))


def _min_row(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [row for row in rows if row.get(key) is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda row: float(row[key]))


def _first_value(rows: list[dict[str, Any]], key: str) -> Any:
    for row in rows:
        value = row.get(key)
        if value is not None:
            return value
    return None


def _find_row(rows: list[dict[str, Any]], platform: Any) -> dict[str, Any] | None:
    if platform is None:
        return None
    for row in rows:
        if str(row.get("platform")) == str(platform):
            return row
    return None


def _first_mapped_entity(rows: list[dict[str, Any]], key: str, *, reverse: bool) -> str | None:
    candidates = [
        row for row in rows
        if row.get(key) is not None and not is_unmapped_entity(row.get("platform"))
    ]
    if not candidates:
        return None
    return str(sorted(candidates, key=lambda row: float(row[key]), reverse=reverse)[0].get("platform"))


def _has_unmapped_entity(items: list[Any]) -> bool:
    for item in items:
        details = getattr(item, "details", {}) or {}
        rows = details.get("rows") if isinstance(details, dict) else None
        if rows and any(is_unmapped_entity(row.get("entity_value") or row.get("platform")) for row in rows):
            return True
        if isinstance(details, dict) and "entity_value" in details and is_unmapped_entity(details.get("entity_value")):
            return True
    return False


def _profile_month(task_profile: Any | None) -> str | None:
    time_scope = getattr(task_profile, "time_scope", {}) or {}
    return time_scope.get("month") or time_scope.get("current_month")


def _platform(details: dict[str, Any]) -> str | None:
    value = details.get("platform") or details.get(COL_PLATFORM)
    return str(value) if value is not None else None


def _metric_name(metric: Any) -> str:
    return {
        "revenue": "營收",
        "revenue_amount": "營收",
        "inventory_amount": "庫存金額",
        "inventory_qty": "庫存數量",
        "revenue_inventory_amount_ratio": "營收相對庫存效率",
    }.get(str(metric), "指標")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_number(value: Any, *, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    return format_number(value, decimals=decimals)
