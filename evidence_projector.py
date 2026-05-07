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
    max_items = int(getattr(answer_plan, "max_key_observations", 3) or 3)
    evidence_items = list(getattr(rubric_result, "evidence", []))
    primary = [item for item in evidence_items if getattr(item, "role", None) == "primary"]
    supporting = [item for item in evidence_items if getattr(item, "role", None) == "supporting"]

    headline = _build_headline(task_profile, primary, supporting)
    observations = _project_observations([*primary, *supporting], max_items)
    table = None
    if bool(getattr(task_profile, "requires_table", False)) or bool(getattr(answer_plan, "requires_table", False)):
        table = _project_table(primary)

    return DisplayBlocks(
        headline=headline,
        key_observations=[item.text for item in observations],
        table=table,
        limitations=list(dict.fromkeys(limitations))[:3],
    ).to_dict()


def _build_headline(task_profile: Any | None, primary: list[Any], supporting: list[Any]) -> str:
    if not primary:
        return "目前沒有足夠證據形成明確結論。"

    task_family = getattr(task_profile, "task_family", None)
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
    return _fallback_headline(primary[0])


def _cross_section_headline(task_profile: Any | None, primary: list[Any]) -> str:
    rows = _metric_rows(primary)
    month = _profile_month(task_profile) or _first_value(rows, "month") or "目前期間"
    if not rows:
        return "目前沒有足夠證據形成完整橫向比較。"

    top_revenue = _max_row(rows, "revenue")
    top_inventory = _max_row(rows, "inventory_amount")
    weakest_ratio = _min_row(rows, "revenue_inventory_ratio")
    if not (top_revenue and top_inventory and weakest_ratio):
        return "目前沒有足夠證據形成完整橫向比較。"

    return (
        f"結論：{month} 各平台比較下，{top_revenue['platform']} 營收規模較高，"
        f"{top_inventory['platform']} 庫存水位較高；但 {weakest_ratio['platform']} "
        "的營收相對庫存效率較弱，需搭配庫存壓力判讀。"
    )


def _performance_headline(task_profile: Any | None, primary: list[Any], supporting: list[Any]) -> str:
    polarity = getattr(task_profile, "polarity", None)
    snapshot = _first_evidence(primary, "platform_performance_snapshot")
    if snapshot:
        details = getattr(snapshot, "details", {}) or {}
        summary = details.get("summary") or {}
        rows = _metric_rows([snapshot])
        if polarity in {"best", "strong"}:
            best_platform = summary.get("best_platform")
            best_row = _find_row(rows, best_platform)
            if best_row:
                return (
                    f"結論：目前綜合表現較佳的平台是 {best_platform}，因為其 "
                    f"{best_row.get('primary_strength') or 'health_score 較高'}，"
                    f"health_score 為 {_format_number(best_row.get('health_score'))}。"
                )
        if polarity in {"worst", "weak"}:
            weakest_platform = summary.get("weakest_platform")
            weakest_row = _find_row(rows, weakest_platform)
            if weakest_row:
                return (
                    f"結論：目前表現較弱的平台優先看 {weakest_platform}，因為其 "
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
                f"結論：目前較佳的平台候選是 {strongest['platform']}，因為其營收相對庫存效率 proxy "
                "較高，且在目前 primary/supporting evidence 中未見直接異常訊號。"
            )
        if weakest:
            return (
                "結論：目前資料較適合辨識弱勢平台，尚不足以明確判定最佳平台；"
                f"可先排除 {weakest['platform']} 等效率偏弱平台。"
            )
        return "目前沒有足夠證據形成明確結論。"

    anomaly = _top_anomaly(supporting)
    if weakest:
        suffix = ""
        if anomaly and _platform(getattr(anomaly, "details", {}) or {}) == weakest.get("platform"):
            suffix = "，且同平台也有異常訊號需要追蹤"
        return (
            f"結論：目前表現較弱的平台優先看 {weakest['platform']}，因為其營收相對庫存效率 proxy "
            f"偏弱{suffix}。"
        )
    if anomaly:
        details = getattr(anomaly, "details", {}) or {}
        return f"結論：目前表現較弱的平台優先看 {_platform(details) or 'N/A'}，因為其異常訊號較明顯。"
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
    if evidence_type == "platform_performance_snapshot":
        summary = details.get("summary") or {}
        best = summary.get("best_platform")
        weakest = summary.get("weakest_platform")
        rows = _metric_rows([item])
        best_row = _find_row(rows, best)
        score_text = f"，health_score={_format_number(best_row.get('health_score'))}" if best_row else ""
        return f"平台 scorecard 綜合營收規模、營收動能、營收相對庫存效率 proxy 與異常訊號；最佳候選為 {best}{score_text}，需優先注意 {weakest}。"
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
    return str(getattr(item, "summary", "")).strip()


def _project_table(primary_items: list[Any]) -> dict[str, Any] | None:
    rows = _metric_rows(primary_items)
    if not rows:
        return None
    score_columns = ["health_score", "risk_score", "performance_label"]
    has_scorecard = any(any(row.get(column) is not None for column in score_columns) for row in rows)
    columns = ["month", "platform", "revenue", "inventory_amount", "inventory_qty", "revenue_inventory_ratio"]
    if has_scorecard:
        columns.extend(score_columns)
    return {
        "columns": columns,
        "rows": [
            {
                "month": row.get("month"),
                "platform": row.get("platform"),
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
        if evidence_type == "platform_performance_snapshot":
            for row in details.get("rows") or []:
                mapped = _scorecard_metric_row(row, getattr(item, "source_tool", ""))
                if mapped:
                    rows.append(mapped)
            continue
        if evidence_type == "platform_performance_row":
            mapped = _scorecard_metric_row(details, getattr(item, "source_tool", ""))
            if mapped:
                rows.append(mapped)
            continue
        if evidence_type not in {"platform_ratio", "inventory_turnover_proxy", "platform_metric_snapshot"}:
            continue
        platform = _platform(details)
        if not platform:
            continue
        rows.append(
            {
                "month": details.get("month") or details.get(COL_MONTH),
                "platform": platform,
                "group_code": details.get("group_code") or details.get(COL_GROUP_CODE),
                "revenue": _to_float(details.get("revenue") if details.get("revenue") is not None else details.get(COL_REVENUE)),
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
    platform = _platform(details)
    if not platform:
        return None
    return {
        "month": details.get("month") or details.get(COL_MONTH),
        "platform": platform,
        "group_code": details.get("group_code") or details.get(COL_GROUP_CODE),
        "revenue": _to_float(details.get("revenue") if details.get("revenue") is not None else details.get(COL_REVENUE)),
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


def _profile_month(task_profile: Any | None) -> str | None:
    time_scope = getattr(task_profile, "time_scope", {}) or {}
    return time_scope.get("month") or time_scope.get("current_month")


def _platform(details: dict[str, Any]) -> str | None:
    value = details.get("platform") or details.get(COL_PLATFORM)
    return str(value) if value is not None else None


def _metric_name(metric: Any) -> str:
    return {
        "revenue": "營收",
        "inventory_amount": "庫存金額",
        "inventory_qty": "庫存數量",
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
