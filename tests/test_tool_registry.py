from __future__ import annotations

import unittest

from tool_registry import get_tool_contract, is_tool_allowed_for_task, tool_registry_payload, validate_tool_args_against_registry


class ToolRegistryTest(unittest.TestCase):
    def test_entity_month_table_allowed_for_month_table_lookup(self) -> None:
        self.assertTrue(is_tool_allowed_for_task("get_entity_month_table", "entity_month_table_lookup"))

    def test_entity_time_series_allowed_for_entity_time_series(self) -> None:
        self.assertTrue(is_tool_allowed_for_task("get_entity_time_series", "entity_time_series"))

    def test_legacy_platform_ratios_has_replacement(self) -> None:
        contract = get_tool_contract("get_platform_ratios")

        self.assertTrue(contract.is_legacy)
        self.assertIsNotNone(contract.replacement_tool)
        self.assertIn("get_", contract.replacement_tool or "")

    def test_registry_payload_contains_contract_fields(self) -> None:
        payload = tool_registry_payload()

        self.assertIn("get_entity_month_table", payload)
        self.assertEqual(payload["get_entity_month_table"]["output_evidence_type"], "entity_month_table")
        self.assertFalse(payload["get_entity_month_table"]["is_legacy"])

    def test_overall_dimension_accepted_for_supported_period_pair_tool(self) -> None:
        contract = get_tool_contract("get_period_pair_metric_comparison")

        self.assertIn("overall", contract.supported_entity_dimensions)
        self.assertTrue(is_tool_allowed_for_task("get_period_pair_metric_comparison", "period_pair_compare"))
        ok, error = validate_tool_args_against_registry(
            "get_period_pair_metric_comparison",
            {"metric": "revenue", "period_a": "2025-12", "period_b": "2026-01", "dimension": "overall"},
            enforce_required=True,
        )
        self.assertTrue(ok, error)

    def test_overall_time_series_declares_overall_dimension(self) -> None:
        contract = get_tool_contract("get_overall_time_series")

        self.assertEqual(contract.supported_entity_dimensions, ("overall",))


if __name__ == "__main__":
    unittest.main()
