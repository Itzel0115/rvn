from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import (
    ANOMALY_MOM_THRESHOLD,
    CORRELATION_MIN_OBSERVATIONS,
    HIGH_INVENTORY_REVENUE_RATIO_THRESHOLD,
    HIGH_REVENUE_INVENTORY_QTY_RATIO_THRESHOLD,
)

# Minimum consecutive months to trigger divergence anomaly
DIVERGENCE_CONSECUTIVE_MONTHS = 2
from mapping_parser import ParsedMapping
from utils import MessageCollector, dataframe_to_records


@dataclass
class AnalysisArtifacts:
    inventory_enriched: pd.DataFrame
    revenue_enriched: pd.DataFrame
    monthly_revenue: pd.DataFrame
    monthly_inventory_amount: pd.DataFrame
    monthly_inventory_qty: pd.DataFrame
    revenue_by_group: pd.DataFrame
    inventory_by_group: pd.DataFrame
    merged_analysis: pd.DataFrame
    platform_monthly_analysis: pd.DataFrame
    anomalies: pd.DataFrame
    correlation_analysis: pd.DataFrame
    summary_metrics: dict[str, pd.DataFrame]
    report_context: dict


def analyze_data(
    inventory_df: pd.DataFrame,
    revenue_df: pd.DataFrame,
    parsed_mapping: ParsedMapping,
) -> tuple[AnalysisArtifacts, MessageCollector]:
    collector = MessageCollector()

    inventory_enriched = enrich_inventory(inventory_df, parsed_mapping, collector)
    revenue_enriched = enrich_revenue(revenue_df, parsed_mapping, collector)

    monthly_revenue = aggregate_monthly(revenue_enriched, "營收", "monthly_revenue")
    monthly_inventory_amount = aggregate_monthly(inventory_enriched, "金額", "monthly_inventory_amount")
    monthly_inventory_qty = aggregate_monthly(inventory_enriched, "QTY", "monthly_inventory_qty")
    revenue_by_group = aggregate_by_group(revenue_enriched, "營收", "revenue_by_group")
    inventory_by_group = aggregate_by_group(inventory_enriched, "金額", "inventory_by_group")

    merged_analysis, platform_monthly_analysis = build_merged_analysis(
        inventory_enriched,
        revenue_enriched,
        collector,
    )

    anomalies = detect_anomalies(
        monthly_revenue,
        monthly_inventory_amount,
        platform_monthly_analysis,
        collector,
    )
    correlation_analysis = analyze_correlations(
        monthly_revenue,
        monthly_inventory_amount,
        monthly_inventory_qty,
        revenue_by_group,
        inventory_by_group,
        platform_monthly_analysis,
        collector,
    )

    summary_metrics = {
        "monthly_revenue": monthly_revenue,
        "monthly_inventory_amount": monthly_inventory_amount,
        "monthly_inventory_qty": monthly_inventory_qty,
        "revenue_by_group": revenue_by_group,
        "inventory_by_group": inventory_by_group,
        "anomalies": anomalies,
        "correlation_analysis": correlation_analysis,
        "mapping_bridge_candidates": parsed_mapping.bridge_candidates,
    }

    report_context = {
        "inventory_rows": len(inventory_enriched),
        "revenue_rows": len(revenue_enriched),
        "mapping_rows": len(parsed_mapping.structured_mapping),
        "business_group_count": parsed_mapping.business_group_mapping["事業群代碼"].nunique()
        if not parsed_mapping.business_group_mapping.empty
        else 0,
        "inventory_hqbu_count": parsed_mapping.inventory_hqbu_mapping["庫存HQBU代碼"].nunique()
        if not parsed_mapping.inventory_hqbu_mapping.empty
        else 0,
        "revenue_platform_count": parsed_mapping.revenue_platform_mapping["營收平台代碼"].nunique()
        if not parsed_mapping.revenue_platform_mapping.empty
        else 0,
        "mapping_success": parsed_mapping.mapping_success,
        "bridge_candidate_count": len(parsed_mapping.bridge_candidates),
        "monthly_revenue_records": dataframe_to_records(monthly_revenue),
        "monthly_inventory_amount_records": dataframe_to_records(monthly_inventory_amount),
        "monthly_inventory_qty_records": dataframe_to_records(monthly_inventory_qty),
        "revenue_by_group_records": dataframe_to_records(revenue_by_group),
        "inventory_by_group_records": dataframe_to_records(inventory_by_group),
        "anomaly_records": dataframe_to_records(anomalies, limit=20),
        "correlation_records": dataframe_to_records(correlation_analysis, limit=20),
        "platform_analysis_records": dataframe_to_records(platform_monthly_analysis, limit=20),
        "merged_analysis_available": not merged_analysis.empty,
    }

    artifacts = AnalysisArtifacts(
        inventory_enriched=inventory_enriched,
        revenue_enriched=revenue_enriched,
        monthly_revenue=monthly_revenue,
        monthly_inventory_amount=monthly_inventory_amount,
        monthly_inventory_qty=monthly_inventory_qty,
        revenue_by_group=revenue_by_group,
        inventory_by_group=inventory_by_group,
        merged_analysis=merged_analysis,
        platform_monthly_analysis=platform_monthly_analysis,
        anomalies=anomalies,
        correlation_analysis=correlation_analysis,
        summary_metrics=summary_metrics,
        report_context=report_context,
    )
    return artifacts, collector


