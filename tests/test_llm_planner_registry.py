from __future__ import annotations

import unittest

from llm_planner import ALLOWED_TOOL_REGISTRY, LLMToolPlanner, allowed_tools_registry_payload
from tool_registry import build_allowed_tool_names_for_task_family, build_llm_allowed_tools_from_registry, validate_tool_args_against_registry


class LLMPlannerRegistryTest(unittest.TestCase):
    def test_allowed_tools_can_be_generated_from_tool_registry(self) -> None:
        generated = build_llm_allowed_tools_from_registry(["get_entity_month_table", "get_entity_time_series"])

        self.assertIn("get_entity_month_table", generated)
        self.assertIn("get_entity_time_series", generated)
        self.assertEqual(generated["get_entity_month_table"].output_evidence_type, "entity_month_table")


    def test_allowed_tools_generated_from_registry_for_task_family(self) -> None:
        allowed = build_allowed_tool_names_for_task_family("entity_month_table_lookup")

        self.assertIn("get_entity_month_table", allowed)
        self.assertNotIn("get_entity_period_pair_comparison", allowed)
        self.assertNotIn("get_platform_ratios", allowed)

    def test_llm_planner_allowed_registry_uses_tool_registry_contracts(self) -> None:
        payload = allowed_tools_registry_payload()

        self.assertIn("get_entity_month_table", ALLOWED_TOOL_REGISTRY)
        self.assertIn("get_entity_month_table", payload)
        self.assertIn("inventory_amount", payload["get_entity_month_table"]["allowed_metrics"])
        self.assertIn("product_line_5", payload["get_entity_month_table"]["allowed_dimensions"])

    def test_validate_tool_args_against_registry_accepts_valid_args(self) -> None:
        ok, error = validate_tool_args_against_registry(
            "get_entity_month_table",
            {"entity_dimension": "product_line_5", "metric": "inventory_amount", "month": "2025-03"},
        )

        self.assertTrue(ok, error)

    def test_llm_planner_validation_rejects_invalid_args(self) -> None:
        with self.assertRaises(ValueError):
            LLMToolPlanner._validate_tool_args(
                "get_entity_month_table",
                {"entity_dimension": "product_line_5", "metric": "inventory_amount", "month": "2025-03", "foo": "bar"},
            )


if __name__ == "__main__":
    unittest.main()
