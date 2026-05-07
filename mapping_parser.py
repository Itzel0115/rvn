from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from config import BU_CODE_PATTERN, MAPPING_POSITION_COLUMNS
from utils import MessageCollector, normalize_code


@dataclass
class ParsedMapping:
    raw_mapping: pd.DataFrame
    structured_mapping: pd.DataFrame
    business_group_mapping: pd.DataFrame
    inventory_hqbu_mapping: pd.DataFrame
    revenue_platform_mapping: pd.DataFrame
    anonymization_rules: pd.DataFrame
    bridge_candidates: pd.DataFrame
    mapping_success: bool
    warnings: list[str]


def parse_mapping(df: pd.DataFrame) -> tuple[ParsedMapping, MessageCollector]:
    collector = MessageCollector()
    if df.empty:
        collector.add_error("mapping.xlsx 無法讀取或內容為空。")
        empty = pd.DataFrame()
        return (
            ParsedMapping(empty, empty, empty, empty, empty, empty, empty, False, collector.warnings),
            collector,
        )

    if df.shape[1] < 9:
        collector.add_error(f"mapping.xlsx 欄位不足，至少需要 9 欄，實際僅有 {df.shape[1]} 欄。")
        empty = pd.DataFrame()
        return (
            ParsedMapping(df, empty, empty, empty, empty, empty, empty, False, collector.warnings),
            collector,
        )

    structured = df.iloc[:, :9].copy()
    structured.columns = [MAPPING_POSITION_COLUMNS[key] for key in MAPPING_POSITION_COLUMNS]
    structured = structured.dropna(how="all").reset_index(drop=True)

    for code_column in ["庫存HQBU代碼", "營收平台代碼"]:
        structured[code_column] = structured[code_column].apply(normalize_code)
    structured["事業群代碼"] = pd.to_numeric(structured["事業群代碼"], errors="coerce").astype("Int64")

    _validate_bu_codes(structured["庫存HQBU代碼"], "庫存HQBU代碼", collector)
    _validate_bu_codes(structured["營收平台代碼"], "營收平台代碼", collector)

    business_group_mapping = (
        structured[["事業群名稱", "事業群代碼"]]
        .dropna(subset=["事業群代碼"])
        .drop_duplicates()
        .sort_values(by=["事業群代碼", "事業群名稱"])
        .reset_index(drop=True)
    )
    inventory_hqbu_mapping = (
        structured[["事業群代碼", "庫存HQBU分類名稱", "庫存HQBU代碼"]]
        .dropna(subset=["庫存HQBU代碼"])
        .drop_duplicates()
        .sort_values(by=["庫存HQBU代碼", "事業群代碼"])
        .reset_index(drop=True)
    )
    revenue_platform_mapping = (
        structured[["事業群代碼", "營收平台分類名稱", "營收平台代碼"]]
        .dropna(subset=["營收平台代碼"])
        .drop_duplicates()
        .sort_values(by=["營收平台代碼", "事業群代碼"])
        .reset_index(drop=True)
    )
    anonymization_rules = structured[
        [
            "事業群代碼",
            "事業群名稱",
            "庫存HQBU代碼",
            "金額處理方式",
            "QTY處理方式",
            "營收平台代碼",
            "實際營收處理方式",
        ]
    ].copy()

    bridge_candidates = build_code_bridge(inventory_hqbu_mapping, revenue_platform_mapping, collector)
    mapping_success = not bridge_candidates.empty
    if mapping_success:
        collector.add_info("成功建立部分 HQBU -> 平台候選對應。")
    else:
        collector.add_warning("無法從 mapping 穩定建立 HQBU -> 平台候選對應，跨表整合將受限。")

    parsed = ParsedMapping(
        raw_mapping=df,
        structured_mapping=structured,
        business_group_mapping=business_group_mapping,
        inventory_hqbu_mapping=inventory_hqbu_mapping,
        revenue_platform_mapping=revenue_platform_mapping,
        anonymization_rules=anonymization_rules,
        bridge_candidates=bridge_candidates,
        mapping_success=mapping_success,
        warnings=collector.warnings.copy(),
    )
    return parsed, collector


def build_code_bridge(
    inventory_hqbu_mapping: pd.DataFrame,
    revenue_platform_mapping: pd.DataFrame,
    collector: MessageCollector,
) -> pd.DataFrame:
    if inventory_hqbu_mapping.empty or revenue_platform_mapping.empty:
        return pd.DataFrame(columns=["事業群代碼", "HQBU代碼", "平台代碼", "對應型態", "對應可信度"])

    merged = inventory_hqbu_mapping.merge(
        revenue_platform_mapping,
        on="事業群代碼",
        how="inner",
        suffixes=("_庫存", "_營收"),
    )
    if merged.empty:
        collector.add_warning("mapping 中找不到共用的新事業群代碼來串接 HQBU 與平台。")
        return pd.DataFrame(columns=["事業群代碼", "HQBU代碼", "平台代碼", "對應型態", "對應可信度"])

    bridge = merged.rename(columns={"庫存HQBU代碼": "HQBU代碼", "營收平台代碼": "平台代碼"})[
        ["事業群代碼", "HQBU代碼", "平台代碼"]
    ].drop_duplicates()
    bridge["對應型態"] = bridge.apply(
        lambda row: "direct_code_match" if row["HQBU代碼"] == row["平台代碼"] else "business_group_bridge",
        axis=1,
    )
    bridge["對應可信度"] = bridge["對應型態"].map(
        {"direct_code_match": "high", "business_group_bridge": "medium"}
    )

    duplicated_hqbu = bridge.duplicated(subset=["HQBU代碼"], keep=False)
    if duplicated_hqbu.any():
        count = bridge.loc[duplicated_hqbu, "HQBU代碼"].nunique()
        collector.add_warning(f"有 {count} 個 HQBU 代碼對應到多個平台代碼，將保留候選關係並標記限制。")

    return bridge.reset_index(drop=True)


def _validate_bu_codes(series: pd.Series, column_name: str, collector: MessageCollector) -> None:
    non_null = series.dropna().astype(str)
    invalid = non_null.loc[~non_null.str.match(re.compile(BU_CODE_PATTERN))]
    if not invalid.empty:
        collector.add_warning(f"mapping 欄位 {column_name} 有不符合 GG-01~GG-91 的值。樣本: {invalid.head(5).tolist()}")
