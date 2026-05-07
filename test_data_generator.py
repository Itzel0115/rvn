from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import INVENTORY_FILE, MAPPING_FILE, REVENUE_FILE
from utils import MessageCollector, ensure_directories


def generate_test_data() -> MessageCollector:
    collector = MessageCollector()
    ensure_directories([INVENTORY_FILE.parent])

    mapping_df = build_mapping_data()
    revenue_df = build_revenue_data()
    inventory_df = build_inventory_data()

    inventory_df.to_excel(INVENTORY_FILE, index=False)
    revenue_df.to_excel(REVENUE_FILE, index=False)
    mapping_df.to_excel(MAPPING_FILE, index=False)

    collector.add_info(f"已建立測試資料: {INVENTORY_FILE.name}, {REVENUE_FILE.name}, {MAPPING_FILE.name}")
    return collector


def build_mapping_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["智慧裝置", 1, "裝置-主力", "GG-01", "*0.72", "*40", "平台-主力", "GG-01", "*0.81"],
            ["智慧裝置", 1, "裝置-庫存壓力", "GG-02", "*0.72", "*38", "平台-庫存壓力", "GG-02", "*0.76"],
            ["雲端服務", 2, "雲端-穩定", "GG-03", "*0.66", "*22", "平台-雲端", "GG-03", "*0.69"],
            ["雲端服務", 2, "雲端-新品", "GG-04", "*0.66", "*24", "平台-新品", "GG-04", "*0.71"],
            ["零售通路", 3, "通路-季節型", "GG-05", "*0.59", "*16", "平台-零售", "GG-05", "*0.61"],
            ["零售通路", 3, "通路-清庫存", "GG-06", "*0.59", "*18", "平台-清庫存", "GG-06", "*0.57"],
        ],
        columns=[
            "事業群",
            "事業群代碼",
            "庫存:HQBU分類名稱",
            "庫存:HQBU代碼",
            "金額",
            "QTY",
            "營收:平台分類名稱",
            "營收:平台代碼",
            "實際營收",
        ],
    )


def build_revenue_data() -> pd.DataFrame:
    months = ["202401", "202402", "202403", "202404", "202405", "202406", "202407", "202408"]
    rows = []
    revenue_map = {
        (1, "GG-01"): [1200, 1280, 1350, 1450, 1510, 1630, 1750, 1890],
        (1, "GG-02"): [860, 900, 910, 920, 880, 790, 760, 730],
        (2, "GG-03"): [980, 995, 1005, 1010, 1025, 1040, 1060, 1075],
        (2, "GG-04"): [420, 450, 520, 610, 760, 930, 1110, 1290],
        (3, "GG-05"): [760, 840, 1120, 1180, 980, 900, 870, 820],
        (3, "GG-06"): [690, 670, 650, 620, 600, 560, 510, 470],
    }
    for (group_code, platform), values in revenue_map.items():
        for month, revenue in zip(months, values):
            rows.append({"日期": month, "平台": platform, "營收": revenue, "新事業群": group_code})
    return pd.DataFrame(rows)


def build_inventory_data() -> pd.DataFrame:
    months = ["202401", "202402", "202403", "202404", "202405", "202406", "202407", "202408"]
    rows = []
    inventory_map = {
        (1, "GG-01"): {
            "金額": [910, 930, 960, 980, 1010, 1040, 1080, 1120],
            "QTY": [220, 225, 228, 232, 240, 244, 250, 258],
        },
        (1, "GG-02"): {
            "金額": [780, 820, 860, 910, 960, 1080, 1210, 1360],
            "QTY": [180, 188, 194, 202, 214, 238, 262, 290],
        },
        (2, "GG-03"): {
            "金額": [640, 638, 642, 645, 650, 648, 646, 644],
            "QTY": [120, 121, 121, 122, 123, 123, 122, 122],
        },
        (2, "GG-04"): {
            "金額": [320, 330, 350, 390, 460, 560, 690, 830],
            "QTY": [90, 93, 97, 104, 118, 136, 159, 186],
        },
        (3, "GG-05"): {
            "金額": [420, 450, 520, 560, 610, 620, 600, 580],
            "QTY": [100, 108, 122, 128, 136, 138, 132, 126],
        },
        (3, "GG-06"): {
            "金額": [610, 650, 680, 700, 730, 760, 780, 790],
            "QTY": [150, 160, 168, 176, 184, 192, 198, 202],
        },
    }
    for (group_code, hqbu), metrics in inventory_map.items():
        for idx, month in enumerate(months):
            rows.append(
                {
                    "日期": month,
                    "HQBU": hqbu,
                    "金額": metrics["金額"][idx],
                    "QTY": metrics["QTY"][idx],
                    "新事業群": group_code,
                }
            )
    return pd.DataFrame(rows)
