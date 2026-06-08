from __future__ import annotations

import unittest

from analysis_tools import AnalysisToolbox
from tests.support import get_context


class AnalysisToolboxTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = get_context()
        cls.toolbox = AnalysisToolbox(cls.context, "test-analysis-tools")

    def test_get_data_coverage_reports_real_latest_common_month(self) -> None:
        coverage = self.toolbox.get_data_coverage()
        quality = coverage["real_data_quality_report"]

        self.assertEqual(quality["latest_common_month"], "2026-02")
        self.assertIn("2026-02", quality["common_months"])
        self.assertGreater(quality["aligned_rows"], 0)

    def test_get_entity_performance_snapshot_business_group_has_rows(self) -> None:
        payload = self.toolbox.get_entity_performance_snapshot(entity_dimension="business_group")

        self.assertEqual(payload["dimension"], "business_group")
        self.assertEqual(payload["entity_label"], "事業群")
        self.assertTrue(payload["rows"])
        self.assertIn("best_entity", payload["summary"])
        self.assertNotIn("GG-01", {row["entity_value"] for row in payload["rows"]})
        first = payload["rows"][0]
        for column in [
            "entity_value",
            "revenue_amount",
            "revenue_rank",
            "inventory_amount",
            "inventory_rank",
            "inventory_qty",
            "revenue_inventory_amount_ratio",
            "efficiency_rank",
            "anomaly_count",
            "health_score",
            "risk_score",
            "performance_label",
        ]:
            self.assertIn(column, first)

    def test_get_entity_performance_snapshot_product_line_has_rows(self) -> None:
        payload = self.toolbox.get_entity_performance_snapshot(entity_dimension="product_line_5")

        self.assertEqual(payload["dimension"], "product_line_5")
        self.assertEqual(payload["entity_label"], "產品線")
        self.assertTrue(payload["rows"])
        self.assertTrue(any(row.get("product_line_5") for row in payload["rows"]))

    def test_product_line_snapshot_supports_parent_filter(self) -> None:
        payload = self.toolbox.get_entity_performance_snapshot(
            entity_dimension="product_line_5",
            parent_filter={"business_group": "3通路方案"},
        )

        self.assertEqual(payload["entity_dimension"], "product_line_5")
        self.assertEqual(payload["parent_filter"], {"business_group": "3通路方案"})
        self.assertTrue(payload["rows"])
        self.assertTrue(all(row.get("business_group") == "3通路方案" for row in payload["rows"]))

    def test_entity_cross_section_and_period_pair_evidence_types(self) -> None:
        comparison = self.toolbox.get_entity_cross_section_comparison(entity_dimension="product_line_5")
        period = self.toolbox.get_entity_period_pair_comparison(
            entity_dimension="business_group",
            metric="revenue",
            period_a="2026-01",
            period_b="2026-02",
        )

        self.assertEqual(comparison["evidence_type"], "entity_cross_section_comparison")
        self.assertEqual(comparison["source_tool"], "get_entity_cross_section_comparison")
        self.assertEqual(period["evidence_type"], "entity_period_pair_comparison")
        self.assertEqual(period["source_tool"], "get_entity_period_pair_comparison")

    def test_entity_metric_ranking_returns_top_mapped_entity(self) -> None:
        payload = self.toolbox.get_entity_metric_ranking(
            entity_dimension="business_group",
            metric="revenue_amount",
        )

        self.assertEqual(payload["evidence_type"], "entity_metric_ranking")
        self.assertEqual(payload["source_tool"], "get_entity_metric_ranking")
        self.assertEqual(payload["entity_label"], "事業群")
        self.assertEqual(payload["metric"], "revenue_amount")
        self.assertEqual(payload["sort_direction"], "descending")
        self.assertTrue(payload["rows"])
        self.assertIsNotNone(payload["top_entity"])
        self.assertNotEqual(payload["top_entity"], "未對應")
        self.assertIn("rank", payload["rows"][0])

    def test_entity_metric_ranking_supports_product_line_inventory(self) -> None:
        payload = self.toolbox.get_entity_metric_ranking(
            entity_dimension="product_line_5",
            metric="inventory_amount",
        )

        self.assertEqual(payload["entity_dimension"], "product_line_5")
        self.assertEqual(payload["entity_label"], "產品線")
        self.assertEqual(payload["metric"], "inventory_amount")
        self.assertTrue(payload["rows"])

    def test_get_inventory_turnover_proxy_is_proxy_not_formal_turnover(self) -> None:
        rows = self.toolbox.get_inventory_turnover_proxy(entity_dimension="product_line_5", top_n=3)

        self.assertTrue(rows)
        self.assertIn("proxy", rows[0]["limitation"])
        self.assertIn("非正式周轉指標", rows[0]["limitation"])

    def test_platform_wrapper_maps_to_business_group(self) -> None:
        payload = self.toolbox.get_platform_performance_snapshot()

        self.assertEqual(payload["dimension"], "business_group")
        self.assertTrue(payload["rows"])
        self.assertIn("best_platform", payload["summary"])

    def test_entity_period_pair_comparison_uses_2026_periods(self) -> None:
        payload = self.toolbox.get_entity_period_pair_comparison(
            entity_dimension="business_group",
            metric="revenue",
            period_a="2026-01",
            period_b="2026-02",
        )

        self.assertEqual(payload["period_a"], "2026-01")
        self.assertEqual(payload["period_b"], "2026-02")
        self.assertTrue(payload["overall"])
        self.assertTrue(payload["breakdown"])

    def test_get_entity_time_series_returns_named_business_group_rows(self) -> None:
        payload = self.toolbox.get_entity_time_series(
            entity_dimension="business_group",
            entity_value="3通路方案",
            metric="revenue_amount",
        )

        self.assertEqual(payload["evidence_type"], "entity_time_series")
        self.assertEqual(payload["entity_value"], "3通路方案")
        self.assertTrue(payload["rows"])
        self.assertEqual(payload["rows"][0]["month"], "2025-01")
        self.assertEqual(payload["summary"]["latest_month"], "2026-02")

    def test_get_overall_time_series_returns_monthly_rows(self) -> None:
        payload = self.toolbox.get_overall_time_series(metric="revenue_amount")

        self.assertEqual(payload["evidence_type"], "overall_time_series")
        self.assertTrue(payload["rows"])
        self.assertEqual(payload["rows"][0]["month"], "2025-01")
        self.assertEqual(payload["summary"]["latest_month"], "2026-02")

    def test_get_entity_trend_comparison_returns_entity_summaries(self) -> None:
        payload = self.toolbox.get_entity_trend_comparison(
            entity_dimension="business_group",
            metric="revenue_amount",
            recent_n=6,
        )

        self.assertEqual(payload["evidence_type"], "entity_trend_comparison")
        self.assertTrue(payload["rows"])
        self.assertTrue(payload["entity_summaries"])
        self.assertEqual(payload["summary"]["latest_month"], "2026-02")

    def test_get_revenue_inventory_relationship_returns_labels(self) -> None:
        payload = self.toolbox.get_revenue_inventory_relationship(entity_dimension="business_group")

        self.assertEqual(payload["evidence_type"], "metric_relationship")
        self.assertTrue(payload["rows"])
        self.assertIn(payload["rows"][0]["relationship_label"], {"revenue_down_inventory_up", "revenue_up_inventory_up", "revenue_flat_inventory_up", "ratio_worsening", "aligned_growth", "mixed"})
        self.assertIn("relationship_counts", payload["summary"])

    def test_get_entity_contribution_analysis_preserves_period_pair(self) -> None:
        payload = self.toolbox.get_entity_contribution_analysis(
            entity_dimension="business_group",
            metric="revenue_amount",
            period_a="2025-12",
            period_b="2026-01",
        )

        self.assertEqual(payload["evidence_type"], "entity_contribution_analysis")
        self.assertEqual(payload["period_a"], "2025-12")
        self.assertEqual(payload["period_b"], "2026-01")
        self.assertEqual(payload["summary"]["top_contributor"], "3通路方案")

    def test_new_chart_keys_return_payloads(self) -> None:
        for chart_key in [
            "business_group_revenue_inventory",
            "business_group_health_score",
            "product_line_revenue_inventory",
            "product_line_health_score",
            "business_group_revenue_bar",
            "business_group_inventory_bar",
            "business_group_health_score_bar",
            "business_group_revenue_inventory_ratio_bar",
            "product_line_revenue_bar",
            "product_line_inventory_bar",
            "product_line_health_score_bar",
            "product_line_revenue_inventory_ratio_bar",
            "current_month_business_group_revenue_bar",
            "business_group_ratio_rank",
        ]:
            payload = self.toolbox.get_chart_payload(chart_key)
            self.assertIsNotNone(payload, chart_key)
            self.assertTrue(payload["table_preview"], chart_key)

    def test_unmapped_entity_is_not_best_entity(self) -> None:
        payload = self.toolbox.get_entity_performance_snapshot(entity_dimension="business_group")

        self.assertNotEqual(payload["summary"].get("best_entity"), "未對應")
        if any(row.get("entity_value") == "未對應" for row in payload["rows"]):
            self.assertTrue(any("未對應" in item for item in payload["limitations"]))

    def test_phase10f_entity_period_pair_table_preserves_explicit_months_and_metric(self) -> None:
        payload = self.toolbox.get_entity_period_pair_table(
            entity_dimension="product_line_5",
            metric="inventory_amount",
            period_a="2025-02",
            period_b="2025-03",
        )

        self.assertEqual(payload["evidence_type"], "entity_period_pair_table")
        self.assertEqual(payload["source_tool"], "get_entity_period_pair_table")
        self.assertEqual(payload["period_a"], "2025-02")
        self.assertEqual(payload["period_b"], "2025-03")
        self.assertEqual(payload["entity_dimension"], "product_line_5")
        self.assertEqual(payload["metric"], "inventory_amount")
        self.assertTrue(payload["rows"])
        self.assertIn("value_a", payload["rows"][0])
        self.assertIn("value_b", payload["rows"][0])

    def test_phase10f_entity_multi_month_table_returns_month_entity_rows(self) -> None:
        payload = self.toolbox.get_entity_multi_month_table(
            entity_dimension="business_group",
            metric="revenue_amount",
            start_month="2025-01",
            end_month="2025-03",
        )

        self.assertEqual(payload["evidence_type"], "entity_multi_month_table")
        self.assertEqual(payload["start_month"], "2025-01")
        self.assertEqual(payload["end_month"], "2025-03")
        self.assertTrue(payload["rows"])
        self.assertIn("month", payload["rows"][0])
        self.assertIn("entity_value", payload["rows"][0])

    def test_phase10f_entity_period_pair_value_returns_single_entity_rows(self) -> None:
        payload = self.toolbox.get_entity_period_pair_value(
            entity_dimension="business_group",
            entity_value="3通路方案",
            metric="revenue_amount",
            period_a="2025-02",
            period_b="2025-03",
        )

        self.assertEqual(payload["evidence_type"], "entity_period_pair_value")
        self.assertEqual(payload["entity_value"], "3通路方案")
        self.assertEqual(payload["period_a"], "2025-02")
        self.assertEqual(payload["period_b"], "2025-03")
        self.assertEqual(len(payload["rows"]), 2)


if __name__ == "__main__":
    unittest.main()
