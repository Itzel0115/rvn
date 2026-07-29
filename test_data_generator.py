from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import INVENTORY_FILE, REVENUE_FILE
from utils import MessageCollector, ensure_directories


def generate_test_data() -> MessageCollector:
    collector = MessageCollector()
    ensure_directories([INVENTORY_FILE.parent])

    revenue_df = build_revenue_data()
    inventory_df = build_inventory_data()

    inventory_df.to_excel(INVENTORY_FILE, index=False)
    revenue_df.to_excel(REVENUE_FILE, index=False)

    collector.add_info(f"已建立測試資料: {INVENTORY_FILE.name}, {REVENUE_FILE.name}")
    return collector
