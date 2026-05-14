from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import (
    COL_GROUP_CODE,
    COL_GROUP_NAME,
    COL_INV_AMOUNT,
    COL_INV_QTY,
    COL_MONTH,
    COL_PLATFORM,
    COL_REVENUE,
    COL_REVENUE_INV_AMOUNT_RATIO,
    COL_REVENUE_INV_QTY_RATIO,
)
from utils import MessageCollector


INVENTORY_RAW_COLUMNS = [
    "Wn日期",
    "年",
    "月",
    "HQBU",
    "typename",
    "金額",
    "QTY",
    "Productline_5",
    "五大產品線",
    "新事業群",
]

REVENUE_RAW_COLUMNS = [
    "公司類別",
    "年度",
    "月份",
    "合併事業群",
    "產品類別名稱",
    "實際營收",
    "五大產品線",
    "新事業群",
]


@dataclass
class RealAnalysisTables:
    inventory: pd.DataFrame
    revenue: pd.DataFrame
    inventory_monthly_entity: pd.DataFrame
    revenue_monthly_entity: pd.DataFrame
    revenue_inventory_aligned: pd.DataFrame
    data_quality_report: dict[str, Any]
    messages: list[str]


def normalize_month_key(value: Any = None, *, year: Any = None, month: Any = None) -> str | None:
    if year is not None and month is not None and not pd.isna(year) and not pd.isna(month):
        try:
            year_int = int(float(str(year).strip()))
            month_int = int(float(str(month).strip()))
        except (TypeError, ValueError):
            return None
        if 1 <= month_int <= 12:
            return f"{year_int:04d}-{month_int:02d}"
        return None

    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m")

    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        year_text = digits[:4]
        month_text = digits[4:6]
        try:
            year_int = int(year_text)
            month_int = int(month_text)
        except ValueError:
            return None
        if 1 <= month_int <= 12:
            return f"{year_int:04d}-{month_int:02d}"
    return None


