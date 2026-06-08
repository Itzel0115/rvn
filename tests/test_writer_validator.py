from __future__ import annotations

import unittest
from dataclasses import replace

from business_question_classifier import classify_business_question
from canonical_task import CanonicalTaskProfile
from evidence_contracts import EvidenceContract
from task_profile import build_task_profile
from tests.test_evidence_contracts import EvidenceContractsTest
from writer_validator import WriterValidator


class WriterValidatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        EvidenceContractsTest.setUpClass()
        helper = EvidenceContractsTest()
        _, cls.period_contracts = helper._contracts_for("列出 2025/09 與 2025/10 產品線的庫存")
        routing = classify_business_question("列出 2025/09 與 2025/10 產品線的庫存")
        task_profile = build_task_profile("列出 2025/09 與 2025/10 產品線的庫存", routing)
        cls.period_canonical = CanonicalTaskProfile.from_task_profile(task_profile, routing)
        cls.validator = WriterValidator()

    def _validate(self, output, contracts=None, canonical=None, display=None):
        selected_contracts = self.period_contracts if contracts is None else contracts
        return self.validator.validate(
            canonical or self.period_canonical,
            selected_contracts,
            output,
            deterministic_display_blocks=display,
        )


    def _contract(self, *, metric="revenue_amount", rows=None, summary=None, evidence_type="test_evidence"):
        return EvidenceContract(
            evidence_id=f"ev-{metric}",
            evidence_type=evidence_type,
            source_tool="test_tool",
            task_family="test_task",
            time_scope={"month": "2025-03"},
            entity_scope={"dimension": "business_group", "scope": "all"},
            metric=metric,
            metric_label={
                "revenue_amount": "營收",
                "inventory_amount": "庫存金額",
                "health_score": "health_score",
                "risk_score": "risk_score",
            }.get(metric, metric),
            rows=rows or [],
            summary=summary or {},
            limitations=[],
            data_quality_flags=[],
        )

    def _valid_output(self):
        limitations = []
        for contract in self.period_contracts:
            limitations.extend(contract.limitations)
        return {
            "headline": "結論：已列出 2025-09 與 2025-10 各產品線庫存金額資料；2025-10 最高的是 Server。",
            "key_observations": ["表格保留兩期庫存金額與 change 欄位。"],
            "limitations": limitations,
            "table_caption": "2025-09 與 2025-10 各產品線庫存金額",
            "confidence_note": "依已提供資料整理。",
        }

    def test_valid_writer_output_passes(self) -> None:
        validation = self._validate(self._valid_output())

        self.assertTrue(validation["valid"], validation)

    def test_new_number_rejected(self) -> None:
        output = self._valid_output()
        output["headline"] += " 另有 999,999,999。"

        validation = self._validate(output)

        self.assertFalse(validation["valid"])
        self.assertIn("number_not_in_evidence", validation["reason"])

    def test_wrong_month_rejected(self) -> None:
        output = self._valid_output()
        output["headline"] = output["headline"].replace("2025-09", "2024-09")

        validation = self._validate(output)

        self.assertFalse(validation["valid"])
        self.assertIn("month_not_in_evidence", validation["reason"])

    def test_wrong_entity_rejected(self) -> None:
        output = self._valid_output()
        output["headline"] += " 最高的是 ABC產品線。"

        validation = self._validate(output)

        self.assertFalse(validation["valid"])
        self.assertIn("entity_not_in_evidence", ",".join(validation["violations"]))

    def test_wrong_metric_rejected(self) -> None:
        contracts = [self._contract(metric="inventory_amount", rows=[{"entity_value": "Server", "inventory_amount": 50}])]
        output = {
            "headline": "結論：2025-03 營收最高的是 Server。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "",
        }

        validation = self._validate(
            output,
            contracts=contracts,
            canonical={"task_family": "entity_month_table_lookup", "metric": "inventory_amount"},
        )

        self.assertFalse(validation["valid"])
        self.assertIn("metric_violation", ",".join(validation["violations"]))

    def test_forecast_claim_rejected(self) -> None:
        output = {
            "headline": "結論：下個月會改善。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "",
        }

        validation = self._validate(output, contracts=[], canonical={"task_family": "forecast_unsupported"})

        self.assertFalse(validation["valid"])
        self.assertIn("forecast_violation", ",".join(validation["violations"]))

    def test_root_cause_claim_rejected(self) -> None:
        output = self._valid_output()
        output["headline"] += " 原因就是產品組合變化。"

        validation = self._validate(output)

        self.assertFalse(validation["valid"])
        self.assertIn("root_cause_violation", ",".join(validation["violations"]))

    def test_internal_tool_name_rejected(self) -> None:
        output = self._valid_output()
        output["confidence_note"] = "source_tool=get_entity_period_pair_table"

        validation = self._validate(output)

        self.assertFalse(validation["valid"])
        self.assertIn("internal_tool_name_violation", ",".join(validation["violations"]))

    def test_debug_string_rejected(self) -> None:
        output = self._valid_output()
        output["confidence_note"] = "table rows=9"

        validation = self._validate(output)

        self.assertFalse(validation["valid"])
        self.assertIn("debug_string_violation", ",".join(validation["violations"]))

    def test_limitation_deletion_rejected(self) -> None:
        limited_contracts = [
            replace(self.period_contracts[0], limitations=["此表僅比較庫存金額，不能判定根本原因。"]),
            *self.period_contracts[1:],
        ]
        output = self._valid_output()
        output["limitations"] = []

        validation = self._validate(output, contracts=limited_contracts)

        self.assertFalse(validation["valid"])
        self.assertIn("limitation_violation", ",".join(validation["violations"]))

    def test_forecast_safe_refusal_passes(self) -> None:
        output = {
            "headline": "結論：目前無法判斷下個月營收是否改善。",
            "key_observations": ["現有 evidence 不包含預測模型或訂單資料。"],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "依現有資料限制回答。",
        }

        validation = self._validate(output, contracts=[], canonical={"task_family": "forecast_unsupported"})

        self.assertTrue(validation["valid"], validation)

    def test_multi_metric_evidence_allows_revenue_and_inventory(self) -> None:
        contracts = [
            self._contract(metric="revenue_amount", rows=[{"entity_value": "A", "revenue_amount": 100}]),
            self._contract(metric="inventory_amount", rows=[{"entity_value": "A", "inventory_amount": 50}]),
        ]
        output = {
            "headline": "結論：2025-03 各事業群營收與庫存金額重點已整理。",
            "key_observations": ["表格列出營收與庫存金額。"],
            "limitations": [],
            "table_caption": "2025-03 營收與庫存金額",
            "confidence_note": "依 evidence 整理。",
        }

        validation = self._validate(output, contracts=contracts, canonical={"task_family": "latest_month_entity_summary"})

        self.assertTrue(validation["valid"], validation)

    def test_inventory_only_evidence_rejects_revenue_mention(self) -> None:
        contracts = [self._contract(metric="inventory_amount", rows=[{"entity_value": "A", "inventory_amount": 50}])]
        output = {
            "headline": "結論：2025-03 各事業群營收最高的是 A。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "",
        }

        validation = self._validate(output, contracts=contracts, canonical={"task_family": "entity_month_table_lookup", "metric": "inventory_amount"})

        self.assertFalse(validation["valid"])
        self.assertIn("metric_violation", ",".join(validation["violations"]))

    def test_performance_snapshot_allows_health_and_risk_score(self) -> None:
        contracts = [
            self._contract(
                metric="health_score",
                evidence_type="entity_performance_snapshot",
                rows=[{"entity_value": "A", "health_score": 0.8, "risk_score": 0.2}],
            )
        ]
        output = {
            "headline": "結論：A 的 health_score 與 risk_score 已整理為 scorecard。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "scorecard",
            "confidence_note": "scorecard proxy",
        }

        validation = self._validate(output, contracts=contracts, canonical={"task_family": "performance_assessment"})

        self.assertTrue(validation["valid"], validation)

    def test_unrelated_metric_not_in_evidence_rejected(self) -> None:
        contracts = [self._contract(metric="revenue_amount", rows=[{"entity_value": "A", "revenue_amount": 100}])]
        output = {
            "headline": "結論：2025-03 毛利最高的是 A。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "",
        }

        validation = self._validate(output, contracts=contracts, canonical={"task_family": "metric_lookup", "metric": "revenue_amount"})

        self.assertFalse(validation["valid"])
        self.assertIn("metric_violation", ",".join(validation["violations"]))

    def test_percent_formatting_from_ratio_passes(self) -> None:
        contracts = [self._contract(metric="inventory_amount", rows=[{"change_pct": 0.5586758007567629}])]
        output = {
            "headline": "結論：變化率為 55.87%。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "",
        }

        validation = self._validate(output, contracts=contracts, canonical={"task_family": "period_pair_compare", "metric": "inventory_amount"})

        self.assertTrue(validation["valid"], validation)

    def test_rounded_large_number_passes(self) -> None:
        contracts = [self._contract(metric="inventory_amount", rows=[{"value": 34414943688.651}])]
        output = {
            "headline": "結論：庫存金額為 34,414,943,689。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "",
        }

        validation = self._validate(output, contracts=contracts, canonical={"task_family": "metric_lookup", "metric": "inventory_amount"})

        self.assertTrue(validation["valid"], validation)

    def test_unknown_number_rejected(self) -> None:
        contracts = [self._contract(metric="inventory_amount", rows=[{"value": 34414943688.651}])]
        output = {
            "headline": "結論：庫存金額另有 999,999,999。",
            "key_observations": [],
            "limitations": [],
            "table_caption": "",
            "confidence_note": "",
        }

        validation = self._validate(output, contracts=contracts, canonical={"task_family": "metric_lookup", "metric": "inventory_amount"})

        self.assertFalse(validation["valid"])
        self.assertIn("number_not_in_evidence", ",".join(validation["violations"]))


if __name__ == "__main__":
    unittest.main()
