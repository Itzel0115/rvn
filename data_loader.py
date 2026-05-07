from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import EXPECTED_INVENTORY_COLUMNS, EXPECTED_REVENUE_COLUMNS
from preprocess import (
    coerce_numeric_column,
    normalize_code_column,
    normalize_date_column,
    normalize_text_column,
)
from utils import MessageCollector


def load_excel_file(path: Path, collector: MessageCollector, sheet_name: int | str = 0) -> pd.DataFrame:
    if not path.exists():
        collector.add_error(f"找不到檔案: {path}")
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    except Exception as exc:
        collector.add_error(f"讀取 Excel 失敗: {path} ({exc})")
        return pd.DataFrame()


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    source_name: str,
    collector: MessageCollector,
) -> dict[str, list[str]]:
    existing = set(df.columns)
    missing = [col for col in required_columns if col not in existing]
    extra = [col for col in df.columns if col not in required_columns]
    if missing:
        collector.add_error(f"{source_name} 缺少必要欄位: {missing}")
    else:
        collector.add_info(f"{source_name} 必要欄位檢查通過。")
    return {"missing": missing, "extra": extra}


def load_inventory(path: Path) -> tuple[pd.DataFrame, dict[str, list[str]], MessageCollector]:
    collector = MessageCollector()
    df = load_excel_file(path, collector)
    check = validate_required_columns(df, EXPECTED_INVENTORY_COLUMNS, "庫存", collector)
    if check["missing"]:
        return df, check, collector

    df = df[EXPECTED_INVENTORY_COLUMNS].copy()
    df = normalize_date_column(df, "庫存", collector)
    df = normalize_code_column(df, "HQBU")
    df = coerce_numeric_column(df, "金額", "庫存", collector)
    df = coerce_numeric_column(df, "QTY", "庫存", collector, integer=True)
    df = coerce_numeric_column(df, "新事業群", "庫存", collector, integer=True)
    return df, check, collector


def load_revenue(path: Path) -> tuple[pd.DataFrame, dict[str, list[str]], MessageCollector]:
    collector = MessageCollector()
    df = load_excel_file(path, collector)
    check = validate_required_columns(df, EXPECTED_REVENUE_COLUMNS, "營收", collector)
    if check["missing"]:
        return df, check, collector

    df = df[EXPECTED_REVENUE_COLUMNS].copy()
    df = normalize_date_column(df, "營收", collector)
    df = normalize_code_column(df, "平台")
    df = coerce_numeric_column(df, "營收", "營收", collector)
    df = coerce_numeric_column(df, "新事業群", "營收", collector, integer=True)
    return df, check, collector


def load_mapping_raw(path: Path) -> tuple[pd.DataFrame, MessageCollector]:
    collector = MessageCollector()
    df = load_excel_file(path, collector, sheet_name=0)
    if not df.empty:
        df.columns = [str(col).strip() for col in df.columns]
        for column in df.columns:
            df = normalize_text_column(df, column)
    return df, collector
