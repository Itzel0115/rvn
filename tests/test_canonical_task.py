from __future__ import annotations

import unittest

from business_question_classifier import classify_business_question
from canonical_task import CanonicalTaskProfile
from task_profile import build_task_profile


class CanonicalTaskProfileTest(unittest.TestCase):
    def _canonical(self, question: str) -> CanonicalTaskProfile:
        routing = classify_business_question(question)
        task_profile = build_task_profile(question, routing)
        return CanonicalTaskProfile.from_task_profile(task_profile, routing)

    def test_product_line_inventory_month_table(self) -> None:
        canonical = self._canonical("列出2025年3月各產品線庫存資料")

        self.assertEqual(canonical.task_family, "entity_month_table_lookup")
        self.assertEqual(canonical.time_scope["mode"], "single_month")
        self.assertEqual(canonical.time_scope["month"], "2025-03")
        self.assertEqual(canonical.target_entity["dimension"], "product_line_5")
        self.assertEqual(canonical.target_entity["scope"], "all")
        self.assertIsNone(canonical.target_entity["value"])
        self.assertEqual(canonical.metric, "inventory_amount")
        self.assertIn("2025-03", canonical.constraints.preserve_months)
        ok, errors = canonical.validate_basic()
        self.assertTrue(ok, errors)

    def test_business_group_revenue_pie_chart(self) -> None:
        canonical = self._canonical("畫出2025年2月各事業群營收圓餅圖")

        self.assertEqual(canonical.task_family, "chart_request")
        self.assertEqual(canonical.time_scope["mode"], "single_month")
        self.assertEqual(canonical.time_scope["month"], "2025-02")
        self.assertEqual(canonical.target_entity["dimension"], "business_group")
        self.assertEqual(canonical.target_entity["scope"], "all")
        self.assertEqual(canonical.metric, "revenue_amount")
        self.assertEqual(canonical.chart_type, "pie")
        ok, errors = canonical.validate_basic()
        self.assertTrue(ok, errors)


if __name__ == "__main__":
    unittest.main()
