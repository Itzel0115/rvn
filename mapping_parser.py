"""保留 `ParsedMapping` 的 compatibility data structure。

本檔案目前不解析 `mapping.xlsx`，也不包含 workbook schema、validation 或
bridge-building。結構由 inventory/revenue pipeline 以 normalized entity
metadata 建立；保留名稱是為避免既有 API、Agent 與 tests 失效，未來不應在此
重新加入外部 workbook parsing。
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass


@dataclass
class ParsedMapping:
    """承載由正式資料衍生的相容欄位，不代表第三份 Excel 輸入。"""
    raw_mapping: pd.DataFrame
    structured_mapping: pd.DataFrame
    business_group_mapping: pd.DataFrame
    inventory_hqbu_mapping: pd.DataFrame
    revenue_platform_mapping: pd.DataFrame
    anonymization_rules: pd.DataFrame
    bridge_candidates: pd.DataFrame
    mapping_success: bool
    warnings: list[str]
