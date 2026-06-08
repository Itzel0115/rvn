from __future__ import annotations

import unittest

from business_question_classifier import classify_business_question
from canonical_task import CanonicalTaskProfile
from evidence_contracts import EvidenceContract, EvidenceContractBuilder
from task_profile import build_task_profile
from tests.support import build_stubbed_assistant


class EvidenceContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = build_stubbed_assistant("test-evidence-contracts", use_llm_planner=False, use_llm_rewriter=False)
        cls.builder = EvidenceContractBuilder()

    def _contracts_for(self, question: str):
        response = self.assistant.answer(question)
        routing = classify_business_question(question)
        task_profile = build_task_profile(question, routing)
        canonical = CanonicalTaskProfile.from_task_profile(task_profile, routing)
        return response, self.builder.build_evidence_contracts(response["domain_results"], canonical)

    def _first_contract(self, question: str, evidence_type: str) -> EvidenceContract:
        _, contracts = self._contracts_for(question)
        for contract in contracts:
            if contract.evidence_type == evidence_type:
                return contract
        self.fail(f"missing evidence contract type {evidence_type}; got {[contract.evidence_type for contract in contracts]}")

    def test_entity_month_table_output_can_be_converted(self) -> None:
        contract = self._first_contract("列出2025年3月各產品線庫存資料", "entity_month_table")

        self.assertEqual(contract.source_tool, "get_entity_month_table")
        self.assertEqual(contract.time_scope["month"], "2025-03")
        self.assertEqual(contract.entity_scope["dimension"], "product_line_5")
        self.assertEqual(contract.metric, "inventory_amount")
        self.assertTrue(contract.rows)
        self.assertTrue(contract.validate_basic()[0])

    def test_entity_period_pair_table_output_can_be_converted(self) -> None:
        contract = self._first_contract("列出 2025/09 與 2025/10 產品線的庫存", "entity_period_pair_table")

        self.assertEqual(contract.time_scope["period_a"], "2025-09")
        self.assertEqual(contract.time_scope["period_b"], "2025-10")
        self.assertEqual(contract.entity_scope["dimension"], "product_line_5")
        self.assertEqual(contract.metric, "inventory_amount")
        self.assertTrue(contract.rows)
        self.assertIn("value_a", contract.rows[0])
        self.assertIn("value_b", contract.rows[0])
        self.assertIn("change", contract.rows[0])

    def test_entity_multi_month_table_output_can_be_converted(self) -> None:
        contract = self._first_contract("列出 2025/01 到 2025/03 各產品線庫存", "entity_multi_month_table")

        self.assertEqual(contract.time_scope["start_month"], "2025-01")
        self.assertEqual(contract.time_scope["end_month"], "2025-03")
        self.assertEqual(contract.entity_scope["dimension"], "product_line_5")
        self.assertEqual(contract.metric, "inventory_amount")
        self.assertTrue(contract.rows)

    def test_entity_metric_lookup_output_can_be_converted(self) -> None:
        contract = self._first_contract("列出通路方案 2026/2 最新營收", "entity_metric_lookup")

        self.assertEqual(contract.entity_scope["value"], "3通路方案")
        self.assertEqual(contract.time_scope["month"], "2026-02")
        self.assertEqual(contract.metric, "revenue_amount")
        self.assertTrue(contract.rows)
        self.assertIsNotNone(contract.rows[0].get("value"))

    def test_entity_time_series_output_can_be_converted(self) -> None:
        contract = self._first_contract("比較 3通路方案 各月營收", "entity_time_series")

        self.assertEqual(contract.entity_scope["value"], "3通路方案")
        self.assertEqual(contract.metric, "revenue_amount")
        self.assertTrue(contract.rows)
        self.assertIn("month", contract.rows[0])

    def test_period_pair_comparison_output_can_be_converted(self) -> None:
        contract = self._first_contract("比較 2025 年 12 月與 2026 年 1 月營收差別", "period_pair_comparison")

        self.assertEqual(contract.time_scope["period_a"], "2025-12")
        self.assertEqual(contract.time_scope["period_b"], "2026-01")
        self.assertEqual(contract.metric, "revenue_amount")
        self.assertIn("overall", contract.summary)

    def test_chart_payload_output_can_be_converted(self) -> None:
        contract = self._first_contract("畫出 2025/02 與 2025/03 各產品線庫存比較圖", "chart_payload")

        self.assertEqual(contract.summary["chart_type"], "grouped_bar")
        self.assertEqual(contract.time_scope["period_a"], "2025-02")
        self.assertEqual(contract.time_scope["period_b"], "2025-03")
        self.assertEqual(contract.entity_scope["dimension"], "product_line_5")
        self.assertEqual(contract.metric, "inventory_amount")

    def test_validate_basic_catches_missing_required_fields(self) -> None:
        contract = EvidenceContract(
            evidence_id="ev-test",
            evidence_type="",
            source_tool="",
            task_family="metric_lookup",
            time_scope={},
            entity_scope={},
            metric=None,
            metric_label=None,
        )

        ok, errors = contract.validate_basic()
        self.assertFalse(ok)
        self.assertIn("missing_source_tool", errors)
        self.assertIn("missing_evidence_type", errors)
        self.assertIn("missing_metric", errors)


if __name__ == "__main__":
    unittest.main()
