from __future__ import annotations

import unittest

from config import INVENTORY_FILE, REVENUE_FILE
from real_data import build_real_analysis_tables, load_real_data_sources, normalize_month_key
from utils import MessageCollector


class RealDataLoaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.collector = MessageCollector()
        cls.inventory, cls.revenue, cls.metadata = load_real_data_sources(INVENTORY_FILE, REVENUE_FILE, cls.collector)
        cls.tables = build_real_analysis_tables(cls.inventory, cls.revenue, cls.metadata)

    def test_real_inventory_columns_are_read(self) -> None:
        self.assertGreater(len(self.inventory), 0)
        for column in ["month_key", "business_group", "product_line_5", "inventory_amount", "inventory_qty"]:
            self.assertIn(column, self.inventory.columns)

    def test_real_revenue_columns_are_read(self) -> None:
        self.assertGreater(len(self.revenue), 0)
        for column in ["month_key", "business_group", "product_line_5", "revenue_amount"]:
            self.assertIn(column, self.revenue.columns)

    def test_month_key_normalization(self) -> None:
        self.assertEqual(normalize_month_key(202501), "2025-01")
        self.assertEqual(normalize_month_key(year=2026, month=2), "2026-02")

    def test_business_group_and_product_line_join_grain(self) -> None:
        aligned = self.tables.revenue_inventory_aligned
        self.assertGreater(len(aligned), 0)
        self.assertIn("both", set(aligned["data_presence_flag"]))
        self.assertIn("revenue_only", set(aligned["data_presence_flag"]))
        self.assertIn("inventory_only", set(aligned["data_presence_flag"]))

    def test_ratio_only_calculated_for_both_rows(self) -> None:
        aligned = self.tables.revenue_inventory_aligned
        one_sided = aligned[aligned["data_presence_flag"] != "both"]
        self.assertTrue(one_sided["revenue_inventory_amount_ratio"].isna().all())
        both_with_ratio = aligned[(aligned["data_presence_flag"] == "both") & aligned["revenue_inventory_amount_ratio"].notna()]
        self.assertGreater(len(both_with_ratio), 0)

    def test_quality_report_counts(self) -> None:
        report = self.tables.data_quality_report
        self.assertEqual(report["inventory_rows"], 122935)
        self.assertEqual(report["revenue_rows"], 1982)
        self.assertEqual(report["latest_common_month"], "2026-02")
        self.assertGreater(report["both_rows"], 0)


if __name__ == "__main__":
    unittest.main()