def enrich_inventory(
    inventory_df: pd.DataFrame,
    parsed_mapping: ParsedMapping,
    collector: MessageCollector,
) -> pd.DataFrame:
    df = inventory_df.copy()
    df["新事業群"] = pd.to_numeric(df["新事業群"], errors="coerce").astype("Int64")

    df = df.merge(
        parsed_mapping.business_group_mapping.rename(columns={"事業群代碼": "新事業群"}),
        on="新事業群",
        how="left",
    )
    df = df.merge(
        parsed_mapping.inventory_hqbu_mapping.rename(
            columns={"事業群代碼": "新事業群", "庫存HQBU代碼": "HQBU"}
        ),
        on=["新事業群", "HQBU"],
        how="left",
    )

    bridge = parsed_mapping.bridge_candidates.rename(
        columns={"事業群代碼": "新事業群", "HQBU代碼": "HQBU", "平台代碼": "平台"}
    )
    if bridge.empty:
        df["平台"] = pd.NA
        df["對應型態"] = pd.NA
        df["對應可信度"] = pd.NA
    else:
        # Prefer direct_code_match (HQBU code == Platform code) — always 1:1 and reliable.
        # Fall back to single-candidate bridges only when no direct match exists.
        direct = bridge.loc[
            bridge["對應型態"] == "direct_code_match",
            ["新事業群", "HQBU", "平台", "對應型態", "對應可信度"],
        ].drop_duplicates(subset=["新事業群", "HQBU"])

        if not direct.empty:
            resolved = direct
        else:
            bridge_count = bridge.groupby(["新事業群", "HQBU"]).size().reset_index(name="候選平台數")
            single_bridge = bridge_count.loc[bridge_count["候選平台數"] == 1, ["新事業群", "HQBU"]]
            resolved = bridge.merge(single_bridge, on=["新事業群", "HQBU"], how="inner")
            resolved = resolved[["新事業群", "HQBU", "平台", "對應型態", "對應可信度"]].drop_duplicates()
        df = df.merge(resolved, on=["新事業群", "HQBU"], how="left")
        if df["平台"].isna().all():
            collector.add_warning("庫存資料雖有 bridge 候選，但沒有可直接套用的單一平台對應。")

    unmatched = df["庫存HQBU分類名稱"].isna() & df["HQBU"].notna()
    if unmatched.any():
        collector.add_warning(f"庫存資料有 {unmatched.sum()} 筆 HQBU 無法在 mapping 對到分類名稱。")

    return df