def normalize_business_keys(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in ["business_group", "product_line_5"]:
        if column in result.columns:
            result[column] = result[column].apply(_clean_text)
    return result


def load_real_inventory_data(path: Path | str, collector: MessageCollector | None = None) -> pd.DataFrame:
    collector = collector or MessageCollector()
    raw = _load_excel(Path(path), collector)
    return normalize_real_inventory_data(raw, collector)


def load_real_revenue_data(path: Path | str, collector: MessageCollector | None = None) -> pd.DataFrame:
    collector = collector or MessageCollector()
    raw = _load_excel(Path(path), collector)
    return normalize_real_revenue_data(raw, collector)


def load_real_data_sources(
    inventory_path: Path | str,
    revenue_path: Path | str,
    collector: MessageCollector | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    collector = collector or MessageCollector()
    inventory = load_real_inventory_data(inventory_path, collector)
    revenue = load_real_revenue_data(revenue_path, collector)
    metadata = {
        "inventory_path": str(Path(inventory_path)),
        "revenue_path": str(Path(revenue_path)),
    }
    return inventory, revenue, metadata


def normalize_real_inventory_data(df: pd.DataFrame, collector: MessageCollector | None = None) -> pd.DataFrame:
    collector = collector or MessageCollector()
    if df.empty:
        return pd.DataFrame(columns=_inventory_standard_columns())

    missing = [col for col in INVENTORY_RAW_COLUMNS if col not in df.columns]
    if missing:
        collector.add_error(f"庫存檔缺少必要欄位: {missing}")
        return pd.DataFrame(columns=_inventory_standard_columns())

    result = pd.DataFrame()
    result["month_key"] = [
        normalize_month_key(row.get("Wn日期"), year=row.get("年"), month=row.get("月"))
        for _, row in df.iterrows()
    ]
    result["year"] = pd.to_numeric(df["年"], errors="coerce").astype("Int64")
    result["month"] = pd.to_numeric(df["月"], errors="coerce").astype("Int64")
    result["hqbu"] = df["HQBU"].apply(_clean_text)
    result["inventory_type"] = df["typename"].apply(_clean_text)
    result["inventory_amount"] = pd.to_numeric(df["金額"], errors="coerce")
    result["inventory_qty"] = pd.to_numeric(df["QTY"], errors="coerce")
    result["productline_raw"] = df["Productline_5"].apply(_clean_text)
    result["product_line_5"] = df["五大產品線"].apply(_clean_text)
    result["business_group"] = df["新事業群"].apply(_clean_text)
    return normalize_business_keys(result)


def normalize_real_revenue_data(df: pd.DataFrame, collector: MessageCollector | None = None) -> pd.DataFrame:
    collector = collector or MessageCollector()
    if df.empty:
        return pd.DataFrame(columns=_revenue_standard_columns())

    missing = [col for col in REVENUE_RAW_COLUMNS if col not in df.columns]
    if missing:
        collector.add_error(f"營收檔缺少必要欄位: {missing}")
        return pd.DataFrame(columns=_revenue_standard_columns())

    result = pd.DataFrame()
    result["month_key"] = [
        normalize_month_key(year=row.get("年度"), month=row.get("月份"))
        for _, row in df.iterrows()
    ]
    result["year"] = pd.to_numeric(df["年度"], errors="coerce").astype("Int64")
    result["month"] = pd.to_numeric(df["月份"], errors="coerce").astype("Int64")
    result["company_type"] = df["公司類別"].apply(_clean_text)
    result["merged_business_group"] = df["合併事業群"].apply(_clean_text)
    result["product_category_name"] = df["產品類別名稱"].apply(_clean_text)
    result["revenue_amount"] = pd.to_numeric(df["實際營收"], errors="coerce")
    result["product_line_5"] = df["五大產品線"].apply(_clean_text)
    result["business_group"] = df["新事業群"].apply(_clean_text)
    return normalize_business_keys(result)


def build_real_analysis_tables(
    inventory: pd.DataFrame,
    revenue: pd.DataFrame,
    source_metadata: dict[str, Any] | None = None,
) -> RealAnalysisTables:
    source_metadata = source_metadata or {}
    inventory_monthly_entity = _build_inventory_monthly_entity(inventory)
    revenue_monthly_entity = _build_revenue_monthly_entity(revenue)
    aligned = _build_revenue_inventory_aligned(revenue_monthly_entity, inventory_monthly_entity)
    quality = build_real_data_quality_report(inventory, revenue, aligned, source_metadata)
    messages = build_real_data_quality_messages(quality)
    return RealAnalysisTables(
        inventory=inventory,
        revenue=revenue,
        inventory_monthly_entity=inventory_monthly_entity,
        revenue_monthly_entity=revenue_monthly_entity,
        revenue_inventory_aligned=aligned,
        data_quality_report=quality,
        messages=messages,
    )


def build_legacy_compatible_frames(tables: RealAnalysisTables) -> dict[str, pd.DataFrame]:
    revenue = tables.revenue.copy()
    inventory = tables.inventory.copy()
    aligned = tables.revenue_inventory_aligned.copy()

    revenue_enriched = pd.DataFrame(
        {
            COL_MONTH: revenue.get("month_key"),
            COL_PLATFORM: revenue.get("business_group"),
            COL_GROUP_CODE: revenue.get("business_group"),
            COL_GROUP_NAME: revenue.get("business_group"),
            COL_REVENUE: revenue.get("revenue_amount"),
            "product_line_5": revenue.get("product_line_5"),
            "business_group": revenue.get("business_group"),
        }
    )
    inventory_enriched = pd.DataFrame(
        {
            COL_MONTH: inventory.get("month_key"),
            COL_PLATFORM: inventory.get("business_group"),
            COL_GROUP_CODE: inventory.get("business_group"),
            COL_GROUP_NAME: inventory.get("business_group"),
            COL_INV_AMOUNT: inventory.get("inventory_amount"),
            COL_INV_QTY: inventory.get("inventory_qty"),
            "HQBU": inventory.get("hqbu"),
            "product_line_5": inventory.get("product_line_5"),
            "business_group": inventory.get("business_group"),
        }
    )

    monthly_revenue = _monthly_metric(revenue_enriched, COL_REVENUE, "monthly_revenue")
    monthly_inventory_amount = _monthly_metric(inventory_enriched, COL_INV_AMOUNT, "monthly_inventory_amount")
    monthly_inventory_qty = _monthly_metric(inventory_enriched, COL_INV_QTY, "monthly_inventory_qty")
    revenue_by_group = _group_metric(revenue_enriched, COL_REVENUE, "revenue_by_group")
    inventory_by_group = _group_metric(inventory_enriched, COL_INV_AMOUNT, "inventory_by_group")

    platform_monthly = aligned.rename(
        columns={
            "month_key": COL_MONTH,
            "business_group": COL_PLATFORM,
            "revenue_amount": COL_REVENUE,
            "inventory_amount": COL_INV_AMOUNT,
            "inventory_qty": COL_INV_QTY,
            "revenue_inventory_amount_ratio": COL_REVENUE_INV_AMOUNT_RATIO,
            "revenue_inventory_qty_ratio": COL_REVENUE_INV_QTY_RATIO,
        }
    )
    platform_monthly[COL_GROUP_CODE] = platform_monthly[COL_PLATFORM]
    platform_monthly[COL_GROUP_NAME] = platform_monthly[COL_PLATFORM]
    platform_monthly["business_group"] = platform_monthly[COL_PLATFORM]
    if "product_line_5" not in platform_monthly.columns:
        platform_monthly["product_line_5"] = None

    return {
        "inventory_enriched": inventory_enriched,
        "revenue_enriched": revenue_enriched,
        "monthly_revenue": monthly_revenue,
        "monthly_inventory_amount": monthly_inventory_amount,
        "monthly_inventory_qty": monthly_inventory_qty,
        "revenue_by_group": revenue_by_group,
        "inventory_by_group": inventory_by_group,
        "merged_analysis": platform_monthly.copy(),
        "platform_monthly_analysis": platform_monthly,
        "anomalies": _build_real_anomalies(platform_monthly),
        "correlation_analysis": pd.DataFrame(),
    }


def build_real_data_quality_report(
    inventory: pd.DataFrame,
    revenue: pd.DataFrame,
    aligned: pd.DataFrame,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory_months = _sorted_unique(inventory, "month_key")
    revenue_months = _sorted_unique(revenue, "month_key")
    common_months = sorted(set(inventory_months) & set(revenue_months))
    inventory_groups = set(_sorted_unique(inventory, "business_group"))
    revenue_groups = set(_sorted_unique(revenue, "business_group"))
    common_groups = sorted(inventory_groups & revenue_groups)

    report = {
        "inventory_rows": int(len(inventory)),
        "revenue_rows": int(len(revenue)),
        "inventory_months": inventory_months,
        "revenue_months": revenue_months,
        "common_months": common_months,
        "latest_common_month": common_months[-1] if common_months else None,
        "inventory_business_group_count": int(len(inventory_groups)),
        "revenue_business_group_count": int(len(revenue_groups)),
        "common_business_groups": common_groups,
        "unmatched_inventory_business_groups": sorted(inventory_groups - revenue_groups),
        "unmatched_revenue_business_groups": sorted(revenue_groups - inventory_groups),
        "missing_business_group_rows": int(_missing_count(inventory, "business_group") + _missing_count(revenue, "business_group")),
        "missing_product_line_rows": int(_missing_count(inventory, "product_line_5") + _missing_count(revenue, "product_line_5")),
        "numeric_parse_errors": {
            "inventory_amount": int(_numeric_parse_error_count(inventory, "inventory_amount")),
            "inventory_qty": int(_numeric_parse_error_count(inventory, "inventory_qty")),
            "revenue_amount": int(_numeric_parse_error_count(revenue, "revenue_amount")),
        },
        "aligned_rows": int(len(aligned)),
        "both_rows": int((aligned.get("data_presence_flag") == "both").sum()) if not aligned.empty else 0,
        "revenue_only_rows": int((aligned.get("data_presence_flag") == "revenue_only").sum()) if not aligned.empty else 0,
        "inventory_only_rows": int((aligned.get("data_presence_flag") == "inventory_only").sum()) if not aligned.empty else 0,
        "source_metadata": source_metadata or {},
    }
    return report


def build_real_data_quality_messages(report: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    if report.get("missing_business_group_rows"):
        messages.append(f"缺少新事業群的資料列: {report['missing_business_group_rows']}")
    if report.get("missing_product_line_rows"):
        messages.append(f"缺少五大產品線的資料列: {report['missing_product_line_rows']}")
    if report.get("unmatched_inventory_business_groups"):
        messages.append(f"有新事業群只出現在庫存: {report['unmatched_inventory_business_groups']}")
    if report.get("unmatched_revenue_business_groups"):
        messages.append(f"有新事業群只出現在營收: {report['unmatched_revenue_business_groups']}")
    inventory_months = set(report.get("inventory_months", []))
    revenue_months = set(report.get("revenue_months", []))
    unmatched_months = sorted(inventory_months ^ revenue_months)
    if unmatched_months:
        messages.append(f"有月份未能對齊: {unmatched_months}")
    if report.get("revenue_only_rows") or report.get("inventory_only_rows"):
        messages.append(
            f"存在 revenue_only / inventory_only rows: revenue_only={report.get('revenue_only_rows', 0)}, "
            f"inventory_only={report.get('inventory_only_rows', 0)}"
        )
    return messages


def _build_inventory_monthly_entity(inventory: pd.DataFrame) -> pd.DataFrame:
    columns = ["month_key", "business_group", "product_line_5", "inventory_amount", "inventory_qty", "row_count", "hqbu_count"]
    if inventory.empty:
        return pd.DataFrame(columns=columns)
    grouped = (
        inventory.dropna(subset=["month_key", "business_group", "product_line_5"])
        .groupby(["month_key", "business_group", "product_line_5"], dropna=False)
        .agg(
            inventory_amount=("inventory_amount", "sum"),
            inventory_qty=("inventory_qty", "sum"),
            row_count=("inventory_amount", "size"),
            hqbu_count=("hqbu", pd.Series.nunique),
        )
        .reset_index()
    )
    return grouped[columns]


def _build_revenue_monthly_entity(revenue: pd.DataFrame) -> pd.DataFrame:
    columns = ["month_key", "business_group", "product_line_5", "revenue_amount", "row_count"]
    if revenue.empty:
        return pd.DataFrame(columns=columns)
    grouped = (
        revenue.dropna(subset=["month_key", "business_group", "product_line_5"])
        .groupby(["month_key", "business_group", "product_line_5"], dropna=False)
        .agg(revenue_amount=("revenue_amount", "sum"), row_count=("revenue_amount", "size"))
        .reset_index()
    )
    return grouped[columns]


def _build_revenue_inventory_aligned(revenue_monthly: pd.DataFrame, inventory_monthly: pd.DataFrame) -> pd.DataFrame:
    join_keys = ["month_key", "business_group", "product_line_5"]
    aligned = revenue_monthly.merge(
        inventory_monthly,
        on=join_keys,
        how="outer",
        suffixes=("_revenue", "_inventory"),
        indicator=True,
    )
    if aligned.empty:
        return pd.DataFrame(
            columns=[
                *join_keys,
                "revenue_amount",
                "inventory_amount",
                "inventory_qty",
                "revenue_inventory_amount_ratio",
                "revenue_inventory_qty_ratio",
                "data_presence_flag",
                "limitation",
            ]
        )

    presence = {"both": "both", "left_only": "revenue_only", "right_only": "inventory_only"}
    aligned["data_presence_flag"] = aligned["_merge"].map(presence)
    aligned = aligned.drop(columns=["_merge"])
    aligned["revenue_inventory_amount_ratio"] = None
    aligned["revenue_inventory_qty_ratio"] = None
    aligned["limitation"] = None

    both_mask = aligned["data_presence_flag"] == "both"
    amount_valid = both_mask & aligned["inventory_amount"].notna() & (aligned["inventory_amount"] != 0)
    qty_valid = both_mask & aligned["inventory_qty"].notna() & (aligned["inventory_qty"] != 0)
    aligned.loc[amount_valid, "revenue_inventory_amount_ratio"] = (
        aligned.loc[amount_valid, "revenue_amount"] / aligned.loc[amount_valid, "inventory_amount"]
    )
    aligned.loc[qty_valid, "revenue_inventory_qty_ratio"] = (
        aligned.loc[qty_valid, "revenue_amount"] / aligned.loc[qty_valid, "inventory_qty"]
    )

    aligned.loc[aligned["data_presence_flag"] == "revenue_only", "limitation"] = "庫存資料缺失，未計算 proxy ratio。"
    aligned.loc[aligned["data_presence_flag"] == "inventory_only", "limitation"] = "營收資料缺失，未計算 proxy ratio。"
    zero_amount = both_mask & (aligned["inventory_amount"].isna() | (aligned["inventory_amount"] == 0))
    zero_qty = both_mask & (aligned["inventory_qty"].isna() | (aligned["inventory_qty"] == 0))
    aligned.loc[zero_amount | zero_qty, "limitation"] = "分母為 0 或缺值，部分 proxy ratio 未計算。"
    return aligned.sort_values(join_keys).reset_index(drop=True)


def _load_excel(path: Path, collector: MessageCollector) -> pd.DataFrame:
    if not path.exists():
        collector.add_error(f"找不到資料檔案: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as exc:
        collector.add_error(f"讀取 Excel 失敗: {path} ({exc})")
        return pd.DataFrame()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def _monthly_metric(df: pd.DataFrame, value_column: str, metric_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[COL_MONTH, value_column, "月增率", "指標"])
    result = (
        df.dropna(subset=[COL_MONTH])
        .groupby(COL_MONTH, as_index=False)[value_column]
        .sum(min_count=1)
        .sort_values(COL_MONTH)
        .reset_index(drop=True)
    )
    result["月增率"] = result[value_column].pct_change().replace([np.inf, -np.inf], np.nan)
    result["指標"] = metric_name
    return result


def _group_metric(df: pd.DataFrame, value_column: str, metric_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[COL_GROUP_CODE, COL_GROUP_NAME, value_column, "占比", "指標"])
    result = (
        df.groupby([COL_GROUP_CODE, COL_GROUP_NAME], dropna=False, as_index=False)[value_column]
        .sum(min_count=1)
        .sort_values(value_column, ascending=False)
        .reset_index(drop=True)
    )
    total = result[value_column].sum()
    result["占比"] = result[value_column] / total if total else np.nan
    result["指標"] = metric_name
    return result


def _build_real_anomalies(platform_monthly: pd.DataFrame) -> pd.DataFrame:
    if platform_monthly.empty:
        return pd.DataFrame()
    records: list[dict[str, Any]] = []
    ratio_col = COL_REVENUE_INV_AMOUNT_RATIO
    both = platform_monthly[platform_monthly.get("data_presence_flag") == "both"].copy()
    if ratio_col not in both.columns or both.empty:
        return pd.DataFrame()
    latest_month = both[COL_MONTH].dropna().astype(str).max()
    latest = both[both[COL_MONTH].astype(str) == latest_month].copy()
    for _, row in latest.sort_values(ratio_col, ascending=True).head(5).iterrows():
        if pd.notna(row.get(ratio_col)):
            records.append(
                {
                    "異常類型": "營收/庫存金額 proxy 偏弱",
                    COL_MONTH: row.get(COL_MONTH),
                    COL_GROUP_CODE: row.get(COL_GROUP_CODE),
                    COL_PLATFORM: row.get(COL_PLATFORM),
                    "訊號": row.get(ratio_col),
                    "原因": "最新共同月份中，營收相對庫存金額 proxy 排名較低，需搭配資料品質與營運脈絡判讀。",
                }
            )
    return pd.DataFrame(records)


def _sorted_unique(df: pd.DataFrame, column: str) -> list[str]:
    if df.empty or column not in df.columns:
        return []
    return sorted(str(value) for value in df[column].dropna().unique().tolist() if str(value).strip())


def _missing_count(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    series = df[column]
    return int(series.isna().sum() + (series.astype(str).str.strip() == "").sum())


def _numeric_parse_error_count(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(df[column].isna().sum())


def _clean_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _inventory_standard_columns() -> list[str]:
    return [
        "month_key",
        "year",
        "month",
        "hqbu",
        "inventory_type",
        "inventory_amount",
        "inventory_qty",
        "productline_raw",
        "product_line_5",
        "business_group",
    ]


def _revenue_standard_columns() -> list[str]:
    return [
        "month_key",
        "year",
        "month",
        "company_type",
        "merged_business_group",
        "product_category_name",
        "revenue_amount",
        "product_line_5",
        "business_group",
    ]
