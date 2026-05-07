from __future__ import annotations

from typing import Any

import pandas as pd

from utils import MessageCollector, normalize_code, safe_strip


def parse_yyyymm_to_period(value: Any) -> str | None:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m")

    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 6:
        return None

    year = digits[:4]
    month = digits[4:]
    try:
        month_int = int(month)
    except ValueError:
        return None
    if month_int < 1 or month_int > 12:
        return None
    return f"{year}-{month_int:02d}"


def normalize_date_column(df: pd.DataFrame, source_name: str, collector: MessageCollector) -> pd.DataFrame:
    df = df.copy()
    parsed = df["日期"].apply(parse_yyyymm_to_period)
    invalid_mask = parsed.isna()
    if invalid_mask.any():
        samples = df.loc[invalid_mask, "日期"].head(5).tolist()
        collector.add_warning(
            f"{source_name} 有 {invalid_mask.sum()} 筆日期無法解析為 YYYYMM，將保留資料列但標記空值。樣本: {samples}"
        )
    df["月份"] = parsed
    return df


def coerce_numeric_column(
    df: pd.DataFrame,
    column: str,
    source_name: str,
    collector: MessageCollector,
    integer: bool = False,
) -> pd.DataFrame:
    df = df.copy()
    converted = pd.to_numeric(df[column], errors="coerce")
    invalid_mask = converted.isna() & df[column].notna()
    if invalid_mask.any():
        samples = df.loc[invalid_mask, column].head(5).tolist()
        collector.add_warning(
            f"{source_name} 欄位 {column} 有 {invalid_mask.sum()} 筆無法轉成數值，將標記為空值。樣本: {samples}"
        )
    if integer:
        df[column] = converted.round().astype("Int64")
    else:
        df[column] = converted.astype(float)
    return df


def normalize_text_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].apply(safe_strip)
    return df


def normalize_code_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    df[column] = df[column].apply(normalize_code)
    return df