def enrich_revenue(
    revenue_df: pd.DataFrame,
    parsed_mapping: ParsedMapping,
    collector: MessageCollector,
) -> pd.DataFrame:
    df = revenue_df.copy()
    df["新事業群"] = pd.to_numeric(df["新事業群"], errors="coerce").astype("Int64")

    df = df.merge(
        parsed_mapping.business_group_mapping.rename(columns={"事業群代碼": "新事業群"}),
        on="新事業群",
        how="left",
    )
    df = df.merge(
        parsed_mapping.revenue_platform_mapping.rename(
            columns={"事業群代碼": "新事業群", "營收平台代碼": "平台"}
        ),
        on=["新事業群", "平台"],
        how="left",
    )

    unmatched = df["營收平台分類名稱"].isna() & df["平台"].notna()
    if unmatched.any():
        collector.add_warning(f"營收資料有 {unmatched.sum()} 筆平台代碼無法在 mapping 對到分類名稱。")

    return df


def aggregate_monthly(df: pd.DataFrame, value_column: str, metric_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["月份", value_column, "月增率", "指標"])

    result = (
        df.dropna(subset=["月份"])
        .groupby("月份", as_index=False)[value_column]
        .sum(min_count=1)
        .sort_values("月份")
        .reset_index(drop=True)
    )
    result["月增率"] = result[value_column].pct_change().replace([np.inf, -np.inf], np.nan)
    result["指標"] = metric_name
    return result


def aggregate_by_group(df: pd.DataFrame, value_column: str, metric_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["新事業群", "事業群名稱", value_column, "占比", "指標"])

    result = (
        df.groupby(["新事業群", "事業群名稱"], dropna=False, as_index=False)[value_column]
        .sum(min_count=1)
        .sort_values(value_column, ascending=False)
        .reset_index(drop=True)
    )
    total = result[value_column].sum()
    result["占比"] = result[value_column] / total if total else np.nan
    result["指標"] = metric_name
    return result


