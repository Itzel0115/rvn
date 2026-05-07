from __future__ import annotations

import unittest

from analysis_tools import AnalysisToolbox, QueryFilters
from tests.support import get_context


class AnalysisToolboxTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.toolbox = AnalysisToolbox(get_context(), "test-analysis-tools")

    def test_get_top_groups_returns_sorted_revenue_groups(self) -> None:
        rows = self.toolbox.get_top_groups("revenue")
        self.assertGreaterEqual(len(rows), 3)
        self.assertEqual(rows[0]["value_text"], "18,810.00")

    def test_get_anomalies_returns_records(self) -> None:
        rows = self.toolbox.get_anomalies(top_n=3)
        self.assertEqual(len(rows), 3)
        self.assertIn("異常類型", rows[0])
        self.assertTrue("原因" in rows[0] or "說明" in rows[0])

    def test_get_chart_payload_returns_table_preview(self) -> None:
        payload = self.toolbox.get_chart_payload("current_month_platform_revenue_bar")
        self.assertIsNotNone(payload)
        self.assertEqual(payload["chart_type"], "bar")
        self.assertTrue(payload["table_preview"])

    def test_get_observation_table_returns_rows(self) -> None:
        payload = self.toolbox.get_observation_table(
            {
                "row_dimension": "platform",
                "metric": "revenue",
                "current_month": "2024-08",
            }
        )
        self.assertEqual(payload["selection"]["current_month"], "2024-08")
        self.assertGreater(len(payload["rows"]), 0)

    def test_get_data_coverage_reports_latest_month(self) -> None:
        coverage = self.toolbox.get_data_coverage()
        self.assertEqual(coverage["months"][-1], "2024-08")
        self.assertTrue(coverage["supported_domains"]["sales"])
        self.assertTrue(coverage["supported_domains"]["financial"])

    def test_scoped_revenue_query_respects_filters(self) -> None:
        df = self.toolbox.get_metric_table("revenue_trend", QueryFilters(month="2024-08", platform="GG-02"))
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["月份"], "2024-08")

    def test_get_yoy_mom_breakdown_returns_list(self) -> None:
        rows = self.toolbox.get_yoy_mom_breakdown(metric="revenue", dimension="overall", top_n=2)
        self.assertIsInstance(rows, list)
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["month"], "2024-08")
        self.assertEqual(rows[0]["previous_month"], "2024-07")

    def test_get_yoy_mom_breakdown_marks_yoy_unavailable_without_prior_year(self) -> None:
        rows = self.toolbox.get_yoy_mom_breakdown(metric="revenue", dimension="overall", top_n=1)
        self.assertFalse(rows[0]["yoy_available"])
        self.assertIn("prior-year", rows[0]["yoy_reason"])

    def test_get_contribution_analysis_returns_contributors(self) -> None:
        payload = self.toolbox.get_contribution_analysis(metric="revenue", dimension="platform", top_n=3)
        self.assertEqual(payload["month"], "2024-08")
        self.assertTrue(payload["contributors"])
        self.assertEqual(payload["contributors"][0]["name"], "GG-04")

    def test_contribution_pct_is_computed_when_total_change_is_non_zero(self) -> None:
        payload = self.toolbox.get_contribution_analysis(metric="revenue", dimension="platform", top_n=3)
        self.assertNotEqual(payload["total_change"], 0)
        self.assertIsNotNone(payload["contributors"][0]["contribution_pct"])

    def test_get_inventory_turnover_proxy_returns_limitation(self) -> None:
        rows = self.toolbox.get_inventory_turnover_proxy(top_n=2)
        self.assertEqual(rows[0]["platform"], "GG-02")
        self.assertEqual(
            rows[0]["limitation"],
            "此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。",
        )

    def test_turnover_proxy_does_not_claim_formal_turnover(self) -> None:
        rows = self.toolbox.get_inventory_turnover_proxy(top_n=2)
        self.assertNotIn("正式庫存週轉率為", rows[0]["risk_label"])
        self.assertEqual(rows[0]["efficiency_level"], "low")

    def test_get_platform_performance_snapshot_returns_scorecard(self) -> None:
        payload = self.toolbox.get_platform_performance_snapshot(QueryFilters(month="2024-08"))

        self.assertEqual(payload["month"], "2024-08")
        self.assertEqual(payload["dimension"], "platform")
        self.assertTrue(payload["rows"])
        self.assertIn("summary", payload)
        self.assertIn("rubric", payload)
        self.assertTrue(payload["limitations"])
        first = payload["rows"][0]
        for field_name in [
            "platform",
            "revenue",
            "revenue_rank",
            "inventory_amount",
            "inventory_rank",
            "revenue_inventory_amount_ratio",
            "efficiency_rank",
            "revenue_mom_change",
            "anomaly_count",
            "health_score",
            "risk_score",
            "performance_label",
            "primary_strength",
            "primary_risk",
        ]:
            self.assertIn(field_name, first)

    def test_platform_performance_snapshot_scores_are_deterministic_and_bounded(self) -> None:
        first = self.toolbox.get_platform_performance_snapshot(QueryFilters(month="2024-08"))
        second = self.toolbox.get_platform_performance_snapshot(QueryFilters(month="2024-08"))

        self.assertEqual(first["summary"], second["summary"])
        self.assertEqual(first["rows"], second["rows"])
        for row in first["rows"]:
            self.assertGreaterEqual(row["health_score"], 0.0)
            self.assertLessEqual(row["health_score"], 1.0)
            self.assertGreaterEqual(row["risk_score"], 0.0)
            self.assertLessEqual(row["risk_score"], 1.0)

    def test_platform_performance_snapshot_best_is_not_inventory_amount_alone(self) -> None:
        payload = self.toolbox.get_platform_performance_snapshot(QueryFilters(month="2024-08"))

        self.assertNotEqual(payload["summary"]["best_platform"], payload["summary"]["top_inventory_platform"])
        best_row = next(row for row in payload["rows"] if row["platform"] == payload["summary"]["best_platform"])
        self.assertIn("health_score", best_row)
        self.assertIn("營收相對庫存效率", best_row["primary_strength"])

    def test_platform_performance_snapshot_weakest_has_risk_signal(self) -> None:
        payload = self.toolbox.get_platform_performance_snapshot(QueryFilters(month="2024-08"))

        weakest_row = next(row for row in payload["rows"] if row["platform"] == payload["summary"]["weakest_platform"])
        self.assertTrue(
            weakest_row["anomaly_count"] > 0
            or weakest_row["efficiency_rank"] >= 3
            or "偏弱" in weakest_row["primary_risk"]
        )


    def test_get_root_cause_candidates_returns_dict(self) -> None:
        payload = self.toolbox.get_root_cause_candidates(metric="revenue", top_n=4)
        self.assertIsInstance(payload, dict)
        self.assertFalse(payload["root_cause_available"])
        self.assertEqual(payload["month"], "2024-08")

    def test_root_cause_candidates_include_required_fields(self) -> None:
        payload = self.toolbox.get_root_cause_candidates(metric="revenue", top_n=4)
        self.assertIsInstance(payload["candidates"], list)
        self.assertTrue(payload["candidates"])
        first = payload["candidates"][0]
        for field_name in [
            "candidate_type",
            "title",
            "description",
            "supporting_tools",
            "supporting_evidence",
            "confidence",
            "recommended_check",
            "limitation",
        ]:
            self.assertIn(field_name, first)

    def test_root_cause_candidates_do_not_claim_confirmed_cause(self) -> None:
        payload = self.toolbox.get_root_cause_candidates(metric="revenue", top_n=4)
        combined = " ".join(
            [
                candidate["title"] + " " + candidate["description"] + " " + candidate["limitation"]
                for candidate in payload["candidates"]
            ]
        )
        self.assertNotIn("已確認根本原因", combined)
        self.assertNotIn("原因就是", combined)
        self.assertNotIn("一定是", combined)


if __name__ == "__main__":
    unittest.main()
