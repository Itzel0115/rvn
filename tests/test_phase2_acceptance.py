from __future__ import annotations

import unittest

from answer_plan import AnswerPlan
from semantic_layer import get_catalog
from semantic_layer.adapters import enrich_answer_plan
from semantic_layer.validation import validate_catalog
from tool_registry import TOOL_REGISTRY

class Phase2AcceptanceTest(unittest.TestCase):
    def test_catalog_has_controlled_coverage_for_every_known_task(self) -> None:
        catalog = get_catalog()
        self.assertEqual(validate_catalog(catalog)["errors"], [])
        coverage = {item.task_type: item for item in catalog.list_task_coverage()}
        self.assertTrue(coverage)
        for requirement in catalog.list_task_requirements():
            self.assertEqual(coverage[requirement.task_type].runtime_path, "semantic")
        self.assertFalse([item for item in coverage.values() if item.coverage_status == "missing"])

    def test_semantic_plan_keeps_required_limitation_concise(self) -> None:
        canonical = type("Canonical", (), {"task_family":"performance_assessment"})()
        plan = enrich_answer_plan(AnswerPlan(primary_tools=["get_entity_performance_snapshot"]), canonical)
        self.assertEqual(plan.semantic_requirement_id, "req.performance_assessment.v1")
        self.assertIn("proxy", " ".join(plan.required_limitations).lower())

    def test_mcp_allowlist_equals_low_risk_registry_contracts(self) -> None:
        actual = {item.mcp_name or item.tool_name for item in TOOL_REGISTRY.values() if item.mcp_exposable}
        expected = {"get_entity_month_table", "get_entity_metric_ranking", "get_entity_performance_snapshot", "get_overall_time_series", "get_revenue_inventory_relationship", "get_data_coverage"}
        self.assertEqual(actual, expected)