def build_merged_analysis(
    inventory_df: pd.DataFrame,
    revenue_df: pd.DataFrame,
    collector: MessageCollector,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    revenue_base = (
        revenue_df.dropna(subset=["月份", "平台"])
        .groupby(["月份", "新事業群", "平台"], as_index=False)["營收"]
        .sum(min_count=1)
    )

    inventory_with_platform = inventory_df.dropna(subset=["月份", "平台"])
    if inventory_with_platform.empty:
        collector.add_warning("庫存資料無法可靠映射到平台，將不產生完整平台整合主表。")
        return pd.DataFrame(), pd.DataFrame()

    inventory_base = (
        inventory_with_platform.groupby(["月份", "新事業群", "平台"], as_index=False)[["金額", "QTY"]]
        .sum(min_count=1)
    )

    merged = inventory_base.merge(revenue_base, on=["月份", "新事業群", "平台"], how="outer")
    merged["營收_庫存金額比值"] = merged["營收"] / merged["金額"]
    merged["營收_庫存QTY比值"] = merged["營收"] / merged["QTY"]
    merged = merged.sort_values(["月份", "新事業群", "平台"]).reset_index(drop=True)
    return merged, merged.copy()


def detect_anomalies(
    monthly_revenue: pd.DataFrame,
    monthly_inventory_amount: pd.DataFrame,
    platform_monthly_analysis: pd.DataFrame,
    collector: MessageCollector,
) -> pd.DataFrame:
    findings: list[dict] = []

    for _, row in monthly_revenue.dropna(subset=["月增率"]).iterrows():
        if abs(row["月增率"]) >= ANOMALY_MOM_THRESHOLD:
            findings.append(
                {
                    "異常類型": "營收月增率異常",
                    "月份": row["月份"],
                    "新事業群": None,
                    "平台": None,
                    "訊號": row["月增率"],
                    "說明": f"月增率 {row['月增率']:.2%} 超過門檻 {ANOMALY_MOM_THRESHOLD:.0%}",
                }
            )

    for _, row in monthly_inventory_amount.dropna(subset=["月增率"]).iterrows():
        if abs(row["月增率"]) >= ANOMALY_MOM_THRESHOLD:
            findings.append(
                {
                    "異常類型": "庫存金額月增率異常",
                    "月份": row["月份"],
                    "新事業群": None,
                    "平台": None,
                    "訊號": row["月增率"],
                    "說明": f"月增率 {row['月增率']:.2%} 超過門檻 {ANOMALY_MOM_THRESHOLD:.0%}",
                }
            )

    if platform_monthly_analysis.empty:
        collector.add_warning("因平台整合不足，跨表異常只執行月趨勢層級檢查。")
        return pd.DataFrame(findings)

    detailed = platform_monthly_analysis.sort_values(["新事業群", "平台", "月份"]).copy()
    detailed["營收月增率"] = detailed.groupby(["新事業群", "平台"])["營收"].pct_change()
    detailed["庫存金額月增率"] = detailed.groupby(["新事業群", "平台"])["金額"].pct_change()

    for _, row in detailed.iterrows():
        revenue_mom = row.get("營收月增率")
        inventory_mom = row.get("庫存金額月增率")

        if pd.notna(inventory_mom) and pd.notna(revenue_mom):
            if inventory_mom >= ANOMALY_MOM_THRESHOLD and revenue_mom <= 0:
                findings.append(
                    {
                        "異常類型": "庫存升但營收未同步升",
                        "月份": row["月份"],
                        "新事業群": row["新事業群"],
                        "平台": row["平台"],
                        "訊號": inventory_mom - revenue_mom,
                        "說明": f"庫存金額月增率 {inventory_mom:.2%}，營收月增率 {revenue_mom:.2%}",
                    }
                )

            if revenue_mom <= -ANOMALY_MOM_THRESHOLD and pd.notna(row.get("金額")) and row["金額"] > 0:
                findings.append(
                    {
                        "異常類型": "營收降但庫存仍高",
                        "月份": row["月份"],
                        "新事業群": row["新事業群"],
                        "平台": row["平台"],
                        "訊號": revenue_mom,
                        "說明": f"營收月增率 {revenue_mom:.2%}，當月庫存金額 {row['金額']:.2f}",
                    }
                )

        amount_ratio = row.get("營收_庫存金額比值")
        qty_ratio = row.get("營收_庫存QTY比值")

        if pd.notna(amount_ratio) and amount_ratio <= HIGH_INVENTORY_REVENUE_RATIO_THRESHOLD:
            findings.append(
                {
                    "異常類型": "營收/庫存金額比偏低",
                    "月份": row["月份"],
                    "新事業群": row["新事業群"],
                    "平台": row["平台"],
                    "訊號": amount_ratio,
                    "說明": f"營收/庫存金額比 {amount_ratio:.2f} 低於 {HIGH_INVENTORY_REVENUE_RATIO_THRESHOLD:.2f}",
                }
            )

        if pd.notna(qty_ratio) and qty_ratio <= HIGH_REVENUE_INVENTORY_QTY_RATIO_THRESHOLD:
            findings.append(
                {
                    "異常類型": "營收/庫存QTY比偏低",
                    "月份": row["月份"],
                    "新事業群": row["新事業群"],
                    "平台": row["平台"],
                    "訊號": qty_ratio,
                    "說明": f"營收/庫存QTY比 {qty_ratio:.2f} 低於 {HIGH_REVENUE_INVENTORY_QTY_RATIO_THRESHOLD:.2f}",
                }
            )

    # Detect persistent divergence: inventory rising while revenue falling
    # (catches slow-burn patterns that don't hit single-month MoM thresholds)
    if not platform_monthly_analysis.empty:
        for (group, platform), grp in platform_monthly_analysis.sort_values("月份").groupby(["新事業群", "平台"]):
            grp = grp.copy()
            grp["營收月增率"] = grp["營收"].pct_change()
            grp["庫存金額月增率"] = grp["金額"].pct_change()
            diverge = grp["庫存金額月增率"] > 0
            decline = grp["營收月增率"] < 0
            consecutive = 0
            for i in range(len(grp)):
                if diverge.iloc[i] and decline.iloc[i]:
                    consecutive += 1
                    if consecutive >= DIVERGENCE_CONSECUTIVE_MONTHS:
                        row = grp.iloc[i]
                        findings.append({
                            "異常類型": "庫存持續升但營收持續降",
                            "月份": row["月份"],
                            "新事業群": group,
                            "平台": platform,
                            "訊號": round(consecutive, 0),
                            "說明": f"連續 {consecutive} 個月庫存金額上升、營收下降（平台 {platform}）",
                        })
                        break
                else:
                    consecutive = 0

    return pd.DataFrame(findings)


def analyze_correlations(
    monthly_revenue: pd.DataFrame,
    monthly_inventory_amount: pd.DataFrame,
    monthly_inventory_qty: pd.DataFrame,
    revenue_by_group: pd.DataFrame,
    inventory_by_group: pd.DataFrame,
    platform_monthly_analysis: pd.DataFrame,
    collector: MessageCollector,
) -> pd.DataFrame:
    records: list[dict] = []

    monthly = monthly_revenue.merge(
        monthly_inventory_amount[["月份", "金額"]],
        on="月份",
        how="inner",
    ).merge(
        monthly_inventory_qty[["月份", "QTY"]],
        on="月份",
        how="inner",
    )

    records.extend(
        [
            _correlation_record(monthly, "營收", "金額", "monthly", "overall", "月營收對月庫存金額"),
            _correlation_record(monthly, "營收", "QTY", "monthly", "overall", "月營收對月庫存QTY"),
        ]
    )

    group = revenue_by_group.merge(
        inventory_by_group[["新事業群", "金額"]],
        on="新事業群",
        how="inner",
    )
    records.append(_correlation_record(group, "營收", "金額", "group", "overall", "各新事業群營收對庫存金額"))

    if not platform_monthly_analysis.empty:
        records.extend(
            [
                _correlation_record(
                    platform_monthly_analysis,
                    "營收",
                    "金額",
                    "platform_monthly",
                    "overall",
                    "平台月營收對庫存金額",
                ),
                _correlation_record(
                    platform_monthly_analysis,
                    "營收",
                    "QTY",
                    "platform_monthly",
                    "overall",
                    "平台月營收對庫存QTY",
                ),
            ]
        )
        for platform, subset in platform_monthly_analysis.groupby("平台"):
            records.append(
                _correlation_record(
                    subset,
                    "營收",
                    "金額",
                    "platform_monthly",
                    str(platform),
                    f"平台 {platform} 營收對庫存金額",
                )
            )

    result = pd.DataFrame([record for record in records if record is not None])
    if result.empty:
        collector.add_warning("可用於關聯性分析的資料點不足。")
    return result


def _correlation_record(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    scope: str,
    entity: str,
    label: str,
) -> dict | None:
    subset = df[[x_col, y_col]].dropna()
    if len(subset) < CORRELATION_MIN_OBSERVATIONS:
        return {
            "分析層級": scope,
            "分析對象": entity,
            "指標組合": label,
            "樣本數": len(subset),
            "相關係數": np.nan,
            "關聯判讀": "資料點不足",
        }

    corr = subset[x_col].corr(subset[y_col])
    return {
        "分析層級": scope,
        "分析對象": entity,
        "指標組合": label,
        "樣本數": len(subset),
        "相關係數": corr,
        "關聯判讀": describe_correlation(corr),
    }


def describe_correlation(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "無法判讀"
    absolute = abs(value)
    if absolute >= 0.8:
        strength = "高度"
    elif absolute >= 0.5:
        strength = "中度"
    elif absolute >= 0.3:
        strength = "低度"
    else:
        strength = "弱"
    direction = "正相關" if value >= 0 else "負相關"
    return f"{strength}{direction}"
